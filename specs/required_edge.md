# Required Edge

## Motivation
Consider two token_ids A and B, both have same price_ratio_diff (theoretical mispricing in units of price_ratio)
- A and B both offered at 10 (TVs are equal). Order book is 10,11,12 for rarest trait in A vs. 10,15,20 for rarest trait in B. Prefer buying B for 10 b/c can likely sell higher than A (arguably should be reflected in TV by taking deeper levels into account)
- A offered at 10, B offered at 15 (TVs differ). Order book is 10,11,12.1 for rarest trait in A vs. 15,16.5,18.15 for rarest trait in B (10% increase per level). Prefer buying A b/c less capital and closer to floor is more liquid

## Logic
Assume 4 orthogonal components estimate true/market required edge:
- floor_price_ratio_edge: prefer price closer to global floor (unless infinite capital)
- global_rarity_edge: prefer rarer trait
- rarest_trait_depth_edge: prefer first level for rarest trait
- rarest_trait_liquidity_edge: prefer difference with level behind to be high for rarest trait

Additional fudge components:
- otm_fudge_edge: require exponentially more edge if price is more than 75% above global floor price
- itm_fudge_factor: require less edge if price is below (filtered) global floor price, floored at 99% of rss of 4 core components

Calculate 4 core components:

	scaling_factor = 10
	floor_price_ratio_edge = price_ratio / scaling_factor
	global_rarity_edge = global_rarity of rarest trait
	rarest_trait_depth_edge = log(level in rarest trait order book) / scaling_factor
	rarest_trait_liquidity_edge = log(1 / (max(next_level_price_diff / global_floor_price, 0.0001))) / scaling_factor

Calculate OTM fudge edge component:

	f = 1.75
	otm_fudge_edge = exp(price_ratio - f) / scaling_factor if (price_ratio > f and edge > 0) else 0

Note *edge > 0* condition included because required_edge increases with out-of-the-moneyness, leading to negative edge_ratio close to 0 for listings with negative edge (these would be ranked higher than negative edge listings where price_ratio < f).

Calculate ITM fudge factor:
	k = 6
	itm_fudge_factor = (exp(k * price_ratio) - 1) / (exp(k) - 1) if price_ratio < 1 else 1

Note higher *k* -> steeper exponential. Always between 0 and 1. Reference: https://math.stackexchange.com/questions/297768/how-would-i-create-a-exponential-ramp-function-from-0-0-to-1-1-with-a-single-val

Calculate root sum of squares including fudge components:

	required_edge = sqrt(floor_price_ratio_edge^2 + global_rarity_edge^2 + rarest_trait_depth_edge^2 + rarest_trait_liquidity_edge^2 + otm_fudge_edge^2) * itm_fudge_factor

Edge Ratio

	edge_ratio = edge / required_edge

Opportunities are ranked in descending order by edge_ratio. Buy if edge_ratio > edge_ratio_trade_alert

## Edge Mult Tuning
Find optimal edge_mult (edge_ratio_trade_alert, i.e. minimum edge_ratio needed to trade) per collection based on historical marginal profitability analysis

Define:
- backtest_window: how many days of historical data to include
- profitability_metric: PnL for asset bought on day X and sold on day Y, if Y-X < trade_window, otherwise ignore
- optimal edge_mult: edge_mult where profitability_metric > 0 in cumulative profitability_metric vs edge_mult plot

Example:
- world-of-women-nft can be traded profitably down to edge_ratio ~0.5

![alt text](../analysis/world-of-women-nft/world-of-women-nft_cumul_pnl_zoom_20220219.png?raw=true)

- Histogram of PnL per flip

![alt text](../analysis/world-of-women-nft/world-of-women-nft_pnl.png?raw=true)

- Histogram of holding period per flip

![alt text](../analysis/world-of-women-nft/world-of-women-nft_holding_period.png?raw=true)