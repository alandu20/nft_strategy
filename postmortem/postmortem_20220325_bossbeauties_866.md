# PnL
2022-03-26 02:42:08 UTC: bought 1.3 eth. https://etherscan.io/tx/0x09eec56d381303d0b8118509b0a93b6516b3340a8e89e95f4a9f74a996d32609 \

# Pricing

| token_id | name | date | time_est | rarity | theo | price | edge | edge_ratio | rarest_trait | coeff | global_rarity | lvl | nxt_lvl_diff | lvl_1 | lvl_2 | lvl_3 | lvl_4 | lvl_5 | floor_price |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 866 | boss beauties #866 | 2022-03-25 | 2022-03-25 22:41:37 | 3357 | 2.5789999999999997 | 1.3 | 0.825 | 7.675 | flair_crown | 0.47 | 0.006999999999999999 | 1 | 0.23 | 1.3 | 1.53 | 1.599 | 1.62 | 1.65 |

OS displayed global floor was 1.55.

# Whale Observation

Whale https://opensea.io/0x2e90606D7c5F13BbaBD54188c9c84f58Ab400570 (jtyler), holder of ~125 BBs, started listing en masse within last 12 hours or so. Has done so in waves over last couple months. Interestingly also occasionally buys, e.g. bought 5844 from me on 2022-03-25. Perhaps should take into account whale suppressing price somehow. Probably most effective way is just to increase edge_mult

# Required edge trait parsing bug

Levels are wrong, should have been [1.3, 3.59, 3.95, 7, 7]. Bug is due to "string contains" logic. "Flair" trait category has multiple traits containing substring "crown": "Flower Crown", "Crown", "Surfer Crown". "Flower Crown" is in group_traits, which is the source of the incorrect levels used. Only levels for "Crown" should be used. Even removing "Flower Crown" from group_traits did not work, since the levels for "Flower Crown" individually (not including others in the group) would be used.

## Fix

https://github.com/alandu20/NFT/commit/3e84c341f115507f0272d1dfbb613cf5b6adde18