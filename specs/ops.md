# Operations

## Trading

### Data pipeline

Save floor prices

	watch -n 1200 python nft.py -s clonex --floor -w

Scrape last sale price and active listings

	python nft.py -s clonex -p lasso -w

Top opportunities using last scraped sales and listings

	python nft.py -s clonex --load_sales --load_listed [-p {ols,robust,lasso}]

Real-time opportunities from OS events endpoint

	watch -n 30 python nft.py -s clonex -f -p lasso -v 0 -w

Aggregated real-time opportunities (all collections, dummy slug arg)

	watch -n 600 python nft.py -s clonex --ticker

### Collection specific notes

rumble-kong-league
- Coefficients can change dramatically if rare furs are included in pricing. Suggested setting is to leave rare furs out of pricing (done so in run_pricer)
- Coefficients can also be sensitive to the number of days of sales used. Typically use "-d 120", sometimes use "-d 180", depending on which coefficents seem more logical (or if there is large r-squared difference)

clonex
- Has many more traits than the average collection. Attempted to regularize but beware of overfit pricing

## Backtest

To backtest and/or tune edge mults for a new collection with no previously scraped data (floor prices, sales, listings):

1. Get floor price from Dune Analytics (e.g. https://dune.xyz/queries/489731/928244?Contract%20Address_t6c1ea=x7ea3cca10668b8346aec0bf1844a49e995527c8b) or Lucky Trader (no table export) to recreate {collection}_floor_prices.csv

2. Scrape sales from blockchain (via etherscan API). Set start time of scrape in start_time_est_dict (recommend setting to earliest floor price date + 1 day, or post-reveal date if known), hardcoded in scrape_etherscan_sales function

	python nft.py -s {collection} --scrape_block all -w

3. Backpopulate sales files for the past X days (make sure have floor price and etherscan-scraped sales this far back; recommend at least 2 weeks after first scraped sale date). Set first_os_scrape dict, hardcoded in backpopulate_sales function (if no scrapes yet, set to today's date temporarily). Creates a separate sales file per day

	python nft.py -s {collection} --backpop_sales -d {days} -w

4. Run OS scrape at least once. Or create temporary dynamic sales file (copy last backpopulated file) and dynamic listings file (any filler works even from other collection)

	python nft.py -s {collection} -p lasso -w

5. Set group_traits in config. Make collection specific changes like removing certain traits, combination of traits, or even trait_categories. Check stability of regression r-squared over different windows. Consider setting zscore_cutoff_dict.

6. Train models for each sales file to calculate perceived edge at time of every sale. Set override_start_dates dict, recommend around the time of earliest floor price unless there is specific event to anchor at (all sales prior to this date will be removed, so if there is a sales file created in step 3 with no sales after this date, then process will break). Generates backtest plots. Since OS listings are very annoying to retroactively scrape, backtest edge not edge_ratio

	python nft.py -s {collection} -t edge -w


## Track Wallets

1. Scrape wallet activity (starts from latest saved block if wallet sales file already exists), save to sales file, and calculate flip pnl. Does not handle cases where owner buys in wallet 1, transfers to wallet 2, and sells in wallet 2 (everything calculated within 1 wallet)

	python nft.py -s clonex --wallet {address} -w

2. Calculate aggregate strategy pnls. Strategies: (1) any flip, (2) WETH buy then flip

	python nft.py -s clonex --wallet pnl


## Reveal Strategy

1. Save current listings

	python arb.py -s gossamer-seed -m listings -w

2. Save new listings

	watch -n 60 python arb.py -s gossamer-seed -m listings --load_listed -w

3. Get latest metadata URL

	python arb.py -s fear-city -m url

4. Scrape metadata for listed or all assets

	python scrape_metadata_parallel.py -s fear-city --listed -w
	python scrape_metadata_parallel.py -s fear-city -w

5. Find opps (at reveal)

	python arb.py -s fear-city -m opps -w

6. Find opps (after reveal)

	watch -n 20 python arb.py -s fear-city -m listings_w_meta --load_listed

	