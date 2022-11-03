# Reveal Strategy

## Motivation

Scenario: Minting started and owners are listing but reveal has not occured yet.

Upon reveal:
- Scrape metadata source to identify which assets have been revealed
- If revealed asset has rare trait, check if asset is listed
- Buy rare trait asset if listed near floor. Assuming some relative value relationship between floor vs rare assets

Example: WoWG reveal 2022-03-27
- https://opensea.io/assets/0xf61f24c2d93bf2de187546b14425bf631f28d6dc/16752
	- https://etherscan.io/tx/0x449412d19ebf7064327221b8d95cb54f183d98e5cb0b32808407c24d439a56f9 buy tx
- 1 minute after reveal started, Night Goddess rare trait bought for 1.9, ~0.5 eth above WoWG floor, despite Night Goddess rare trait trading for minimum 5x floor in genesis WoW collection
- Get metadata from https://qm5fuyzuoxfb-wowg-prod.s3.amazonaws.com/t/16752. Given AWS typically has some rate limiting and 16752 was bought only 1 minute after scheduled 8:00 EST reveal, it is possible this was available slightly before 8:00 EST

Example: Steedz reveal 2022-04-15
- https://opensea.io/assets/0xef4fc659254954d83597a33c68c47cc7d9fd24a4/2592
	- https://etherscan.io/tx/0x52ae8118a6871b71ed40146b2dac3bc5a6f4d5ec651cb4e36d1b2bede06a88b2 buy tx
- Reveal can only be triggered by owner via steedz website. However this owner did not delist and revealed a semi-rare character type (robohorse)
- It was extremely difficult to see traits on OS. Only source of truth was the metadata site. Even 5-10 minutes after reveal, OS may not display revealed traits even after clicking refresh metadata on OS. Being able to see metadata is a real advantage

Example: Otherside Deed reveal 2022-05-01
- [otherdeed reveal](../postmortem/otherdeed_reveal.md)
- Estimated $10M edge

## Devops spec

Goal:
- Input: list of token_ids to pull metadata for
- Output: csv file with metadata for each token_id

Metadata details:
- Approximate metadata upload time is known. Sometimes the reveal can be slightly early or late. Occasionally it may be very late (20+ minutes) if collection devs have technical difficulties. In very rare cases the metadata may be accidentally uploaded/leaked well in advance for a short period of time (apparently happened in Otherside deed drop), which if noticed is a huge source of alpha
- Contents of metadata is unknown until reveal. Metadata file should be in 1 of 2 formats (with or without an asset "name"). There can be any number of traits
- Request volume will likely be very high at time of reveal due to other bots. Method of rate limiting is currently unknown but likely by IP. The metadata site is always publically accessible though, so there is no API key based rate limiting
- Based on timestamps of opportunities in highly anticipated mints (Otherside deeds), need the metadata pulling logic to complete within a few minutes to be competitive. The fastest competitors are on the order of seconds, and the slowest are ~10 minutes

Basic logic:
1. Start AWS server #1 ~5 minutes before announced reveal time
2. Server #1 pings metadata url with 1 request every ~1 second until request returns populated metadata
3. Once metadata is available, start other servers
4. Distribute requests for N assets across servers #1-#M
5. Save metadata as csv with columns token_id, name, {trait 1}, {trait 2}, etc

Advanced logic in addition to above
- The logic above is the "critical path" (most latency sensitive) where the input will be token_ids listed on a marketplace. In a slower path, we also want the metadata for unlisted token_ids (see Strategy 2)
- Furthermore the list of token_ids listed is dynamic (there can be listings at cheap prices anytime, including after reveal). It is reasonable to assume the chances of a good opportunity among these is relatively low thought, so this can be in a slower path too
- Some collections do not reveal all assets automatically at a given time, sometimes they are triggered by the user clicking a reveal button for example. The time at which the reveal occurs will be unknown. For these collections, the critical path logic must be triggered continously until all listed token_ids have been revealed

## Strategy spec

Once metadata is received, the goal is to identify rare assets that are listed at low prices.

Data:
- Continously scrape for listings leading up to and after reveal
- Remove listings that already been sold or are expired

Strategy 1: high value rare trait known pre-reveal
- Rank by known rare trait(s) and price
- Buy assets listed at lowest prices

Strategy 2: no rare trait is known pre-reveal
- Calculate distribution by trait using listed token_ids (or using all token_ids if available from slow path)
- Rank by known rare trait(s) and price. Need to make judgement call on most sought after trait categories and traits
- Buy assets listed at lowest prices

