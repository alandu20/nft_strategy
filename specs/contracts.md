# Contracts

## ERC-721 Transactions
* SetApprovalForAll
	* topic 0: 0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31
* Approval
	* topic 0: 0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925
	* topic 1: address owner
	* topic 2: address approved
	* topic 3: uint256 tokenId
* Transfer
	* topic 0: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
	* topic 1: address from
	* topic 2: address to
	* topic 3: uint256 tokenId

## Opensea Wyvern Transactions
* OrdersMatched, OrderCancelled: 0x7be8076f4ea4a4ad08075c2508e481d6c946d12b
	* OrdersMatched topic 0: 0xc4109843e0b7d514e4c093114b863f8e7d8d9a458c372cd51bfe526b588006c9
	* OrderCancelled topic 0: 0x5152abf959f6564662358c2e52b702259b78bac5ee7842a0f01937e670efcc7d
	* OrderCancelled topic 1: appears to be unique 32-bit hex id for OS to internally match with listing id off-chain

## Examples

* Collection events
	* Contains SetApprovalForAll, Approval, Transfer (includes NFTTrader private sales)
	* knights-of-degen-official: https://etherscan.io/address/0xe3f92992bb4f0f0d173623a52b2922d65172601d#events
	* world-of-women-nft: https://etherscan.io/address/0xe785e82358879f061bc3dcac6f0444462d4b5330#events
	* karafuru: https://etherscan.io/address/0xd2f668a8461d6761115daf8aeb3cdf5f40c532c6#events
* Enable listings: https://etherscan.io/tx/0x014cdd0a2ee6185b700fd144b68b9f23a2d69e5d4bb1cfba440b2c8b1d920949#eventlog
	* SetApprovalForAll for bossbeauties collection
* Cancel listing: https://etherscan.io/tx/0xb183aad29fa31b978e23c80c5e91271a1fa4852b6d770dd5d0e1b1442a06332e#eventlog
	* OrderCancelled for world-of-women-nft token_id 8643
* Sale: https://etherscan.io/tx/0xad2e884e0e768a476a0b6e158693f29eb8cdc3e98ccb27809f2674602cccf96a#eventlog
	* Approval, Transfer, and OrdersMatched for world-of-women-nft token_id 6398
* NFTTrader Private Sale: https://etherscan.io/tx/0xcede00bc31a2b03c596cbd0e4b96b75f183d47d6acf065401bbc9a31a22fa170#eventlog
	* paymentReceived, Approval, Transfer, swapEvent for world-of-women-nft token_id 9740
	* Search block 14000195 in world-of-women-nft event page
* Old listing exploitation: https://etherscan.io/tx/0x263de70e03f5ba15cf86e78256120d35e2d79d40cfdc24b4510a949de3af6519
	* cool-cats-nft token_id 9575: https://opensea.io/assets/0x1a92f7381b9f03921564a437210bb9396471050c/9575
	* List at 2.68 by bingbong900 on 2021-08-24
	* Transfer to 0x0394 on 2021-08-24: https://etherscan.io/tx/0xf43431189c5739b57374cc755a08ec77b2ac8842aadd7ca8048bf423cad2657e
	* Sale/transfer to E16DD6 (flashbot): https://etherscan.io/tx/0x263de70e03f5ba15cf86e78256120d35e2d79d40cfdc24b4510a949de3af6519
	* bingbong900 wallet: https://etherscan.io/address/0x631040c35b5971e764549e2d975381cff27afba3
	* E16DD6 wallet: https://etherscan.io/address/0xe16dd613ba42537f8bb071995fcc438eb006541e
* Contract event specification (ABI):
	* world-of-women-nft: https://api.etherscan.io/api?module=contract&action=getabi&address=0x7be8076f4ea4a4ad08075c2508e481d6c946d12b&apikey=P5Z51F71UR9ZAIVH66FWRXHPE4JY1CHADY