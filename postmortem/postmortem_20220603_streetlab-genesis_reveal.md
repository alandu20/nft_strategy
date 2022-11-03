# streetlab-genesis reveal

## Background
Traits:
- 88 with secret attribute granting access to Curator Club
	- Get one of the 88 Streetlab Genesis NFTs with a secret attribute that grant you a membership pass to the Curator Club (those secret attribute are going to be revealed right after the mint). Earn a share of "Streetlab Curated" profits on a quarterly basis
	- Secret attribute revealed on Twitter spaces: Golden Crown
		- https://discord.com/channels/896053160425189446/896057291349049404/982365097890566145
	- https://medium.com/@streetlab.io/streetlab-io-roadmap-3f816350da5f

Reveal Details:
- Scheduled for 2022-06-03 16:00 EST. Ended up revealing around 15:44 EST

## Opportunities
Golden Crown (estimated flippable price: 2 eth)
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/3382 in opp list. bought 0.36 eth at 15:44 EST. Sold 3 eth 20 minutes later
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/3174 in opp list. listed 12 hours before, somehow I saw on OS filter page for golden crown (clicked on trait filter after seeing first sale about 30 seconds before), might have been able to buy it if not for confusion. received 2 weth bid within 15 minutes
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/800 in opp list. bought 0.98 eth 15:55
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/3857 bought 1.3 eth 15:55
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/3413 already revealed, listed, bought for 1.5 eth within 1 minute, probably around fair value
- https://opensea.io/assets/ethereum/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/3220 already revealed, listed, bought for 1.88 eth within 1 minute

## Issues
- Getting the metadata url from asset call is too slow: https://api.opensea.io/api/v1/asset/0x165a2ed732eb15b54b5e8c057cbce6251370d6e8/217/?format=json
	- Original url was https://metadata-6e9t2e4f6v9jp.streetlab.io
	- Changed to https://opensea.mypinata.cloud/ipfs/bafybeih5grmobvfoft5arfsd5xplkrbvakaha4h5cavxfzvdb57qa25rxm
	- Could not see this change until around 10 minutes after reveal
	- Should try https://docs.opensea.io/reference/validate-assets (I believe this is a newer endpoint). Returns metadata url ("token_uri"), guessing this updates faster than the /asset endpoint
	- Should try https://docs.opensea.io/reference/retrieving-a-single-collection. Returns metadata url ("token_uri"), maybe updates faster than the /asset endpoint
	- Consider getting metadata values directly from /asset endpoint if cannot find metadata url and/or metadata url has unexpected safeguards to prevent scraping
	- https://etherscan.io/address/0xfd5e3eb879798125e0363f54a8e6a0bb6e9a48d7#code contract code should also have metadata url