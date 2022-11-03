# Microprice

## Motivation
- Suppose book is [10, 10.1, 10.2, 10.3] when offer for 5 comes in. If asset is priced off global floor price of 5, then TV will be too low and will perceive little edge. Furthermore required edge will be too high since a higher price_ratio leads to a higher required edge. True global floor should be closer to 10, or even simply 10. Need concept of microprice
- One wrinkle is that global floor price from OS /collection endpoint sometimes lags listings. In this scenario, pricing and required edge use a global floor that is likely close to the "true" global floor that pricing and required edge should use (e.g. ~10 in example above). However a microprice provides a more accurate estimate
- Ideally should consider listing age in addition to price levels. Suppose book is [7, 10, 10.1, 10.2, 10.3]. It's natural to drop the first level and price off a global floor of ~10, since the price of 7 seems like an outlier. But the longer that level rests in the book, the more weight it should be given as a true level

## Microprice 1.0 [NOT IMPLEMENTED]

Only need this logic if OS displayed global floor keeps up with every new listing. As of 2022-03-25, it appears the displayed price always lags, so this is unnecessary at the moment.

	if newly listed price < OS displayed global floor:
	   microprice = OS displayed global floor

## Microprice 2.0 [IN DEVELOPMENT]

Data:
- Use saved listed prices from dynamic path, sorted by price, as source of orderbook
- Edge cases:
	- If listings have not been scraped from either dynamic or slow paths in a while, orderbook will be missing any listings since last run
	- Slow path overwrites dynamic listings file. If assets are listed during the slow path run, orderbook will be missing these, unless they are picked up by next dynamic path run. They will however be picked up in next slow path run

Input parameters:

	MP_MIN_SIZE = 4
	MP_MIN_TOP_LVL_PRICE_RATIO = 0.15 # TODO: inflection point should probably be smooth not step function
	MP_MAX_TOP_LVL_SZ = 1 # must be < MP_MIN_SIZE
	MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH = 0.05

Compute orderbook components:

	prices = prices at each level in orderbook, rounded to nearest 0.05
	szs = sizes at each level in orderbook
	lvl_at_min_size_depth = index of level where cumulative sum of szs is MP_MIN_SIZE

If first level size exceeds MP_MAX_TOP_LVL_SZ or first level price within MP_MAX_TOP_LVL_RATIO of second level, just use OS displayed global floor:

	if (1 - prices[1] / prices[2] <= MP_MIN_TOP_LVL_PRICE_RATIO) or (szs[1] > MP_MAX_TOP_LVL_SZ):
	   microprice = OS displayed global floor

If price at MP_MIN_SIZE depth is more than MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH away from second level, just use OS displayed global floor:

	if 1 - prices[2] / prices[lvl_at_min_size_depth] > MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH:
	   microprice = OS displayed global floor

Else compute size-weighted average microprice, capped at second level price:

	sum_szs = sum(szs[i] for i in 1:prices[lvl_at_min_size_depth])
	for i in 1:prices[lvl_at_min_size_depth]:
	   sz_wgts[i] = szs[i] / sum_szs
	   lvl_wgts[i] = prices[i] * sz_wgts[i]
	microprice = min(sum(lvl_wgts), prices[lvl_at_min_size_depth-1])

Sanity check microprice against OS displayed global floor price:

	MP_EDGE_TOO_GREAT = 0.2
	assert microprice is within MP_EDGE_TOO_GREAT of /collection endpoint global floor price

Substitute microprice for "global floor price" in pricing and required edge calculations.

### Examples

Input parameters:

	MP_MIN_SIZE = 4
	MP_MIN_TOP_LVL_PRICE_RATIO = 0.15
	MP_MAX_TOP_LVL_SZ = 1
	MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH = 0.05

#### Example: lvl_at_min_size_depth = 4

| price | size |
| --- | --- |
| 7 | 1 |
| 10 | 1 |
| 10.1 | 1 |
| 10.2 | 1 |

1 - prices[1] / prices[2] = 0.3 \
prices[lvl_at_min_size_depth] = 10.2 \
1 - prices[2] / prices[lvl_at_min_size_depth] = 0.02 \
microprice = 9.33

#### Example: lvl_at_min_size_depth = 3

| price | size |
| --- | --- |
| 7 | 1 |
| 10 | 2 |
| 10.1 | 1 |
| 10.2 | 1 |

1 - prices[1] / prices[2] = 0.3 \
prices[lvl_at_min_size_depth] = 10.1 (so 10.2 level ignored) \
1 - prices[2] / prices[lvl_at_min_size_depth] = 0.01 \
microprice = 9.28

#### Example: lvl_at_min_size_depth = 3 with large szs[3]

| price | size |
| --- | --- |
| 7 | 1 |
| 10 | 1 |
| 10.5 | 8 |

1 - prices[1] / prices[2] = 0.3 \
prices[lvl_at_min_size_depth] = 10.5 \
1 - prices[2] / prices[lvl_at_min_size_depth] = 0.048 \
sum(lvl_wgts) = 10.1 > prices[2] \
microprice = 10

#### Example: lvl_at_min_size_depth = 2

| price | size |
| --- | --- |
| 7 | 1 |
| 10 | 5 |

1 - prices[1] / prices[2] = 0.3 \
prices[lvl_at_min_size_depth] = 10 \
1 - prices[2] / prices[lvl_at_min_size_depth] = 0 \
microprice = 9.5

#### Example: sz[1] > 1

| price | size |
| --- | --- |
| 7 | 2 |
| 10 | 1 |
| 10.1 | 1 |
| 10.2 | 1 |

sz[1] = 2 > MP_MAX_TOP_LVL_SZ \
microprice = 7

#### Example: MP_MIN_TOP_LVL_PRICE_RATIO condition not satisfied

| price | size |
| --- | --- |
| 8.5 | 1 |
| 10 | 1 |
| 10.1 | 1 |
| 10.2 | 1 |

1 - prices[1] / prices[2] = 0.15 <= MP_MIN_TOP_LVL_PRICE_RATIO \
microprice = 9

#### Example: MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH condition not satisfied

| price | size |
| --- | --- |
| 7 | 1 |
| 10 | 1 |
| 12 | 1 |
| 14 | 1 |

1 - prices[1] / prices[2] = 0.3 \
prices[lvl_at_min_size_depth] = 14 \
1 - prices[2] / prices[lvl_at_min_size_depth] = 0.29 > MP_MAX_PRICE_RATIO_AT_MIN_SIZE_DEPTH \
microprice = 7
