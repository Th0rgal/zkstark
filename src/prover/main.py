from tools.field import P, FieldElement
from tools.pedersen import trace_pedersen_hash
from tools.polynomial import X, interpolate_poly, Polynomial
from tools.merkle import MerkleTree
import random
import json

# Given public b, a commitments list and a private a, we need to generate a proof
# that we know a such that hash(a, b) belongs to the list:
# ∃ a, hash(a, b) ∈ commitments

# we use a seed to keep this example deterministic
random.seed(0)

# 1) we generate two random felts, 0 is forbidden
a = FieldElement(random.randrange(1, P))
b = FieldElement(random.randrange(1, P))

# 2) we compute hash(a, b) with https://docs.starkware.co/starkex/pedersen-hash-function.html
trace = []
trace.append(a)
trace.append(b)
trace_pedersen_hash(trace)
hashed = trace[-3]  # CurvePoint.from_trace(trace).x
assert len(trace) == 9133

# 3) we find a small subgroup of F which can contain the trace
# P-1 = 2^192 * 5 * 7 * 98714381 * 166848103
# so 10240 = 5*2^11 | P-1
# we can find the generator of this subgroup
g = FieldElement.generator() ** (2 ** (192 - 11) * 7 * 98714381 * 166848103)
assert g.is_order(10240)

# we can then find the elements of this subgroup
G = [g**i for i in range(10240)]

# 4) we interpolate the trace to find the polynomial

# f = interpolate_poly(G[: len(trace)], trace)
precomputed = open("polynom.precomputed.json", "r")
f = Polynomial([FieldElement(felt) for felt in json.load(precomputed)])
precomputed.close()

# 5) we extend the trace polynomial by evaluating it over a larger domain

# 5) A - we find a 8 = 2^3 times bigger subgroup of F which can contain the trace
w = FieldElement.generator()
h = w ** (2 ** (192 - 14) * 7 * 98714381 * 166848103)
assert h.is_order(8 * 10240)
H = [h**i for i in range(8 * 10240)]
# 5) B - we find a coset from this subgroup by multiplying by the F generator
eval_domain = [w * x for x in H]

# 5) C - we evaluate the trace polynomial

# f_eval = [f(d).val for d in eval_domain]
precomputed = open("evaluation.precomputed.json", "r")
f_eval = [FieldElement(felt) for felt in json.load(precomputed)]

# 6) Commitment
# first_tree = MerkleTree(f_eval)
# commitment_1 = first_tree.root.as_felt()
commitment_1 = FieldElement(
    -892985561352262060265542067674069167736680963668018777433588830440521106473
)
