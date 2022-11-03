# Pricer

## Filtering
- Get all sales in ETH or WETH
- Remove sales prior to current date minus *days* input. Default 45 days. Note this default may be too low/high depending on liquidity conditions
- Remove obvious error sales:
	- Fat finger or WETH accepted offer well below global floor (defined in *data_warehouse/sales/ignore_sales*)
	- OS old listing loophole (list w/ no expiration->transfer to new wallet to avoid paying cancellation gas->transfer back to original wallet->submit cancel request->bot front runs in same block)
- Remove sales <1st percentile or >99.9th percentile. More aggressive on low end due to obvious error sales
- Remove price_ratio <0.1 or >50. Should primarily be data issues, if any
- If *pricer* input is OLS or LASSO:
	- Drop collection-specific ultra high value traits that are essentially outliers that can muddle pricing and strategies are priced out of. These two pricers are not as robust to outliers and are intended for pricing non-outlier assets
	- Remove price_ratio z-scores > zscore_cutoff_dict[collection], default set conservatively at 3, much higher for most collections

## Design Matrix
- If *use_rarity_score* input is True, include rarity_score (only recommended if using rarity.tools score)
- Drop any trait category or individual trait that is in *ignore_traits_theo* input. Some collections (rumble-kong-league) are best priced in practice with a subset of trait categories
- Replace categorial traits with dummy features:
	- Drop any traits with 0 occurences (in sales)
	- Group traits together if exists in *group_traits* input. Essentially feature engineering primarily to avoid overfitting
	- For each trait_group, drop first grouped feature in *group_traits* input if exists, or drop first dummy feature. Avoids perfect colinearity and rank deficiency
	- If *group_traits* input empty, then drop first feature in each trait category
	- Skip dropping logic for any trait category that is exhibited by <=5% of all assets
- Add feature interaction (x*y) terms (not recommended due to overfitting)
- If *pricer* input is OLS or Robust, remove features with VIF > 5 or >90th percentile VIF, which ever is greater. Reduces colinearity

## Theoretical Value
- Train OLS, LASSO, or Theil-Sen robust regression model to predict price_ratio based on design matrix data
- In practice (assuming goal is not to price 3 SD opportunities well, but rather to focus on achievable assets):
	- minimal outlier removal + Theil-Sen robust regression performs well for less mature collections with no obvious outlier sales that should be removed
	- z-score based outlier removal + standard OLS performs well for more mature collections with obvious outlier sales
	- z-score based outlier removal + LASSO prefered over OLS for easier/quicker interpretation and lower chance of overfitting
- Note that theo is in price_ratio space
- Calculate theo for all listed assets

## Edge

	edge = (price / global_floor_price) - predicted price_ratio

Interpretation: edge = 0.5 means theo is 0.5 * global_floor_price higher than current price. Edge is in price-to-global-floor-ratio units.