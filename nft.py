"""Find mispricings on Opensea for a particular NFT collection.

Usage:
    Configuration: python nft.py -s clonex -c -w
    Save floor price periodically: watch -n 1200 python nft.py -s clonex --floor -w
    
    Rank all opps: python nft.py -s clonex [-p {ols,robust,lasso}] [-w]
    Rank all opps in dynamic saved files: python nft.py -s clonex --load_sales --load_listed [-p {ols,robust,lasso}]
    Rank latest opps from OS activity page: watch -n 60 python nft.py -s clonex -f -v 0 [-p {ols,robust,lasso}] [-w]
    Price single asset: python nft.py -s clonex --load_sales -f --price_token 11832 [-p {ols,robust,lasso}]
    Update dynamic last sales file using etherscan: python nft.py -s clonex --scrape_block last [-w]
    Aggregate opp ticker (dummy slug): watch -n 600 python nft.py -s clonex --ticker -w
    
    Scrape all etherscan sales: python nft.py -s clonex --scrape_block all [-w]
    Backpopulate OS sales files using etherscan history: python nft.py -s clonex --backpop_sales -d 10 [-w]
    Run backtest / tune edge mult: python nft.py -s clonex -t edge_ratio [-w]
    
    Study wallet (dummy slug): python nft.py -s clonex --wallet xyz [-w]
    Aggregate PnL by strategy (dummy slug): python nft.py -s clonex --wallet pnl
    All sales for saved wallets (dummy slug): python nft.py -s clonex --wallet all_sales
    Event history for weth adding liquidity strategy: python nft.py -s clonex --full_history analyze

TODO:
- Weight kong stats by % existence instead of arbitrary 80 boost semi pro 90 boost pro
- Weight pricing by list-to-sale time
- Which collections have the most successful flips within 24 hours, and which have most total edge
- Listings for rarest trait below last sale should be incorporated into pricing.
- DRT
- Listing-to-sale time integrated into pricing
- Private sales and LooksRare removed when overwritting dynamic sales file with OS scrape
- Find optimal price to flip at by looking at average edge of flips.
- Edge too great
- study highest and lowest edge trades
- Find opps on LooksRare.
- Support numerical traits in required edge.
- Scrape all historical listings from OS. Handle expired listings
- Realtime trade ticker.
- Realtime opportunity monitor tracking volume, unique owners, sweeps, highest sales.
- Get hourly floor price from dune.
- Twitter or Discord bot tracking project updates.
"""

import argparse
import cloudscraper
import config as cfg
from datetime import datetime, timedelta
import json
import logging
import numpy as np
import os
import pandas as pd
pd.options.display.max_columns = 200
pd.options.display.max_rows = 700
pd.set_option('display.width', 400)
pd.set_option('display.max_colwidth', None)
import pytz
import requests
import scipy as sp
from sklearn.linear_model import TheilSenRegressor
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import pinv_extended
import sys
import time
import warnings


class NftTrader(object):
    def __init__(self, collection_slug, collection_params, bankroll, write_to_file, days):
        self.COLLECTION_SLUG = collection_slug
        self.SLUG_SHORT = collection_params["slug_short"]
        self.CONTRACT_ADDRESS = collection_params["contract_address"]
        self.META_URL = collection_params["meta_url"]
        self.CNT_TOKEN_IDS = collection_params["cnt_token_ids"]
        self.TOKEN_ID_START = collection_params["token_id_start"]
        self.GLOBAL_CNT_TH = collection_params["global_cnt_th"]
        self.GLOBAL_RARITY_TH = collection_params["global_rarity_th"]
        self.LOCAL_DIVERSITY_TH = collection_params["local_diversity_th"]
        self.USE_RARITY_SCORE = collection_params["use_rarity_score"]
        self.THEIL_SEN_SAMPLE_RATIO = collection_params["theil_sen_sample_ratio"]
        self.TRAIT_CATEGORIES = collection_params["trait_categories"]
        self.USE_REQUIRED_EDGE = collection_params["use_required_edge"]
        self.REQUIRE_TRAITS = collection_params["require_traits"]
        self.IGNORE_TRAITS_THEO = collection_params["ignore_traits_theo"]
        self.IGNORE_TRAITS_REQUIRED_EDGE = collection_params["ignore_traits_required_edge"]
        self.PRIORITY_TRAITS = dict((k.lower(), v) for k,v in collection_params["priority_traits"].items())
        self.GROUP_TRAITS = collection_params["group_traits"]
        self.bankroll = 100 if bankroll is None else bankroll
        self.write_to_file = write_to_file
        self.days = 90 if days is None else days

    @staticmethod
    def get_request_with_error_handling(url, connection_timeout=120, throttle_delay=20, use_cloudscraper=True, use_api_key=False):
        """Retry for up to connection_timeout seconds if connection error occurs in GET request.

        Args:
            connection_timeout: number of seconds for retry attempts if connection error occurs in GET request.
            use_cloudscraper: mimic browser to get around cloudflare anti-bot protection used by OpenSea.
        Returns:
            GET request response.
        """
        headers = {
            "Accept": "application/json",
            "X-API-KEY": "85dc024ae3b7495cb53210994bf5469e"

            # keys
            # 85dc024ae3b7495cb53210994bf5469e
            # e6c66790f9d642eaaf40f135f6ed77da (rate limit 4/sec)
        }

        if use_cloudscraper:
            scraper = cloudscraper.create_scraper(browser={'browser':'chrome','platform':'linux','mobile':False})
            url = url + "&format=json"

        request_start_time = time.time()
        while True:
            try:
                if use_cloudscraper:
                    if use_api_key:
                        response_assets = scraper.get(url, headers=headers)
                    else:
                        response_assets = scraper.get(url)
                else:
                    if use_api_key:
                        response_assets = requests.request("GET", url, headers=headers)
                    else:
                        response_assets = requests.request("GET", url)
                
                if response_assets is None:
                    return None
                else:
                    try:
                        response_text = json.loads(response_assets.text)
                    except json.decoder.JSONDecodeError:
                        return None
                
                if ("detail" in response_text) and ("throttled" in response_text["detail"].lower()):
                    print("OS response detail: {}".format(response_text["detail"]))
                    print("GET request throttled, retry after {} seconds {}".format(throttle_delay, url))
                    time.sleep(throttle_delay)
                    continue
                break
            except requests.exceptions.ConnectionError:
                if time.time() > request_start_time + connection_timeout:
                    raise Exception('Unable to get updates after {} seconds of ConnectionErrors'.format(connection_timeout))
                else:
                    logging.info("GET request ConnectionError, retry after 3 seconds {}".format(url))
                    time.sleep(3)
        return response_assets

    def scrape_traits(self, override_url_meta=None, url_meta_extension=None, override_token_list=None, unknown_trait_categories=False, override_rate_limit_seconds=None):
        """Run once to save metadata properties.
        
        Rate limits:
        - IPFS: ~200 calls per minute
        - boredapeyachtclub: ~10 calls per 10 seconds
        """

        if override_url_meta is not None:
            url_meta = override_url_meta
        else:
            url_meta = self.META_URL

        if unknown_trait_categories:
            df = pd.DataFrame(columns=["token_id","name"])
        else:
            cols_trait_file = list(self.TRAIT_CATEGORIES)
            cols_trait_file.insert(0, "token_id")
            cols_trait_file.insert(1, "name")
            df = pd.DataFrame(columns=cols_trait_file)

        corrupt_tokens = []

        if override_token_list is not None:
            tokenids_to_scrape = override_token_list
        else:
            tokenids_to_scrape = range(self.TOKEN_ID_START, self.CNT_TOKEN_IDS + self.TOKEN_ID_START)

        for tokenid in tokenids_to_scrape:
            if override_rate_limit_seconds is not None:
                logging.info("{} done, pausing {} sec".format(tokenid, override_rate_limit_seconds))
                time.sleep(override_rate_limit_seconds)
            else:
                if tokenid > self.TOKEN_ID_START:
                    if tokenid % 21 == 0:
                        logging.info("{} done, pausing 2 sec".format(tokenid))
                        time.sleep(2)
                    if tokenid % 77 == 0:
                        logging.info("{} done, pausing 5 sec".format(tokenid))
                        time.sleep(5)
                    if tokenid % 188 == 0:
                        logging.info("{} done, pausing 30 sec".format(tokenid))
                        time.sleep(20)
                    if (tokenid % 100 == 0) and (tokenid > self.TOKEN_ID_START):
                        if self.write_to_file:
                            logging.info("{} done, writing to file".format(tokenid))

                            # Save progress in case process breaks.
                            df.to_csv("data_warehouse/traits/temp/{}_{}.csv".format(self.COLLECTION_SLUG, tokenid), index=False)
            
            if url_meta_extension is not None:
                url_token_meta = "{}/{}{}".format(url_meta, tokenid, url_meta_extension)
            else:
                url_token_meta = "{}/{}".format(url_meta, tokenid)
            
            response = self.get_request_with_error_handling(url=url_token_meta, use_cloudscraper=False)

            if response is None:
                # Custom None handling needed for some collections.
                if self.COLLECTION_SLUG in ["cyberkongz-vx","knights-of-degen-official"]:
                    request_start_time = time.time()
                    while True:
                        if response is None:
                            logging.info("Metadata is None for token_id {}, trying again after 3 seconds: {}".format(tokenid, url_token_meta))
                            time.sleep(3)
                            response = self.get_request_with_error_handling(url=url_token_meta, use_cloudscraper=False)
                        elif time.time() > request_start_time + 60:
                            logging.info("Metadata is still None after 60 seconds of attempts, skipping")
                            continue
                        else:
                            break
                else:
                    logging.info("Metadata is None for token_id {}, skipping: {}".format(tokenid, url_token_meta))
                    
                    continue
            
            try:
                df_json = pd.json_normalize(json.loads(response.text), "attributes", ["name"], errors='ignore') # name is null if not in json
            except (json.decoder.JSONDecodeError, KeyError):
                logging.info("Decoding json failed, skipping token_id {} and pausing 3 seconds: {}".format(tokenid, url_token_meta))
                corrupt_tokens.append(tokenid)
                logging.info("Running list of corrupt tokens: {}".format(corrupt_tokens))
                time.sleep(3)
                continue
            if df_json["name"].isnull().values.any():
                df_json["name"] = "{} {}".format(self.COLLECTION_SLUG, tokenid)
            df_row = df_json.pivot_table("value", "name", "trait_type", aggfunc="first").reset_index()
            df_row.columns = [c.lower() for c in df_row.columns]
            df_row["token_id"] = str(tokenid)
            try:
                df = df.append(df_row)
            except ValueError:
                logging.info("Columns are not matching up for some reason, skipping:\n{}".format(df_row))
                continue

        logging.info("Full list of tokens with corrupt metadata: {}".format(corrupt_tokens))

        if self.write_to_file:
            df = df[cols_trait_file]
            df.to_csv("data_warehouse/traits/{}.csv".format(self.COLLECTION_SLUG), index=False)

        return df

    def save_custom_rarity_score(self):
        """Compute custom rarity score.

        Similar claculation to rarity.tools score.
        """
        df_assets = pd.read_csv("data_warehouse/traits/{}.csv".format(self.COLLECTION_SLUG))
        trait_categories = [col for col in df_assets.columns if col not in ["token_id", "name", "rarity_score", "rarity_rank"]]
        df_rarity_scores = pd.DataFrame()
        for trait_category in trait_categories:
            df_rarity_score = df_assets.groupby(trait_category, as_index=False).agg({"token_id":"count"}).rename(columns={trait_category:"trait", "token_id":"cnt"})
            df_rarity_score["rarity_score"] = 1 / (df_rarity_score["cnt"] / self.CNT_TOKEN_IDS)
            df_rarity_scores = df_rarity_scores.append(df_rarity_score[["trait", "rarity_score"]])
        df_assets_rarity = df_assets.replace(df_rarity_scores.set_index("trait").to_dict()["rarity_score"]).fillna(0)
        df_assets["rarity_score"] = df_assets_rarity[trait_categories].sum(axis=1)
        df_assets["rarity_rank"] = df_assets["rarity_score"].rank(ascending=False)
        if self.write_to_file:
            df_assets.to_csv("data_warehouse/traits/{}.csv".format(self.COLLECTION_SLUG), index=False)

    @staticmethod
    def load_traits(slug):
        df_assets = pd.read_csv("data_warehouse/traits/{}.csv".format(slug))
        df_assets.columns = [col.lower() for col in df_assets.columns]
        df_assets["token_id"] = df_assets["token_id"].astype(str)
        df_assets = df_assets.applymap(lambda s: s.lower() if type(s) == str else s)
        return df_assets

    @staticmethod
    def create_partitions(token_ids, assets_query_limit=10):
        """Partition list of token_ids into chunks with length assets_query_limit. /assets call can be unstable if >10 assets.

        Args:
            token_ids: list of token_ids.
            assets_query_limit: number of token_ids per /assets call.
        Returns:
            list of partitions, where partition is a list of token_ids.
        """
        cnt_assets = len(token_ids)
        pidxs = np.linspace(0, cnt_assets-1, cnt_assets)
        partitions = [pidxs[i:i+assets_query_limit] for i in range(0, len(pidxs), assets_query_limit)]
        return partitions

    @classmethod
    def get_collection_info(cls, slug, connection_timeout=180, use_saved=False, write_to_file=False):
        """/collection API call with option to use saved file for static info like trait counts.

        Returns:
            dataframe with trait counts, current global floor price, etc.
        """
        file_name = "data_warehouse/traits/{}_collection_info.csv".format(slug)
        if use_saved and os.path.isfile(file_name):
            logging.info("Loading saved collection info file")
            return pd.read_csv(file_name)
        url_collection = "https://api.opensea.io/api/v1/collection/{}?".format(slug)
        response_collection = cls.get_request_with_error_handling(url=url_collection, connection_timeout=connection_timeout)
        try:
            df_collection = pd.json_normalize(json.loads(response_collection.text))
        except (ValueError, KeyError, json.decoder.JSONDecodeError):
            logging.info("/collection call appears to be broken")
            return None
        if write_to_file:
            df_collection.to_csv(file_name, index=False)
        return df_collection

    def get_floor_price(self):
        """Get floor price from /collection endpoint or use saved file if endpoint down.

        TODO: Dune Analytics may have real time floor prices so continuously saving floor price may be unnecessary.
        """
        df_collection = self.get_collection_info(slug=self.COLLECTION_SLUG, write_to_file=self.write_to_file)
        global_floor_price = df_collection["collection.stats.floor_price"].values[0]
        if global_floor_price is None:
            raise Exception("Global floor from collection.stats.floor_price is None")
        if self.write_to_file:
            df_floor_prices = pd.read_csv("data_warehouse/floor_prices/{slug}_floor_prices.csv".format(slug=self.COLLECTION_SLUG))
            current_dt = datetime.now()
            current_date = current_dt.strftime("%Y-%m-%d")
            current_time = current_dt.strftime("%Y-%m-%d %H:%M:%S")
            df_floor_prices = df_floor_prices.append(pd.Series([current_date,current_time,global_floor_price], index=["date","time_est","floor_price"]), ignore_index=True)
            logging.info("Saving global floor price {} at {} to {}_floor_prices.csv".format(global_floor_price, current_time, self.COLLECTION_SLUG))
            df_floor_prices.to_csv("data_warehouse/floor_prices/{}_floor_prices.csv".format(self.COLLECTION_SLUG), index=False)
        return global_floor_price

    def get_latest_listings(self, lookback_seconds=120, override_contract_address=None):
        """Get latest listings using OS events endpoint. May include duplicate token_ids at different prices (and even same price?).
        """

        start_time_dt = datetime.now() - timedelta(seconds=lookback_seconds)
        print("Getting listings after {}".format(start_time_dt.strftime("%Y-%m-%d %H:%M:%S")))
        start_time_epoch = int(start_time_dt.timestamp())

        if override_contract_address is not None:
            contract_address = override_contract_address
        else:
            contract_address = self.CONTRACT_ADDRESS

        url_events = "https://api.opensea.io/api/v1/events?asset_contract_address={}&only_opensea=false&event_type=created&occurred_after={}".format(contract_address, start_time_epoch)
        response_events = self.get_request_with_error_handling(url=url_events, use_api_key=True, throttle_delay=5, connection_timeout=20)

        if response_events is None:
            raise Exception("/events call is broken. Response is None")

        try:
            df_listings = pd.json_normalize(json.loads(response_events.text)["asset_events"])
        except (ValueError, KeyError, json.decoder.JSONDecodeError):
            raise Exception("/events call appears to be broken. Missing asset_events key for some reason")

        if len(df_listings) == 0:
            print("No listings on OS in last {} seconds".format(lookback_seconds))
            return None

        df_listings["token_id"] = df_listings["asset.token_id"]
        df_listings["is_auction"] = [True if x is not None else False for x in df_listings["auction_type"]]
        if len(df_listings[df_listings["is_auction"]==False]) == 0:
            print("No non-auction listings in last {} seconds".format(lookback_seconds))
            return None
        df_listings["price"] = np.round(df_listings["starting_price"].astype(float) / (10.**df_listings["payment_token.decimals"].astype(float)), 3)
        df_listings = df_listings[df_listings["asset_bundle"].isnull()]
        df_listings = df_listings[["token_id","price","payment_token.symbol","payment_token.eth_price","payment_token.usd_price","created_date","is_auction"]]
        df_listings["time_est"] = df_listings["created_date"].apply(lambda x: pytz.timezone("UTC").localize(datetime.strptime(x[0:19], "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S"))
        df_listings["price_eth"] = np.round(df_listings["payment_token.eth_price"].astype(float) * df_listings["price"], 3) # eth_price (conversion factor) is 1 if currency is eth
        df_listings["price_usd"] = np.round(df_listings["payment_token.usd_price"].astype(float) * df_listings["price"], 2) # usd_price (conversion factor) is 1 if currency is usdc
        df_listings["currency"] = df_listings["payment_token.symbol"].apply(lambda x: x.lower())
        df_listings["token_id"] = df_listings["token_id"].astype(str) # should be redundant
        # df_listings = df_listings.rename(columns={"created_date":"time_utc"})
        df_listings = df_listings[["token_id","time_est","is_auction","price","currency","price_eth","price_usd"]]

        return df_listings

    def get_latest_listings_lr(self, lookback_seconds=300):
        """Get latest listings from LR.
        """

        start_time_dt = (datetime.now() - timedelta(seconds=lookback_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        print("Getting listings after {}".format(start_time_dt))

        url_events = "https://api.looksrare.org/api/v1/events?collection={}&type=LIST&pagination[first]=10".format(self.CONTRACT_ADDRESS)
        response_events = self.get_request_with_error_handling(url=url_events, use_api_key=True, throttle_delay=5, connection_timeout=20)

        df_listings = pd.json_normalize(json.loads(response_events.text)["data"])

        if response_events is None:
            raise Exception("/events call is broken. Response is None")

        df_listings["time_est"] = df_listings["createdAt"].apply(lambda x: pytz.timezone("UTC").localize(datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ")).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S"))
        df_listings = df_listings[df_listings["time_est"] > start_time_dt]
        if len(df_listings) == 0:
            print("No listings on LR in last {} seconds".format(lookback_seconds))
            return None

        df_listings = df_listings[(df_listings["order.status"].str.lower()=="valid") & (df_listings["order.isOrderAsk"]==True)]
        df_listings["token_id"] = df_listings["order.tokenId"]
        df_listings["is_auction"] = np.where(df_listings["order.strategy"] != "0x56244Bb70CbD3EA9Dc8007399F61dFC065190031", True, False)
        df_listings["price"] = np.round(df_listings["order.price"].astype(float) / (10.**18), 3)
        df_listings["currency"] = np.where(df_listings["order.currencyAddress"] == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "weth", "unknown")
        df_listings["price_eth"] = np.nan
        df_listings["price_usd"] = np.nan
        df_listings = df_listings[["token_id","time_est","is_auction","price","currency","price_eth","price_usd"]]

        return df_listings

    @classmethod
    def get_current_listings(cls, token_ids, token_contract_address):
        """Get listed prices for list of token_ids using listings endpoint.

        Notes as of 2022-07-29:
        /listings endpoint: supports single asset, appears to be missing listings submitted prior to seaport migration
        /asset endpoint: supports single asset, appears to be missing listings submitted prior to seaport migration
        /assets endpoint: supports multiple assets, but includes_orders=true does not actually return orders
        /orders endpoint: supports multiple assets, but missing many orders (50%+, not just those prior to seaport migration)

        Args:
            token_ids: list of token_ids.
            token_contract_address: collection address.
        Returns:
            dataframe of currently listed assets and their prices, empty if none listed.
        """

        df_prices = pd.DataFrame()
        throttle_counter = 0

        for tokenid in token_ids:
            url_assets = "https://api.opensea.io/api/v1/asset/{}/{}/listings?limit=1".format(token_contract_address, tokenid)
            response_assets = cls.get_request_with_error_handling(url=url_assets, use_api_key=True)
            
            if response_assets is None:
                logging.info("/listings call appears to be broken, skipping partition {}".format(partition))
                continue
            
            try:
                df_prices_part = pd.json_normalize(json.loads(response_assets.text)["seaport_listings"])
            except (ValueError, KeyError):
                logging.info("Decoding json failed, skipping and pausing 3 seconds: {}".format(url_assets))
                time.sleep(3)
                continue
            
            if len(df_prices_part) == 0:
                logging.info("Asset not listed: {}".format(url_assets))
                throttle_counter += 1
                if throttle_counter == 10:
                    time.sleep(1.5)
                    throttle_counter -= 10
                else:
                    time.sleep(0.3)
                continue
            else:
                logging.info("Asset listed: {}".format(url_assets))
                df_prices_part["price"] = np.round(df_prices_part["current_price"].astype(float) / (10.**18), 3) # not correct for USDC
                df_prices_part = df_prices_part.sort_values(by="price")
                df_prices_part["token_id"] = tokenid
                df_prices_part = df_prices_part.drop_duplicates(subset=["token_id"], keep="first") # listings must already be sorted by price from low to high
                df_prices_part["is_auction"] = np.where(df_prices_part["order_type"]=="english", True, False)
                currency_hash = df_prices_part["protocol_data.parameters.consideration"].iloc[0][0]["token"]
                currency_hash_map = {
                    "0x0000000000000000000000000000000000000000":"eth",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48":"usdc",
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2":"weth",
                    "0x4d224452801ACEd8B2F0aebE155379bb5D594381":"ape"
                    }
                df_prices_part["currency"] = currency_hash_map[currency_hash] if currency_hash in currency_hash_map else "unknown"
                df_prices_part = df_prices_part[["token_id","price","currency","created_date","is_auction"]]
                df_prices = df_prices.append(df_prices_part)
                throttle_counter -= 1
            time.sleep(0.25)
        
        if len(df_prices) > 0:
            df_prices["time_est"] = df_prices["created_date"].apply(lambda x: pytz.timezone("UTC").localize(datetime.strptime(x[0:19], "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S"))
            df_prices["price_eth"] = np.nan
            df_prices["price_usd"] = np.nan
            df_prices["token_id"] = df_prices["token_id"].astype(str) # should be redundant
            # df_prices = df_prices.rename(columns={"created_date":"time_utc"})
            df_prices = df_prices[["token_id","time_est","is_auction","price","currency","price_eth","price_usd"]]

        return df_prices

    @classmethod
    def get_current_listings_unstable(cls, token_ids, token_contract_address):
        """Get listed prices for list of token_ids using orders endpoint. Known to be more unstable than listings endpoint, starting after seaport migration.

        Args:
            token_ids: list of token_ids.
            token_contract_address: collection address.
        Returns:
            dataframe of currently listed assets and their prices, empty if none listed.
        """

        partitions = cls.create_partitions(token_ids)
        cnt_partitions = len(partitions)
        df_prices = pd.DataFrame()
        throttle_counter = 0
        PAGE_LIMIT = 20

        for p, partition in enumerate(partitions):
            token_id_query_params = ""
            for i in partition:
                token_id_query_params += ("token_ids="+str(token_ids[i])+"&")

            url_assets = "https://api.opensea.io/wyvern/v1/orders?asset_contract_address={}&{}side=1&bundled=false&include_bundled=false&sale_kind=0&order_by=created_date&order_direction=desc&limit={}".format(token_contract_address, token_id_query_params, PAGE_LIMIT)

            if (p % 100 == 0) and (p > 0):
                logging.info("Starting partition {} / {} : {}".format(p, cnt_partitions-1, url_assets))
            
            response_assets = cls.get_request_with_error_handling(url=url_assets, use_api_key=True)
            
            if response_assets is None:
                logging.info("/orders call appears to be broken, skipping partition {}".format(partition))
                continue
            
            try:
                df_prices_part = pd.json_normalize(json.loads(response_assets.text)["orders"])
                
                # If more than 1 page of orders, append those pages.
                if len(df_prices_part) == PAGE_LIMIT:
                    page = 1
                    while True:
                        offset = PAGE_LIMIT * page + 1
                        url_assets_page = url_assets + "&offset={}".format(offset)
                        logging.info("More than {} listings in partition, must use offset: {}".format(PAGE_LIMIT, url_assets_page))
                        response_assets_page = cls.get_request_with_error_handling(url=url_assets_page, use_api_key=True)
                        if "orders" not in json.loads(response_assets_page.text):
                            logging.info("No listings on this page")
                            break
                        df_prices_part_page = pd.json_normalize(json.loads(response_assets_page.text)["orders"])
                        df_prices_part = df_prices_part.append(df_prices_part_page)
                        if len(df_prices_part_page) < PAGE_LIMIT:
                            logging.info("Less than {} listings on this page (offset={}). No additional listings on next page".format(PAGE_LIMIT, offset))
                            break
                        page += 1
            except (ValueError, KeyError):
                logging.info("Decoding json failed, skipping partition {} and pausing 3 seconds: {}".format(partition, url_assets))
                time.sleep(3)
                continue
            
            if len(df_prices_part) == 0:
                logging.info("No assets listed in current partition: {}".format(url_assets))
                throttle_counter += 1
                if throttle_counter == 3:
                    time.sleep(4)
                    throttle_counter -= 2
                else:
                    time.sleep(0.6)
                continue
            else:
                df_prices_part["token_id"] = df_prices_part["asset.token_id"]
                df_prices_part = df_prices_part.drop_duplicates(subset=["token_id"], keep="first") # listings should already be sorted from newest to oldest
                df_prices_part["is_auction"] = np.where(df_prices_part["maker_relayer_fee"].astype(int)==0, True, False)
                df_prices_part["price"] = np.round(df_prices_part["current_price"].astype(float) / (10.**df_prices_part["payment_token_contract.decimals"].astype(float)), 3)
                df_prices_part = df_prices_part[["token_id","price","payment_token_contract.symbol","payment_token_contract.eth_price","payment_token_contract.usd_price","created_date","is_auction"]]
                df_prices = df_prices.append(df_prices_part)
                throttle_counter -= 1
            time.sleep(3)
        
        if len(df_prices) > 0:
            df_prices["time_est"] = df_prices["created_date"].apply(lambda x: pytz.timezone("UTC").localize(datetime.strptime(x[0:19], "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S"))
            df_prices["price_eth"] = np.round(df_prices["payment_token_contract.eth_price"].astype(float) * df_prices["price"], 3) # eth_price (conversion factor) is 1 if currency is eth
            df_prices["price_usd"] = np.round(df_prices["payment_token_contract.usd_price"].astype(float) * df_prices["price"], 2) # usd_price (conversion factor) is 1 if currency is usdc
            df_prices["currency"] = df_prices["payment_token_contract.symbol"].apply(lambda x: x.lower())
            df_prices["token_id"] = df_prices["token_id"].astype(str) # should be redundant
            # df_prices = df_prices.rename(columns={"created_date":"time_utc"})
            df_prices = df_prices[["token_id","time_est","is_auction","price","currency","price_eth","price_usd"]]
        
        return df_prices

    @classmethod
    def get_last_sale(cls, token_ids, token_contract_address):
        """Get last sales for list of token_ids.

        Args:
            token_ids: list of token_ids.
            token_contract_address: collection address.
        Returns:
            dataframe of assets with (existing) last sales.

        TODO: does not include private sales which are common in higher priced collections.
        """

        partitions = cls.create_partitions(token_ids)
        cnt_partitions = len(partitions)
        df_prices = pd.DataFrame()
        for p, partition in enumerate(partitions):
            token_id_query_params = ""
            for i in partition:
                token_id_query_params += ("token_ids="+str(token_ids[i])+"&")
            url_assets = "https://api.opensea.io/api/v1/assets?{}asset_contract_address={}".format(token_id_query_params, token_contract_address)
            
            if (p % 100 == 0) and (p > 0):
                logging.info("Starting partition {} / {} : {}".format(p, cnt_partitions-1, url_assets))
            
            response_assets = cls.get_request_with_error_handling(url=url_assets)
            
            if response_assets is None:
                logging.info("/assets call appears to be broken, skipping partition {}".format(partition))
                continue
            
            try:
                df_prices_part = pd.json_normalize(json.loads(response_assets.text)["assets"])
            except (ValueError, KeyError):
                logging.info("Decoding json failed, skipping partition {} and pausing 10 seconds: {}".format(partition, url_assets))
                time.sleep(10)
                continue
            
            # Starting around mid July 2022, last_sale.transaction.timestamp no longer exists
            if "last_sale.event_timestamp" not in df_prices_part.columns:
                logging.info("No sales in current partition: {}".format(url_assets))
                continue
            else:
                df_prices_part = df_prices_part.dropna(subset=["last_sale.event_timestamp","last_sale.total_price"])
                df_prices_part["price"] = np.round(df_prices_part["last_sale.total_price"].astype(float) / (10.**df_prices_part["last_sale.payment_token.decimals"].astype(float)), 3)
                df_prices_part = df_prices_part[["token_id","price","last_sale.event_timestamp","last_sale.payment_token.symbol","last_sale.payment_token.eth_price","last_sale.payment_token.usd_price"]]
                df_prices = df_prices.append(df_prices_part)
                logging.info("Found sales in current partition: {}".format(url_assets))
            time.sleep(0.5)

        if len(df_prices) > 0:
            df_prices["time_est"] = df_prices["last_sale.event_timestamp"].apply(lambda x: pytz.timezone("UTC").localize(datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S"))
            df_prices["price_eth"] = np.round(df_prices["last_sale.payment_token.eth_price"].astype(float) * df_prices["price"], 3) # eth_price (conversion factor) is 1 if currency is eth
            df_prices["price_usd"] = np.round(df_prices["last_sale.payment_token.usd_price"].astype(float) * df_prices["price"], 2) # usd_price (conversion factor) is 1 if currency is usdc
            df_prices["currency"] = df_prices["last_sale.payment_token.symbol"].apply(lambda x: "unknown" if x is None else str(x).lower())
            df_prices["token_id"] = df_prices["token_id"].astype(str) # should be redundant
            # df_prices = df_prices.rename(columns={"last_sale.transaction.timestamp":"time_utc"})
            df_prices = df_prices[["token_id","time_est","price","currency","price_eth","price_usd"]]

        return df_prices

    def process_sales(self, df_sales_w_traits, end_date=datetime.today(), override_start_date=None):
        df_reg = df_sales_w_traits.copy()

        # Remove non-eth prices.
        logging.info("Count sales before removing non-eth prices: {}".format(len(df_reg)))
        if "currency" not in df_reg.columns:
            df_reg["currency"] = "eth"
        df_reg = df_reg[df_reg["currency"].isin(["eth","weth"])] # known issue: usdc-to-eth conversion factor returned by OS is off, so keep only eth sales
        logging.info("Count sales after removing non-eth prices: {}".format(len(df_reg)))

        # Remove known wrong looksrare prices scraped from blockchain.
        if "src" in df_reg.columns:
            df_reg["price_decimals"] = df_reg["price"].apply(lambda x: str(x)[::-1].find(".")) # returns -1 if no decimal
            df_reg = df_reg[~((df_reg["price_decimals"] > 2) & (df_reg["src"]=="looksrare"))]
            logging.info("Count sales after dropping looksrare prices with over 2 decimal places (block parsing issue): {}".format(len(df_reg)))

        # Remove sales more than x days ago.
        if override_start_date is not None:
            df_reg = df_reg[df_reg["time_est"] > override_start_date]
            logging.info("Count sales after removing sales prior to {}: {}".format(override_start_date, len(df_reg)))
        else:
            df_reg = df_reg[df_reg["time_est"] > (end_date - timedelta(days=self.days)).strftime("%Y-%m-%d")]
            logging.info("Count sales after removing sales >{} days ago: {}".format(self.days, len(df_reg)))
        print("Earliest sale time_est in pricing: {}".format(df_reg["time_est"].min()))
        print("Latest sale time_est in pricing: {}".format(df_reg["time_est"].max()))
        df_reg = df_reg.sort_values(by="price", ascending=False)
        logging.info("Max prices before filtering:\n {}".format(df_reg[["token_id","time_est","price","currency"]].head(10)))
        logging.info("Min prices before filtering:\n {}".format(df_reg[["token_id","time_est","price","currency"]].tail(10)))

        # Remove known obvious error sales (fat finger, OS old listing loophole, weth sale well below global floor).
        try:
            df_ignore_sales = pd.read_csv("data_warehouse/sales/ignore_sales/{}_ignore_sales.csv".format(self.COLLECTION_SLUG), dtype={"token_id": object})
            df_reg = df_reg.merge(df_ignore_sales, on=["token_id","time_est","price","currency"], how="left", indicator=True)
            logging.info("Dropping obvious error sales:\n {}".format(df_reg[df_reg["_merge"]=="both"][["token_id","time_est","price","currency"]]))
            df_reg = df_reg[df_reg["_merge"]=="left_only"]
            df_reg = df_reg.drop(columns="_merge")
            logging.info("Counted sales after dropping obvious errors: {}".format(len(df_reg)))
        except FileNotFoundError:
            logging.info("No file with obvious errors")

        # Remove obvious outlier sales based on price quantile. More aggressively filter lower prices due to erroneous fat finger prices.
        max_eth = df_reg["price"].quantile(0.999, interpolation="lower")
        min_eth = df_reg["price"].quantile(0.01, interpolation="higher")
        logging.info("Removing outlier prices <{} eth and >{} eth".format(np.round(min_eth, 2), np.round(max_eth, 2)))
        df_reg = df_reg[(df_reg["price"] > min_eth) & (df_reg["price"] < max_eth)]
        logging.info("Count sales after removing outlier prices: {}".format(len(df_reg)))

        # Join global floor price on sale datetime to calculate price_ratio (price / global floor).
        df_floor_prices = pd.read_csv("data_warehouse/floor_prices/{slug}_floor_prices.csv".format(slug=self.COLLECTION_SLUG))
        df_floor_prices["time_est"] = df_floor_prices["time_est"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
        df_reg["time_est"] = df_reg["time_est"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
        try:
            df_reg = pd.merge_asof(df_reg.sort_values(by="time_est"), df_floor_prices[["time_est","floor_price"]], on="time_est", direction="backward")
        except ValueError:
            raise Exception("Merge with floor price file failed. Check datetimes in {}_floor_prices csv are correct".format(self.COLLECTION_SLUG))
        df_reg["price_ratio"] = df_reg["price"] / df_reg["floor_price"]
        assert np.sum(df_reg["price_ratio"].isna()) == 0, "There should be no price_ratio NaNs"

        # Remove obvious outliers based on price_ratio.
        logging.info("Removing price_ratio < 0.1 and > 50")
        df_reg = df_reg[(df_reg["price_ratio"] > 0.1) & (df_reg["price_ratio"] < 50)]
        logging.info("Count sales after price_ratio filter: {}".format(len(df_reg)))

        # Only regress on top traits (beta).
        # df_collection = self.get_collection_info(slug=self.COLLECTION_SLUG)
        # df_rare_traits = self.get_rare_traits(df_collection)
        # df_rare_traits = df_rare_traits.sort_values(by="global_rarity")
        # for trait_category in self.TRAIT_CATEGORIES:
        #     print(df_rare_traits[df_rare_traits["trait_category"]==trait_category])
        #     rare_traits = list(df_rare_traits[df_rare_traits["trait_category"]==trait_category]["trait"])
        #     rare_traits = np.sort(rare_traits)
        #     print(rare_traits)
        #     trait_category_cleaned = [c if c in rare_traits else np.nan for c in list(df_reg[trait_category])]
        #     print(np.sort(np.unique(trait_category_cleaned)))
        #     print(df_reg[trait_category].isna().sum())
        #     df_reg[trait_category] = trait_category_cleaned
        #     print(df_reg[trait_category].isna().sum())

        return df_reg

    def run_pricer(self, df_reg, reg_mode):
        """Multivariable regression: price vs all traits + optional rarity_score. Train on assets with last sales.

        Robust, LASSO, or OLS regression. LASSO and OLS have additional filtering for outlier removal.
        """

        if reg_mode == "robust":
            logging.info("Max prices after filtering:\n {}".format(df_reg[["token_id","time_est","price","price_ratio","rarity_rank"]].head()))
            logging.info("Min prices after filtering:\n {}".format(df_reg[["token_id","time_est","price","price_ratio","rarity_rank"]].tail()))

            logging.info("Pricing: Theil-Sen robust regression")
            y_train = df_reg["price_ratio"]
            X_train = self.construct_design_matrix(df_reg, drop_vif=True)
            if self.THEIL_SEN_SAMPLE_RATIO is not None:
                n_subsample = int(self.THEIL_SEN_SAMPLE_RATIO * len(X_train))
                logging.info("n_subsample {}".format(n_subsample))
                model = TheilSenRegressor(fit_intercept=True, random_state=0, n_subsamples=n_subsample).fit(X_train, y_train)
                df_coeff = pd.DataFrame()
                df_coeff["feature"] = X_train.columns
                df_coeff["coeff"] = model.coef_
                logging.info("Theil-Sen coefficients:\n {}".format(df_coeff))
                logging.info("intercept: {}".format(model.intercept_))
                logging.info("Total examples: {}".format(len(X_train)))
                logging.info("r-squared: {}".format(model.score(X_train, y_train)))
            else:
                for n_subsample in [50, 100, 150, 200, 300, 400, 500, 800]:
                    logging.info("n_subsample {}".format(n_subsample))
                    model = TheilSenRegressor(fit_intercept=True, random_state=0, n_subsamples=n_subsample).fit(X_train, y_train)
                    df_coeff = pd.DataFrame()
                    df_coeff["feature"] = X_train.columns
                    df_coeff["coeff"] = model.coef_
                    logging.info("Theil-Sen coefficients:\n {}".format(df_coeff))
                    logging.info("intercept: {}".format(model.intercept_))
                    logging.info("Total examples: {}".format(len(X_train)))
                    print("Theil-Sen r-squared: {}".format(model.score(X_train, y_train)))

                raise Exception("theil_sen_sample_ratio not set in config. Determine best robust-efficiency tradeoff based on r-squared above")
        else: # LASSO or OLS
            # Remove specific traits.
            if self.COLLECTION_SLUG == "3landers":
                df_reg = df_reg[df_reg["legendary"].isna()]

            if self.COLLECTION_SLUG == "karafuru":
                df_reg = df_reg[df_reg["legendary"].isna()]

            if self.COLLECTION_SLUG == "mfers":
                df_reg = df_reg[df_reg["1/1"].isna()]
                df_reg = df_reg[~(df_reg["eyes"] == "zombie eyes")]
                df_reg = df_reg[~(df_reg["eyes"] == "alien eyes")]

            if self.COLLECTION_SLUG == "rumble-kong-league":
                df_reg = df_reg[~(df_reg["fur"].isin(["aurora","camo","gold","zebra","hyper cat","crystal"]))]
                
            if self.COLLECTION_SLUG == "world-of-women-galaxy":
                df_reg = df_reg[df_reg["champion"].isna()]
                df_reg = df_reg[df_reg["guardian"].isna()]

            if self.COLLECTION_SLUG == "world-of-women-nft":
                df_reg = df_reg[~(df_reg["skin tone"] == "night goddess")]
                df_reg = df_reg[~((df_reg["earrings"] == "wow coins") & (df_reg["necklace"] == "wow coin"))] # royalty club
                df_reg = df_reg[~(df_reg["earrings"] == "artist palettes")] # curator club

            # Remove high z-score sales.
            zscore_cutoff_dict = {
                "3landers": 8,
                "bossbeauties": 8,
                "clonex": 3,
                "cyberbrokers": 6,
                "fluf": 8,
                "karafuru": 6, # legendary removed above
                "meebits": 6,
                "mfers": 6,
                "phantabear": 8,
                "pudgypenguins": 8,
                "rumble-kong-league": 10,
                "world-of-women-galaxy": 8,
                "world-of-women-nft": 8, # night goddess, royalty club, and curator club were removed above
            }
            if self.COLLECTION_SLUG in zscore_cutoff_dict:
                logging.info("Removing {} with z-score > {}".format("price_ratio", zscore_cutoff_dict[self.COLLECTION_SLUG]))
                df_reg = df_reg[np.abs(sp.stats.zscore(df_reg["price_ratio"])) < zscore_cutoff_dict[self.COLLECTION_SLUG]]
            else:
                logging.info("Removing {} with z-score > 5".format("price_ratio"))
                df_reg = df_reg[np.abs(sp.stats.zscore(df_reg["price_ratio"])) < 6]

            df_reg = df_reg.sort_values(by="price", ascending=False)
            logging.info("Max prices after all filtering:\n {}".format(df_reg[["token_id","time_est","price","price_ratio","rarity_rank"]].head()))
            logging.info("Min prices after all filtering:\n {}".format(df_reg[["token_id","time_est","price","price_ratio","rarity_rank"]].tail()))

            if reg_mode == "lasso":
                logging.info("Pricing: LASSO regression")
                y_train = df_reg["price_ratio"]
                X_train = self.construct_design_matrix(df_reg)
                X_train = sm.add_constant(X_train)
                mod = sm.OLS(y_train, X_train)
                model = mod.fit_regularized(method='elastic_net', L1_wt=1, alpha=0.0003)
                df_coeff = pd.DataFrame(model.params).reset_index()
                df_coeff.columns = ["feature","coeff"]
                pinv_wexog,_ = pinv_extended(mod.wexog)
                normalized_cov_params = np.dot(pinv_wexog, np.transpose(pinv_wexog))
                logging.info(sm.regression.linear_model.OLSResults(mod, model.params, normalized_cov_params).summary())
                print("LASSO regression r-squared: {}".format(sm.regression.linear_model.OLSResults(mod, model.params, normalized_cov_params).rsquared.round(2)))
            else:
                # OLS.
                logging.info("Pricing: OLS regression")
                y_train = df_reg["price_ratio"]
                X_train = self.construct_design_matrix(df_reg, drop_vif=True)
                X_train = sm.add_constant(X_train)
                logging.info("Fitting OLS")
                model = sm.OLS(y_train, X_train).fit()
                df_coeff = pd.DataFrame(model.params).reset_index()
                df_coeff.columns = ["feature","coeff"]
                logging.info(model.summary())
                print("OLS regression r-squared: {}".format(model.rsquared))

        return model, df_coeff

    def construct_design_matrix(self, df_reg, add_interaction_terms=False, drop_colinear=True, drop_vif=False):
        """Contruct design matrix from dataframe with traits.

        Remove columns that are not trait features, add x*y interaction terms, remove colinear features.
        Avoid dummy variable trap (perfect colinearity and rank deficiency, resulting in large coefficients and stderr).

        Args:
            df_reg: dataframe for regression containing traits.
            add_interaction_terms: add x*y interaction features (not recommended due to overfitting).
            drop_colinear: drop one dummy variable per trait to avoid perfect colinearity.
            drop_vif: drop high VIF variables to reduce colinearity.
        Returns:
            dataframe of dummy variable features for each trait.

        TODO: consider adding option to only include traits or trait groups where rarity within trait_category is low (local_rarity).
        """

        # Hacks for specific collections.
        if self.COLLECTION_SLUG == "meebits":
            df_reg["jersey number"] = np.where(df_reg["jersey number"].isna(), "no_jersey_number", "has_jersey_number")
            df_reg["tattoo motif"] = np.where(df_reg["tattoo motif"].isna(), "no_tattoo_motif", "has_tattoo_motif")
        if self.COLLECTION_SLUG == "raidparty":
            df_reg["genesis"] = df_reg["genesis"].apply(lambda x: str(x)) # TODO: probably should change boolean True/False column to string for all collections
        
        # Config defines whether to add rarity score to design matrix.
        rarity_score = df_reg["rarity_score"]
        if self.USE_RARITY_SCORE:
            logging.info("Rarity scores:\n {}".format(rarity_score.describe()))

        # Remove config ignored traits.
        if self.IGNORE_TRAITS_THEO is not None and len(self.IGNORE_TRAITS_THEO) > 0:
            cols_ignore = [self.IGNORE_TRAITS_THEO["trait_category"][i].lower() for i in range(0, len(self.IGNORE_TRAITS_THEO["trait_category"])) if self.IGNORE_TRAITS_THEO["trait"][i] == "*"]
            df_reg = df_reg.drop(columns=cols_ignore)
            trait_categories_kept = [c for c in self.TRAIT_CATEGORIES if c not in cols_ignore]
        else:
            trait_categories_kept = self.TRAIT_CATEGORIES

        # Remove numeric features (if exists) from categorical variable processing.
        cols_numeric_features = df_reg[trait_categories_kept].select_dtypes(include=np.number).columns.tolist()
        if len(cols_numeric_features) > 0:
            df_reg_numeric = df_reg[cols_numeric_features]
            df_reg = df_reg.drop(columns=cols_numeric_features)
            cols_dummy_trait_categories = [c for c in trait_categories_kept if c not in cols_numeric_features]
        else:
            cols_dummy_trait_categories = trait_categories_kept

        # Categorical variable processing.
        if len(cols_dummy_trait_categories) == 0:
            assert len(cols_numeric_features) > 0, "Must have at least 1 categorial or numeric feature"
            X = df_reg_numeric
        else:
            # Create dummy variables using get_dummies, which drops any columns with only NaNs.
            cols_zero_sum = [col for col in df_reg.columns if df_reg[col].count()==0]
            cols_dummy_trait_categories = [c for c in cols_dummy_trait_categories if c not in cols_zero_sum]
            X = pd.get_dummies(df_reg[cols_dummy_trait_categories], drop_first=False, dummy_na=False)

            if len(self.GROUP_TRAITS) > 0:
                for trait in self.GROUP_TRAITS:
                    trait_groups = self.GROUP_TRAITS[trait]
                    for i in range(0, len(trait_groups)):
                        trait_group = list(trait_groups[i])
                        trait_ungrouped_names = [trait.lower() + "_{}".format(t.lower()) for t in trait_group]
                        trait_ungrouped_names = [t for t in trait_ungrouped_names if t in X.columns]

                        # Sum ungrouped features.
                        sum_trait_group = X[trait_ungrouped_names].sum(axis=1)

                        # New grouped trait feature.
                        trait_group_name = "{}_grouping".format(trait.lower())
                        for j in range(0, len(trait_group)):
                            trait_group_name += "_{}".format(trait_group[j].lower())

                        # Drop ungrouped features and add new grouped feature.
                        X = X.drop(columns=trait_ungrouped_names)
                        logging.info("\nDropped ungrouped features: {}".format(trait_ungrouped_names))
                        X[trait_group_name] = sum_trait_group
                        logging.info("Added grouped feature: {} (count={})".format(trait_group_name, X[trait_group_name].sum()))

            # Interaction terms are not recommended.
            if add_interaction_terms:
                for i in range(0, len(X.columns)):
                    for j in range(0, len(X.columns)):
                        if i > j:
                            X["interaction_{}_{}".format(X.columns[i],X.columns[j])] = X[X.columns[i]] * X[X.columns[j]]

            # Avoid perfect colinearity by dropping one dummy variable per trait. Drop grouped feature (if defined in config) instead of first feature.
            if drop_colinear:
                # Trait counts for informational purposes.
                trait_sums = [np.sum(X[X.columns[X.columns.str.contains(col)]].sum()) for col in cols_dummy_trait_categories]
                df_sums = pd.DataFrame()
                df_sums["trait_category"] = cols_dummy_trait_categories
                df_sums["cnt"] = [np.sum(X[X.columns[X.columns.str.contains("{}_".format(col))]].sum()) for col in cols_dummy_trait_categories]
                df_sums["pct"] = 100 * df_sums["cnt"] / np.sum(df_sums["cnt"])
                logging.info("Trait category counts:\n {}".format(df_sums))

                # Drop first grouped feature if groupings exist.
                if len(self.GROUP_TRAITS) > 0:
                    colinear_traits_drop = []
                    for col in cols_dummy_trait_categories:
                        # Skip any trait category with no traits or is exhibited by <=5% of all assets.
                        if (len(X.columns[X.columns.str.contains(col)]) == 0) or (df_sums[df_sums["trait_category"]==col.split("_")[0]]["pct"].values[0] <= 5.0):
                            continue
                        elif col in [g.lower() for g in self.GROUP_TRAITS]:
                            try:
                                colinear_traits_drop.append(X.columns[X.columns.str.startswith("{}_grouping_".format(col))][0])
                            except IndexError:
                                raise Exception("Index Error: check for typo or missing special character in config value for group_traits")
                        else:
                            colinear_traits_drop.append(X.columns[X.columns.str.startswith("{}_".format(col))][0])
                # Otherwise drop first raw dummy feature.
                else:
                    colinear_traits_drop = [X.columns[X.columns.str.startswith("{}_".format(col))][0] for col in cols_dummy_trait_categories if len(X.columns[X.columns.str.contains(col)]) > 0]
                    colinear_traits_drop = [t for t in colinear_traits_drop if df_sums[df_sums["trait_category"]==t.split("_")[0]]["pct"].values[0] > 5.0]
                logging.info("Dropping features to avoid perfect colinearity: {}".format(colinear_traits_drop))
                X = X.drop(columns=colinear_traits_drop)

            # Add numeric features back in if removed earlier.
            if len(cols_numeric_features) > 0:
                assert len(X) == len(df_reg_numeric), "Number of rows should match"
                X[cols_numeric_features] = df_reg_numeric

        # Further reduce colinearity based on vif score.
        if drop_vif and len(X.columns) > 5:
            logging.info("Calculating VIF for each feature")
            df_vif = pd.DataFrame()
            df_vif["feature"] = X.columns
            df_vif["vif"] = [variance_inflation_factor(X.values, i) for i in range(0, len(X.columns))]
            logging.info(df_vif.describe())
            logging.info(df_vif.sort_values(by="vif", ascending=False))
            max_vif = max(5.0, df_vif["vif"].quantile(0.9))
            vif_drop = df_vif[df_vif.vif>max_vif]["feature"].values
            logging.info("Dropping features w/ VIF > {}: {}".format(max_vif, vif_drop))
            X = X.drop(columns=vif_drop)

        if self.USE_RARITY_SCORE:
            logging.info("Including rarity_score in design matrix")
            X["rarity_score"] = rarity_score

        logging.info("Design matrix dim: {}".format(X.shape))

        return X

    def get_rare_traits(self, df_collection):
        """Calculate rare traits from collection info as defined by config params.
        """

        # Some collections are missing traits in /collection api call
        if self.COLLECTION_SLUG == "cyberbrokers":
            df_assets = self.load_traits(self.COLLECTION_SLUG)
            df_assets = df_assets[self.TRAIT_CATEGORIES]
            df_traits = pd.DataFrame()
            for col in df_assets.columns:
                df_traits_col = pd.DataFrame(df_assets[col].value_counts()).reset_index()
                df_traits_col.columns = ["trait","count"]
                df_traits_col["trait_category"] = col
                df_traits_col = df_traits_col[["trait_category", "trait", "count"]]
                df_traits = df_traits.append(df_traits_col)
        else:
            trait_cols = [col for col in df_collection.columns if "collection.traits" in col]
            df_traits = df_collection[trait_cols].transpose().reset_index().set_axis(["trait_name","count"], axis=1)
            df_traits["trait_category"] = df_traits["trait_name"].apply(lambda x: x.split(".")[2].lower())
            df_traits["trait"] = df_traits["trait_name"].apply(lambda x: x.split(".")[3].lower())
            df_traits = df_traits[["trait_category", "trait", "count"]]

        # Hacks for specific collections. TODO: not sure if this is working correctly
        if self.COLLECTION_SLUG == "meebits":
            cnt_jersey = df_traits[df_traits["trait_category"]=="jersey number"]["count"].sum()
            cnt_tattoo_motif = df_traits[df_traits["trait_category"]=="tattoo motif"]["count"].sum()
            df_traits = df_traits[df_traits["trait_category"]!="jersey number"]
            df_traits = df_traits[df_traits["trait_category"]!="tattoo motif"]
            df_traits = df_traits.append(pd.Series(["jersey number","has_jersey_number",cnt_tattoo_motif]), ignore_index=True)
            df_traits = df_traits.append(pd.Series(["tattoo motif","has_tattoo_motif",cnt_tattoo_motif]), ignore_index=True)

        df_traits["global_rarity"] = df_traits["count"] / self.CNT_TOKEN_IDS
        df_traits["local_diversity"] = 1. / df_traits["count"].groupby(df_traits["trait_category"]).transform("count")
        df_rare_traits = df_traits[(df_traits["count"] > self.GLOBAL_CNT_TH) & (df_traits["global_rarity"] < self.GLOBAL_RARITY_TH) & (df_traits["local_diversity"] > self.LOCAL_DIVERSITY_TH)].reset_index(drop=True)

        # Add config required traits.
        if len(self.REQUIRE_TRAITS) > 0:
            manual_adds = pd.DataFrame()
            for i in range(0, len(self.REQUIRE_TRAITS["trait_category"])):
                manual_adds = manual_adds.append(df_traits[(df_traits["trait_category"]==self.REQUIRE_TRAITS["trait_category"][i].lower()) & (df_traits["trait"]==self.REQUIRE_TRAITS["trait"][i].lower())])
            df_rare_traits = df_rare_traits.append(manual_adds).drop_duplicates(subset=["trait_category","trait"])
        
        # Remove config ignored traits.
        if len(self.IGNORE_TRAITS_REQUIRED_EDGE) > 0:
            for i in range(0, len(self.IGNORE_TRAITS_REQUIRED_EDGE["trait_category"])):
                if self.IGNORE_TRAITS_REQUIRED_EDGE["trait"][i] == "*":
                    logging.info("Ignoring trait category in required edge: {}".format(self.IGNORE_TRAITS_REQUIRED_EDGE["trait_category"][i]))
                    df_rare_traits = df_rare_traits.drop(labels=df_rare_traits[df_rare_traits["trait_category"]==self.IGNORE_TRAITS_REQUIRED_EDGE["trait_category"][i].lower()].index, axis=0)
                else:
                    df_rare_traits = df_rare_traits.drop(labels=df_rare_traits[(df_rare_traits["trait_category"]==self.IGNORE_TRAITS_REQUIRED_EDGE["trait_category"][i].lower()) & (df_rare_traits["trait"]==self.IGNORE_TRAITS_REQUIRED_EDGE["trait"][i].lower())].index, axis=0)
       
        df_rare_traits = df_rare_traits.sort_values(by=["trait_category","count"]).reset_index(drop=True)

        if len(df_rare_traits) == 0:
            raise ValueError("No rare traits under TH contraints")
        return df_rare_traits

    def prep_required_edge(self, df_assets, df_assets_saved=None, max_price_level=8):
        """Add order book of rarest trait, defined as any trait with global_rarity < global_rarity_th (config).
        Traits in priority_traits (config) supersede other traits with lower global_rarity.
        If global_rarity of asset's rarest trait is > global_rarity_th (config), then it will be ranked at the bottom of opportunity set.

        Args:
            max_price_level: max depth of order book (1 indexed, meaning 1 is the top level).

        TODO: support numerical traits (e.g. rumble kongs)
        """

        def get_price_levels(r):
            """Helper function to find lowest prices for trait.
            """
            if df_assets_saved is not None:
                df_listed_match = df_assets_saved[df_assets_saved[r["trait_category"]]==r["trait"]].sort_values(by="price")
            else:
                df_listed_match = df_assets[df_assets[r["trait_category"]]==r["trait"]].sort_values(by="price")
            return pd.Series(list(df_listed_match["price"].iloc[0:max_price_level]))

        def process_grouped_traits(r):
            """Helper function to add grouped trait column.
            """
            for trait_category in self.GROUP_TRAITS:
                if trait_category == r["trait_category"]:
                    trait_groups = self.GROUP_TRAITS[trait_category]
                    for i in range(0, len(trait_groups)):
                        trait_group = [t.lower() for t in list(trait_groups[i])] # really should change entire config to lower case
                        if r["trait"] in trait_group:
                            trait_group_name = "{}_grouping".format(trait_category.lower())
                            for j in range(0, len(trait_group)):
                                trait_group_name += "_{}".format(trait_group[j].lower())
                            return trait_group_name
            return r["trait"]

        def get_rarest_trait_levels(r):
            """Helper function to get book for rarest trait.

            Returns:
                pandas series where index 0 is rarest trait formatted name, index 1 is global_rarity, and index >=2 are rarest trait prices levels.
            """

            global_rarity_lowest = 1
            rarest_trait_levels = [np.nan] * max_price_level

            # Get levels for rarest trait.
            for trait_category in self.TRAIT_CATEGORIES:
                if (len(self.IGNORE_TRAITS_THEO) > 0) and (trait_category in self.IGNORE_TRAITS_THEO["trait_category"]): # TODO: should have and trait="*"
                    logging.debug("Ignoring trait category in pricer: {}".format(trait_category))
                    continue
                
                # Rare trait price levels.
                df_rare_trait_match = df_rare_traits[(df_rare_traits["trait_category"]==trait_category) & (df_rare_traits["trait"]==r[trait_category])]
                cnt_rare = len(df_rare_trait_match)
                assert cnt_rare <= 1, "There should not be more than 1 match"
                
                # Rare trait group price levels, if trait category is in group_traits.
                if (len(self.GROUP_TRAITS) > 0) and (pd.isna(r[trait_category]) == False):
                    df_rare_trait_group_match = df_rare_traits[(df_rare_traits["trait_category"]==trait_category) & ((df_rare_traits["trait_group"]==r[trait_category]) | (df_rare_traits["trait_group"].str.contains("_"+r[trait_category]+"_", regex=False)))]
                    cnt_group = len(df_rare_trait_group_match) # this is 1 if trait not in group_traits (but trait is not nan), since trait_group = trait in that case based on process_grouped_traits, can be 0 or >1 too
                else:
                    cnt_group = 0

                # Trait category is in group_traits.
                if (cnt_rare == 1) and (cnt_group > 1):
                    global_rarity = df_rare_trait_match["global_rarity"].iloc[0]
                    if global_rarity < global_rarity_lowest:
                        prices_group = []
                        for i in range(0, cnt_group):
                            prices_group.extend(list(df_rare_trait_group_match[["price_{}".format(p+1) for p in range(0,max_price_level)]].iloc[i]))
                        prices_group = sorted(prices_group, key=lambda f: float('inf') if np.isnan(f) else f)
                        prices_group = prices_group[0:max_price_level]
                        trait_formatted = "{}_{}".format(df_rare_trait_match["trait_category"].iloc[0], df_rare_trait_match["trait"].iloc[0])
                        rarest_trait_levels = [trait_formatted, global_rarity]
                        rarest_trait_levels.extend(prices_group)
                        global_rarity_lowest = df_rare_trait_match["global_rarity"].iloc[0]
                # Trait category is not in group_traits.
                if (cnt_rare == 1) and (cnt_group <= 1):
                    is_priority_trait = ((trait_category in [t.lower() for t in self.PRIORITY_TRAITS]) and (r[trait_category] in [t.lower() for t in self.PRIORITY_TRAITS[trait_category][0]]))
                    global_rarity = df_rare_trait_match["global_rarity"].iloc[0]
                    if (global_rarity < global_rarity_lowest) or is_priority_trait:
                        trait_formatted = "{}_{}".format(df_rare_trait_match["trait_category"].iloc[0], df_rare_trait_match["trait"].iloc[0])
                        rarest_trait_levels = [trait_formatted, global_rarity]
                        rarest_trait_levels.extend(list(df_rare_trait_match[["price_{}".format(p+1) for p in range(0,max_price_level)]].iloc[0]))
                        global_rarity_lowest = df_rare_trait_match["global_rarity"].iloc[0]
                        if is_priority_trait:
                            break
                    else:
                        continue

            # In fast mode, add newly listed price. Note price is not added if already in top levels.
            if df_assets_saved is not None:
                logging.info("Adding new price level for token_id {} rarest trait: {}".format(r["token_id"], r["price"]))
                saved_rarest_trait_levels = rarest_trait_levels[2:] # index 0 and 1 are trait_formatted and global_rarity
                if r["price"] in rarest_trait_levels:
                    return pd.Series(rarest_trait_levels)
                saved_rarest_trait_levels.append(r["price"])
                saved_rarest_trait_levels = sorted(saved_rarest_trait_levels, key=lambda f: float('inf') if np.isnan(f) else f)
                del saved_rarest_trait_levels[-1]
                rarest_trait_levels[2:len(rarest_trait_levels)] = saved_rarest_trait_levels
            return pd.Series(rarest_trait_levels)

        # Get price levels for rare traits (global_rarity < global_rarity_th).
        df_collection = self.get_collection_info(slug=self.COLLECTION_SLUG, use_saved=True)
        df_rare_traits = self.get_rare_traits(df_collection)
        df_rare_traits = df_rare_traits.sort_values(by="global_rarity")

        if len(self.GROUP_TRAITS) > 0:
            df_rare_traits["trait_group"] = df_rare_traits.apply(lambda r: process_grouped_traits(r), axis=1)

        df_rare_traits[["price_{}".format(p+1) for p in range(0,max_price_level)]] = df_rare_traits.apply(lambda r: get_price_levels(r), axis=1)
        logging.info("Example rare traits (global_rarity < global_rarity_th):\n {}".format(df_rare_traits.head(10)))

        # Find rarest trait for asset and append price levels for that trait.
        price_level_cols = ["rarest_trait","global_rarity"]
        price_level_cols.extend(["rarest_trait_price_{}".format(p+1) for p in range(0,max_price_level)])
        try:
            df_assets[price_level_cols] = df_assets.apply(lambda r: get_rarest_trait_levels(r), axis=1)
        except ValueError:
            print("No token_ids with traits within global_rarity_th so required_edge cannot be calculated:\n{}".format(df_assets))
        df_assets = df_assets.sort_values(by="price_ratio_diff", ascending=False)
        logging.info("Count NaN rows after appending rarest trait order book: {} (out of {} total rows)".format(len(df_assets[df_assets["rarest_trait"].isna()]), len(df_assets)))
        return df_assets

    def calc_required_edge(self, df_assets):
        """Calculate required edge for each listed token_id.

        Some rationale. Consider two token_ids A and B, both have same price_ratio_diff (theoretical mispricing in units of price_ratio):
        - A and B both offered at 10 (TVs are equal). Order book is 10,11,12 for rarest trait in A vs. 10,15,20 for rarest trait in B. Prefer buying B for 10 b/c can likely sell higher than A (arguably should be reflected in TV by taking deeper levels into account).
        - A offered at 10, B offered at 15 (TVs differ). Order book is 10,11,12.1 for rarest trait in A vs. 15,16.5,18.15 for rarest trait in B (10% increase per level). Prefer buying A b/c less capital and closer to floor is more liquid.

        Assume 4 orthogonal components estimate true/market required edge:
            floor_price_ratio_edge: prefer price closer to global floor (unless infinite capital).
            global_rarity_edge: prefer rarer trait.
            rarest_trait_depth_edge: prefer first level for rarest trait.
            rarest_trait_liquidity_edge: prefer difference with level behind to be high for rarest trait.
        Additional OTM and ITM fudge components:
            otm_fudge_edge: require exponentially more edge if price is more than 75% above global floor price.
            itm_fudge_factor: require exponentially less edge if price is below global floor price 

        TODO: may need a mid-tier or relative dict for prioritizing traits, e.g. skin tone cool blue (5%) should probably supercede facial feature flashy blue (3%), but cool blue shouldn't supercede red blue bolt.
        TODO: maybe incorporate rarest trait trait category diversity (e.g. 0.5% rarity worth more if only 5 traits in category vs 50 traits).
        TODO: maybe incorporate time since last sale of rarest trait and/or how many recent sales.
        """

        def check_is_rarest_trait_large_group(r, large_group_cnt_th=3):
            """For heuristic in lieu of grouping price levels together based on group_traits in prep_required_edge.
            """
            if type(r["rarest_trait"]) != str:
                if np.isnan(r["rarest_trait"]):
                    logging.info("There is at least one nan rarest_trait. Consider raising global_rarity_th")
                    return False
                else:
                    raise Exception("Malformed rarest_trait: {}".format(r["rarest_trait"]))
            rarest_trait_category = r["rarest_trait"].split("_", 1)[0]
            trait_category_groups = [c.lower() for c in self.GROUP_TRAITS]
            if rarest_trait_category not in trait_category_groups:
                return False
            rarest_trait_category_group = [t.lower() for t in self.GROUP_TRAITS[rarest_trait_category][0]]
            rarest_trait = r["rarest_trait"].split("_", 1)[1]
            if rarest_trait in rarest_trait_category_group and len(rarest_trait_category_group) > large_group_cnt_th:
                return True
            return False

        scaling_factor = 10.

        # Floor price ratio edge.
        df_assets["floor_price_ratio_edge"] = df_assets["price_ratio"] / scaling_factor

        # Global rarity edge.
        df_assets["global_rarity_edge"] = df_assets["global_rarity"]

        # Rarest trait depth edge.
        price_level_cols = [c for c in df_assets.columns if "rarest_trait_price_" in c]
        df_assets["level"] = df_assets.apply(lambda r: list(r[price_level_cols]).index(r["price"]) + 1 if r["price"] in list(r[price_level_cols]) else len(price_level_cols) + 2, axis=1)
        df_assets["rarest_trait_depth_edge"] = np.log(df_assets["level"]) / scaling_factor

        # Rarest trait liquidity edge.
        df_assets["floor_price"] = df_assets["price"] / df_assets["price_ratio"] # TODO: ugly way to get global floor
        df_assets["next_level_price"] = df_assets.apply(lambda r: r[price_level_cols].iloc[r["level"]] if r["level"] < len(r[price_level_cols]) else np.nan, axis=1)
        df_assets["is_rarest_trait_large_group"] = df_assets.apply(lambda r: check_is_rarest_trait_large_group(r), axis=1)
        df_assets["next_level_price_diff"] = df_assets.apply(lambda r: r["next_level_price"] - r["price"] if r["level"] < len(r[price_level_cols]) and r["is_rarest_trait_large_group"]==False else 0, axis=1)
        df_assets["rarest_trait_liquidity_edge"] = df_assets.apply(lambda r: np.log(1 / (r["next_level_price_diff"] / r["floor_price"])) / scaling_factor if r["next_level_price_diff"] > 0 else np.log(1 / 0.0001) / scaling_factor, axis=1)

        # OTM fudge edge.
        f = 1.75
        df_assets["otm_fudge_edge"] = np.where((df_assets["price_ratio"] > f) & (df_assets["price_ratio_diff"] > 0), np.exp(df_assets["price_ratio"] - f) / scaling_factor, 0) # always >= 0

        # ITM fudge factor.
        k = 6.
        df_assets["itm_fudge_factor"] = np.where(df_assets["price_ratio"] < 1, (np.exp(k * df_assets["price_ratio"]) - 1) / (np.exp(k) - 1), 1) # always >0 and <=1

        # Root sum of squares of components including fudge factors to get total required edge.
        df_assets["required_edge"] = np.sqrt(df_assets["floor_price_ratio_edge"]**2 + df_assets["global_rarity_edge"]**2 + df_assets["rarest_trait_depth_edge"]**2 + df_assets["rarest_trait_liquidity_edge"]**2 + df_assets["otm_fudge_edge"]**2) * df_assets["itm_fudge_factor"]
        
        # Ratio of theoretical edge to required edge (both in price/floor_price space).
        df_assets["edge"] = df_assets["price_ratio_diff"]
        df_assets["edge_ratio"] = df_assets["edge"] / df_assets["required_edge"]
        return df_assets

    def find_dumb_opps(self):
        """Naive alert for listings much lower than global floor.
        """

        logging.info("Getting latest listings from OS activity page")
        df_listed = self.get_latest_listings(lookback_seconds=60)
        df_collection = self.get_collection_info(slug=self.COLLECTION_SLUG, connection_timeout=4)
        if df_collection is None:
            print("Loading saved floor price NOT live")
            df_floor_prices = pd.read_csv("data_warehouse/floor_prices/{slug}_floor_prices.csv".format(slug=self.COLLECTION_SLUG))
            global_floor_price = df_floor_prices.iloc[-1]["floor_price"]
        else:
            global_floor_price = df_collection["collection.stats.floor_price"].values[0]
        print("Global floor: {}".format(global_floor_price))
        df_listed = df_listed[df_listed["is_auction"]==False]
        df_listed = df_listed[["token_id","time_est","price","currency"]]
        df_listed = df_listed.sort_values(by="price")
        logging.info("Latest listings:\n{}\n".format(df_listed))
        for i, row in df_listed.iterrows():
            if row["price"] < global_floor_price * 0.9:
                print("https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, row["token_id"]))
                os.system("say -v Samantha 'Listing below floor.'")

    def find_opps(self, load_saved_sales=False, load_saved_listed=False, reg_mode="ols", fast_mode=False, last_sale_only=True, edge_ratio_trade_alert=1.0, price_single_asset=None, looks=False):
        """Calculate theoretical value, edge, and required edge to rank opportunities.

        Theoretical value: regress last sale price_ratio vs traits + rarity score.
        Edge: difference between regression prediction and current listed price_ratio.
        Required edge: required edge to trade, a function of asset price, rarest trait order book, rarest trait global rarity, and global floor. Independent of regression.
        Interpretation: price_ratio_diff=0.5 means theoretical value is 0.5*global_floor_price higher than current price. This is the "edge" in price-to-global-floor-ratio units.
        Anecdotally, z-score based outlier removal + standard OLS preferred for more mature collections with obvious outlier sales, while minimal outlier removal + Theil-Sen robust regression (robust_mode=True) preferred for less mature collections with no huge sales.

        TODO: number of traits could matter (e.g. exhibits 1/6 vs 6/6 possible trait categories).
        TODO: check how many top opps traded at the listed price or were relisted higher.
        TODO: weigh recent data more: https://stats.stackexchange.com/questions/454415/how-to-account-for-the-recency-of-the-observations-in-a-regression-problem
        TODO: instead of group_traits, just include rare traits (e.g. <5%). useful for collections like clonex with high number of traits and some rare trait categories.
        """

        find_opps_start_time = time.time()

        df_assets = self.load_traits(self.COLLECTION_SLUG)

        # TODO: maybe add assertion that rarity.tools (if exists) score is saved to traits file instead of custom score.

        # Get sales (if any) for each asset.
        if load_saved_sales or fast_mode:
            # Default is last sales only.
            if last_sale_only == False:
                file_path = "data_warehouse/sales/{slug}/{slug}_snapshot_sales_dynamic_all.csv".format(slug=self.COLLECTION_SLUG)
            else:
                file_path = "data_warehouse/sales/{slug}/{slug}_snapshot_sales_dynamic.csv".format(slug=self.COLLECTION_SLUG)
            logging.info("Loading sales snapshot: {}".format(file_path))
            df_sales_w_traits = pd.read_csv(file_path, dtype={"token_id": object})

            # Ensure using latest rarity scores (redundant if saved rarity scores have not been changed).
            df_sales_w_traits = df_sales_w_traits.drop(columns=["rarity_score","rarity_rank"], errors='ignore')
            df_sales_w_traits = pd.merge(df_sales_w_traits, df_assets[["token_id","rarity_score","rarity_rank"]], on="token_id", how="left")
        else:
            logging.info("Getting sales")
            df_sales = self.get_last_sale(token_ids=df_assets["token_id"], token_contract_address=self.CONTRACT_ADDRESS)
            df_sales_w_traits = pd.merge(df_sales, df_assets, on="token_id", how="left")
            if self.write_to_file:
                logging.info("Saving sales snapshot")
                df_sales_w_traits.to_csv("data_warehouse/sales/{slug}/{slug}_snapshot_sales_{ts}.csv".format(slug=self.COLLECTION_SLUG, ts=datetime.now().strftime("%Y%m%dT%H%M%S")), index=False)

                # Default is last sales only.
                if last_sale_only == False:
                    logging.info("Updating dynamic all sales file (not just last sale)")
                    df_sales_w_traits["src"] = "opensea"
                    file_path = "data_warehouse/sales/{slug}/{slug}_snapshot_sales_dynamic_all_sales.csv".format(slug=self.COLLECTION_SLUG)
                    df_sales_dynamic = pd.read_csv(file_path, dtype={"token_id": object})
                    df_sales_w_traits["time_est_trunc"] = df_sales_w_traits["time_est"].astype(str).apply(lambda x: x[:-1]) # truncate second
                    df_sales_dynamic["time_est_trunc"] = df_sales_dynamic["time_est"].apply(lambda x: x[:-1]) # truncate second
                    df_sales_dynamic = df_sales_dynamic.append(df_sales_w_traits)
                    df_sales_dynamic = df_sales_dynamic.drop_duplicates(subset=["token_id","time_est_trunc"], keep="first")
                    df_sales_dynamic = df_sales_dynamic.drop(columns=["time_est_trunc"])
                    logging.info("Count sales after updating with latest sales from OS: {}".format(len(df_sales_dynamic)))
                    df_sales_dynamic.to_csv("data_warehouse/sales/{slug}/{slug}_snapshot_sales_dynamic_all_sales.csv".format(slug=self.COLLECTION_SLUG), index=False)
                else:
                    logging.info("Updating dynamic sales file")
                    df_sales_w_traits.to_csv("data_warehouse/sales/{slug}/{slug}_snapshot_sales_dynamic.csv".format(slug=self.COLLECTION_SLUG), index=False)
        logging.info("Count sales before removing non-eth prices: {}".format(len(df_sales_w_traits)))
        df_sales_w_traits = df_sales_w_traits[df_sales_w_traits["currency"].isin(["eth","weth"])] # known issue: usdc-to-eth conversion factor returned by OS is off, so keep only eth sales
        logging.info("Count sales after removing non-eth prices: {}".format(len(df_sales_w_traits)))

        # Get listed assets.
        if load_saved_listed:
            file_path = "data_warehouse/listed/{slug}/{slug}_snapshot_listed_dynamic.csv".format(slug=self.COLLECTION_SLUG)
            logging.info("Loading latest listed snapshot (dynamic file): {}".format(file_path))
            df_listed = pd.read_csv(file_path, dtype={"token_id": object})
        elif fast_mode:
            file_path = "data_warehouse/listed/{slug}/{slug}_snapshot_listed_dynamic.csv".format(slug=self.COLLECTION_SLUG)
            logging.info("Loading saved listed snapshot (for required edge calc): {}".format(file_path))
            df_listed_saved = pd.read_csv(file_path, dtype={"token_id": object})

            if price_single_asset is not None:
                cols = ["token_id","time_est","is_auction","price","currency","price_eth","price_usd"]
                df_listed = pd.DataFrame(columns=cols)
                # TODO: this price is a filler placeholder, probably should remove later on in output
                price_input = 1.25
                df_listed = df_listed.append(pd.Series([price_single_asset,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),False,price_input,"eth",1,3000.0], index=cols), ignore_index=True)
                logging.info("Pricing single asset:\n".format(df_listed))
            else:
                if looks:
                    logging.info("Getting latest listings from LR")
                    df_listed = self.get_latest_listings_lr()
                else:
                    logging.info("Getting latest listings from OS")
                    df_listed = self.get_latest_listings()

                if df_listed is None:
                    # sys.exit()
                    return None # TODO: Heroku change

                logging.info("Count listings before updating with latest listings from OS activity page: {}".format(len(df_listed_saved)))
                df_listed_saved = df_listed_saved.append(df_listed)
                df_listed_saved = df_listed_saved.sort_values(by="price") # will keep lowest price if multiple listings for same token_id
                df_listed_saved = df_listed_saved.drop_duplicates(subset=["token_id"], keep="first") # does not take listing expiration time into account
                logging.info("Count listings after updating with latest listings from OS activity page: {}".format(len(df_listed_saved)))

                if self.write_to_file:
                    logging.info("Saving latest listings to {}".format(file_path))
                    df_listed_saved.to_csv("data_warehouse/listed/{slug}/{slug}_snapshot_listed_dynamic.csv".format(slug=self.COLLECTION_SLUG), index=False)
        else:
            logging.info("Getting currently listed prices")
            df_listed = self.get_current_listings(token_ids=df_assets["token_id"], token_contract_address=self.CONTRACT_ADDRESS)
            if self.write_to_file:
                logging.info("Saving listed snapshot")
                df_listed.to_csv("data_warehouse/listed/{slug}/{slug}_snapshot_listed_{ts}.csv".format(slug=self.COLLECTION_SLUG, ts=datetime.now().strftime("%Y%m%dT%H%M%S")), index=False)
                
                # Note if listing is added during the scrape, it will not show up in dynamic file even if was previously in it from OS activity fast_mode scrape, since the entire file is overwritten
                logging.info("Updating dynamic listing file")
                df_listed.to_csv("data_warehouse/listed/{slug}/{slug}_snapshot_listed_dynamic.csv".format(slug=self.COLLECTION_SLUG), index=False)
        logging.info("Count listed before removing non-eth prices: {}".format(len(df_listed)))
        df_listed = df_listed[df_listed["currency"].isin(["eth","weth"])] # known issue: usdc-to-eth conversion factor returned by OS is off, so keep only eth sales
        logging.info("Count listed after removing non-eth prices: {}".format(len(df_listed)))

        # Filtering data for regression.
        df_reg = self.process_sales(df_sales_w_traits)
        logging.info("Sale price distribution (entire regression range):\n{}".format(df_reg[["price","price_ratio"]].describe(percentiles=[.25,.5,.75,.9,.95])))
        logging.info("Sale price distribution (last 3 days):\n{}".format(df_reg[df_reg["time_est"] > (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d")][["price","price_ratio"]].describe(percentiles=[.25,.5,.75,.9,.95])))

        # Run regression.
        y_var = "price_ratio" # currently only price_ratio space is supported
        model, df_coeff = self.run_pricer(df_reg, reg_mode)

        # Predict for all assets. TODO: only need to predict for assets with currently listed prices (currently construct_design_matrix does not work properly for subset of assets).
        logging.info("Calculating theoretical values for all assets")
        X_all = self.construct_design_matrix(df_assets, drop_colinear=False)
        cols_missing_in_train = [col for col in X_all.columns if col not in df_coeff["feature"].tolist()]
        logging.info("Columns removed in training: {}".format(cols_missing_in_train))
        X_all = X_all.drop(columns=cols_missing_in_train) # note traits removed in process_sales are ignored
        if reg_mode != "robust":
            X_all = sm.add_constant(X_all)
        X_all = X_all[df_coeff["feature"]] # set column order (redundant here but needed if loading pickled model)
        y_pred = model.predict(X_all)
        df_assets["{}_pred".format(y_var)] = y_pred
        
        # Get global floor and calc price_ratio for each asset.
        if fast_mode or (price_single_asset is not None):
            logging.info("Removing auctions\n".format(df_listed_saved[df_listed_saved["is_auction"]==False]))
            # Use last saved listings in required edge calc
            df_assets_saved = pd.merge(df_assets, df_listed_saved[df_listed_saved["is_auction"]==False][["token_id","time_est","price"]], on="token_id", how="inner")
        df_assets = pd.merge(df_assets, df_listed[df_listed["is_auction"]==False][["token_id","time_est","price"]], on="token_id", how="inner") # TODO: rename df_assets from here down and move fast_mode above to within use_required_edge
        df_collection = self.get_collection_info(slug=self.COLLECTION_SLUG, connection_timeout=4)
        if df_collection is None:
            print("Loading saved floor price NOT live")
            df_floor_prices = pd.read_csv("data_warehouse/floor_prices/{slug}_floor_prices.csv".format(slug=self.COLLECTION_SLUG))
            global_floor_price = df_floor_prices.iloc[-1]["floor_price"]
        else:
            global_floor_price = df_collection["collection.stats.floor_price"].values[0]
        print("Global floor: {}".format(global_floor_price))
        df_assets["price_ratio"] = df_assets["price"] / global_floor_price

        # Calc edge (predicted vs listed difference) and rank by edge.
        df_assets["{}_diff".format(y_var)] = df_assets["{}_pred".format(y_var)].astype(float) - df_assets[y_var].astype(float)
        logging.info("Listed opps distribution:\n{}".format(df_assets[["price","price_ratio","{}_pred".format(y_var),"{}_diff".format(y_var)]].describe()))
        logging.info("Top opportunities by edge (price_ratio_diff):\n")
        logging.info(df_assets.sort_values(by="{}_diff".format(y_var), ascending=False).reset_index(drop=True).set_index("token_id").head(10))

        if self.USE_REQUIRED_EDGE: # TODO: refactor
            # Append required edge.
            logging.info("Calculating required edge for listed assets")
            if fast_mode or (price_single_asset is not None):
                df_assets = self.prep_required_edge(df_assets=df_assets, df_assets_saved=df_assets_saved)
            else:
                df_assets = self.prep_required_edge(df_assets=df_assets)
            df_assets = self.calc_required_edge(df_assets=df_assets)

            # Join regression coefficient, handles grouped features correctly. NaN means feature was not included in model.
            df_coeff["trait_category"] = df_coeff["feature"].apply(lambda x: x.split("_", 1)[0] if x not in ["const","rarity_score"] else x)
            df_coeff["trait"] = df_coeff["feature"].apply(lambda x: x.split("_", 1)[1] if x not in ["const","rarity_score"] else x)
            df_coeff["trait"] = df_coeff["trait"].apply(lambda x: x.split("_", 1)[1] if "grouping_" in x else x)
            traits_w_underscore = ["cool_1","cool_2","classy_1","classy_2","wild_1","wild_2","exotic_1","exotic_2"] # only cool-cats-nft has traits with "_" in name
            df_coeff["trait"] = df_coeff["trait"].apply(lambda x: x.replace("_","") if x in traits_w_underscore else x)
            df_coeff["trait_cnt"] = df_coeff["trait"].apply(lambda x: len(x.split("_")) if x != "rarity_score" else 1)
            df_coeff = df_coeff.loc[df_coeff.index.repeat(df_coeff["trait_cnt"])]
            if self.COLLECTION_SLUG == "cool-cats-nft":
                df_coeff["rn"] = df_coeff.groupby(["feature"]).cumcount() + 1
            else:
                df_coeff["rn"] = df_coeff.groupby(["trait"]).cumcount() + 1
            df_coeff["trait"] = df_coeff.apply(lambda r: r["trait"].split("_")[r["rn"]-1] if r["trait_cnt"] > 1 else r["trait"], axis=1)
            df_coeff["trait"] = df_coeff.apply(lambda r: "{}_{}".format(r["trait_category"], r["trait"]) if r["trait"] not in ["const","rarity_score"] else r["trait"], axis=1)
            df_assets = pd.merge(df_assets, df_coeff.rename(columns={"trait":"rarest_trait"}), on="rarest_trait", how="left")
            df_assets = df_assets.drop(columns=["rn","trait_cnt"])

            # Rank by edge ratio.
            df_assets = df_assets.sort_values(by="edge_ratio", ascending=False)
            df_assets = df_assets.drop(columns=list(self.TRAIT_CATEGORIES), errors="ignore")
            if self.write_to_file and fast_mode==False:
                logging.info("Saving opps snapshot")
                # Timestamp in file name is misleading if load_listed=True b/c it is time at run time using old listed prices (and also current global floor).
                df_assets.to_csv("data_warehouse/opportunities/{slug}/{pricer}/{slug}_opps_{pricer}_{ts}.csv".format(slug=self.COLLECTION_SLUG, pricer=reg_mode, ts=datetime.now().strftime("%Y%m%dT%H%M%S")), index=False)
            df_assets["theo"] = np.round(df_assets["edge"] * global_floor_price + df_assets["price"], 3)
            df_assets = df_assets.rename(columns={"rarity_rank":"rarity", "level":"lvl", "next_level_price_diff":"nxt_lvl_diff", "rarest_trait_price_1":"lvl_1", "rarest_trait_price_2":"lvl_2", "rarest_trait_price_3":"lvl_3", "rarest_trait_price_4":"lvl_4", "rarest_trait_price_5":"lvl_5"})
            cols = ["name","rarity","theo","price","edge","edge_ratio","rarest_trait","coeff","global_rarity","lvl","nxt_lvl_diff","lvl_1","lvl_2","lvl_3","lvl_4","lvl_5"]
            df_output = df_assets.reset_index(drop=True).set_index("token_id")[cols]
            df_output["rarity"] = df_output["rarity"].astype(int)
            df_output["theo"] = np.round(df_output["theo"], 3)
            df_output["edge"] = np.round(df_output["edge"], 3)
            df_output["edge_ratio"] = np.round(df_output["edge_ratio"], 3)
            df_output["coeff"] = np.round(df_output["coeff"], 3)
            df_output["global_rarity"] = np.round(df_output["global_rarity"], 3)
            print("Top opportunities by edge ratio:\n", df_output.head(5))

            if load_saved_listed:
                print("\nTop opportunities by edge ratio with price < global floor removed:\n", df_output[df_output["price"] > global_floor_price].head(20))

            # Sound alerts.
            if fast_mode:
                return df_output.to_dict() # TODO: Heroku change

                file_path_fast_opps = "data_warehouse/opportunities/{slug}/{pricer}/{slug}_fast_opps.csv".format(slug=self.COLLECTION_SLUG, pricer=reg_mode)
                df_fast_saved = pd.read_csv(file_path_fast_opps, index_col="token_id")
                date_today = datetime.now().strftime("%Y-%m-%d")
                df_fast_saved_today = df_fast_saved[df_fast_saved["date"]==date_today]

                # TODO: change this to actual listing time
                df_output["date"] = datetime.now().strftime("%Y-%m-%d")
                df_output["time_est"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if (len(df_fast_saved_today)==0) and (len(df_output[df_output["edge_ratio"] > edge_ratio_trade_alert]) > 0):
                    os.system("say -v Samantha 'Found {} first one today.'".format(self.SLUG_SHORT))
                else:
                    for i, opp in df_output[df_output["edge_ratio"] > edge_ratio_trade_alert].iterrows():
                        if opp["name"] not in df_fast_saved_today["name"].tolist():
                            if opp["edge_ratio"] > 6 * edge_ratio_trade_alert:
                                os.system("say -v Samantha 'Insane {}.'".format(self.SLUG_SHORT))
                            elif (opp["edge_ratio"] > 3 * edge_ratio_trade_alert) or (opp["edge"] > 2):
                                os.system("say -v Samantha 'Amazing {}.'".format(self.SLUG_SHORT))
                            elif (opp["edge_ratio"] > edge_ratio_trade_alert) or (opp["edge"] > 1):
                                os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                            else:
                                print("Found opp")
                                # os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                            print("Buy: https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, opp.name)) # pandas.Series.name not opp["name"]
                        else:
                            existing_row = df_fast_saved_today[(df_fast_saved_today["name"]==opp["name"]) & (np.round(df_fast_saved_today["price"],3)==np.round(opp["price"],3))]
                            if len(existing_row) == 0:
                                if opp["edge_ratio"] > 6 * edge_ratio_trade_alert:
                                    os.system("say -v Samantha 'Insane {}.'".format(self.SLUG_SHORT))
                                elif (opp["edge_ratio"] > 3 * edge_ratio_trade_alert) or (opp["edge"] > 2):
                                    os.system("say -v Samantha 'Amazing {}.'".format(self.SLUG_SHORT))
                                elif (opp["edge_ratio"] > edge_ratio_trade_alert) or (opp["edge"] > 1):
                                    os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                                else:
                                    print("Found opp")
                                    # os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                                print("Buy: https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, opp.name))
                if self.write_to_file:
                    logging.info("Saving to fast_mode file")
                    df_fast_saved = pd.read_csv(file_path_fast_opps, index_col="token_id")
                    df_fast_saved = df_fast_saved.append(df_output)
                    df_fast_saved = df_fast_saved.drop_duplicates(subset=["name","date","price","lvl","nxt_lvl_diff"])
                    df_fast_saved.to_csv(file_path_fast_opps)
        else: # TODO: refactor (this sorting by edge section since it overlaps with edge ratio section above)
            # Currently only rumble-kong-league is edge-only, since there is no required edge logic for numerical only features
            if fast_mode:
                file_path_fast_opps = "data_warehouse/opportunities/{slug}/{pricer}/{slug}_fast_opps.csv".format(slug=self.COLLECTION_SLUG, pricer=reg_mode)

                df_output = df_assets.copy()
                df_output = df_output.rename(columns={"price_ratio_diff":"edge", "rarity_rank":"rarity"})
                df_output["theo"] = np.round(df_output["edge"] * global_floor_price + df_output["price"], 3)
                
                if self.COLLECTION_SLUG == "rumble-kong-league":
                    for i, opp in df_output.iterrows():
                        if opp["fur"] in ["aurora","camo","gold","zebra","hyper cat","crystal"]:
                            print("Rare fur kong: https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, opp["token_id"]))
                            os.system("say -v Samantha 'Rare fur {}.'".format(self.SLUG_SHORT))
                    df_output["sum_boost"] = df_output["defense"] + df_output["finish"] + df_output["shooting"] + df_output["vision"]
                    cols = ["name","rarity","theo","price","edge","defense","finish","shooting","vision","sum_boost"]
                else:
                    cols = ["name","rarity","theo","price","edge"]
                df_output = df_output.reset_index(drop=True).set_index("token_id")[cols]
                df_output = df_output.sort_values(by="edge", ascending=False)
                print("Top opportunities by edge:\n", df_output.head(20))
                
                df_fast_saved = pd.read_csv("data_warehouse/opportunities/{slug}/{pricer}/{slug}_fast_opps.csv".format(slug=self.COLLECTION_SLUG, pricer=reg_mode), index_col="token_id")
                date_today = datetime.now().strftime("%Y-%m-%d")
                df_fast_saved_today = df_fast_saved[df_fast_saved["date"]==date_today]

                # TODO: change this to actual listing time
                df_output["date"] = datetime.now().strftime("%Y-%m-%d")
                df_output["time_est"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                edge_trade_alert = 0.14
                if (len(df_fast_saved_today)==0) and (len(df_output[df_output["edge"] > edge_trade_alert]) > 0):
                    os.system("say -v Samantha 'Found {} first one today.'".format(self.SLUG_SHORT))
                else:
                    for i, opp in df_output[df_output["edge"] > edge_trade_alert].iterrows():
                        if opp["name"] not in df_fast_saved_today["name"].tolist():
                            if opp["edge"] > 4 * edge_trade_alert:
                                os.system("say -v Samantha 'Insane {}.'".format(self.SLUG_SHORT))
                            elif opp["edge"] > 2 * edge_trade_alert:
                                os.system("say -v Samantha 'Amazing {}.'".format(self.SLUG_SHORT))
                            else:
                                os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                            print("Buy: https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, opp.name))
                        else:
                            existing_row = df_fast_saved_today[(df_fast_saved_today["name"]==opp["name"]) & (np.round(df_fast_saved_today["price"],3)==np.round(opp["price"],3))]
                            if len(existing_row) == 0:
                                if opp["edge"] > 4 * edge_trade_alert:
                                    os.system("say -v Samantha 'Insane {}.'".format(self.SLUG_SHORT))
                                elif opp["edge"] > 2 * edge_trade_alert:
                                    os.system("say -v Samantha 'Amazing {}.'".format(self.SLUG_SHORT))
                                else:
                                    os.system("say -v Samantha 'Found {}.'".format(self.SLUG_SHORT))
                                print("Buy: https://opensea.io/assets/{}/{}".format(self.CONTRACT_ADDRESS, opp.name))
                if self.write_to_file:
                    logging.info("Saving to fast_mode file")
                    df_fast_saved = pd.read_csv(file_path_fast_opps, index_col="token_id")
                    df_fast_saved = df_fast_saved.append(df_output)
                    df_fast_saved = df_fast_saved.drop_duplicates(subset=["name","date","price"])
                    df_fast_saved.to_csv(file_path_fast_opps)

        find_opps_end_time = time.time()
        logging.info("\nRun time for find_opps: {} seconds".format(np.round(find_opps_end_time - find_opps_start_time, 2)))

def main():
    # Read args and get params for collection.
    parser = argparse.ArgumentParser(description="Opensea NFT opportunities by trait.")
    parser.add_argument("-s", "--slug", type=str, help="Collection slug (in Opensea URL)", required=True)
    parser.add_argument("-b", "--bankroll", type=int, help="Max trade amount in ETH")
    parser.add_argument("-w", "--write", action='store_true')
    parser.add_argument("-c", "--configure", action='store_true')
    parser.add_argument("--floor", action='store_true', help="Scrape floor")
    parser.add_argument("-d", "--days", type=int, help="Use last d days of sales in regression")
    parser.add_argument("--load_sales", action='store_true', help="Use last saved sales file for pricing")
    parser.add_argument("--load_listed", action='store_true', help="Use last saved listed file in opportunity search")
    parser.add_argument("-p", "--pricer", default="ols", choices=["ols","robust","lasso"], help="Regression model type for theo pricing")
    parser.add_argument("-f", "--fast", action='store_true', help="Fast mode gets latest listings from OS activity page")
    parser.add_argument("-e", "--edge_mult", type=float, help="Edge ratio threshold to trade")
    parser.add_argument("--price_token", type=str, help="Token_id of individual asset to price. Requires --fast arg")
    parser.add_argument("-t", "--tune", choices=["edge_ratio","edge"], help="Tune edge_ratio or edge thresholds")
    parser.add_argument("--scrape_block", choices=["all","last"], help="Scrape blockchain for sales")
    parser.add_argument("--backpop_sales", action='store_true', help="Backpopulate sales files using scraped blockchain data. Must specify number of days to backpopulate")
    parser.add_argument("--wallet", type=str, help="Wallet address to scrape, or output saved sales or pnl. Must input a dummy collection slug (not used)")
    parser.add_argument("--full_history", choices=["scrape","analyze"], help="Full event history for WETH sales on OS")
    parser.add_argument("--dumb", action='store_true', help="Dumb opp logic")
    parser.add_argument("--ticker", action='store_true', help="Show ticker of opps from today")
    parser.add_argument("--looks", action='store_true', help="LooksRare")
    parser.add_argument("--stats", action='store_true', help="Listing stats")
    parser.add_argument("--adding", action='store_true', help="Adding liquidity strategy")
    parser.add_argument("-v", "--verbosity", default=1, choices=[0,1], type=int, help="Logging verbosity level (higher = more verbose)")
    args = vars(parser.parse_args())
    collection_slug = args["slug"]
    bankroll = args["bankroll"]
    write_to_file = args["write"]
    configure = args["configure"]
    get_floor = args["floor"]
    days = args["days"]
    load_saved_sales = args["load_sales"]
    load_saved_listed = args["load_listed"]
    pricer = args["pricer"]
    fast_mode = args["fast"]
    edge_mult = args["edge_mult"] if args["edge_mult"] is not None else 1.0
    price_single_asset = args["price_token"] if args["price_token"] is not None else None
    tune = args["tune"] if args["tune"] is not None else None
    scrape_block = args["scrape_block"] if args["scrape_block"] is not None else None
    backpop_sales = args["backpop_sales"]
    wallet = args["wallet"] if args["wallet"] is not None else None
    full_history = args["full_history"] if args["full_history"] is not None else None
    dumb = args["dumb"]
    opp_ticker = args["ticker"]
    looks = args["looks"]
    stats = args["stats"]
    adding = args["adding"]
    verbosity = args["verbosity"]
    collection_params = cfg.collection_mapping[collection_slug]

    if verbosity == 0:
        logging.basicConfig(level=logging.ERROR, format="%(message)s")
        warnings.filterwarnings("ignore", category=RuntimeWarning)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    start_time = time.time()
    print("Current local time: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    nftTrader = NftTrader(collection_slug, collection_params, bankroll, write_to_file, days)
    nftTrader.find_opps(load_saved_sales=load_saved_sales, load_saved_listed=load_saved_listed, reg_mode=pricer, fast_mode=fast_mode, edge_ratio_trade_alert=edge_mult, price_single_asset=price_single_asset, looks=looks)

    end_time = time.time()
    print("\nTotal run time: {} seconds".format(np.round(end_time - start_time, 2)))
    logging.info("Current local time: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

if __name__ == "__main__":
    main()

