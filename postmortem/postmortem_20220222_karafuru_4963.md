# PnL
2022-02-22 21:51:09 UTC: bought 4.2 weth. https://etherscan.io/tx/0x2cd81fd6d0826a45e78c40b43f07e275baa124860885964cb8e4a54949856baa \
2022-02-23 01:10:30 UTC: sold 5.5 eth. https://etherscan.io/tx/0x22dfc0e610a1b4358d5fab155d123d7ec795ed4122df56dab9c2d6ec9e59c9ff \
**PnL after fees: 0.86 eth**

# Pricing

| token_id | name | date | time_est | rarity | theo | price | edge | edge_ratio | description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4963 | ku'roi #4963 | 2022-02-22 | 2022-02-22 11:55:28 | 107 | 8.739 | 6.5 | 0.759 | 3.427 | passed earlier in day |
| 4963 | ku'roi #4963 | 2022-02-22 | 2022-02-22 16:00:16 | 107 | 8.519 | 5.0 | 1.218 | 6.934 | pricing for listed price of 5.0 around time of 4.2 weth offer |
| 4963 | ku'roi #4963 | 2022-02-22 | 2022-02-22 17:11:30 | 107 | 7.866 | 5.5 | 0.867 | 4.277 | pricing around time of sale |

4.2 weth fill was for edge=1.8259, the highest edge ever perceived for karafuru collection, per [analysis/karafuru/karafuru_edge_all_sales_20220223.csv](karafuru_edge_all_sales_20220223.csv).

Got away with it here but need a "deeps" liquidity factor that increases required edge (potentially exponentially) when the price is past a certain factor of the global floor. Number of recent sales could be an input too (i.e. need more edge for deeps but if there's a lot of trading then can relax the increase in edge requirement). Almost all of the high edge_ratio opportunities have been deeps, suggesting the existing rarest_trait_depth_edge is not doing enough. EDIT: 2022-03-14 added OTM fudge component into required edge. New required edge at 5.5 is 3.72 (versus 4.277).

Maybe also need to find "optimal" price to list at. Surprisingly someone bought within 4 hours with very little market activity (only 6 other trades on OS before the sale). EDIT: 2022-03-09 new philosophy is to flip within a day or two, even if at loss, to avoid negative selection (letting losers run and cutting off winners).

# Required edge prep bug in get_rarest_trait_levels

## Bug description
When using fast mode or price_single_asset, the listing at hand is supposed to be included in the order book used for required edge calc. The existing logic was appending the new listed price to the end of the list of saved listed prices and then sorting via .sort(). But this fails to sort lists with NaNs (https://stackoverflow.com/questions/18062697/each-time-i-sort-a-list-of-floats-which-has-nan-values-i-get-a-different-list). In fact it appears the list is simply not changed, and the existing logic drops the last element in the list. So for rare traits with a thin order book (less than max_price_level=8 levels), the new listed price was ignored.

## Using price_single_asset to price 5.5 offer

| token_id | name | rarity | theo | price | edge | edge_ratio | rarest_trait | coeff | global_rarity | lvl | nxt_lvl_diff | lvl_1 | lvl_2 | lvl_3 | lvl_4 | lvl_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4963 | ku'roi #4963 | 107 | 7.865 | 5.5 | 0.866 | 0.893 | mouth_gold teeth | 1.096 | 0.005 | 10 | 0 | 5.0 | 8.888 | 9.99 | 12.0 | 20.0 |

| feature | coefficient |
| --- | --- |
| const | 1.1246 |
| background_beach | 0 |
| base_ku'roi | 0.2319 |
| eyes_wide open | 0 |
| headgear_horns | 0 |
| mouth_gold teeth | 1.0958 |
| outfit_ghost | 0.2105 |
| skin_mecha | 0.2182 |
| **SUM** | **2.881** |

global floor: 2.73 \
theo = 2.8810 * 2.73 = 7.865 \
listed price_ratio = 5.5 / 2.73 = 2.01465 \
predicted price_ratio = 2.8810 \
edge = 2.8810 - 2.01465 = 0.866 \
edge_ratio = 0.893, so required_edge = 0.866 / 0.893 = 0.97

Notice lvl = 10, the default value lvl is set to when the price is not found in the order book.

## Using price_single_asset to price 5.0 offer:

| token_id | name | rarity | theo | price | edge | edge_ratio | rarest_trait | coeff | global_rarity | lvl | nxt_lvl_diff | lvl_1 | lvl_2 | lvl_3 | lvl_4 | lvl_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4963 | ku'roi #4963 | 107 | 8.079 | 5.0 | 1.128 | 6.045 | mouth_gold teeth | 1.132 | 0.005 | 1 | 3.888 | 5.0 | 8.888 | 9.99 | 12.0 | 20.0 |

| feature | coefficient |
| --- | --- |
| const | 1.1215 |
| background_beach | 0.113 |
| base_ku'roi | 0.1319 |
| eyes_wide open | 0 |
| headgear_horns | 0 |
| mouth_gold teeth | 1.1317 |
| outfit_ghost | 0.2345 |
| skin_mecha | 0.2269 |
| **SUM** | **2.9595** |

global floor: 2.73 \
theo = 2.9595 * 2.73 = 8.079 \
listed price_ratio = 5.0 / 2.73 = 1.8315 \
predicted price_ratio = 2.9595 \
edge = 2.9595 - 1.8315 = 1.128 \
edge_ratio = 6.045, so required_edge = 1.128 / 6.045 = 0.1866

Notice lvl = 1 because the price input (5.0) was the same as the last saved lvl_1.

## Fix
https://github.com/alandu20/NFT/commit/0dfdf5e5d99edb98f1aef4e0a4aa5f71f2f463a6#diff-1e26af61f1a3fb0e4d4c57138dd88cfd998b035d665c30c1844df99ed1d56f9eR841
