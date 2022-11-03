import argparse
import config as cfg
import json
import multiprocessing as mp
import numpy as np
import os
import pandas as pd
import requests
import sys
import time
pd.options.display.max_rows = 1000

def get_meta_parallel(tokenid):
    # url_meta = "https://mflowers-prod.s3.us-west-1.amazonaws.com"
    # url_meta = "https://api.otherside.xyz/lands"
    
    response = requests.request("GET", "{}/{}".format(url_meta, tokenid))
    
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
        # print(df_json)
        df_json["name"] = "#{}".format(tokenid)
    else:
        df_json = pd.json_normalize(response_json, "attributes", ["name"], errors='ignore')
        try:
            df_json = df_json[df_json["trait_type"]!="name"]
        except KeyError:
            return None

    # Check trait_type and value keys exist, if not return none.
    try:
        df_row = df_json.pivot_table("value", "name", "trait_type", aggfunc="first").reset_index()
    except KeyError:
        return None

    # Formatting.
    df_row.columns = [c.lower() for c in df_row.columns]
    df_row["token_id"] = str(tokenid)

    # Change to dict since appending dicts is faster than pandas dfs.
    dict_row = df_row.to_dict(orient="records")[0]
    
    return dict_row

def main():
    parser = argparse.ArgumentParser(description="Opensea NFT opportunities by trait.")
    parser.add_argument("-s", "--slug", type=str, help="Collection slug (in Opensea URL)", required=True)
    parser.add_argument("-b", "--bankroll", type=int, help="Max trade amount in ETH")
    parser.add_argument("-l", "--listed", action='store_true', help="Get metadata for listed assets only")
    parser.add_argument("-w", "--write", action='store_true')
    args = vars(parser.parse_args())
    collection_slug = args["slug"]
    max_eth = args["bankroll"]
    listed = args["listed"]
    write_to_file = args["write"]

    path_arb = "data_warehouse/arb"
    global url_meta
    url_meta = cfg.collection_mapping[collection_slug]["meta_url"]

    # Specify which token_ids to get metadata for.
    if listed:
        # Get saved listings.
        path_listed = "{}/listed/".format(path_arb)
        path_files = [f for f in os.listdir(path_listed) if os.path.isfile(os.path.join(path_listed, f)) and collection_slug in f]
        df_listed = pd.read_csv(path_listed + path_files[0], dtype={"token_id": object})
        df_listed = df_listed.dropna(subset=["token_id"])

        # Bankroll filter.
        if max_eth is not None:
            max_ape = max_eth * 2000 * 6.5
            df_listed = df_listed[((df_listed["price"] <= max_eth) & (df_listed["currency"]=="eth")) | ((df_listed["price"] <= max_ape) & (df_listed["currency"]=="ape"))]

        # Listed token_ids
        target_token_ids = list(set([int(x) for x in df_listed["token_id"]]))
        # target_token_ids = target_token_ids[0:100]
    else:
        token_id_start = cfg.collection_mapping[collection_slug]["token_id_start"]
        cnt_token_ids = cfg.collection_mapping[collection_slug]["cnt_token_ids"]
        target_token_ids = [x for x in range(token_id_start, token_id_start + cnt_token_ids)]
        # target_token_ids = target_token_ids[0:1000] # only sample first 1000

    # Get metadata for target token_ids.
    print(target_token_ids)
    print("Count target token_ids: {}".format(len(target_token_ids)))

    start_time = time.time()

    pool = mp.Pool(mp.cpu_count())
    batch = pool.map(get_meta_parallel, target_token_ids)

    requests_end_time = time.time()
    print("\nGet requests run time: {} seconds".format(np.round(requests_end_time - start_time, 2)))

    dict_meta_list = []
    for b in batch:
        if b is not None:
            dict_meta_list.append(b)
    
    df_meta = pd.DataFrame.from_dict(dict_meta_list)

    end_time = time.time()
    print("\nTotal run time: {} seconds".format(np.round(end_time - start_time, 2)))
    print(df_meta)

    if len(df_meta) > 0:
        if write_to_file:
            if listed:
                df_meta.to_csv("{}/metadata/{}_listed_metadata.csv".format(path_arb, collection_slug), index=False)
            else:
                df_meta.to_csv("{}/metadata/{}_all_metadata.csv".format(path_arb, collection_slug), index=False)

if __name__ == "__main__":
    main()