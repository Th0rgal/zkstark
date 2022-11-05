from tools.field import P, FieldElement
from tools.pedersen import pedersen_hash
import random

# Given public b, a commitments list and a private a, we need to generate a proof
# that we know a such that hash(a, b) belongs to the list:
# ∃ a, hash(a, b) ∈ commitments

# we use a seed to keep this example deterministic
random.seed(0)

# 1) we generate two random felts
a = FieldElement(random.randrange(P))
b = FieldElement(random.randrange(P))

# 2) we compute hash(a, b) with https://docs.starkware.co/starkex/pedersen-hash-function.html
hashed = pedersen_hash(a, b)

# 3) we deposit to the contract using this hash

# 4) we query the commited elements
# here I just put a few other random values
commitments = [
    hashed,
    random.randrange(P),
    random.randrange(P),
    random.randrange(P),
    random.randrange(P),
]
