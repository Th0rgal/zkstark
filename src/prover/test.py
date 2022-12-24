from tools.field import FieldElement
from tools.curve import Curve, CurvePoint, O
from tools.pedersen import pedersen_hash, trace_pedersen_hash

P1 = CurvePoint(
    FieldElement(
        996781205833008774514500082376783249102396023663454813447423147977397232763
    ),
    FieldElement(
        1668503676786377725805489344771023921079126552019160156920634619255970485781
    ),
)

P2 = CurvePoint(
    FieldElement(
        2251563274489750535117886426533222435294046428347329203627021249169616184184
    ),
    FieldElement(
        1798716007562728905295480679789526322175868328062420237419143593021674992973
    ),
)

stark_curve = Curve(
    FieldElement(1),
    FieldElement(
        3141592653589793238462643383279502884197169399375105820974944592307816406665
    ),
)

# DOUBLING


# ADDITION
trace = []
P1.write(trace)
P2.write(trace)
stark_curve.trace_add(trace)
SUM = CurvePoint.from_trace(trace)
assert SUM == stark_curve.add(P1, P2)
assert SUM == CurvePoint(
    FieldElement(
        -840379066985468601426872530654310600905589140482619510985184461406513980119
    ),
    FieldElement(
        1766833773244291378193284881884048571357968568316774999938879144915788008901
    ),
)

# MULTIPLICATION BY NORMAL
trace = []
trace.append(
    FieldElement(562728905295480679789526322175868328062420237419143593021674992973)
)
P1.write(trace)
stark_curve.trace_mul(trace)
MUL = CurvePoint.from_trace(trace)
assert MUL == stark_curve.mul(
    FieldElement(562728905295480679789526322175868328062420237419143593021674992973), P1
)
assert MUL == CurvePoint(
    830622876391243870810758107378185438468588767299207469706082586445063579803,
    196178297664111760854440048084856873001074966363221495014829545319669371394,
)


# MULTIPLICATION BY ZERO
trace.append(FieldElement(0))
P1.write(trace)
stark_curve.trace_mul(trace)
MUL = CurvePoint.from_trace(trace)
assert MUL == stark_curve.mul(FieldElement(0), P1)
assert MUL == O

# MULTIPLICATION BY ONE
trace.append(FieldElement(1))
P1.write(trace)
stark_curve.trace_mul(trace)
MUL = CurvePoint.from_trace(trace)
assert MUL == stark_curve.mul(FieldElement(1), P1)
assert MUL == P1

# PEDERSEN HASH

a = FieldElement(12345)
b = FieldElement(
    1395468594777789475957636303561172780005680120301357285285003256932339552272
)
trace = []
trace.append(a)
trace.append(b)
trace_pedersen_hash(trace)
hashed = CurvePoint.from_trace(trace).x
assert hashed == pedersen_hash(a, b)
assert (
    hashed
    == 1542017980271000938816108123437786423529808864567079555458315006906729086202
)
