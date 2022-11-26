# My naive implementation of Elliptic curves over a finite field
# source: https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication#Point_addition

from tools.field import FieldElement


class CurvePoint:
    def __init__(self, x: FieldElement, y: FieldElement, infinity: bool = 0) -> None:
        self.x = x
        self.y = y
        self.infinity = infinity

    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y

    def __str__(self):
        return "O" if self.infinity else "(" + repr(self.x) + ", " + repr(self.y) + ")"

    def write(self, trace):
        trace.append(self.x)
        trace.append(self.y)
        trace.append(self.infinity)


O = CurvePoint(0, 1, 1)


class Curve:
    def __init__(self, alpha, beta) -> None:
        self.alpha = alpha
        self.beta = beta

    def negate(self, p: CurvePoint):
        return CurvePoint(p.x, -p.y, p.infinity)

    # idk how to support point at infinity in the trace for now

    def add(self, p: CurvePoint, q: CurvePoint):
        assert p != q
        if p == O:
            return q
        if q == O:
            return p
        coef = (q.y - p.y) / (q.x - p.x)
        x = coef**2 - p.x - q.x
        y = coef * (p.x - x) - p.y
        return CurvePoint(x, y)

    # [input trace:]
    # p.x
    # p.y
    # p.infinity
    # q.x
    # q.y
    # q.infinity
    # [appended trace:]
    # coef -> coef * (trace[ap - 3] - trace[ap - 6]) - (trace[ap - 2] - trace[ap - 5]) = 0
    # x -> x - ( (coef**2 - trace[ap - 7] - trace[ap - 4]) * (1-p.infinity) * (1-q.infinity) + p.infinity*q.x + q.infinity*p.x ) = 0
    # y -> similar idea
    def trace_add(self, trace):
        ap = len(trace)
        trace.append((trace[ap - 2] - trace[ap - 5]) / (trace[ap - 3] - trace[ap - 6]))
        ap += 1
        coef = trace[ap - 1]
        # if p = O, q.x, if q = O, return p.x
        trace.append(
            (coef**2 - trace[ap - 7] - trace[ap - 4])
            * (1 - trace[ap - 5])
            * (1 - trace[ap - 2])
            + (trace[ap - 5] * trace[ap - 4])
            + (trace[ap - 2] * trace[ap - 7])
        )
        ap += 1
        x = trace[ap - 1]
        # if p = O, q.x, if q = O, return p.x
        trace.append(
            (coef * (trace[ap - 8] - x) - trace[ap - 7])
            * (1 - trace[ap - 6])
            * (1 - trace[ap - 3])
            + (trace[ap - 6] * trace[ap - 4])
            + (trace[ap - 3] * trace[ap - 7])
        )
        # infinity of p + q = inf(p) and inf(q)
        trace.append((trace[ap - 6]) * (trace[ap - 3]))

    def double(self, p):
        if p == O:
            return O
        coef = (3 * (p.x**2) + self.alpha) / (2 * p.y)
        x = coef**2 - p.x - p.x
        y = coef * (p.x - x) - p.y
        return CurvePoint(x, y)

    def trace_double(self, trace: list):
        ap = len(trace)
        p = CurvePoint(trace[ap - 3], trace[ap - 2], trace[ap - 1])

        coef = (3 * (p.x**2) + self.alpha) / (2 * p.y)
        trace.append(coef)

        if p.infinity:
            O.write(trace)
        else:
            x = coef**2 - p.x - p.x
            y = coef * (p.x - x) - p.y
            trace.append(x)
            trace.append(y)
            trace.append(0)

    # multiplication implemented with montgomery ladder
    def mul(self, k: int, p: CurvePoint):
        R0 = O
        R1 = p
        bits = []
        while k != 0:
            bits.append(k % 2)
            k //= 2

        for bit in reversed(bits):
            if bit == 0:
                R1 = self.add(R0, R1)
                R0 = self.double(R0)
            else:
                R0 = self.add(R0, R1)
                R1 = self.double(R1)

        return R0

    # multiplication implemented with montgomery ladder
    def trace_mul(self, trace, max_bit_size=252):
        ap = len(trace)

        k = trace[ap - 4]
        R1 = CurvePoint(trace[ap - 3], trace[ap - 2], trace[ap - 1])
        R0 = O
        bits = []

        R1.write(trace)
        ap += 3

        R0.write(trace)
        ap += 3

        while k != 0:
            bits.append(k % 2)
            k //= 2

        while len(bits) < max_bit_size:
            bits.append(0)

        for bit in reversed(bits):

            self.trace_add(trace)
            ap += 4
            added = CurvePoint(trace[ap - 3], trace[ap - 2], trace[ap - 1])

            trace.append(bit)
            ap += 1

            if bit == 0:
                R0.write(trace)
                ap += 3
                self.trace_double(trace)
                ap += 4
                doubled = CurvePoint(trace[ap - 3], trace[ap - 2], trace[ap - 1])
                R1 = added
                R0 = doubled
            else:
                R1.write(trace)
                ap += 3
                self.trace_double(trace)
                ap += 4
                doubled = CurvePoint(trace[ap - 3], trace[ap - 2], trace[ap - 1])
                R1 = doubled
                R0 = added

            R1.write(trace)
            ap += 3

            R0.write(trace)
            ap += 3

        return trace
