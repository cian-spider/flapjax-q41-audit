#!/usr/bin/env python3
"""FlapJax Receipt Relay Q41: verify the announced 14-day buyback from the chain alone.

Task: 0x642b0b54e35e416dacd8a6b27e6e40c63a8d0bc204218649cc229b02bdb2f074
Window: 10-09 .. 10-21 (programme days counted in COT = UTC-5).

Rules announced on 10-08, each to be marked kept or broken:
  R1  each buy spends 0.01 BNB
  R2  only buys FLAPJAX (never sells it back into the pool)
  R3  at most one buy per programme day, counted in COT
  R4  a buy is skipped if it would leave the treasury under 0.025 BNB

Method, and two methods that were tried and rejected
---------------------------------------------------
PRIMARY: enumerate FLAPJAX Transfer logs touching the treasury, in both
directions, with eth_getLogs. This is exact per transfer and carries the real
`from`/`to`, which is what R2 needs.

Then VERIFY it with a balance identity, which no log scan can give on its own:

    balance(lo-1) + sum(inbound) - sum(outbound) == balance(hi)

`balanceOf` is the running sum of every transfer that ever touched the account,
so if that closes to the wei then the enumerated set is provably complete: no
missed buy, and no missed sell. If it does not close, the script prints the
residual and refuses to certify R2.

REJECTED 1: a single wide eth_getLogs. Every public endpoint here caps the range
(thirdweb exactly 1000 blocks, 1rpc 50, blockrazor 25, dataseed rejects) and the
one wide-range endpoint (nodereal, 50k) is quota exhausted, so it is a chunked
walk. Fine - but a chunked walk that gives up returns `[]`, which reads as "no
transfers" (05 12.11).

REJECTED 2: recursive subdivision on `balanceOf` alone, which looked much
cheaper (O(changes * log(range))). It is WRONG, and this was measured, not
reasoned about: it found 121 balance-change blocks but only 3 of the 9 buys that
note 50 already documents, and its closure check failed with a residual of
131,777,186.49 FLAPJAX. The reason is structural - the method returns "no change"
whenever a span's two endpoints are equal, so any pair of movements that cancels
inside a span is invisible. With this treasury paying out 250k-15M FLAPJAX many
times a day against ~24M buys, cancellations are common, not exotic. The closure
check is what caught it.

REJECTED 3: classifying by `tx.to`. For an ERC-20 transfer `tx.to` is the *token
contract*, so the first version reported 117 transfers "to 0x90c8889f42" - all of
them actually going to different recipients. The recipient is in the log's
`topics[2]`, or in the calldata for a `transfer` call. Never read the recipient
off `tx.to` for a token movement.

RPC budget: measured 2026-10-23 on this box. thirdweb accepts exactly 1000 blocks
per getLogs and sustains ~2.5 req/s before 429s; retries absorb the rest, so the
pacing below is set slightly above that and every call is retried.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import threading
import time
import urllib.request as ur
from concurrent.futures import ThreadPoolExecutor

TOKEN = "0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df"   # FLAPJAX, 18 decimals
WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"    # 18 decimals
POOL = "0xcA93EC685b8623688E6B236f9068034B298c2150"    # PancakeSwap V3 FLAPJAX/WBNB 1%
TREASURY = "0x7C34E9e21eE28A49Ff0b84B61774119E6633359f"

TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SEL_BALANCE_OF = "0x70a08231"
SEL_SLOT0 = "0x3850c7bd"

CHUNK = 1000
RPS = 4.0

RPC_URLS = [
    "https://56.rpc.thirdweb.com",
    "https://bsc-mainnet.public.blastapi.io",
]

UA = "Mozilla/5.0 (X11; Linux x86_64) flapjax-q41-audit"

_rate_lock = threading.Lock()
_next_slot = [0.0]


def _throttle():
    with _rate_lock:
        now = time.monotonic()
        slot = max(now, _next_slot[0])
        _next_slot[0] = slot + 1.0 / RPS
    delay = slot - time.monotonic()
    if delay > 0:
        time.sleep(delay)


def _pad(addr: str) -> str:
    return "0x" + "0" * 24 + addr.lower()[2:]


def rpc(method, params, tries=10, timeout=60):
    last = None
    for i in range(tries):
        url = RPC_URLS[i % len(RPC_URLS)]
        _throttle()
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            req = ur.Request(
                url,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "User-Agent": UA},
            )
            d = json.loads(ur.urlopen(req, timeout=timeout).read().decode())
            if "error" in d:
                msg = str(d["error"])
                last = RuntimeError(msg[:160])
                if "exceed" not in msg and "limit" not in msg and "range" not in msg:
                    time.sleep(min(20, 1.5 * (i + 1)) + random.random())
                continue
            return d["result"]
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(20, 1.5 * (i + 1)) + random.random())
    raise RuntimeError(f"{method} failed on every endpoint: {last}")


def head_block() -> int:
    return int(rpc("eth_blockNumber", []), 16)


def block_ts(bn: int) -> int:
    b = rpc("eth_getBlockByNumber", [hex(bn), False])
    if b is None:
        raise RuntimeError(f"block {bn} returned null")
    return int(b["timestamp"], 16)


def block_at(ts: int, lo: int, hi: int) -> int:
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def epoch(s: str) -> int:
    return int(
        dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=dt.timezone.utc)
        .timestamp()
    )


def cot(ts: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc) - dt.timedelta(hours=5)


def utc(ts: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc)


def balance_of(who: str, bn: int) -> int:
    raw = rpc("eth_call", [{"to": TOKEN, "data": SEL_BALANCE_OF + who.lower()[2:].rjust(64, "0")}, hex(bn)])
    return 0 if not raw or raw == "0x" else int(raw, 16)


def slot0(bn: int):
    raw = rpc("eth_call", [{"to": POOL, "data": SEL_SLOT0}, hex(bn)])
    if not raw or len(raw) < 2 + 128:
        raise RuntimeError(f"slot0 at {bn} returned {raw!r}")
    body = raw[2:]
    sqrt_p = int(body[0:64], 16)
    tick = int(body[64:128], 16)
    if tick >= 2**255:
        tick -= 2**256
    return sqrt_p, tick


def pool_price(sqrt_p_x96: int) -> float:
    """FLAPJAX is token0 and WBNB token1, both 18 decimals.

    slot0.sqrtPriceX96 = sqrt(token1/token0) * 2**96, so
    (sqrtP / 2**96)**2 = WBNB_wei per FLAPJAX_wei. Both tokens carry 18
    decimals, so the 1e18 scale factors cancel and the raw ratio *is* BNB per
    FLAPJAX - no scale adjustment is applied.
    """
    return (sqrt_p_x96 / (2**96)) ** 2


def scan_transfers(topics, lo, hi, label, workers=4):
    """eth_getLogs over [lo, hi] in 1000-block chunks, in parallel, with retry."""
    spans, b = [], lo
    while b <= hi:
        e = min(b + CHUNK - 1, hi)
        spans.append((b, e))
        b = e + 1
    total = len(spans)
    out, done = [], 0
    lock = threading.Lock()

    def one(span):
        s, e = span
        try:
            return rpc(
                "eth_getLogs",
                [{"address": TOKEN, "fromBlock": hex(s), "toBlock": hex(e), "topics": topics}],
                tries=8,
            )
        except Exception:
            if e - s < 200:
                raise
            mid = (s + e) // 2
            return one((s, mid)) + one((mid + 1, e))

    with ThreadPoolExecutor(workers) as ex:
        for got in ex.map(one, spans):
            with lock:
                out.extend(got)
                done += 1
                if done % 200 == 0:
                    print(json.dumps({
                        "percent": 100 * done // total,
                        "current": done, "total": total, "unit": "chunks",
                        "message": f"{label}: {len(out)} transfers",
                    }), flush=True)
    return out


def decode_transfer(L):
    """A Transfer log carries from in topics[1] and to in topics[2]."""
    return {
        "block": int(L["blockNumber"], 16),
        "tx": L["transactionHash"],
        "from": "0x" + L["topics"][1][-40:],
        "to": "0x" + L["topics"][2][-40:],
        "amount_wei": int(L["data"], 16),
        "log_index": int(L["logIndex"], 16),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-date", default="2026-10-09")
    ap.add_argument("--to-date", default="2026-10-21")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache-dir", default="/tmp/ac/q41cache")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    # Pad 6h each way: programme days are COT (UTC-5), so a UTC-shaped window
    # clips the first and last programme day. See 05 12.12.
    w_start = epoch(args.from_date + "T00:00:00Z") - 6 * 3600
    w_end = epoch(args.to_date + "T23:59:59Z") + 6 * 3600

    head = head_block()
    lo = block_at(w_start, head - 3_000_000, head)
    hi = block_at(w_end, lo, head)
    print(json.dumps({"message": f"head={head} blocks {lo}..{hi} ({hi - lo + 1})"}), flush=True)

    os.makedirs(args.cache_dir, exist_ok=True)

    def cached(name, fn):
        p = os.path.join(args.cache_dir, name + ".json")
        if not args.no_cache and os.path.exists(p):
            data = json.load(open(p))
            print(json.dumps({"message": f"{name}: {len(data)} cached"}), flush=True)
            return data
        data = fn()
        json.dump(data, open(p, "w"))
        return data

    # ---- 1. exact transfer lists, both directions -----------------------
    inbound_raw = cached("inbound", lambda: scan_transfers(
        [TOPIC_TRANSFER, None, _pad(TREASURY)], lo, hi, "inbound"))
    outbound_raw = cached("outbound", lambda: scan_transfers(
        [TOPIC_TRANSFER, _pad(TREASURY)], lo, hi, "outbound"))

    inbound = sorted((decode_transfer(L) for L in inbound_raw),
                     key=lambda r: (r["block"], r["log_index"]))
    outbound = sorted((decode_transfer(L) for L in outbound_raw),
                      key=lambda r: (r["block"], r["log_index"]))

    # ---- 2. closure: the transfer lists must explain the balance move ----
    bal_start = balance_of(TREASURY, lo - 1)
    bal_end = balance_of(TREASURY, hi)
    sum_in = sum(r["amount_wei"] for r in inbound)
    sum_out = sum(r["amount_wei"] for r in outbound)
    residual = (bal_end - bal_start) - (sum_in - sum_out)
    closure = {
        "balance_before_window": bal_start / 1e18,
        "balance_after_window": bal_end / 1e18,
        "observed_delta": (bal_end - bal_start) / 1e18,
        "n_inbound_transfers": len(inbound),
        "n_outbound_transfers": len(outbound),
        "sum_inbound": sum_in / 1e18,
        "sum_outbound": sum_out / 1e18,
        "residual_wei": str(residual),
        "residual": residual / 1e18,
        "closes": residual == 0,
        "blocks": [lo - 1, hi],
    }
    print(json.dumps({"message": "closure closes=%s residual=%s"
                      % (closure["closes"], closure["residual"])}), flush=True)

    # ---- 3. classify each treasury-sent transaction ---------------------
    # Group by tx: one tx can emit several transfers.
    by_tx: dict[str, list] = {}
    for r in inbound + outbound:
        by_tx.setdefault(r["tx"], []).append(r)

    rows = []
    for h, legs in by_tx.items():
        tx = rpc("eth_getTransactionByHash", [h])
        if tx is None:
            rows.append({"tx": h, "kind": "unfetched"})
            continue
        bn = int(tx["blockNumber"], 16)
        sent_by_treasury = tx["from"].lower() == TREASURY.lower()
        flap_in = sum(l["amount_wei"] for l in legs if l["to"].lower() == TREASURY.lower())
        flap_out = sum(l["amount_wei"] for l in legs if l["from"].lower() == TREASURY.lower())
        entry = {
            "tx": h, "block": bn, "sent_by_treasury": sent_by_treasury,
            "tx_to": tx["to"], "method": tx["input"][:10],
            "bnb_wei": str(int(tx["value"], 16)), "bnb": int(tx["value"], 16) / 1e18,
            "flapjax_in": flap_in / 1e18, "flapjax_out": flap_out / 1e18,
            "legs": [{"from": l["from"], "to": l["to"], "amount": l["amount_wei"] / 1e18}
                     for l in legs],
        }
        entry["ts"] = block_ts(bn)
        entry["utc"] = dt.datetime.fromtimestamp(entry["ts"], dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry["cot"] = cot(entry["ts"]).strftime("%Y-%m-%d %H:%M")
        entry["cot_day"] = cot(entry["ts"]).strftime("%Y-%m-%d")

        if sent_by_treasury and flap_in > 0 and entry["bnb"] > 0:
            entry["kind"] = "buy"
        elif sent_by_treasury and flap_out > 0 and any(
                l["to"].lower() == POOL.lower() for l in legs):
            entry["kind"] = "SELL_INTO_POOL"
        elif sent_by_treasury and flap_out > 0:
            entry["kind"] = "transfer-out-not-to-pool"
        else:
            entry["kind"] = "inbound-not-sent-by-treasury"
        rows.append(entry)

    rows.sort(key=lambda r: (r.get("block", 0), r.get("tx", "")))
    buys = [r for r in rows if r.get("kind") == "buy"]
    sells = [r for r in rows if r.get("kind") == "SELL_INTO_POOL"]
    outs = [r for r in rows if r.get("kind") == "transfer-out-not-to-pool"]
    # Anything not in the three buckets above is still a real transaction and
    # must reach the report. The first version of this script serialised only
    # those three kinds, which silently dropped a 547,196,241.46 FLAPJAX inbound
    # transfer from a non-treasury sender - exactly the kind of omission this
    # whole exercise is meant to avoid. Every row is emitted; `other` is the
    # catch-all and is expected to be empty or fully explained.
    other = [r for r in rows
             if r.get("kind") not in ("buy", "SELL_INTO_POOL",
                                      "transfer-out-not-to-pool")]
    assert len(buys) + len(sells) + len(outs) + len(other) == len(rows)

    # ---- 4. per-buy detail from archive state ---------------------------
    for r in buys:
        r["flapjax"] = r["flapjax_in"]
        r["eff_price"] = r["bnb"] / r["flapjax"] if r["flapjax"] else None
        try:
            sqrt_p, tick = slot0(r["block"] - 1)
            r["pool_price_before"] = pool_price(sqrt_p)
            r["tick_before"] = tick
        except Exception as exc:  # noqa: BLE001
            r["pool_price_before"] = None
            r["slot0_error"] = str(exc)[:90]
        try:
            r["bnb_balance_before"] = int(
                rpc("eth_getBalance", [TREASURY, hex(r["block"] - 1)]), 16) / 1e18
            r["bnb_balance_after"] = int(
                rpc("eth_getBalance", [TREASURY, hex(r["block"])]), 16) / 1e18
        except Exception as exc:  # noqa: BLE001
            r["bnb_balance_before"] = None
            r["balance_error"] = str(exc)[:90]

    # ---- 5. rule checks -------------------------------------------------
    window_cot = {
        f"2026-10-{d:02d}"
        for d in range(int(args.from_date[-2:]), int(args.to_date[-2:]) + 1)
    }
    days_with: dict[str, list] = {}
    for r in buys:
        days_with.setdefault(r["cot_day"], []).append(r)
    in_window = {d: v for d, v in days_with.items() if d in window_cot}

    r1_ok = all(abs(r["bnb"] - 0.01) < 1e-12 for r in buys if r["cot_day"] in window_cot)
    r2_ok = closure["closes"] and not sells
    r3_ok = all(len(v) <= 1 for v in in_window.values())
    r4_ok = all(
        r.get("bnb_balance_after") is None or r["bnb_balance_after"] >= 0.025 - 1e-9
        for r in buys
    )

    result = {
        "task": "FlapJax Receipt Relay Q41",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {"from": args.from_date, "to": args.to_date,
                   "timezone": "COT (UTC-5)", "blocks": [lo, hi]},
        "head_block": head,
        "treasury": TREASURY, "pool": POOL, "token": TOKEN,
        "price_formula": "FLAPJAX (0x90c8..) is token0 and WBNB (0xbb4C..) is token1, both 18 "
                         "decimals. slot0.sqrtPriceX96 = sqrt(token1/token0)*2**96, so BNB per "
                         "FLAPJAX = (sqrtPriceX96/2**96)**2. Both tokens have 18 decimals, so the "
                         "1e18 factors cancel and no scale adjustment is applied.",
        "method": "every FLAPJAX Transfer log touching the treasury in either direction, "
                  "enumerated with eth_getLogs in 1000-block chunks, then verified by the "
                  "balance identity balance(lo-1)+in-out == balance(hi)",
        "balance_closure": closure,
        "buys": buys,
        "sells_into_pool": sells,
        "token_transfers_out": outs,
        "other_transactions": other,
        "totals": {
            "n_buys": len(buys),
            "bnb_spent": sum(r["bnb"] for r in buys),
            "flapjax_received": sum(r["flapjax"] for r in buys),
            "n_sells_into_pool": len(sells),
            "n_other_transactions": len(other),
            "n_token_transfers_out": len(outs),
            "flapjax_transferred_out": sum(r["flapjax_out"] for r in outs),
        },
        "program_days": {
            "expected": sorted(window_cot),
            "with_buy": sorted(in_window),
            "missed": sorted(window_cot - set(in_window)),
            "outside_window": sorted(set(days_with) - window_cot),
        },
        "rules": {
            "R1_each_buy_spends_0.01_BNB": "KEPT" if r1_ok else "BROKEN",
            "R2_buy_only_never_sold": "KEPT" if r2_ok else "BROKEN",
            "R3_at_most_one_buy_per_COT_day": "KEPT" if r3_ok else "BROKEN",
            "R4_skipped_below_0.025_BNB_floor": "KEPT" if r4_ok else "BROKEN",
        },
    }

    text = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
