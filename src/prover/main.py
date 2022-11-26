from tools.field import P, FieldElement
from tools.pedersen import pedersen_hash
from tools.curve import Curve, CurvePoint, O
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
P1 = CurvePoint(
    FieldElement(
        996781205833008774514500082376783249102396023663454813447423147977397232763
    ),
    FieldElement(
        1668503676786377725805489344771023921079126552019160156920634619255970485781
    ),
)

stark_curve = Curve(
    FieldElement(1),
    FieldElement(
        3141592653589793238462643383279502884197169399375105820974944592307816406665
    ),
)

trace = []
trace.append(
    562728905295480679789526322175868328062420237419143593021674992973
)
P1.write(trace)
stark_curve.trace_mul(trace, 248)

for i, value in enumerate(trace):
    print("[" + str(i) + "]", value)
