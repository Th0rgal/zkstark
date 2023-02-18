from tools.field import P, FieldElement
from tools.pedersen import trace_pedersen_hash, P0, P1, P2, P3, P4
from tools.polynomial import X, interpolate_poly, Polynomial
from tools.merkle import MerkleTree
from tools.channel import Channel
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
# it needs to be a power of two for the FRI operator we are going to use later
# P-1 = 2^192 * 5 * 7 * 98714381 * 166848103
# so 16384 = 2^14 | P-1
# we can find the generator of this subgroup
g = FieldElement.generator() ** (2 ** (192 - 14) * 5 * 7 * 98714381 * 166848103)
assert g.is_order(16384)

# we can then find the elements of this subgroup
G = [g**i for i in range(16384)]

# 4) we interpolate the trace to find the polynomial

# f = interpolate_poly(G[: len(trace)], trace)
precomputed = open("trace.precomputed.json", "r")
f = Polynomial([FieldElement(felt) for felt in json.load(precomputed)])
precomputed.close()

# 5) we extend the trace polynomial by evaluating it over a larger domain

# 5) A - we find a 8 = 2^3 times bigger subgroup of F which can contain the trace
w = FieldElement.generator()
h = w ** (2 ** (192 - 17) * 5 * 7 * 98714381 * 166848103)
assert h.is_order(8 * 16384)
H = [h**i for i in range(131072)]
# 5) B - we find a coset from this subgroup by multiplying by the F generator
eval_domain = [w * x for x in H]

# 5) C - we evaluate the trace polynomial

# f_eval = [f(d) for d in eval_domain]
precomputed = open("evaluation.precomputed.json", "r")
# json.dump([felt.val for felt in f_eval], precomputed)
f_eval = [FieldElement(felt) for felt in json.load(precomputed)]
precomputed.close()

# 6) Commitment
channel = Channel()
# tree1 = MerkleTree(f_eval)
# commitment_1 = tree1.root.as_felt()
commitment_1 = FieldElement(
    1595787962022531245624847181090830808081998341433042357041337723410218745237
)
channel.send("root of evaluation on coset", commitment_1)

# 7) Creating the constraints

# 7) A - CONSTANTS (P0 - P4)


def load_constraints():
    constraints = []
    # [P1] f(x) = P1.x for x = G[3]
    constraints.append((f - P1.x) / (X - G[3]))
    constraints.append((f - P1.y) / (X - G[4]))
    constraints.append((f - P1.infinity) / (X - G[5]))

    # [P2]
    constraints.append((f - P2.x) / (X - G[4477]))
    constraints.append((f - P2.y) / (X - G[4478]))
    constraints.append((f - P2.infinity) / (X - G[4479]))

    # [P3]
    constraints.append((f - P3.x) / (X - G[4559]))
    constraints.append((f - P3.y) / (X - G[4560]))
    constraints.append((f - P3.infinity) / (X - G[4561]))

    # [P4]
    constraints.append((f - P4.x) / (X - G[9033]))
    constraints.append((f - P4.y) / (X - G[9034]))
    constraints.append((f - P4.infinity) / (X - G[9035]))

    # [P5]
    constraints.append((f - P0.x) / (X - G[9126]))
    constraints.append((f - P0.y) / (X - G[9127]))
    constraints.append((f - P0.infinity) / (X - G[9128]))

    # 7) B - lows and highs

    # a) a_low + a_high * 2**128 - a = 0
    # a_id = 0
    # a_low_id = a_id + 2
    # => a_low = f(a_id * g**2)
    # a_high_id = a_id + 4476
    # => a_high = f(a_id * g**4476)
    constraints.append(
        (f(X * g**2) + FieldElement(2**248) * f(X * g**4476) - f) / (X - G[0])
    )

    # for B
    constraints.append(
        (f(X * g**4557) + FieldElement(2**248) * f(X * g**9031) - f) / (X - G[1])
    )

    # todo: make sure a_low and a_high are in the right range

    return constraints


# constraints = load_constraints()
# cp: Polynomial = FieldElement(channel.get_random_felt()) * constraints[0]
# for i in range(1, len(constraints)):
#     cp += FieldElement(channel.get_random_felt()) * constraints[i]

precomputed = open("cp.precomputed.json", "r")
# json.dump([felt.val for felt in cp.poly], precomputed)
cp = Polynomial([FieldElement(felt) for felt in json.load(precomputed)])
precomputed.close()

# cp_eval = [cp(d) for d in eval_domain]
# json.dump([felt.val for felt in cp_eval], precomputed)

precomputed = open("cp_evaluation.precomputed.json", "r")
cp_eval = [FieldElement(felt) for felt in json.load(precomputed)]
precomputed.close()


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


def fri_commit(cp, domain, cp_eval, cp_merkle, channel):
    fri_polys = [cp]
    fri_domains = [domain]
    fri_layers = [cp_eval]
    fri_merkles = [cp_merkle]
    fri_betas = []
    while fri_polys[-1].degree() > 0:
        beta = channel.get_random_felt()
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
    channel.send("fri output constant", fri_polys[-1].poly[0])
    return fri_polys, fri_domains, fri_layers, fri_merkles, fri_betas


import time

# tree2 = MerkleTree(cp_eval)
# commitment_2 = tree2.root.as_felt()  # took a few hours
tree2 = None
commitment_2 = FieldElement(
    -1689479757597063810966045831641560301883693609217504222648469013377678398461
)
channel.send("cp evaluation on lde", commitment_2)

start = time.time()
fri_polys, fri_domains, fri_layers, fri_merkles, fri_betas = fri_commit(
    cp, eval_domain, cp_eval, tree2, channel
)
# took 8906.681478977203 secs
print("took", time.time() - start)

# Now let's generate the proof
# We will do only one query as an example

# Reveal a random value of CP and its sibling (for x, reveal -x whose id = id + k/2 mod k)


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

    # # Verification code:
    # x = domain[domain_id]
    # next_query = fri_layers[layer_id + 1][next_domain_id]
    # beta = fri_betas[layer_id]
    # # Verifier should check test = next_query
    # test = (fx + fsib_x) / FieldElement(2) + beta * (fx - fsib_x) / (
    #     FieldElement(2) * x
    # )
    # assert test == next_query

    return fri_check(layer_id + 1, next_domain_id, fri_domains, fri_layers, fri_merkles)


length = len(eval_domain)
random_id = channel.get_random_felt().val % length
fri_check(0, random_id, fri_domains, fri_layers, fri_merkles)


# Find x**2 in next layer
fri_layers[1]
