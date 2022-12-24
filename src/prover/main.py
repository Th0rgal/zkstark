from tools.field import P, FieldElement
from tools.pedersen import trace_pedersen_hash
from tools.polynomial import X, interpolate_poly
import random

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

# 3) we create a small subgroup of F which can contain the trace
# P-1 = 2^192 * 5 * 7 * 98714381 * 166848103
# So 10240 = 5*2^11 | P-1
# We can find the generator of this subgroup
g = FieldElement.generator() ** (2 ** (192 - 11) * 7 * 98714381 * 166848103)
assert g.is_order(10240)

# We can then find the elements of this subgroup
G = [g**i for i in range(10240)]

# 4) we interpolate the trace to find the polynomial
f = interpolate_poly(G[: len(trace)], trace)
print(f._repr_latex_())
