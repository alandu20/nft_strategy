# NFT Trading System

Note this a partial version of the full repo. Inquiries: alan.du20@gmail.com.

Evaluate NFT opportunities on OpenSea and LooksRare in real-time as they are listed, using a pricing and required edge framework for market making and stat-arb strategies for event-driven opportunities.

Semi-automated using Heroku.

# Files
1. config.py: inputs by collection
2. nft.py: NftTrader class for scraping data and market making strategy
3. arb.py: event-driven strategy
4. scrape_metadata_parallel.py: scrape data for event-driven strategy

# Environment
1. Install all packages into virtual environment (recommended)
2. Download ChromeDriver from https://sites.google.com/chromium.org/driver/downloads and save chromedriver.exe to PATH (e.g. /usr/local/bin)

# Usage

Configuration

	python nft.py -s clonex -c -w

Save floor price periodically

	watch -n 1200 python nft.py -s clonex -floor -w

Rank opportunities by edge ratio

	python nft.py -s clonex [--load_sales] [--load_listed] [-w]

Latest opps from OS activity page

	watch -n 60 python nft.py -s clonex --load_sales -f -v 0 [--pricer {ols,robust,lasso}]

Price single asset

	python nft.py -s clonex --load_sales -f --price_token 11832 [--pricer {ols,robust,lasso}]

# Strategies
- Takeout: Liquidity Removal
	- Calculate edge using relative value pricer (includes microprice and risk adjustment): [pricer spec](specs/pricer.md) ([microprice spec](specs/microprice.md), [risk adjustment spec](specs/risk_adjustment.md))
	- Normalize edge using liquidity-based required edge framework: [required_edge/Logic spec](specs/required_edge.md)
	- Identify removal opportunities using optimal edge mult: [required_edge/Edge Mult Tuning spec](specs/required_edge.md)
- Event-Driven Arbitrage
	- [Metadata reveal arb](specs/reveal_strat.md)
	- Unclaimed asset arb
- Quoter: WETH Liquidity Adding
	- [WETH spec](specs/weth_strat.md) (WIP)
- DRT: Deal Driven Takeout
	- [DRT spec](specs/drt_strat.md) (WIP)
- Complex Takeout: Liquidity Removal of Bundles
	- bundles_strat (TODO)
- Auctions (TODO)

# Data

## Sources
- OS /collection endpoint: trait summaries and current global floor price
- OS /assets endpoint: last sale, current listing if exists
- OS activity page: lastest listings. Needed b/c /events endpoint requires API key that is difficult to obtain
- rarity.tools: rarity score and rank. Typically de-facto source of truth ranking system referenced by community
- Etherscan: scrape sales directly from blockchain. OS listings are off-chain. Contract specs: [contracts.md](specs/contracts.md)

## Pipeline
- Recurring path
	- Periodically get global floor price from OS API
	- Periodically get sales since last slow path run from etherscan, and update saved sales file from slow path
- Slow path
	- Get last sales for each asset from OS API
	- Calc price_ratio at time of sale using saved floor prices from recurring path
	- Get listings from OS API
	- Get global floor price from OS API to calc price_ratio for each listing
	- Run pricer and edge for each listed asset
- Dynamic path
	- Get latest listings from OS activity page, and update saved listings file from slow path
	- Run pricer and edge on latest listings
- Fast path (TODO)
	- Get latest sales in real-time from etherscan
	- If sweep detected, inject sales into saved sales file from slow path, load saved listings file from slow path, and run pricer and edge

## Known Issues
- 2022-03-03 to 2022-03-18: cool-cats-nft global floor not saved

# Events
- 2022-01-31 ~18:00 EST: Cool Pet release, which traded around 2-4 ETH shortly after drop, led to steep sell off for Cats with claimed Pets (1:1). This is regime change - pricing date range should either end before or start after this day
- 2022-02-05 ~05:30 EST: RTFKT-MNLTH airdrop. Seems like this was priced in over a couple days b/c CloneX did not really dip on airdrop. Could also be due to uncertainty in the utility (not announced at time of airdrop)
- 2022-02-10 ~10:00 EST: Karafuru reveal. Avoid including anything around this time or earlier in pricing
- 2022-02-18 ~09:00 EST: Edenhorde reveal. Avoid including anything around this time or earlier in pricing
- 2022-02-22 ~10:00 EST: 3landers reveal (may have been staggered reveal?). https://medium.com/@3landers.nft/hello-and-welcome-to-3landers-nft-community-e48baa4c4a7a. Note pricing r-squared very low (0.1) in first few days after reveal
- 2022-02-23 ~11:45 EST: tubby-cats public mint and instant reveal (pre-sale reveal was in 1k intervals)?
- 2022-03-04: Cyberbrokers mint and instant reveal
- 2022-03-07: CloneX Murakami drip snapshot for murakami flowers whitelist
- 2022-03-11 ~18:00 EST: Yuga Labs acquiring Larva Labs announcement
- 2022-03-17 ~08:30 EST: BAYC/MAYC $APE token drop
- 2022-03-26 14:00 EST: world-of-women-galaxy claim for world-of-women-nft holders. Pricing does not take this into account
- 2022-03-26 16:00 EST: world-of-women-galaxy public sale. Dutch auction starting at 3 eth, sold out ~20:30 EST at ~1 eth
- 2022-03-27 08:00 EST: world-of-women-galaxy reveal
- 2022-03-28 ~23:50 EST: murakami-flowers-seed whitelist mint. CloneX Murakami drip holders auto whitelisted, snapshot taken 2022-03-07
- 2022-04-11: steedz-of-degen snapshot. 2022-04-14 12:00 EST public sale, 2022-04-15 15:00 EST reveal. https://discord.com/channels/880281356335206440/881602538615496724/962804205444288542
- 2022-04-26: veefriends-series-2 mint (and reveal?)
- 2022-04-30 12:00 EST; Otherside land sale in $APE
- 2022-05-01 17:00 EST: Otherside reveal
- 2022-05-17: Karafuru x Hypebeast x Atmos 3D private sale. Public sale next day
- 2022-05-25: Karafuru x Hypebeast x Atmos 3D airdrop snapshot. Revealed 2022-05-30

# Pricing Issues
- bossbeauties token_id 4714 TV = 2.892 despite rarity score 206.62 (rank 73). Sold for 3.5 after listing for 20 hours. Perhaps pricing is less accurate in top ranks
- world-of-women-nft_snapshot_sales_20220216T095018.csv: LASSO and OLS top 6 opps have rarest trait "hairstyle_black and white" probably due to single sale of token_id 7772 at 2022-01-27 09:27:15 (3 other most recent sales fell out of 30 day window). Robust regression works better in this case
- edenhorde-official token_id 5928: lasso price=2.49 edge_ratio = 5 due to overfitting Expression = Weary. Several high sales for this trait but those also had at least one other <1% trait. New listing at 2.1 about hour later, and another at 1.98 next day for Expression = Weary. Regression coefficients highly unstable if expression feature removed. Probably should be priced using Tribe = Oru
- mfers token_id 4956 2022-02-23 TV = ~4.0 but trading much higher, probably b/c missing some trait category
- rumble-kong-league token_id 5283 2022-03-10 TV = 2.2 even though 234 boost overall with 80 defense. Added "*_is_semi_pro" and "*_is_pro" features and now TV = 3.7. R-squared improved from 0.3 to 0.7 with this change and also using last 90 days of sales instead of last 30-45 days (not much liquidity in RKL lately)

# Change Log
- 2022-02-22 Fixed NaN price level sorting bug in required edge ([postmortem_20220222_karafuru_4963.md](postmortem/postmortem_20220222_karafuru_4963.md))
- 2022-02-24 Started using group_traits in required edge order book levels
- 2022-03-03 Increase default days in regression from 30 to 45 due to reduced activity in recent month
- 2022-03-10 Add include_orders=true param into /assets endpoint. Change on OS end was effective evening of 2022-03-08: https://docs.opensea.io/changelog/updated-timeline-for-march-1-api-migrations
- 2022-03-11 Add semi_pro and pro boost features to rumble-kong-league pricing model, increasing R-squared from 0.3 to 0.7 using last 90 days of sales
- 2022-03-14 Add ITM and OTM fudge components to required edge
- 2022-03-16 Change ITM fudge component in required edge
- 2022-03-18 Increase default days in regression from 45 to 90 due to reduced activity in recent months which hurts pricing in less liquid rare trait assets
- 2022-03-20 To get latest listings use new /asset/listings endpoint instead of /assets endpoint, deprecated by OS effective 2022-03-21
- 2022-03-27 Use OS API key to get listings from /orders and /events endpoints
- 2022-04-01 Use exponential overall boost function in lieu of semi_pro/pro overall (not individual stat) boost indicator to rumble-kong-league pricing model, increasing R-squared by ~0.04. Tried exponential for individual stat boosts too but that did not improve R-squared
- 2022-04-08 Logic to remove collection-specific ultra high value traits and parameterize z-score filtering in run_pricer. Previous behavior removing all sales >3 z-scores for all collections is too extreme. New logic removes outlier traits that can muddle pricing, allowing for higher threshold for z-score filter
- 2022-06-25 OS auction_type field from /events endpoint changed at some point within last few weeks, probably during switch to Seaport protocol on 2022-06-14. No longer takes value "dutch" for regular listings, instead is empty (probably was mistakenly set to "dutch" previously). Method for identifying auctions using /orders endpoint has not changed, still maker_relayer_fee=0 for auctions (no auction_type field)
- 2022-07-29 Noticed /orders endpoint missing many (75%) listings, probably started around time to seaport migration. Switched to using /listings endpoint, drawback is it only supports single asset calls, whereas /orders supports multi asset calls. The /listings endpoint also appears to be missing listings submitted prior to seaport migration. The /assets endpoint also supports multi asset calls, but includes_orders=true does not actually return orders. Check back in a couple months to see whether /orders or /assets endpoints are fixed, since single asset calls with throttling is much slower
- 2022-08-16 Noticed /assets endpoint no longer has last_sale.transaction.timestamp field, probably started around mid July based on latest sales in recent scrapes. All sales past mid July were missing in scrapes. Use last_sale.event_timestamp instead, which exists in both pre and post mid July sales

# Checklist for High Value Opps
- How is r-squared relative to the norm for the collection?
- Do coefficients make sense / do they differ from the norm?
- How many sales with a particular trait are in the input?
- If floor is lower/higher than current in past sales, should more edge be required?
