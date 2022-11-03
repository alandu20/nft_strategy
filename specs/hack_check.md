# Hack Check

## Motivation
OS oftentimes freezes trading of an asset if there is enough evidence to deem an asset was stolen. OS will freeze the asset in perpetuity until the asset is returned to the original owner. There are two types of compromised statues on OS: (1) account previously owning the asset is marked as potentially compromised (asset is not frozen), and (2) asset is marked suspended for suspicious activity. Assets are reported stolen to OS by the owner whose account was compromised. Information on the hack is sent to OS, and then a decision is made whether to freeze the account.

Examples:
- https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/2158
- https://opensea.io/assets/0xe785e82358879f061bc3dcac6f0444462d4b5330/3977

## Compromised Account Checks

### OS warning

### Model Based

Connect addresses to known fraudulent addresses
- Degrees of separation
	- Number of transactions with fraudulent address
	- Number of transactions with address that interacted with fraudulent address
	- Number of transactions with address N degress of separation (in terms of interactions) with fraudulent address
- Elastic linking

References
- https://twitter.com/zachxbt/status/1519373126894862337?s=20&t=KTktG8nUq--98xGdMM4UCg