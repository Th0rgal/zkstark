# a little experiment

I am learning how starks work. The goal of this project is to build a prover and a verifier for a super simple circuit. I want to use zkStarks and the field F_(2**251 + 17 * 2**192 + 1) so that there is no trusted setup and it doesn't cost much to use on Starknet (since the operations would be native).