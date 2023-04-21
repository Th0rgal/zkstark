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
    all_roots_but_first = all_roots / (X - subgroup[0])
    constraints.append(
        (id_f(X * g) - id_f(X) - FieldElement.one()) / all_roots_but_last
    )

    # bit = 0 | 1
    bit = interpolated[1]
    constraints.append(
        ((bit(X) - FieldElement.one()) * (bit(X) - FieldElement.zero())) / all_roots
    )

    # elliptic curve add, p = R1, q = R0
    # 1) (λ * (q.x - p.x) - q.y + p.y)*(1-z) = 0
    # 2) x = λ^2 - p.x - q.x AND infinity case
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

    # 2)
    constraints.append(
        (
            x(X * g)
            - (
                (lambda_f(X * g) * lambda_f(X * g) - p_x - q_x) * (1 - p_z) * (1 - q_z)
                + p_z * q_x
                + q_z * p_x
            )
        )
        / all_roots_but_last
    )

    # 3)
    constraints.append(
        (
            y(X * g)
            - (
                (lambda_f(X * g) * (p_x - x(X * g)) - p_y) * (1 - p_z) * (1 - q_z)
                + p_z * q_y
                + q_z * p_y
            )
        )
        / all_roots_but_last
    )

    # 4)
    constraints.append((z(X * g) - p_z(X) * q_z(X)) / all_roots_but_last)

    # to_double: P if bit = 1, Q if bit = 0
    to_double_x = interpolated[6]
    to_double_y = interpolated[7]
    to_double_z = interpolated[8]
    constraints.append(
        (to_double_x(X * g) - bit(X * g) * p_x - (1 - bit(X * g)) * q_x)
        / all_roots_but_last
    )
    constraints.append(
        (to_double_y(X * g) - bit(X * g) * p_y - (1 - bit(X * g)) * q_y)
        / all_roots_but_last
    )
    constraints.append(
        (to_double_z(X * g) - bit(X * g) * p_z - (1 - bit(X * g)) * q_z)
        / all_roots_but_last
    )

    # elliptic curve double, Q if bit = 0, else P

    # 1) λ * (2 * _Y) - 3 * _X^2 - α = 0
    # 2) x - λ^2 + 2*_X = 0
    # 3) y - λ * (_X - x) + _Y = 0
    # 4) z - _Z = 0

    doubled_lambda = interpolated[9]
    doubled_x = interpolated[10]
    doubled_y = interpolated[11]
    doubled_z = interpolated[12]

    # 1)
    constraints.append(
        (
            doubled_lambda * FieldElement(2) * to_double_y
            - (FieldElement(3) * to_double_x**2 + curve.alpha)
        )
        / all_roots_but_first
    )

    # 2)
    constraints.append(
        (doubled_x - doubled_lambda * doubled_lambda + FieldElement(2) * to_double_x)
        * (1 - to_double_z)
        / all_roots_but_first
    )

    # 3)
    constraints.append(
        (doubled_y - doubled_lambda * (to_double_x - doubled_x) + to_double_y)
        * (1 - to_double_z)
        / all_roots_but_first
    )

    # 4)
    constraints.append(
        (doubled_z - ((FieldElement(1) - bit) * q_z + bit * p_z)) / all_roots_but_first
    )

    # r1
    r1_x = interpolated[13]
    r1_y = interpolated[14]
    r1_z = interpolated[15]
    constraints.append((r1_x - doubled_x * bit - x * (1 - bit)) / all_roots_but_first)
    constraints.append((r1_y - doubled_y * bit - y * (1 - bit)) / all_roots_but_first)
    constraints.append((r1_z - doubled_z * bit - z * (1 - bit)) / all_roots_but_first)

    # r0
    r0_x = interpolated[16]
    r0_y = interpolated[17]
    r0_z = interpolated[18]
    constraints.append((r0_x - doubled_x * (1 - bit) - x * bit) / all_roots_but_first)
    constraints.append((r0_y - doubled_y * (1 - bit) - y * bit) / all_roots_but_first)
    constraints.append((r0_z - doubled_z * (1 - bit) - z * bit) / all_roots_but_first)

    # edge constraints:

    first_root_only = X - g**0

    # G
    constraints.append((r1_x - G.x) / first_root_only)
    constraints.append((r1_y - G.y) / first_root_only)
    constraints.append((r1_z - G.infinity) / first_root_only)

    # O
    constraints.append((r0_x - O.x) / first_root_only)
    constraints.append((r0_y - O.y) / first_root_only)
    constraints.append((r0_z - O.infinity) / first_root_only)

    return constraints


constraints = load_constraints(interpolated)

cp: Polynomial = FieldElement(channel.receive_random_int(0, P - 1)) * constraints[0]
for i in range(1, len(constraints)):
    cp += FieldElement(channel.receive_random_int(0, P - 1)) * constraints[i]

cp_eval = [cp(d) for d in eval_domain]


def next_fri_domain(fri_domain):
    return [x**2 for x in fri_domain[: len(fri_domain) // 2]]


def next_fri_polynomial(poly, beta):
    odd_coefficients = poly.poly[1::2]
    even_coefficients = poly.poly[::2]
    odd = beta * Polynomial(odd_coefficients)
    even = Polynomial(even_coefficients)
    return odd + even


def next_fri_layer(poly, domain, beta):
    next_poly = next_fri_polynomial(poly, beta)
    next_domain = next_fri_domain(domain)
    next_layer = [next_poly(x) for x in next_domain]
    return next_poly, next_domain, next_layer


def fri_commit(cp, domain, cp_eval, cp_merkle, channel: Channel):
    fri_polys = [cp]
    fri_domains = [domain]
    fri_layers = [cp_eval]
    fri_merkles = [cp_merkle]
    fri_betas = []
    while fri_polys[-1].degree() > 0:
        beta = channel.receive_random_int(0, P - 1)
        next_poly, next_domain, next_layer = next_fri_layer(
            fri_polys[-1], fri_domains[-1], beta
        )
        fri_polys.append(next_poly)
        fri_domains.append(next_domain)
        fri_layers.append(next_layer)
        fri_betas.append(beta)
        # fri_merkles.append(MerkleTree(next_layer))
        # channel.send("fri step root", fri_merkles[-1].root)

    # free element of degree 0 poly
    channel.send("fri step root: " + str(fri_polys[-1].poly[0]))
    return fri_polys, fri_domains, fri_layers, fri_merkles, fri_betas


evaluation_tree = MerkleTree(cp_eval)
fri_polys, fri_domains, fri_layers, fri_merkles, fri_betas = fri_commit(
    cp, eval_domain, cp_eval, evaluation_tree, channel
)


def fri_check(layer_id, domain_id, fri_domains, fri_layers, fri_merkles):
    if layer_id == len(fri_layers):
        return
    domain = fri_domains[layer_id]
    length = len(domain)
    print("layer:", layer_id, "length:", length)
    sibling_id = (domain_id + length // 2) % length
    fx = fri_layers[layer_id][domain_id]
    fsib_x = fri_layers[layer_id][sibling_id]
    print("- f(x):", fx, "f(-x):", fsib_x)
    # todo: reveal their merkle proof in channel.commitments[1]

    # f(x^2) from next f
    next_domain_id = sibling_id % (length // 2)

    # Verification code:
    # if layer_id <= 5:
    #     x = domain[domain_id]
    #     next_query = fri_layers[layer_id + 1][next_domain_id]
    #     beta = fri_betas[layer_id]
    #     # Verifier should check test = next_query
    #     test = (fx + fsib_x) / FieldElement(2) + beta * (fx - fsib_x) / (
    #         FieldElement(2) * x
    #     )
    #     assert test == next_query

    return fri_check(layer_id + 1, next_domain_id, fri_domains, fri_layers, fri_merkles)


length = len(eval_domain)
random_id = channel.receive_random_int(0, P - 1) % length
fri_check(0, random_id, fri_domains, fri_layers, fri_merkles)
