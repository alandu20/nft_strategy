collection_mapping = {
    "rumble-kong-league": {
        "slug_short": "kong",
        "contract_address": "0xef0182dc0574cd5874494a120750fd222fdb909a",
        "meta_url": "https://ipfs.io/ipfs/QmZmghtNCGYx496Dq2U9nHuxqSbSLhNuXpFPPz6eA2urME",
        "cnt_token_ids": 10000,
        "token_id_start": 0,
        "global_cnt_th": 1,
        "global_rarity_th": 0.05,
        "local_diversity_th": 0.0,
        "use_rarity_score": False,
        "theil_sen_sample_ratio": 0.08,
        "use_required_edge": False,
        "trait_categories":{"background","clothes","eyes","fur","head","head accessory","jewellery","mouth","defense","finish","shooting","vision"},
        "require_traits": {},
        "ignore_traits_theo": {"trait_category":["background","clothes","eyes","head","head accessory","jewellery","mouth"], "trait":["*","*","*","*","*","*","*"]},
        "ignore_traits_required_edge": {},
        "priority_traits": {},
        "group_traits": {"fur":[
                            ("brown","black","grey","pink","red","sky blue","white noise","green"),
                            ("aurora","camo","gold","zebra","hyper cat","crystal")
                            ],
                        },
    },
    "world-of-women-nft": {
        "slug_short": "wow",
        "contract_address": "0xe785e82358879f061bc3dcac6f0444462d4b5330",
        "meta_url": "https://wow-prod-nftribe.s3.eu-west-2.amazonaws.com/t",
        "cnt_token_ids": 10000,
        "token_id_start": 0,
        "global_cnt_th": 1,
        "global_rarity_th": 0.065,
        "local_diversity_th": 0.0,
        "use_rarity_score": True,
        "theil_sen_sample_ratio": 0.1, # 0.08 historically optimal
        "use_required_edge": True,
        "trait_categories":{"background","clothes","earrings","eyes","facial features","hairstyle","lips color","mouth","necklace","skin tone","face accessories"},
        "require_traits":{"trait_category":["face accessories","clothes","skin tone","skin tone","skin tone","mouth"],
                          "trait":["3D Glasses","Warrior Armor","Cool Blue","Burning Red","Cyber Green","Bubble Gum"]},
        "ignore_traits_theo": {},
        "ignore_traits_required_edge": {"trait_category":["Eyes"], "trait":["*"]},
        "priority_traits": {"skin tone":[("Night Goddess","Golden","Rainbow Bright")],
                            "clothes":[("Naiade","Tuxedo")],
                            "hairstyle":[("purple rainbow",)], # must have comma if only 1 trait in tuple
                            },
        "group_traits": {"skin tone":[
                            ("Deep Bronze","Deep Warm Gold","Deep Neutral"),
                            ("Light Warm Olive","Light Warm Yellow","Light Medium Warm Gold","Medium Olive","Medium Gold")
                            ],
                        "eyes":[
                            ("Black Eye Roll","Black To The Left","Black To The Right","Black Straight"),
                            ("Brown Eye Roll","Brown To The Left","Brown To The Right","Brown Straight"),
                            ("Green Eye Roll","Green To The Left","Green To The Right","Green Straight"),
                            ("Blue Eye Roll","Blue To The Left","Blue To The Right","Blue Straight"),
                            ("Purple Eye Roll","Purple To The Left","Purple To The Right","Purple Straight"),
                            ("Yellow Eye Roll","Yellow To The Left","Yellow To The Right","Yellow Straight"),
                            ("Heterochromia Eye Roll","Heterochromia To The Right","Heterochromia To The Left","Heterochromia Straight")
                            ],
                        "hairstyle":[
                            ("Bob","Feeling Turquoise"),
                            ("Platinum Pixie","Boy Cut","Finger Waves"),
                            ("Retro","Curly Ponytail"),
                            ("Lollipop","Natural Red","Bun","Fuchsia","Braided Ponytail","Lucky Green","Long Dark","Rose Hair") # remaining count based
                            ],
                        "mouth":[
                            ("Stern","Slight Smile","Slighly Open","Whistle")
                            ],
                        "lips color":[
                            ("Passion Red","Burgundy")
                            ],
                        "clothes":[ # count + regression coeff + VIF based
                            ("Cherry Tee","Adventurer","Polka Dot Top","Striped Tee","Painter's Overall","Fantasy Shirt","Cabaret Corset",
                                "White Tee","Psychedelic Dress","Little Red Dress","70s Shirt","80s Silk Shirt","Queen's Dress","Red Leather Jacket","Freedom Is Power Tee")
                            ],
                        "background":[
                            ("Dark Emerald","Red Turquoise","Green Orange","Green Purple","Dark Purple"),
                            ("Soft Purple","Blue Green","Orange Yellow","Yellow Pink","Pink Pastel")
                            ],
                        "necklace":[ # count + regression coeff + VIF based
                            ("Sun Keeper","Satin Choker","Golden Flakes","Back To The 90s","Tutti Frutti Beads"),
                            ("Malka","Amazonite Energy","Gold Ruler","Rainbow","Spike Choker")
                            ],
                        "earrings":[ # count + regression coeff + VIF based
                            ("Pearls","Triple Rings","Silver Drops","Classic Hoops","Spikes","Ocean Hoops"),
                            ("Lucky Charms","60s Fantasy","Yam's Fave","Flower Power")
                            ],
                        "face accessories":[ # count + regression coeff + VIF based
                            ("70s Feels","Round Glasses","Red Round Sunglasses"),
                            ("Classic Aviator WoW","Black Round Retro","Black Mask","Oversized Statement Sunglasses","Psychedelic Sunglasses")
                            ],
                        "facial features":[ # count + regression coeff + VIF based
                            ("Marilyn","Eyebrow Piercing","Red Eyeliner","Nose Piercing","Heart Tattoo","Feline Eyes","Antoinette","Freckles","Rainbow"),
                            ("Eye Scar","Flashy Blue","Eyebrow Tattoo MMXXI","Sunset","Rose Tattoo","Claw Scar","Neck Tattoo","Leader","Crystal Queen","Treble Bass Clef Tattoo","Pearl Eyes")
                            ],
                        },
    },
}