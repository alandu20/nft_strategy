# fear-city reveal

## Background
Traits:
- 3333 avatars that provide access to the Fear City brand and ecosystem: 6 characters (Barb Bardot, Helen Helsinki, Baker, Sophia Heaven, Thumper, Shadowkai), 250+ traits, Legendary characters (6)
- The art is generated and it gets randomized along with it preventing the team mint(150 total) from containing a Legendary. The art and metadata is then uploaded to IPFS. Then on reveal, the collection excluding the team mint is shuffled again using a block hash from the contract reveal function so that no one including the team will know what the final NFTs will be. This will ensure that no Legendaries go to the team.   There are 6 total Legendaries in the collection

Reveal Details:
- Scheduled for 2022-06-10 18:00 EST
- https://opensea.io/collection/fear-city

## Opportunities

## Issues
- Bought https://opensea.io/assets/ethereum/0x92ac03d1eb81bb8402fcdbe3ef43c6ca0cbba8f9/2807 at 18:03 (https://etherscan.io/tx/0x4818d6750309a057a9379200ce4b0c571e963e78fe4e33add728bacfe51147bd) for 0.195, about 2x floor. Sold at floor for 0.08 an hour later
	- Thought it was this legendary from metadata: https://opensea.mypinata.cloud/ipfs/QmewMnqsVHdEckqoYmPLXzoE2Q3ko1SCXFq99HLhCHjjTh/2807
	- Turns out the token_id 2807 corresponds to 2881 in metadata: https://opensea.mypinata.cloud/ipfs/QmQzKmAFTTiU9tk7KCPn6sFL2qkSznJD9DuFEdbhyCcnW8/2881. Can confirm this by clicking Details -> Token ID 2807 link
	- Team did this on purpose: "we wanted to ensure that none of the legendaries could be located by token ID" per https://discord.com/channels/948997594728788128/948999060868714496/984967224387309628
	- The actual "Legendary Baker" asset was https://opensea.io/assets/ethereum/0x92ac03d1eb81bb8402fcdbe3ef43c6ca0cbba8f9/2733, with metadata at https://opensea.mypinata.cloud/ipfs/QmQzKmAFTTiU9tk7KCPn6sFL2qkSznJD9DuFEdbhyCcnW8/2807. Note the metadata link at time of trade was https://opensea.mypinata.cloud/ipfs/QmewMnqsVHdEckqoYmPLXzoE2Q3ko1SCXFq99HLhCHjjTh/2807; the team modified the metadata url later on (not sure when). Notice name="Fear City #2807" in the old link, and changed to name="Fear City #2733" in new link
	- Basically at time of trade, https://opensea.mypinata.cloud/ipfs/QmewMnqsVHdEckqoYmPLXzoE2Q3ko1SCXFq99HLhCHjjTh/2807 was the only known information, i.e. 2807 metadata_id was a legendary with name="Fear City #2807". The actual token_id corresponding to this was unknown, though. And even more tricky, the name="Fear City #2807" was misleading (and later on changed in the new metadata link)
	- So given this setup it is very nontrivial to know which token_id to buy
		- Maybe could use OS search bar link: "https://opensea.io/collection/fear-city?search[stringTraits][0][name]=Legendary&search[stringTraits][0][values][0]=Legendary%20Baker&search[sortAscending]=true&search[sortBy]=PRICE"
		- Validate asset endpoint (https://docs.opensea.io/reference/validate-assets) does return https://opensea.mypinata.cloud/ipfs/QmQYosFLaqRPXVBruV7zMkPNKn4MXDaFwMf388RQR6re6B/2807 for token_id 2733, but OS rate limiting would probably make it infeasible to map all token_id to metadata_id
		- Definitely need to click on Details -> Token ID link to confirm the asset's metadata address! This would have at least avoided this erroneous buy (although finding the correct token_id is still unsolved)