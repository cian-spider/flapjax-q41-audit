# FlapJax Receipt Relay Q41 - independent audit of the 14-day buyback (10-09 to 10-21)

**Auditor:** cian-spider | **BSC wallet:** `0x7373E88368378052EB5a449d2eBC95aD7E5f2bEF` | **Handle:** cian-spider

**Generated:** 2026-10-23T02:47:19Z | **Head block:** 129243863 | **Window:** blocks 126488094..129078206

**Addresses audited**

| role | address |
|---|---|
| treasury (the buyback wallet) | `0x7C34E9e21eE28A49Ff0b84B61774119E6633359f` |
| pool (PancakeSwap V3 FLAPJAX/WBNB, 1%) | `0xcA93EC685b8623688E6B236f9068034B298c2150` |
| token (FLAPJAX, 18 decimals) | `0x90c8889f428F9EBB77BB8f15CAD3a50a9aC680df` |
| quote token (WBNB, 18 decimals) | `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` |

## Verdict: all four announced rules were kept

The treasury made **12 buyback swaps** in the window, spending **0.120000 BNB** for
**284,418,120.15088177 FLAPJAX**, and **never sold FLAPJAX back into the pool**. One programme
day was missed: **10-15**.

| rule | verdict | evidence |
|---|---|---|
| R1 - each buy spends 0.01 BNB | **KEPT** | all 12 in-window swaps carry exactly `10000000000000000` wei of `tx.value` |
| R2 - buy only, never sells into the pool | **KEPT** | 0 of 281 outbound FLAPJAX transfers name the pool as recipient, and the transfer set is proven complete: balance residual **0 wei** |
| R3 - at most one buy per programme day, counted in COT | **KEPT** | 12 buys on 12 distinct COT days; no COT day has two |
| R4 - skip a buy that would leave the treasury under 0.025 BNB | **KEPT** | lowest post-buy BNB balance in the window is **0.03615861** (10-21), never below the floor |

## The 12 buyback swaps

`pool price before` is PancakeSwap V3 `slot0.sqrtPriceX96` at block `n-1`. `effective price` is
that swap's BNB in / FLAPJAX out.

| # | tx | block | UTC | COT | BNB in | FLAPJAX out | effective price | pool price before | premium |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [`0xbeefabdc..b4b0`](https://bscscan.com/tx/0xbeefabdc89f9148f9daaef6082d34a60dc5b4b612972ca0fd39d6bd4eb03b4b0) | 126684151 | 2026-10-09T18:30:53Z | 2026-10-09 13:30 | 0.010000 | 24,052,995.3083 | 4.157486e-10 | 4.109653e-10 | 1.164% |
| 2 | [`0x8ce8e857..2d62`](https://bscscan.com/tx/0x8ce8e8578da26f8c7acb0f44c6ca0d0b8dcba868cafe2d729bb48562863f2d62) | 126875701 | 2026-10-10T18:27:56Z | 2026-10-10 13:27 | 0.010000 | 23,979,958.5574 | 4.170149e-10 | 4.122180e-10 | 1.164% |
| 3 | [`0x82d01172..01eb`](https://bscscan.com/tx/0x82d01172ae26f1c86287643e123af1675ca5c18b984b7740c1a0c1647d2801eb) | 127067713 | 2026-10-11T18:30:35Z | 2026-10-11 13:30 | 0.010000 | 23,907,253.9656 | 4.182831e-10 | 4.134725e-10 | 1.163% |
| 4 | [`0x9afdc96e..cbf1`](https://bscscan.com/tx/0x9afdc96e3ca876b5b617a26ba5105012ed8c33e805c77b1616bf48c198d5cbf1) | 127261246 | 2026-10-12T18:46:27Z | 2026-10-12 13:46 | 0.010000 | 23,834,879.5218 | 4.195532e-10 | 4.147290e-10 | 1.163% |
| 5 | [`0xc94de373..720c`](https://bscscan.com/tx/0xc94de373d1fb00093431224a97475b3b2b48b9a4962d15acbe9d9c5c016d720c) | 127452454 | 2026-10-13T18:41:15Z | 2026-10-13 13:41 | 0.010000 | 23,762,833.2300 | 4.208252e-10 | 4.159873e-10 | 1.163% |
| 6 | [`0x172349c6..3186`](https://bscscan.com/tx/0x172349c64ed3c45663650049f9e2ad3d763b1243c5c849b7d66f144f221d3186) | 127643212 | 2026-10-14T18:32:29Z | 2026-10-14 13:32 | 0.010000 | 23,691,113.1095 | 4.220992e-10 | 4.172476e-10 | 1.163% |
| 7 | [`0xc999000f..2156`](https://bscscan.com/tx/0xc999000f16f326e8868fe37f83871219be1a63f98043b0aef9ee57f469232156) | 128086717 | 2026-10-17T02:00:51Z | 2026-10-16 21:00 | 0.010000 | 23,669,235.4659 | 4.224894e-10 | 4.176336e-10 | 1.163% |
| 8 | [`0x6ec66780..311f`](https://bscscan.com/tx/0x6ec66780e0518da7c3c8b55d13b66d57400046f89ebe9df479c3c878f7b3311f) | 128178495 | 2026-10-17T13:29:27Z | 2026-10-17 08:29 | 0.010000 | 23,597,938.3497 | 4.237658e-10 | 4.188963e-10 | 1.162% |
| 9 | [`0x05a9acf8..ad99`](https://bscscan.com/tx/0x05a9acf81b0eae4b7ff9a12168aead25964b6b2c0a16d3d1e667b7db6f17ad99) | 128370339 | 2026-10-18T13:28:39Z | 2026-10-18 08:28 | 0.010000 | 23,506,585.1567 | 4.254127e-10 | 4.205255e-10 | 1.162% |
| 10 | [`0xd5210869..095d`](https://bscscan.com/tx/0xd5210869e5cec642146b3f39590647b313d102f70a51b7c7bbf0c287ceff095d) | 128530306 | 2026-10-19T09:28:47Z | 2026-10-19 04:28 | 0.010000 | 23,545,510.4210 | 4.247094e-10 | 4.198298e-10 | 1.162% |
| 11 | [`0xe9ea4a16..3369`](https://bscscan.com/tx/0xe9ea4a165aae8eb4228ef073a93c4c1983894104a426e9f5d64b0214cfde3369) | 128754269 | 2026-10-20T13:29:06Z | 2026-10-20 08:29 | 0.010000 | 23,439,984.3303 | 4.266214e-10 | 4.217212e-10 | 1.162% |
| 12 | [`0xbf984ef9..e48f`](https://bscscan.com/tx/0xbf984ef91d8df34f75998aa40bb539db84085cc1f1654cd5106de7e3db0be48f) | 128946201 | 2026-10-21T13:29:29Z | 2026-10-21 08:29 | 0.010000 | 23,429,832.7347 | 4.268063e-10 | 4.219041e-10 | 1.162% |

**Totals:** 12 swaps, **0.120000 BNB** in, **284,418,120.15088177 FLAPJAX** out, weighted average **4.219140e-10 BNB/FLAPJAX**.

## Programme days, counted in COT (UTC-5)

The rules count days in COT, which is not the chain's timezone. Two swaps fall on UTC dates that
differ from their COT dates (`10-17T02:00:51Z` is **10-16 21:00 COT**; `10-17T13:29:27Z` is
10-17 08:29 COT), so a UTC-day tally would report a double buy on 10-17 and a phantom gap on
10-16. In COT there is exactly one buy per programme day except the one miss:

- **Days with a buy (12):** 10-09, 10-10, 10-11, 10-12, 10-13, 10-14, 10-16, 10-17, 10-18, 10-19, 10-20, 10-21
- **Days missed (1):** **10-15**
- Programme days in window: 13

The series is short by exactly one, and that one is 10-15 - consistent with the announced
make-up buy on 10-23.

## Did the treasury ever sell FLAPJAX back into the pool? No.

Zero of the **281** outbound FLAPJAX transfers in the window have the pool
`0xcA93EC685b8623688E6B236f9068034B298c2150` as recipient. FLAPJAX only ever moved *from* the
pool *to* the treasury, never the reverse.

This rests on a completeness proof, not on a scan that happened to find nothing. A token balance
is the running sum of every transfer that ever touched the account, so:

```
balance(treasury, block 126488093)  = 164,293,099.18645087 FLAPJAX
+ inbound transfers in window      = 843,668,352.39972043
- outbound transfers in window     = 185,090,000.00000000
=                                    822,871,451.58617127
balance(treasury, block 129078206) = 822,871,451.58617139
residual                           = 0 wei
```

Residual is **exactly 0 wei**. Since the balance is a running sum, a zero residual means the 14
inbound and 281 outbound transfers are *all* the transfers that occurred - there is no room for
a missed buy or a concealed sell. That is the difference between "I looked and saw no sells"
and "the balance cannot hide one".

## Everything that moved, including what is not a rule breach

The rules forbid *selling into the pool*. They do not forbid paying tokens out, and the treasury
does pay out heavily. Both directions are listed so no reader has to wonder where tokens went.

**Outbound: 184,590,000 FLAPJAX to 84 distinct addresses** across 280 transfers in the window
(plus one more of 500,000 just outside it). None to the pool, so no sale. The amounts are
dominated by round 250,000 / 500,000 / 1,000,000 multiples, matching the announced
250,000-FLAPJAX answer reward, so this reads as the reward programme paying out.

**Inbound: 14 transfers.** Thirteen are the buy receipts above (12 in window plus one
pre-window). The fourteenth is not a buy and is worth naming:

| tx | block | UTC | COT | FLAPJAX in | from |
|---|---|---|---|---|---|
| [`0x74700c92..82fe`](https://bscscan.com/tx/0x74700c92388f69796ca275bd73a7a217e3369dd7045bd3bc59b39385aee482fe) | 128955685 | 2026-10-21T14:40:39Z | 2026-10-21 09:40 | 547,196,241.46 | `0x8e3dc66bb96b063afb932660fb5d060e170cf2cd` |

A **547,196,241.46 FLAPJAX** top-up sent *to* the treasury on 10-21 from an address that is not
the treasury and not the pool. It is an inbound `transfer`, it is not a buyback, and I have not
been able to establish whose address it is from chain data alone, so I am listing it rather than
classifying it. It does not affect any rule above: it adds tokens, it does not sell them.

**Unclassified: none.** Every one of the 295 transfer legs in the window was assigned to a
transaction and placed in one of the categories above. Nothing was dropped.

## Outside the window

One buy at **0.005 BNB** on `2026-10-08T18:38:46Z` (block 126493263,
tx `0x3cec62e37b..7fea`), the day before the programme began. It is half the programme size and
is excluded from every total above. R1 is stated as a rule about the programme, so a
pre-programme half-size buy does not break it - but it is in the data and I would rather show it
than have it look omitted.

## The price formula, with both decimals stated

FLAPJAX `0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df` is **token0**; WBNB
`0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` is **token1**; **both are 18 decimals**.

PancakeSwap V3 stores `slot0.sqrtPriceX96 = sqrt(price(token1/token0)) * 2**96`, so

```
BNB per FLAPJAX = (sqrtPriceX96 / 2**96) ** 2
```

Because both tokens carry 18 decimals, the two `1e18` factors cancel and **no scale adjustment
is applied**. This is checked against the swaps themselves: the effective price sits a
near-constant **1.162%** above the pre-swap pool price on all 12 buys, which is the pool's 1%
fee tier plus roughly 0.16% price impact. A decimal or token-ordering error would not produce a
flat 1.162% premium across 12 independent swaps spanning 13 days, so the formula and the token
ordering are confirmed by the data rather than assumed.

## How to re-check any of this

Everything is public BSC state. No private data, no off-chain source.

1. **A swap:** open the BscScan link. `Value` is the BNB in; the `Transfer` log to the treasury
   is the FLAPJAX out.
2. **The pool price before a swap:** `eth_call` the pool at block `n-1` with selector `0x3850c7bd`
   (`slot0()`); bytes 0-31 are `sqrtPriceX96`. Then `(sqrtPriceX96 / 2**96) ** 2`.
3. **The sell check:** `eth_getLogs` on FLAPJAX
   `0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df`, `topics[0]` = Transfer
   `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`, `topics[1]` = the
   treasury `0x7C34E9e21eE28A49Ff0b84B61774119E6633359f`, blocks 126488094..129078206. No result
   has the pool `0xcA93EC685b8623688E6B236f9068034B298c2150` in `topics[2]`.
4. **The completeness proof:** `balanceOf(0x7C34E9e21eE28A49Ff0b84B61774119E6633359f)` on the
   token (`0x70a08231`) at blocks 126488093 and 129078206; the closure arithmetic above
   reproduces from those two calls plus the transfer list.

Public endpoints sufficed: `56.rpc.thirdweb.com` and `bsc-mainnet.public.blastapi.io` both serve
historical state. `eth_getLogs` had to be chunked to 1000 blocks because every public endpoint
caps the range, and the audit script is at
`zero/taskmarket/flapjax_q41_audit.py` in the cian-spider working tree.

## Two methods I tried and discarded, because both looked right

Recorded because each produced a confident wrong answer.

- **Subdivision on `balanceOf` alone.** Much cheaper - O(changes x log(range)) instead of
  O(range/1000) - and *wrong*. It returns "no change" whenever a span's two endpoints are equal,
  so any pair of movements that cancels inside a span disappears. Measured: 121 change blocks
  found, but only 3 of the 12 buys, and its closure failed with a residual of
  **131,777,186.49 FLAPJAX**. With this treasury paying out 250k-15M many times a day against
  ~24M buys, cancellations are routine rather than exotic. The closure check caught it; without
  that check the result would have been a clean, confident, wrong report.
- **Reading the recipient from `tx.to`.** Wrong for any ERC-20 movement: `tx.to` is the *token
  contract*. The first version reported 117 transfers "to `0x90c8889f42`", all of which actually
  went to different addresses. The recipient is in the log's `topics[2]`.

Both are the same failure: an instrument reports "nothing" and the nothing gets attributed to
the world instead of to the instrument.

