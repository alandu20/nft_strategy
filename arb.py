import argparse
import config as cfg
import json
import logging
from nft import NftTrader
import os
import pandas as pd
import requests
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")


class RevealStrat(NftTrader):
    def __init__(self, collection_slug, collection_params, bankroll, write_to_file, days):
        super().__init__(collection_slug, collection_params, bankroll, write_to_file, days)

    def get_metadata_url(self):

        print("\nconfig.py metadata url (excl. /token_id):\n{}".format(self.META_URL))

        print("\nValidate endpoint metadata url")
        token_id = 2733
        url = "https://api.opensea.io/api/v1/asset/{}/{}/validate".format(self.CONTRACT_ADDRESS, token_id)
        headers = {
            "Accept": "application/json",
            "X-API-KEY": "85dc024ae3b7495cb53210994bf5469e"
        }
        response = requests.get(url, headers=headers)
        print(response.text)
        meta_url = json.loads(response.text)["token_uri"]
        print(meta_url)

        # print("\nCollection endpoint metadata url")
        # url = "https://api.opensea.io/api/v1/collection/{}".format(self.COLLECTION_SLUG)
        # response = requests.get(url)
        # print(response.text)
        # meta_url = json.loads(response.text)["token_uri"]
        # print(meta_url)

    def get_listings(self, load_saved_listed, join_meta=False):
        path_listed = "data_warehouse/arb/listed/"

        if load_saved_listed == False:
            logging.info("Getting currently listed prices for {}".format(self.COLLECTION_SLUG))
            # tokens = pd.Series([x for x in range(240, 245)])
            tokens = pd.Series([x for x in range(int(self.TOKEN_ID_START), int(self.CNT_TOKEN_IDS)+1)])
            df_listed = self.get_current_listings(token_ids=tokens, token_contract_address=self.CONTRACT_ADDRESS)
            # print(df_listed)
            # sys.exit()
            df_listed = df_listed[df_listed["is_auction"]==False]
            df_listed = df_listed[df_listed["currency"].isin(["eth","weth"])]
            
            if self.write_to_file:
                logging.info("Saving listed snapshot for {}".format(self.COLLECTION_SLUG))
                df_listed.to_csv(path_listed + "{}_snapshot_listed_latest.csv".format(self.COLLECTION_SLUG), index=False)
        else:
            logging.info("Loading saved listings for {}".format(self.COLLECTION_SLUG))
            df_listed = pd.read_csv(path_listed + "{}_snapshot_listed_latest.csv".format(self.COLLECTION_SLUG), dtype={"token_id": object})
            
            logging.info("Updating saved listings with latest listings")
            df_latest_listings = self.get_latest_listings(lookback_seconds=60)
            if df_latest_listings is not None:
                df_latest_listings = df_latest_listings[df_latest_listings["is_auction"]==False]
                df_latest_listings = df_latest_listings[df_latest_listings["currency"].isin(["eth","weth"])]
                df_latest_listings = df_latest_listings.dropna(subset=["token_id"])
                logging.info("Latest listings:\n{}".format(df_latest_listings))
                df_listed = df_listed.append(df_latest_listings)
                df_listed["price"] = df_listed["price"].round(3)
                df_listed = df_listed.drop_duplicates(subset=["token_id","price"])
            
                if self.write_to_file:
                    logging.info("Saving listings file with latest listings")
                    df_listed.to_csv(path_listed + "{}_snapshot_listed_latest.csv".format(self.COLLECTION_SLUG), index=False)

                if join_meta:
                    df_latest_listings_filtered = df_latest_listings[df_latest_listings["price"]<10]
                    df_latest_listings_filtered_traits = pd.DataFrame()
                    for tokenid in df_latest_listings_filtered["token_id"]:
                        response = requests.request("GET", "{}/{}".format(self.META_URL, tokenid))
                        
                        # Load json.
                        try:
                            response_json = json.loads(response.text)
                        except (json.decoder.JSONDecodeError):
                            print("Could not decode json, skipping token_id {}".format(tokenid))
                            return None

                        # Check attributes key exists, if not return none.
                        if "attributes" not in response_json:
                            print("No 'attributes' key in metadata json for token_id {}. Check if attributes field is named differently:\n{}".format(tokenid, response_json))
                            return None
                        
                        # Check name key exists, if not add filler name.
                        if "name" not in response_json:
                            df_json = pd.json_normalize(response_json, "attributes", errors='ignore')
                            df_json["name"] = "#{}".format(tokenid)
                        else:
                            df_json = pd.json_normalize(response_json, "attributes", ["name"], errors='ignore')
                            df_json = df_json[df_json["trait_type"]!="name"]

                        # Check trait_type and value keys exist, if not return none.
                        try:
                            df_row = df_json.pivot_table("value", "name", "trait_type", aggfunc="first").reset_index()
                        except KeyError:
                            return None

                        # Formatting.
                        df_row.columns = [c.lower() for c in df_row.columns]
                        df_row["token_id"] = str(tokenid)

                        df_latest_listings_filtered_traits = df_latest_listings_filtered_traits.append(df_row)
                    
                    df_latest_listings_filtered_w_traits = pd.merge(df_latest_listings_filtered_traits, df_latest_listings_filtered[["token_id","price"]], on="token_id", how="left")
                    df_latest_listings_filtered_w_traits = df_latest_listings_filtered_w_traits.sort_values(by=["price"])

                    if self.COLLECTION_SLUG == "gene-sis-the-girls-of-armament":
                        if "NOX" in df_latest_listings_filtered_w_traits["class"].tolist():
                            os.system("say -v Samantha 'Found NOX.'")
                        if "EMPREAL" in df_latest_listings_filtered_w_traits["class"].tolist():
                            os.system("say -v Samantha 'Found EMPREAL.'")
                        if any("SUPRA" in s for s in df_latest_listings_filtered_w_traits["clothes"].tolist()):
                            os.system("say -v Samantha 'Found SUPRA.'")
                    if self.COLLECTION_SLUG == "streetlab-genesis":
                        if "Golden Crown" in df_latest_listings_filtered_w_traits["hat"].tolist():
                            os.system("say -v Samantha 'Found Golden Crown.'")
                    
                    print(df_latest_listings_filtered_w_traits)

        return df_listed

    def opps(self):
        df_traits_listed = pd.read_csv("data_warehouse/arb/metadata/{}_listed_metadata.csv".format(self.COLLECTION_SLUG), dtype={"token_id": object})

        df_listed = self.get_listings(load_saved_listed=True)

        df_listed_w_traits = pd.merge(df_listed, df_traits_listed, on="token_id", how="left")
        df_listed_w_traits = df_listed_w_traits.sort_values(by=["price"])

        print("Listed assets ranked by price:\n{}".format(df_listed_w_traits.head(100)))

        if self.write_to_file:
            df_listed_w_traits.to_csv("data_warehouse/arb/opps/{}_ranked.csv".format(self.COLLECTION_SLUG), index=False)

        file_path_all_metadata = "data_warehouse/arb/metadata/{}_all_metadata.csv".format(self.COLLECTION_SLUG)
        if os.path.exists(file_path_all_metadata):
            df_traits = pd.read_csv(file_path_all_metadata, dtype={"token_id": object})

            # df_trait_dist = df_traits.groupby("class").agg({"name":"count"}).rename(columns={"name":"cnt"}).sort_values(by=["cnt"], ascending=False)
            # df_trait_dist["pct"] = df_trait_dist["cnt"] / df_trait_dist["cnt"].sum()
            # print(df_trait_dist)

            print("\nTrait category counts:\n{}".format(df_traits.count()))

            # Rarest traits
            df_traits = df_traits.set_index("token_id")
            df_traits_rarity = pd.DataFrame()
            for col in df_traits.drop(columns=["name"]).columns:
                df_traits_col = pd.DataFrame(df_traits[col].value_counts()).reset_index()
                df_traits_col.columns = ["trait","count"]
                df_traits_col["trait_category"] = col
                df_traits_col = df_traits_col[["trait_category", "trait", "count"]]
                df_traits_rarity = df_traits_rarity.append(df_traits_col)
            df_traits_rarity["global_rarity"] = df_traits_rarity["count"] / len(df_traits)
            df_rare_traits = df_traits_rarity[df_traits_rarity["global_rarity"] < 0.02].reset_index(drop=True)
            df_rare_traits = df_rare_traits.sort_values(by="global_rarity")
            print("\nRarest traits:\n{}".format(df_rare_traits.head(50)))

            # Potential 1/1s
            df_rarest_traits = df_rare_traits[df_rare_traits["count"]<=3]
            df_one = pd.DataFrame()
            for i, row in df_rarest_traits.iterrows():
                df_one = df_one.append(df_traits[(df_traits[row["trait_category"]]==row["trait"])])
            df_one = df_one.drop_duplicates()
            df_one = pd.merge(df_one, df_listed, on="token_id", how="left")
            print("\nRarest assets:\n{}".format(df_one))

            print(df_traits[(df_traits["head"]=="Silver Hero Mask")])
            # print(pd.merge(df_traits[(df_traits["necklace"]=="Ring Silver")], df_listed, on="token_id", how="left"))

def main():
    # Read args and get params for collection.
    parser = argparse.ArgumentParser(description="NFT trader.")
    parser.add_argument("-s", "--slug", type=str, help="Collection slug (in Opensea URL)", required=True)
    parser.add_argument("-b", "--bankroll", type=int, help="Max trade amount in ETH")
    parser.add_argument("-w", "--write", action='store_true')
    parser.add_argument("-d", "--days", type=int, help="Use last d days of sales in regression")
    parser.add_argument("--load_listed", action='store_true', help="Use last saved listed file in opportunity search")
    parser.add_argument("-m", "--mode", choices=["url","listings","listings_w_meta","opps"], help="Reveal strat arb mode")
    args = vars(parser.parse_args())
    collection_slug = args["slug"]
    bankroll = args["bankroll"]
    write_to_file = args["write"]
    days = args["days"]
    load_saved_listed = args["load_listed"]
    mode = args["mode"]
    collection_params = cfg.collection_mapping[collection_slug]

    revealStrat = RevealStrat(collection_slug, collection_params, bankroll, write_to_file, days)
    if mode == "url":
        revealStrat.get_metadata_url()
    elif mode == "listings":
        revealStrat.get_listings(load_saved_listed)
    elif mode == "listings_w_meta":
        revealStrat.get_listings(load_saved_listed, join_meta=True)
    elif mode == "opps":
        revealStrat.opps()

if __name__ == "__main__":
    main()

