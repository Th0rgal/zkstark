# a little experiment

I am learning how starks work. The goal of this project is to build a prover and a verifier for a super simple circuit. I want to use zkStarks and the field F_(2**251 + 17 * 2**192 + 1) so that there is no trusted setup and it doesn't cost much to use on Starknet (since the operations would be native).

## Notes

### Stark friendly curve
See https://docs.starkware.co/starkex/crypto/stark-curve.html
Sagemath:
```py
P = 3618502788666131213697322783095070105623107215331596699973092056135872020481
F = Zmod(P)
curve = EllipticCurve(F, [1, 3141592653589793238462643383279502884197169399375105820974944592307816406665])
0*curve([X, Y])
```