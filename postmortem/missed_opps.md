# Missed Opps

## Too Slow
- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/8204 BB
	- https://etherscan.io/tx/0x441d8f1aa71cf9c7123dac4d0de6eadf84013b708a817ff788a479e9098f2adb tx that won (block 14497384)
	- Was not even fast enough to send out tx
	- Other potential competitors:
		- https://etherscan.io/tx/0xdd61e7372051756c1fc5aecfce0b9b14ef6b3c32a43bf0dad0ebaca7759f409e same block, contract failed due to funny error "f ya life up". History of contract suggests it is also running trade thru weth strategy
			- https://etherscan.io/address/0xac9df97f9cd7a5f66913d107cddd00f40ac9ab4c contract
		- https://etherscan.io/tx/0x5cc05d794a1a4daeb5c3801040d91b45df048ccd0bba1ea6970784965236e9e1 block 14497385, contract failed due to error "sold"
			- https://etherscan.io/address/0xf80d365817e21652b0d17383aa792c1111b8939e contract
		- https://etherscan.io/tx/0x12d63fbc92b95a5013c012861e583f8d5683e4e47943f26c76b9c89e601bc345 block 14497386, failed with generic reverted error, likely a manual execution competitor
- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/7633 RKL
	- Listing 2022-04-01 12:25:34 EST
	- https://etherscan.io/tx/0x6923b66c0f728d0b6efac9a824ea55a8f8c971bc3e26c6582bdbc899967f087e 12:26:22 EST tx that won (block 14501445), 48 seconds after listing
		- https://opensea.io/0x1328d0b3a2f9c35a18dd21361985ea54cbc555ea wallet has been flipping for at least 6 months. Typical latency on minutes scale so may have been human watching listings
		- Only OS tx in block
	- https://etherscan.io/tx/0xd6be3bdb6f8ab9848add23ee10d88694b9b506bbca4ff87d3d3e193f51052e0f 12:26:25 EST my failed tx (block 14501446), lost by 3 seconds
		- Appears to be no other tx in this block or next block going for this opp. So no other competitors close latency-wise
	- Changes:
		- Add "slug_short" to config to reduce audio alert time
		- Reduce lookback_seconds in get_latest_listings to avoid pricing older assets needlessly
		- New throttle_delay param set to 5 seconds for get_latest_listings as opposed to default 20 seconds
		- Run RKL on 5 second watch rather than 10
		- Was also scraping listings and running rinkeby testnet node. Consider getting new computer dedicated to identifying opps
- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/9485 RKL
	- Listing 2022-04-06 20:29:02 EST
	- https://etherscan.io/tx/0xe51e612b272e300a3f8f626ec4c495a317a06fc0f21bc3d99cc4e6782ab7ba16 20:28:58 EST tx that won (block 14535558), somehow 4 seconds before listing WTF??
	- In single tx:
		- Bought for 1 eth on OS (0x722b53fa46C646fDD49bDaF659ea79584C552303 "Adiobox" -> 0x9e9346e082d445f08fab1758984a31648c89241a smart contract "9E9346")
		- Sold for 1.211 weth on LR https://looksrare.org/collections/0xEf0182dc0574cd5874494a120750FD222FdB909a/9485#activity (0x9e9346e082d445f08fab1758984a31648c89241a smart contract "9E9346" -> 0xD86e3031447a197cd24E80bf3913C63bd1021451 "0xfakeout")
- https://opensea.io/assets/0xf61f24c2d93bf2de187546b14425bf631f28d6dc/21800 WoWG
	- Listing 2022-04-16 09:04:15 EST
	- https://etherscan.io/tx/0x5ba0a0b104bbd7f9b6dde7988b4838fb2a908ebcf1bdfe7d51434f14e3a9558d 09:04:05 EST tx that won, somehow 10 seconds before listing WTF??

## Not Around
- https://opensea.io/assets/0xb5c747561a185a146f83cfff25bdfd2455b31ff4/1671 BB
	- https://etherscan.io/tx/0xf1d0012099957c6258ea940cca2ce3524a23e3e1291fb743398cd9a23386d1e7 tx timestamp 2 minutes after listing time
	- 15.5 edge_ratio, 0.93 edge. Floor was ~1.15
	- https://opensea.io/0x8Bd174C242eb2270C45BE52D2eca5Fec21aa095d (Mahatma) wallet has been listing BB for dirt cheap below floor over last couple weeks (occasionally even though weth bid like BB 8204)

## WTF??
- https://opensea.io/assets/0x892848074ddea461a15f337250da3ce55580ca85/6615 cyberbrokers
	- https://etherscan.io/tx/0xa1dc31b7d7643107a8b9cfff167cbf51aaf2f805e0372d9f68fdf731fa9b0349 bought for 4 eth
	- No listing at 4 eth right before sale but somehow bought for 4 eth while floor was 6+. There was 4 eth listing on 2022-03-17, 18 days prior