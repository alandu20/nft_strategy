# Deal Driven Takeout (DRT) Strategy

## Motivation
- Other market participants are attempting this trade. See Examples section
- Combination of recurring, slow, and dynamic paths are not fast enough to identify this opportunity:
	1. Perceiving edge (in price_ratio space) relative to a periodically (~20 minutes) saved global floor price
		- The edge on any sales immediately after the sweep is calculated relative to last saved floor price, even though the floor price in reality is moving up after every sale. For example suppose saved floor price is 10, listed prices are [10, 10, 10, 13, 14, 15], sweeper buys 3x for 10, and then immediately someone buys 13. The edge perceived on 13 is relative to saved floor price of 10, so the edge is substantially less than if perceived floor price was 13
		- The true floor in the above example is 13 at the time of the 13 sale. But what if there was still a 10 level left? Suppose listed prices are [10, 10, 10, 10, 13, 14, 15], sweeper buys 3x for 10, then someone buys the last 10. The edge percieved on the last 10 is relative to a floor price of 10. In reality, there is follow through after the sweep and the last 10 is not a stable floor, i.e. predict floor is somewhere between 10-13, probably closer to 13. The edge perceived on the 13 sale relative to a predicate floor between 10-13 is higher than the edge relative to a floor of 10
		- Actual example of this in clonex on 2022-02-25, see Examples section. Perceived edge on the 13.75 sale is relative to floor of 13 rather than a predicate floor that probably should have been around 13.97
		- Even if snapshots of global floor were saved continously in recurring path, the floor may still be wrong. Have observed cases where OS floor price is wrong in a fast market (e.g. world-of-women-nft floor move from 3.8 to 8 eth on 2022-01-12)
	2. Pricing is updated periodically (~few hours) with latest sales (recurring path)

## Examples
- Sweeps in edenhorde-official on 2022-02-21
	- 12:37:19 UTC block 14249464: sweep #1 (10 assets). All near floor, range 0.779-0.799 eth. https://etherscan.io/tx/0x5180ad34bdc7c25c3993774a365aa5176db8416039968da42074671c23623209
	- 12:38:44 UTC block 14249468: dAlch3mist buys token_id 1210 from ThedreamsGod for 0.777 eth. Lists for 1.5 eth at 13:09 UTC but cannot flip. https://etherscan.io/tx/0xe6ed3aa1e981bac4406bee2903b1a4de16be5d8adfad1f4b78717d93619d560d
	- 12:39:19 UTC block 14249471: sweep #2 (30 assets). All near floor again, range 0.777-0.869 eth. All 3 assets at 0.777 sold by ThedreamsGod. https://etherscan.io/tx/0x29e4263583358b01c31aa77ea1f412b6664b75529d7aa9a9298828153430be03
	- 12:41:04 UTC block 14249488: ThedreamsGod buys token_id 7728 for 3 eth. https://etherscan.io/tx/0x25814de588e29ccee0662541d2f8a34534218f3cea7eed3d0295246650a25908
	- 12:48:01 UTC block 14249519: sweep #3 (5 assets). Some higher value assets, range 0.88-2.19 eth. https://etherscan.io/tx/0xc21c8e7f2e911618eea4abd6a55b8296ff2639ad86925067f6165a3fb6bc7520
	- 13:13 UTC: floor is 0.875
	- 14:45 UTC: floor is 0.91
- Sweeps in edenhorde-official on 2022-02-24
	- 17:24:06 UTC: global floor 0.49
	- 17:31:07 UTC block 14270148: 7 asset floor sweep for 5.3 eth. https://etherscan.io/tx/0x85e62a798b3494ce4a609d78441c93837a1e317266c35dd785c2608506cf545d
	- 17:31:21 UTC block 14270149 (next block): ichivlad buys token_id 6925 for 0.55 eth. Lists for 1 eth few hours later. https://etherscan.io/tx/0x314817788a81e98c3c5c2d6f48046e737c56e6aa4a93d6e15a3a4f967a5825e7
	- 19:47:28 UTC: global floor 0.56
	- 20:37:34 UTC block 14271002: 10 asset floor sweep for 5.85 eth. https://etherscan.io/tx/0x855609836f2c6c58eda530ca52794b07db7ff60c413f53dc173c7e0c1e140b4e
	- 20:38:17 UTC block 14271003 (next block): 0x_davinci buys token_id 3917 for 0.65. https://etherscan.io/tx/0x0925c4710a64ed80c70984fd4ed1e051034d306a7be47496518721bcdc58c91e
	- 21:08:04 UTC: global floor 0.64
- Sweep in clonex on 2022-02-25
	- 03:08:03 UTC: floor is 11.94
	- 03:25:17 UTC block 14272858: 27 asset floor sweep for 355 eth by JohnDonahoe (name of Nike CEO...). https://etherscan.io/tx/0x25aec4668f14e5387af8e2f98cd9c40eed08a2ff430abd4050fd5846bcbc893d
	- 03:28:05 UTC: floor is 13.0. Likely not accurate b/c lowest sales are 13.75, 13.99, 13.98, 13.97 for the next couple hours
	- 03:28:59 UTC block 14272874: bool-nft buys token_id 9328 for 13.75 eth. https://etherscan.io/tx/0x42d32076fe5b83846c8af78c4403773d16c9d7f4de30b123691fc2ce19cb8204
	- 03:41:27 UTC: floor is 13.97
	- 13:40:43 UTC: floor is 14.25
- Sweeps in 3landers on 2022-03-02
	- 01:58:29 UTC: floor is 1.6
	- 02:15:50 UTC: 14 asset sweep near floor (range 1.633-2.1) for 26 eth by FF0288. https://etherscan.io/tx/0x5487d70802bde2f1e4ffa1ac29163e87a726ecee2cec5582bf325a698da7e9c8
	- 02:32:05 UTC: 4 asset sweep near floor for 8.7 eth by Christian2022. https://etherscan.io/tx/0xe79f79a63f7683ef7e143c9084aaa460d2e0090bb462b37a5cd68f01852f2781
	- 02:32:26 UTC: Eneftee99 buys token_id 617 for 1.85. https://etherscan.io/tx/0x551006892a3bdb395d3a3b2d6fd5fc7f93ccf956446cd1412266e6cfa86de8f2
	- 02:34:56 UTC: 9 asset sweep for 17 eth by FF0288. https://etherscan.io/tx/0x4c9bcc3e5d68ed235122dd050bdff6d4033c01d13160b4f004c6b51bf983ea31
	- 02:58:43 UTC: floor is 1.6
	- 03:58:55 UTC: floor is 1.95
- Sweep in edenhorde-official on 2022-03-10
	- 16:55:32 UTC: floor is 0.4
	- 17:04:05 UTC: 36 asset floor sweep for 17.8 eth by Galaktic_Shaman (galaktic.eth), known sweeper active in other collections. https://etherscan.io/tx/0xb648dc063f823857f145fb170825636f7c0bce74e5abbe4f81895b2a71b31d24
	- 17:05:41 UTC: floor is 0.438
	- 17:06:15 UTC: DavidStanley buys token_id 5393 for 0.58 eth. https://etherscan.io/tx/0xc7ca4a930c492fe1495aff973a6f7b054faab19dc9f5492f78150c5213db59c8
	- 17:15:51 UTC: floor is 0.56
- Sweep in mfers on 2022-03-11
	- 16:46:47 UTC: floor is 2.488
	- 16:48:10 UTC: 10 asset floor sweep (7 on OS) for 22.2 eth by 0xjayson.eth. https://etherscan.io/tx/0x07bf9f84fddd24c3a5e75e8afc4e0436ce1684ba951192784fa26e317a2c682b
	- 16:56:15 UTC: moremoney1 buys token_id 7255 for 2.5 eth. https://etherscan.io/tx/0x91b983675422db89d65b6ca34cdea726bbae9b74f642b8fafb7fb7eb6ab9fc9a
	- 17:14:50 UTC: floor is 2.6
	- 17:34:50 UTC: floor is 2.7
	- 18:05:24 UTC: floor is 2.77. 28 sales on OS since time of sweep, a couple for ~8 eth
	- 23:00:00 UTC: Yuga Labs acquiring Larva Labs announcement. May have impacted sentiment
	- 2022-03-12 12:09:33 UTC: floor is 2.51
	- 2022-03-12 19:09:17 UTC: floor is 2.85
	- 2022-03-12 21:57:27 UTC: floor is 2.99
	- 2022-03-13 01:23:23 UTC: floor is 3.469
- Sweeps in edenhorde-official on 2022-03-24
	- 22:00:09 UTC: OS displayed floor is 0.295
	- 22:20:08 UTC: 10 eth floor sweep by EA459A, on OS, LR, and X2Y2 using GemSwap. https://etherscan.io/tx/0xca0ff9f8b191fc6efe432f0144e4b0ed6dccb95890f0770c522ebfed11876159
	- 22:36:21 UTC: 10 eth floor sweep by EA459A, on OS, LR, and X2Y2 using GemSwap. https://etherscan.io/tx/0xba970243c97894a3ea7f2db19f2642bc514941f287627e78cffce4ad85962b3e
	- 23:00:44 UTC: 11.7 eth floor sweep by EA459A, on OS and LR using GemSwap. https://etherscan.io/tx/0x3932aa74f66679a6f4d4ac4ab2ec09df3aaae612017ef0a73d62a2dcf7598723
	- 23:02:48 UTC: EA459A buys 2726 for 0.2949 eth. https://etherscan.io/tx/0x15f7d6b7312cf637ce2db5c0baa3ff0ec354b9cdb1cadb89867634003573af3c
	- 23:03:07 UTC: ajnin buys 8277 for 0.295 eth. https://etherscan.io/tx/0x0228696bea962797f2f600dc0e272f4deddc2ee242c04dc429583a1e864de837
	- 23:04:09 UTC: ajnin buys 6671 for 0.325 eth. https://etherscan.io/tx/0xf9af328d1dea96e38be1ba603f5359da7fc47333d1cb9eeff9863bec138f49a2
	- 23:20:04 UTC: 76A886 buys 7764 for 0.359 eth. https://etherscan.io/tx/0x2267257da506bd919ef3756b5843f1eda851057f712c64e670d9435e0aa48679
	- 23:22:23 UTC: 23x3 buys 8015 for 0.385 eth. https://etherscan.io/tx/0xd4b974a63fd14e3e19632301603ac00dfa4840b0316b17b4af25b1b6e5ed9b6c
	- 23:26:23 UTC: OS displayed floor is 0.45
	- 23:51:42 UTC: OS displayed floor is 0.495
- Sweep in cool-pets
	- Prior to sweep floor ~1.7 eth. Cool Cats tweets at 20:26 UTC that cooltopia has reopened
	- 20:29:18 UTC: 52 eth floor sweep by NFTRelicHunter. https://etherscan.io/tx/0xd359d64fea24a2280c6793769f975d9e119a57fb8761f64fc00e020a84c18903
	- 20:29:28 UTC: 0x79296381BD8690482376fe355E0F68dCa8BB6B4e buys for 1.75 eth. https://etherscan.io/tx/0xb0a54fe1a55ea494bf8e6e79e1e6016f309a00fc2df60d5b5e8e0a717aca6c53. Many others follow
	- 20:30:02 UTC: 1.79 eth https://etherscan.io/tx/0x5c0ae4011730061d57fa0c0bd0525c78c04765b6b86bbd6897f8f2b4243a1ecc
	- 20:41:04 UTC: OS lagging so unclear what is available to buy. A few buys at 1.98 eth despite others trading closer to 2.2 eth, for example https://etherscan.io/tx/0x5885a1f35dd3d852133f0a053cff4c97d236e4b74b4aa8e9e65db589c0f029fc
	- 20:45 UTC: floor ~2.1 eth unclear due to OS lag
	- Within 30 minutes later, floor back down to ~1.8 eth. In evening, back down to ~1.4 eth

## Logic
- Predict floor move based on size of sweep and remaining listed prices (from listings file from slow path)
- Update sales file from slow path and run pricer with predicate floor
- Determine what listings still remain after sweep by comparing sales to listings file. OS oftentimes is slow to update what listings have been sold (e.g. edenhorde 2022-03-24), so it is hard to manually tell what is still listed unless user clicks through each listing and sees they are no longer listed. This is probably a large source of the edge. It is possible external aggregators like gem.xyz are faster to update than OS but unlikely, so really only bots are able to discern quickly what is still available to buy
- Calculate edge on remaining listed prices
