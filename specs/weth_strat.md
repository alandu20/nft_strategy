# WETH Strategy

## Motivation
Observed many examples where seller accepts low bid after listing lower several times in a day
- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/3073 (karafuru): 3.4 -> 3.38 -> 2.9 within 2 hours, then accepts 2.29 weth bid. Global floor was 2.9 when bid accepted
- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/4963 (karafuru): 8 -> 6.5 -> 5 within 6 hours, then accepts 4.2 weth bid
- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/1569 (bossbeauties): lowered 8 times within 24 hours on 2022-03-01. Accepted 2.9525 weth bid was only for 0.25 edge ratio

Successful competitors:
- https://opensea.io/0x3c942d8ccb8840ad3c0dcc7de0576a84d413cbc4. Relatively new player starting 2022-02-20. 12 eth pnl pre-fees, 8 eth pnl post fees between 2022-02-20 and 2022-03-04. Particularly successful in bossbeauties
- https://opensea.io/0x2d1194e75b408c9395a8bbbedc0079322b62c0a4: KJ1AA. Has multiple wallets, all transfer to this one and then sells. Harder to track to due to transfering, but pnl of this base wallet is upwards of 300 eth since Nov 2021, with most flips in 2022
	- Connected wallets (used for bidding): KJ_20 (wow, nft worlds), KJ_47_N (azuki)
	- Likely connected wallets (based on transfers): ajjaffy_vault, MOJOJAFFY, Mojo_Vault1, C310E7
	- Unlike others, goes for a lot of assets above floor, so they have a good pricing model too
	- Getting harder to track. Changes username every so often. Latest connected wallets:
		- 0x701Ec3a1bAC994363016C6C7A1d8a52c32a5dc2f st31ap: MAYC
		- 0xb8AA9A7a1Ea65c80A205Cca2Cf2c51Bec5f144e2 st37ap: MAYC
		- 0x2D1194e75B408C9395A8BBbEdC0079322b62c0a4 CheaperOnX2Y2: intermediate transfer
		- 0x9d6DaAE4A034decC5D5780e4909a0A6FCbA090D7 WillieAndersonVault: listing vault (among others)
- https://opensea.io/0x0ecbba0ccb440e0d396456bacdb3ce2a716b96e5: flash-boi. Same set up as KJ1AA. 40 eth net pnl between 2021-09-16 and 2022-01-12
	- Connected wallets (used for bidding): 15-flash-boi, 16-flash-boi, 17-flash-boi, 12-flash-boi
	- Pretty quick and aggressive bot. Noticed 15/16/17-flash-boi and 0x3c942d8ccb8840ad3c0dcc7de0576a84d413cbc4 diming each other by 0.001/0.0001 increments in boss beauties 764. Bid 0.04 over 16-flash-boi and got dimed by 0.001 within 2 minutes. Then bid 0.43 over (within .04 of floor), did not get dimed
- https://opensea.io/0x0e78c12ad4c2e31ff38c4c0ce2fea1e57b838d47: mrMojito. 22 eth net pnl since 2021-09-19
	- Likely connected wallets (based on transfers): 0x277fce7bdeb3ef12443ce2206bc3e7766892f96c (_NFTVault_), 0x2bb291ece232e44f7f8bb3a55775e18b9d01e591 (2BB291)
- https://opensea.io/0x236dc2ae307e4d88beb35a3295bbc3caeee49f37. Relatively new player starting 2022-01-30. 2.4 eth net pnl on 23 flips as of 2022-03-07. Lists aggressively low for very little profit to ensure short holding period, almost always flips same day
- https://opensea.io/0x88c200aef5e8212d62c32413527b679a7e8fe8cc. Newer player starting 2022-01-03. Started in RKL around 2022-03-14. 4 eth pnl total
- https://opensea.io/0x06b2b209a1e39260a7c0183f036e8ce73503f581. New player 2022-03-14, first trade in RKL

Patterns:
- High listing velocity
	- https://opensea.io/assets/0x79fcdef22feed20eddacbb2587640e45491b757f/2724 mfers: 11 times in 12 days
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/4172 WoW: lowers 3 times in 3 days, then accepts 4 hours later
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/1643 WoW: lowers 5 times in 2 hours, then accepts 30 minutes later
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/7201 WoW: list slightly below floor, lowers further after 20 minutes, relists at same price 20 minutes later, then accepts bid 10 minutes later (wallet: RTCLBPRJCT)
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/545 WoW: lists 5 times in 2 hours (sometimes same or higher price), then accepts 30 minutes later (wallet: RTCLBPRJCT)
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/5797 BB: lowers 4 times in 3 days, then accepts 12 hours later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/3049 BB: lowers 4 times in 2 days, then accepts 30 minutes later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/4269 BB: lowers 3 times in 2 days, then accepts 30 minutes later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/4833 BB: lowers 4 times in 12 hours (lowest offer .15 eth below floor), then accepts bid 0.5 eth below floor 5 minutes later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/7343 BB: lowers 2 times in 2 days, then accepts 1 day later
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/3897 RKL: transfer from potentially compromised account, lowers 7 times in 5 days, then accepts 12 hours later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/6151 BB (flipped): lowers 3 times in 1 day
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/8113 BB (flipped): lowers 3 times in 1 day
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/1856 karafuru (flipped): lowers 3 times in 1 day. 2nd at floor, 3rd below floor
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/3073 karafuru (flipped): lowers 3 times in 1 day (7 timesin 2 weeks). 2nd to last slightly below floor
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/4543 karafuru (flipped): lowers 2 times in 2 days
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/5036 karafuru (flipped): transfers to other wallet a week after buying, lowers 3 times in 3 days
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/556 karafuru (flipped): lowers 2 times in 2 days
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/556 mfers (flipped): lowers 7 times in 5 days
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/556/2802 mfers (flipped): 5 days prior to accepting, listed 2 times at same price in 2 days. Possible these listings expired
	- https://opensea.io/assets/0x1a92f7381b9f03921564a437210bb9396471050c/8976 coolcats (flipped): changed 4 times in 2 days, 2 times were price increases
	- https://opensea.io/assets/0xccc441ac31f02cd96c153db6fd5fe0a2f4e6a68d/8309 fluf: lowers 4 times in 30 minutes before accepting bid 0.6 eth below floor
- List once around or below floor, or for significant edge, and then accept bid. Not mutually exclusive with "lower listing many times" - these do not have the same velocity
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/6813 WoW: list slightly below floor, then accepts bid 20 minutes later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/9962 BB: list slightly above floor, then accepts 30 minutes later
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/7396 BB: list slightly above floor, then accepts 10 minutes later
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/6082 RKL: list slightly below floor, then accepts 6 hours later
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/7815 RKL: lists for 0.13 edge after no activity for 7 months, then accepts 6 hours later
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/9886 RKL: lists for 0.15 edge after no activity for 7 months, then accepts 1 hour later
- Some listing activity but not discernable pattern:
	- https://opensea.io/assets/0x79fcdef22feed20eddacbb2587640e45491b757f/5579 mfers (flipped): listed twice in 3 days, 1 was meme price
	- https://opensea.io/assets/0x1a92f7381b9f03921564a437210bb9396471050c/6653 coolcats (flipped): listed once 5 hours prior to accepting
- Transfer into hot wallet
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/8665 BB: transfer into cold wallet after buying, transfer to hot wallet after holding for 5 months, then accepts 2.1 weth offer (1.13 edge ratio) 30 minutes later w/o listing
	- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/1865 WoW: transfer into cold wallet after buying, transfer into hot wallet that originally bought after holding for 2 weeks, lists 3 times in 30 minutes, then accepts 10 minutes later
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/7580 RKL: transfer into cold wallet after buying, transfer into hot wallet after holding for 2 weeks, then accepts 13 days later w/o listing
	- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/8508 RKL: transfer into cold wallet after buying, transfer into hot wallet after holding for 1 day, then accepts 2 minutes later w/o listing
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/5458 BB (flipped): transfer into cold wallet 24 days after buying, transfer into hot wallet after holding for 4 days, then accepts 2 hours later w/o listing
	https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/5351 karafuru (flipped): transfer into cold wallet 10 days after buying, transfer back into hot wallet that initially bought after holding for 3 days, then accepts 2 minutes later w/o listing
- Not listed
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/8137 BB: holds 4 months then accepts bid 1.5 eth below floor
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/7856 BB
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/7726 BB
	- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/278 BB: lists 9 days prior but possibly expired
	- BB flipped: 1519, 2514, 3049, 4310, 735, 6000, 9070
	- https://opensea.io/assets/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6/1404 karafuru (flipped): transfer into other wallet shortly after buying, accepts 2 weeks later w/o listing
	- karafuru flipped: 2152 (seller compromised), 2471, 4836
	- coolcats flipped: 1941, 6844
- Wallet liquidating
	- 0xD4cF1f7B5A269040a46615210397088131aE34d6 (d4erf43): 3 on 2022-03-23 within 6 minutes, 2 on 2022-03-29 within 1 minute, 3 on 2022-03-30 within 2 minutes. Listed an hour before first

Consider on LooksRare too. Lots of bids accepted below floor in mfers 2022-03-02 to 2022-03-09

## OS SDK
https://opensea.io/blog/guides/how-to-bid-on-crypto-collectibles/

"The moment my first bid gets accepted, the other offers will be instantly invalidated if I no longer have enough WETH in my account."

https://docs.opensea.io/

"Power your in-app economy with OpenSea.js. Enable users to create auctions (w/o paying gas) in any currency, bid on items, and create multi-item bundles. SDK: https://github.com/ProjectOpenSea/opensea-js."

https://github.com/ProjectOpenSea/opensea-js

"It allows developers to access the official orderbook, filter it, create buy orders (offers), create sell orders (auctions), create collections of assets to sell at once (bundles), and complete trades programmatically."

## Alternatives

https://moralis.io/get-an-opensea-api-key-in-2022-full-guide/

https://moralis.io/nft-api-alternatives-comparing-alchemys-nft-api-with-moralis-nft-api/

https://moralis.io/opensea-api-alternative-list-nfts-with-this-opensea-plugin/

## Addressing Risks

Risks
- Exposure to getting picked off on large floor moves lower. Cancelling bids costs gas
	- Use one wallet per collection and keep minimum amount of weth needed to get filled on a bid
	- Once bid is filled, if wallet does not contain enough weth the other bids will not be fillable (gas-less way to "mass cancel")
- Rogue program, data quality issue, and/or pricing issue
	- Cap how much wallet can bid. Must build a lot of confidence before bidding on high value assets
	- Set bid at price equivalent to a very high edge_mult, at least 12 edge_ratios
	- Once there is a fill, kill the program. Or set max number of fills before killing process
	- Keep main wallet (holding other valuable assets) disconnected from OS
	- Thoroughly test any changes on testnets
- Security compromised
	- Encrypt private key
- Blockchain syncing disrupted
	- Check syncing status regularly

Currently implemented safeguards
- Check node is not syncing
- Encrypted private key via keystore file. Decrypt using password
	- TODO: how to read in keystore file
	- TODO: brainstorm safer setup
- Sanity check bid price
	- bid < 90% of lowest listed price
	- bid is strictly less than global floor price (for basic strategy)

