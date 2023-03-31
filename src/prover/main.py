from tools.field import P, FieldElement
from tools.polynomial import X, interpolate_poly, Polynomial
from tools.curve import curve, G, O
from tools.merkle import MerkleTree
from tools.channel import Channel
import random

# G = (72051298 : 2007892845 : 1)
# We need to prove we know a such that a * G is part of a list
# ∃ a, hash(a, b) ∈ list

# we use a seed to keep this example deterministic
random.seed(0)

# 1) we generate a random felt of the curve size, 0 is forbidden
k = random.randrange(1, 149717)

# 2) compute the trace
# we initialize the registers to 0
# [id : 0, bit : 1, add[coeff, x, y, inf] : 2, to_double[x, y, inf] : 6,
# doubled[coeff, x, y, inf] : 9, r1[x, y, z] : 13, r0[x, y, z] : 16 ]

registers = []
# because we have 19 registers
for _ in range(19):
    # because there are 19 steps
    registers.append(32 * [FieldElement(0)])

# we fill registers at t=0
G.write(registers, 0, 13)
O.write(registers, 0, 16)

# and we add our montgmery computation to the registers,
# 18 should be enough but we put 31 to fill the arrays
curve.trace_mul(registers, k, G, O, 31)

# 3) we find a small subgroup of F which can contain the trace
# P-1 = 3 * 2**30
# we can find the generator of this subgroup
g = FieldElement.generator() ** (2**25 * 3)
assert g.is_order(32)
# we can then find the elements of this subgroup
subgroup = [g**i for i in range(32)]

# 4) we interpolate the traces to find the polynomials
interpolated = []
for i, trace in enumerate(registers):
    f = interpolate_poly(subgroup, trace)
    interpolated.append(f)

# 5) we extend the trace polynomial by evaluating it over a larger domain

# 5) A - we find a 8 = 2^3 times bigger subgroup of F which can contain the trace

h = FieldElement.generator() ** (2**22 * 3)
assert h.is_order(8 * 32)
H = [h**i for i in range(256)]
# 5) B - we find a coset from this subgroup by multiplying by the F generator
eval_domain = [g * x for x in H]

# 5) C - we evaluate the trace polynomials

evaluated = []
merkled = []
# We create a channel
channel = Channel()
for f in interpolated:
    evaluation = [f(d) for d in eval_domain]
    evaluated.append(evaluation)
    merkle = MerkleTree(evaluation)
    merkled.append(merkle)
    channel.send(merkle.root)

resultat = (registers[16][31], registers[17][31], registers[18][31])


def load_constraints(interpolated):
    constraints = []

    all_roots = X**32 - 1

    # id register
    id_f = interpolated[0]
    all_roots_but_last = all_roots / (X - subgroup[-1])
    constraints.append(
        (id_f(X * g) - id_f(X) - FieldElement.one()) / all_roots_but_last
    )

    # bit = 0 | 1
    id_bit = interpolated[1]
    constraints.append(
        ((id_bit(X) - FieldElement.one()) * (id_bit(X) - FieldElement.zero()))
        / all_roots
    )

    # elliptic curve add, p = R1, q = R0
    # 1) (λ * (q.x - p.x) - q.y + p.y)*(1-z) = 0
    # 2) x = λ^2 - p.x - q.x
    # 3) y = λ * (p.x - x) - p.y
    # 4) z = p.z * q.z

    lambda_f = interpolated[2]
    x = interpolated[3]
    y = interpolated[4]
    z = interpolated[5]
    p_x = interpolated[13]
    p_y = interpolated[14]
    p_z = interpolated[15]
    q_x = interpolated[16]
    q_y = interpolated[17]
    q_z = interpolated[18]

    # 1)
    constraints.append((lambda_f(X * g) * (q_x - p_x) - q_y + p_y) / all_roots_but_last)

    # edge constraints:


load_constraints(interpolated)
