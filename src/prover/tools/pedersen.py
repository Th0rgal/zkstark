# My naive implementation of starkware pedersen hash, described here: https://docs.starkware.co/starkex/pedersen-hash-function.html
from tools.field import FieldElement
from tools.curve import Curve, CurvePoint

P0 = CurvePoint(
    FieldElement(
        2089986280348253421170679821480865132823066470938446095505822317253594081284
    ),
    FieldElement(
        1713931329540660377023406109199410414810705867260802078187082345529207694986
    ),
)
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
P3 = CurvePoint(
    FieldElement(
        2138414695194151160943305727036575959195309218611738193261179310511854807447
    ),
    FieldElement(
        113410276730064486255102093846540133784865286929052426931474106396135072156
    ),
)
P4 = CurvePoint(
    FieldElement(
        2379962749567351885752724891227938183011949129833673362440656643086021394946
    ),
    FieldElement(
        776496453633298175483985398648758586525933812536653089401905292063708816422
    ),
)

stark_curve = Curve(
    FieldElement(1),
    FieldElement(
        3141592653589793238462643383279502884197169399375105820974944592307816406665
    ),
)

LOW_PART_BITS = 248
LOW_PART_MASK = 2**248 - 1


def pedersen_hash(a: FieldElement, b: FieldElement):

    a_high = a.val >> LOW_PART_BITS
    a_low = a.val & LOW_PART_MASK
    a_part = stark_curve.add(stark_curve.mul(a_low, P1), stark_curve.mul(a_high, P2))

    b_high = b.val >> LOW_PART_BITS
    b_low = b.val & LOW_PART_MASK
    b_part = stark_curve.add(stark_curve.mul(b_low, P3), stark_curve.mul(b_high, P4))

    return stark_curve.add(stark_curve.add(P0, a_part), b_part).x

def trace_pedersen_hash(trace : list):
    ap = len(trace)
    
    a_high = trace[ap-2] >> LOW_PART_BITS
    a_low = trace[ap-3] & LOW_PART_MASK
    b_high = trace[ap-3] >> LOW_PART_BITS
    b_low = trace[ap-4] & LOW_PART_MASK

    trace.append(a_low)
    ap+=1
    P1.write(trace)
    ap

    stark_curve.trace_mul()



    stark_curve.mul(a_low, P1)


    trace.append(a_high)
    ap+=1

    trace.append(b_high)
    ap+=1
    trace.append(b_low)
    ap+=1




    trace.append(a_low)
    P1.write(trace)
    stark_curve.trace_mul(trace)

    a_part = stark_curve.add(stark_curve.mul(a_low, P1), stark_curve.mul(a_high, P2))


    b_part = stark_curve.add(stark_curve.mul(b_low, P3), stark_curve.mul(b_high, P4))

    return stark_curve.add(stark_curve.add(P0, a_part), b_part).x
