# Murakami Flowers Reveal

## Trades
- Attempted to buy https://opensea.io/assets/0x7d8820fa92eb1584636f4f5b8515b5476b75171a/533 for 7 eth, probably about 0.5 eth above global floor
	- https://etherscan.io/tx/0x28c1fa169e6efa9a0179fce56c0cc813b8b248a255c0d9f97d01f19d26f9a143 my tx dropped and replaced
	- https://etherscan.io/tx/0xb5baa71015e946f0edeb9b492ddfe29b24b4ed4f7c5e0388e90debed4b37662d my tx failed (block 14708410)
	- https://etherscan.io/tx/0xf65559ff0ae82a2859c4cb31094709e133817a0c635cff5fb36ce29e6a666372 tx that won (block 14708408), paid 0.125 eth gas, 23 seconds before my failed tx
- Bought https://opensea.io/assets/0x7d8820fa92eb1584636f4f5b8515b5476b75171a/956 for 7.25 eth
	- https://etherscan.io/tx/0x19158835e7526483c95c9a6c89275aa72b4b25931f7e75d77a248d8215fe3062

## Issues
- Reveal was not instant, had to be triggered by minting on website using wallet with Murakami Seed. So many flowers were not revealed initially. Code broke on first token_id that was unrevealed. Also the token_ids did not match up with the flower names, so in the moment I think that confused me in terms of sorting out what was revealed. I still think it is possible that some flowers were not populated on the metadata site despite showing revealed traits on OS, but cannot verify anymore