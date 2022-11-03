# Random Strategy Ideas

## Simple Market Making

In high volume events, OS cannot keep listings up to date. Assets listed well below floor are immediately scooped up, very hard for a human to find these quickly or know what true lowest listed active offer is. Even watching listings events page is too slow (lagging on the order of 30 seconds or more). Really the only way estimating floor price is by watching sales.

Strategy: listen to event listings endpoint, buy listings well below lowest offer, and attempt flip immediately. Latency sensitive

## New claim for existing collection

Scenario: collection X releases a new collection or token Y, where X is given right to redeem Y for free (+gas).

### NFTX single loan

Sub-scenario: Redeem window started and unclaimed assets exist in NFTX liquidity pool.

Example: WoWG claim 2022-03-27 14:00 EST (pnl ~$100K)

Overview: https://mobile.twitter.com/0x_Beans/status/1507900778672926722

NFTX WOW Vault: https://nftx.io/vault/0xb98217f7f050aad1696467a1559e726381879f33/info/

Prior to start of release:
- Buy WOW_2868 and WOW_7734
- Give transfer approval to WOW NFTX vault

Upon start of release (all actions: https://etherscan.io/address/0x5fa83f4d52da8d176cf1826e98521d74007a0a46):
- Block 14463323: Mint WOWG_2868 and WOWG_7734 using WOW_2868 and WOW_7734
	- https://etherscan.io/tx/0xecfbff55ca3f0a9d73b0c505430fb21fe0e7e4fa74c5beba0f7ef550f38d39ba
- Block 14463323: Swap WOW_2868 for WOW NFTX token ("vWOW"). Swap fee paid in vWOW
	- https://etherscan.io/tx/0xecfbff55ca3f0a9d73b0c505430fb21fe0e7e4fa74c5beba0f7ef550f38d39ba send WOW_2868, receive 1 vWOW, pay 0.1 vWOW in fees (split into 0.08 and 0.02 vWOW and sent to 2 wallets)
	- https://etherscan.io/token/0xb98217f7f050aad1696467a1559e726381879f33 vWOW token contract
	- https://etherscan.io/address/0x0bd30c34e4524df28d368d00c2feb534696d0bb7 MEV bot contract
- Block 14463323: Swap WOW_7734 for WOW_9015 from NFTX vault. Swap fee paid in vWOW
- Block 14463323: Mint WOWG_9015 using WOW_9015
- Block 14463323: Swap WOW_9015 for WOW_7488 from NFTX vault. Swap fee paid in vWOW
- Block 14463323: Mint WOWG_7488 using WOW_7488
- Block 14463323: rinse and repeat for all 13 WOWs in NFTX vault. Ends with owning WOW_6785 and 13 WOWGs
	- https://etherscan.io/tx/0x6391237c9d95571e945bcc5e8964b10ec6ce712f63cd34ee47c866bc589dedf4 WOW_7734 -> WOW_9015 -> mint WOWG_9015 -> WOW_7748 -> mint WOWG_7748 -> WOW_247 -> mint WOWG_247 -> ... -> WOW_6785 -> mint WOWG_6785
- Block 14463331: Transfer WOWGs and WOW_6785 to wallet 0x5fa83f4d52da8d176cf1826e98521d74007a0a46
	- https://etherscan.io/tx/0xb45bc3cb0dad8387acb5a56df2253c0670fff969dcdbf9acd13c109e917beb9a transfer WOWGs
	- https://etherscan.io/tx/0x429a6035086258ffa9ee6f89e3c7142a460a6c4bea67c39817c4db011f72748a transfer WOW_6785
- Block 14463343: Approve OS Registry contract in wallet
	- https://etherscan.io/tx/0xfbb3c78f2b927c491c15598684316ef0e09cae6b9c524cfc5f4c4143fb4e258d
- Block 144633435: Approve WOWG on OS in wallet
	- https://etherscan.io/tx/0x74fec000a6ed451394139092387d4a925f1de6daa37fe0f7bb4af58fa94aa362
- Block 14463394: Weird vBAYC transfer from MEV bot contract to wallet
	- https://etherscan.io/tx/0x7a8829d0ea65145df0883d7d8ecb8c5a544bc9bd1e1764b8fc4a5ae56553c622
	- https://etherscan.io/token/0xea47b64e1bfccb773a0420247c0aa0a3c1d2e5c5?a=0xeb8c3bebed11e2e4fcd30cbfc2fb3c55c4ca166003c7f7d319e78eaab9747098 VBAYC token was used in NFTX flash loan arb during $APE drop
- Block 14463399: Approve WOW on OS in wallet
	- https://etherscan.io/tx/0x616788a09d79f7b19b3614ba416c1c507661344568fb052981fbac69d1d7d49f
- Block 14463403: Transfer remaining 0.12 vWOW from MEV bot contract to wallet
	- https://etherscan.io/tx/0xdbfb7c86162b266cabf2afc72e58570fdd467ed4667e550b6276d3f97532410e
- Block 14463407: Approve vWOW on SushiSwap in wallet
	- https://etherscan.io/tx/0x59c1d5e31a0960885d3c1d2d41103201b8acc599869ec6b6780f1130ad045c55
- Block 14463412: Swap 0.12 vWOW for 1.37 eth via SushiSwap
	- https://etherscan.io/tx/0x117b92ac3c0fff1511a3cc66ad5e65366c330f474cbdf29f7ec2ebb8a4a93cfd
- Various blocks: Sell WOWGs on OS, probably averaged ~2.5 eth
	- https://etherscan.io/tx/0xcff8eb65159daf9202f53c49a3cb2ebcd26423e939f05158ed7c5c95b3432bb5 first sale
	- https://etherscan.io/tx/0x521bdc22feed05d99b33a4cce440544d5d46adf53ae6433c85924fcc33c630b3 last sale (after WOW_6785 sold)
- Block 14463447: Approve weth on OS in wallet
	- https://etherscan.io/tx/0x832cac2e19b9cb9cfc95a114951f5ce9c8608f3fe0163c5ec2f7eda3aa3d20e2
- Blocks 14463451 and 14463455: Sell WOW_6785 for 10.2 weth (receive 9.537 weth net), then unwrap into eth
	- https://etherscan.io/tx/0xf7bdc7771a092f71f0fd6a939620aff66625177aa8ff5d192712c9b216027e7b sell
	- https://etherscan.io/tx/0xcbb53939d1d5d27fd8ab5a960ee47f574ff37497ab9af03197f7c8cfdf657224 unwrap
- Blocks 14469949, 14469969, 14475472: transfer eth to 3 different wallets
	- https://etherscan.io/tx/0x334139958c3a4cc6356f2ae0b7297417a6ba28d351510011f138385558b7b445 transfer 3.145 eth
	- https://etherscan.io/tx/0xe0975ab0fc58799999fe3ae89dde3741c2cafccb0615582e31f57dda23570a12 transfer 3.145 eth
	- https://etherscan.io/tx/0x852c7ca4fc8c3f551d61377a4ef3e669a6de0f67c9b97630939bded4d3480552 transfer 41.68 eth

Note block 14463323 is at 13:58:50 EST, meaning minting was actually open slightly before communicated 14:00 EST minting start time.

Code: nftx_wowg_arb_bytecode_decompiled.sol

Seems to be better than flash loan method (see "NFTX flash loan" section) because this is a simpler contract than the flash loan contract. Miner algos will prefer verifying a simpler contract over a more complex one, all else equal (gas limit equal). So using this method with a higher gas limit than the flash loan method should generally guarantee the tx will beat a tx using flash loan method.

### NFTX flash loan

Sub-scenario: Redeem window started and unclaimed assets exist in NFTX liquidity pool.

Example: BAYC/MAYC $APE claim 2022-03-27 14:00 EST (pnl ~$600K)

Overview: https://mobile.twitter.com/0x_Beans/status/1506074195351916544

Upon start of release (all actions: https://etherscan.io/address/0x6703741e913a30d6604481472b6d81f3da45e6e8):
- https://etherscan.io/tx/0x38e5465f09999c815adc3a5e878ec62fb669abed0144323401481c7b1f4cc376
	- Buy BAYC_1060 for 106 eth on OS
- In 1 tx: https://etherscan.io/tx/0xeb8c3bebed11e2e4fcd30cbfc2fb3c55c4ca166003c7f7d319e78eaab9747098
	- Swap BAYC_1060 for 1 vBAYC (will be used to pay swap and flash loan fees). Appears this has no fee
	- Get flash loan of 5.2 vBAYC tokens from NFTX vault
	- Swap 5 vBAYC for 5 BAYCs. Pay 0.2 vBAYC in swap fees (0.16 + 0.04)
	- Claim 60,564 APE using 6 BAYCs
	- Swap 6 BAYCs for 5.2 vBAYC. Appears this has no fee
	- Repay flash loan principal of 5.2 vBAYC. Pay 0.6 vBAYC in flash loan borrow fees (0.48 + 0.12)
	- Swap remaining 0.2 vBAYC for 14.15 weth. Owned 1 vBAYC, paid 0.2 in swap fees and 0.6 in flash loan fees
- Blocks 14403978 to 14404105: Swap $APE for eth. 1 $APE ~ $10 at the time, so ~$600K - (0.8 * 106 eth * $3000/eth) = $350K net pnl
- Block 14404269: transfer 399 eth to wallet 0x29b8d7588674fafbd6b5e3fee2b86a6c927156b0
	- https://etherscan.io/tx/0x7922cd5ce234da7ed832dd6cdcc969cac790a9a65651d33dffe9bd89cd1f9b56

Meebits arb code: https://github.com/Anish-Agnihotri/punk-nftx-meebit-arb/blob/master/contracts/Arb.sol

### Pre-reveal

Sub-scenario: Minting started and owners are listing but reveal has not occured yet.

Upon reveal:
- Scrape metadata source to identify which assets have been revealed
- If revealed asset has rare trait, check if asset is listed
- Buy rare trait asset if listed near floor. Assuming some relative value relationship between floor vs rare assets

Example: WoWG claim 2022-03-27
- https://opensea.io/assets/0xf61f24c2d93bf2de187546b14425bf631f28d6dc/16752
	- https://etherscan.io/tx/0x449412d19ebf7064327221b8d95cb54f183d98e5cb0b32808407c24d439a56f9 buy tx
- 1 minute after reveal started, Night Goddess rare trait bought for 1.9, ~0.5 eth above WoWG floor, despite Night Goddess rare trait trading for minimum 5x floor in genesis WoW collection
- Get metadata from https://qm5fuyzuoxfb-wowg-prod.s3.amazonaws.com/t/16752. Given AWS typically has some rate limiting and 16752 was bought only 1 minute after scheduled 8:00 EST reveal, it is possible this was available slightly before 8:00 EST

Example: Steedz claim 2022-04-15
- https://opensea.io/assets/0xef4fc659254954d83597a33c68c47cc7d9fd24a4/2592
	- https://etherscan.io/tx/0x52ae8118a6871b71ed40146b2dac3bc5a6f4d5ec651cb4e36d1b2bede06a88b2 buy tx
- Reveal can only be triggered by owner via steedz website. However this owner did not delist and revealed a semi-rare character type (robohorse)
- It was extremely difficult to see traits on OS. Only source of truth was the metadata site. Even 5-10 minutes after reveal, OS may not display revealed traits even after clicking refresh metadata on OS. Being able to see metadata is a real advantage

### Unclaimed

Sub-scenario: Suppose X_unclaimed is listed at 12, X_claimed is listed at 10, and Y is listed at 2.

The typical relationship that holds is X_claimed + Y = X_unclaimed. If Y increases to 4:
- Buy X_unclaimed for 12
- Mint Y (X_unclaimed is now X_claimed)
- Sell X_claimed for 10 and sell Y for 4 (pnl = 14 - 12 = 2)

Example: Cool Pets claim 2022-01-31
- Apparently pretty competitive. Suspect automated tx execution

## Trade Thru WETH Arb

Scenario:
- Seller offered at 15 and buyer bid for 13
- Seller does not see 13 bid and lowers offer to 10. This does not automatically match with 13 bid. There are no trade-thru rules in crypto
- Arb: buy 10, sell 13

Example: WoW 2022-03-27
- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/4180
	- https://etherscan.io/tx/0xe704f44ad75cb49c0d17db8b03d06ffced2e5d2dd19eae41cd96b4e13bf66f70 buy and sell tx
	- https://etherscan.io/address/0x553eea17185e5ae6bb72f9528a4c3fc1a844b859 contract (first active 2022-03-04). Makes over 10 tx per day. Estimate 10-15 eth net profit between 2022-03-04 and 2022-03-28
- Buys 10 and sells 13 in same tx. Probably very competitive given this contract executes both legs in same tx, but possible listing-to-tx-sent time is not super fast (i.e. might be able to pull this off manually in separate txs)

Example: WoWG 2022-03-27
- https://opensea.io/assets/0xf61f24c2d93bf2de187546b14425bf631f28d6dc/9187
	- https://etherscan.io/tx/0x199372fe8cc09033425f8bd119252c5a27ebaf59deb9ef2f11e066a549876501 buy and sell tx
	- https://etherscan.io/address/0x553eea17185e5ae6bb72f9528a4c3fc1a844b859 contract (same as above)
- Buys 1.67 and sells 1.67 in same tx

Example: 3landers 2022-03-25
- https://opensea.io/assets/0xb4d06d46a8285f4ec79fd294f78a881799d8ced9/5292
	- https://etherscan.io/tx/0x1368f81db13b7d77aa745fec0d0d0bbed67a8d25d7a3c38f9b6e890963d98274 buy and sell tx
	- https://etherscan.io/address/0x553eea17185e5ae6bb72f9528a4c3fc1a844b859 contract (same as above)
- Buys 1.5 and sells 2.2 in same tx

Example: Cool Cats 2022-01-06
- https://opensea.io/assets/0x1a92f7381b9f03921564a437210bb9396471050c/3980
	- https://etherscan.io/tx/0xd47feb7ba12a03db5d810c309fbb932cd520e2d749332fb810f2f25fc810ae56 buy and sell tx
	- https://etherscan.io/address/0x78695c62d060f9f514de007f9079277c0e31029c contract (last active 2022-01-31)

Example: MAYC 2022-04-06
- https://opensea.io/assets/0x60e4d786628fea6478f785a6d7e704777c86a7c6/3217
	- https://etherscan.io/tx/0xb7a8c5a2636f17479053904cf2c91a8c96adf1663d1c45ac8746f0a3c5c7d3b0 winning tx. Contract: 0x887d0f27f9a8e1f6d9c24fadd3151c67a3d993d4
	- https://etherscan.io/tx/0x94d2ef6287f511c517eb6734584d31c3d11acc6e9a18947c450fa4e0dc280ffd too slow. Contract: 0x9e9346e082d445f08fab1758984a31648c89241a (see competitors)

Example: WoWG 2022-04-16
- https://opensea.io/assets/0xf61f24c2d93bf2de187546b14425bf631f28d6dc/21800
	- https://etherscan.io/tx/0x5ba0a0b104bbd7f9b6dde7988b4838fb2a908ebcf1bdfe7d51434f14e3a9558d winning tx. Contract: 0xac9df97f9cd7a5f66913d107cddd00f40ac9ab4c

Competitors:
- https://etherscan.io/address/0x553eea17185e5ae6bb72f9528a4c3fc1a844b859. Estimate 10-15 eth net profit in March 2022
- https://etherscan.io/address/0x9e9346e082d445f08fab1758984a31648c89241a. Estimate 10-15 eth net profit in March 2022. 714 txs betwen 2022-03-05 and 2022-04-06.
	- https://etherscan.io/tx/0x441d8f1aa71cf9c7123dac4d0de6eadf84013b708a817ff788a479e9098f2adb BB 8204 showed up as 20+ edge_ratio opp but got beat by contract buying 1 and accepting 1.2 offer
	- https://etherscan.io/tx/0xe51e612b272e300a3f8f626ec4c495a317a06fc0f21bc3d99cc4e6782ab7ba16 RKL 9485 OS-LR arb
- https://etherscan.io/address/0x78695c62d060f9f514de007f9079277c0e31029c. Estimate 10-15 eth net profit in Jan 2022
- https://etherscan.io/address/0x887d0f27f9a8e1f6d9c24fadd3151c67a3d993d4. 962 txs between 2021-12-22 and 2022-04-06
- https://etherscan.io/address/0xc5320d697fd3b4aeab6c2c7da5e5c7effbd9fc34

