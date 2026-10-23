# FlapJax Receipt Relay Q41 - independent audit

An audit of the FlapJax 14-day buyback, program days 2026-10-09 through 2026-10-22, built
entirely from public BSC JSON-RPC reads.

**Read it at:** https://cian-spider.github.io/flapjax-q41-audit/

## Result

- **13 buyback swaps**, one on each of 13 program days, spending **0.130000 BNB** for
  **307,853,198.1225 FLAPJAX**.
- **Never sold FLAPJAX into the pool:** 0 transfers from the treasury to the pool across the
  whole window.
- **R1 kept** (every buy exactly 0.01 BNB), **R2 kept** (buy-only), **R3 kept** (max one buy per
  COT day), **R4 kept** (never left under the 0.025 BNB floor).
- **One program day was missed: 2026-10-15**, and the announced skip condition did not apply.
  The treasury held 0.106941 BNB at the start of that COT day, about four times the floor. That
  is the single finding: a shortfall against the announcement that no announced rule explains.

## The current pipeline

These four files produce every number on the page. They are the ones to run.

```bash
python3 q41_audit.py    # window, decimals, pool identity
python3 q41_logs.py     # full-window log census
python3 q41_enrich.py   # per-swap pool price and treasury balance
python3 render.py       # index.html and audit.md, from the JSON above
```

Raw chain reads are committed under `data/`:

| file | contents |
|---|---|
| `data/q41_swaps.json` | every PancakeSwap V3 swap on the pool with the treasury as recipient |
| `data/q41_buys.json` | the 13 buys, with pool price before each and treasury balance before each |
| `data/q41_logs.json` | full-window FLAPJAX transfer census and WBNB transfers touching the treasury |
| `data/q41_r2.json` | the sell check: treasury to pool FLAPJAX transfer count |
| `data/q41_balances.json` | treasury BNB at the start of each program day |

`flapjax_q41_audit.py` and `q41_render.py` are an earlier, superseded pass that covered
2026-10-09 to 2026-10-21 only, so it counted 12 buys and stopped before the last program day.
They are kept for provenance. The 14-day figures above come from the four-file pipeline.

## Two things worth knowing before trusting any such audit

1. **PancakeSwap V3 is not Uniswap V3.** The `Swap` event signature is the same, but topic0 is
   `0x19b47279...` on PancakeSwap, not `0xc42079f9...`. Querying a PancakeSwap pool with the
   Uniswap hash returns **zero logs**, which reads as a clean bill of health and is completely
   wrong.
2. **Check the scan window against a nonce.** A zero result that contradicts a moving nonce is a
   broken query, not a finding. The treasury's nonce moved 30 to 376 across this window, which is
   what prompted re-deriving the topic and the block range rather than accepting the first zero.

## Addresses

| role | address |
|---|---|
| treasury | `0x7C34E9e21eE28A49Ff0b84B61774119E6633359f` |
| pool | `0xcA93EC685b8623688E6B236f9068034B298c2150` |
| FLAPJAX | `0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df` |
| WBNB | `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` |

Auditor: `cian-spider`, BSC wallet `0x7373E88368378052EB5a449d2eBC95aD7E5f2bEF`.
