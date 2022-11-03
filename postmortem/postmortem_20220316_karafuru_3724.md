# PnL
2022-03-15 12:48:25 UTC: bought 2.6 eth. https://etherscan.io/tx/0x077ac4aaf4cb4e54708e8daba0b5ee175aba747fa2981823d6a67b2c5cc8dcf1 \
2022-03-16 12:18:27 UTC: sold 2.87 weth. https://etherscan.io/tx/0x55d36e4a27e1d6fe80c01620783b9b2c4aac18ee4d9c1975216f20b9d64f039e \
**PnL after fees: 0.04 eth**

# Pricing

| token_id | name | date | time_est | rarity | theo | price | edge | edge_ratio | global_floor | price_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3724 | egao #3724 | 2022-03-15 | 2022-03-15 08:48:25 | 3724 | 3.7 | 2.6 | 0.393 | 11 | 2.8 | 0.92 |

First trade using OTM and ITM fudge components in required edge. ITM fudge had a weird discontinuity due to flooring logic. Would jump to a huge edge ratio like 10-20 if price_ratio < 0.88.

# ITM Fudge Factor

Change ITM fudge edge component to a fudge factor between 0-100% that shrinks the RSS of the other components, rather than include it in the RSS. Full logic in required edge spec: [required_edge.md](../specs/required_edge.md).

Sensitivity of edge_ratio to price_ratio using new ITM fudge factor logic:

| token_id | name | date | theo | price | edge | global_rarity | lvl | nxt_lvl_diff | lvl_1 | lvl_2 | floor_price | price_ratio | floor_price_ratio_edge | global_rarity_edge | rarest_trait_depth_edge | rarest_trait_liquidity_edge | rss_core_comp | itm_fudge_edge | itm_fudge_edge_floored | otm_fudge_edge | sum_required_edge | rss_requred_edge | sum_edge_ratio | rss_edge_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3724 | egao #3724 | 2022-03-15 | 3.7 | 2.8 | 0.321 | 0.0058 | 1 | 1 | 3.6 | 4.15 | 2.8 | 1 | 0.1000 | 0.0058 | 0 | 0.1030 | 0.1436481864 | 1 | 0.1436481864 | 0 | 0.3524 | 0.1436 | 0.9121 | 2.2376 |
| 3724 | egao #3724 | 2022-03-15 | 3.7 | 2.6 | 0.393 | 0.0058 | 1 | 1 | 3.6 | 4.15 | 2.8 | 0.9285714286 | 0.0929 | 0.0058 | 0 | 0.1030 | 0.1387704955 | 0.7468405154 | 0.1036394284 | 0 | 0.3053 | 0.1036 | 1.2870 | 3.7906 |
| 3724 | egao #3724 | 2022-03-15 | 3.7 | 2.5 | 0.429 | 0.0058 | 1 | 1 | 3.6 | 4.15 | 2.8 | 0.8928571429 | 0.0893 | 0.0058 | 0 | 0.1030 | 0.1364065256 | 0.6449358304 | 0.08797345584 | 0 | 0.2860 | 0.0880 | 1.4984 | 4.8716 |
| 3724 | egao #3724 | 2022-03-15 | 3.7 | 2.4 | 0.464 | 0.0058 | 1 | 1 | 3.6 | 4.15 | 2.8 | 0.8571428571 | 0.0857 | 0.0058 | 0 | 0.1030 | 0.1340960112 | 0.5565969112 | 0.07463742563 | 0 | 0.2691 | 0.0746 | 1.7252 | 6.2205 |
| 3724 | egao #3724 | 2022-03-15 | 3.7 | 2.3 | 0.500 | 0.0058 | 1 | 1 | 3.6 | 4.15 | 2.8 | 0.8214285714 | 0.0821 | 0.0058 | 0 | 0.1030 | 0.1318417628 | 0.4800178543 | 0.0632864001 | 0 | 0.2542 | 0.0633 | 1.9670 | 7.9006 |

## Fix

https://github.com/alandu20/NFT/commit/a629ba1caef699f94d5e68be6c453d9fdee40e60