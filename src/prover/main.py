from tools.field import P, FieldElement
from tools.polynomial import X, interpolate_poly, Polynomial
from tools.curve import curve, G, O
from tools.merkle import MerkleTree
from tools.channel import Channel
import random
import json

# We need to prove we know a such that a * G is part of a list
# ∃ a, hash(a, b) ∈ list

# we use a seed to keep this example deterministic
random.seed(0)

# 1) we generate a random felt, 0 is forbidden
k = random.randrange(1, P)

# 2) compute the trace
# we initialize the registers to 0
# [id : 0, bit : 1, add[coeff, x, y, inf] : 2, to_double[x, y, inf] : 6,
# doubled[coeff, x, y, inf] : 9, r1[x, y, z] : 13, r0[x, y, z] : 16 ]
registers = 33 * [19 * [0]]

# we fill registers at t=0
G.write(registers[0], 13)
O.write(registers[0], 16)

# and we add our montgmery computation to the registers
curve.trace_mul(registers, k, G, O, 32)

# 3) we find a small subgroup of F which can contain the trace
# P-1 = 3 * 2**30
# we can find the generator of this subgroup
g = FieldElement.generator() ** (2**20 * 3)
assert g.is_order(1024)
