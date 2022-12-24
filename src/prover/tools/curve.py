# My naive implementation of Elliptic curves over a finite field
# source: https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication#Point_addition

from tools.field import FieldElement


class CurvePoint:
    def __init__(self, x: FieldElement, y: FieldElement, infinity: bool = 0) -> None:
        self.x = x
        self.y = y
        self.infinity = infinity

    def from_trace(trace, start_index=None):
        if start_index is None:
            start_index = len(trace) - 3
        return CurvePoint(
            trace[start_index], trace[start_index + 1], trace[start_index + 2]
        )

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

    ############################
    # Normal computing
    ############################

    def negate(self, p: CurvePoint):
        return CurvePoint(p.x, -p.y, p.infinity)

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

    def double(self, p):
        if p == O:
            return O
        coef = (3 * (p.x**2) + self.alpha) / (2 * p.y)
        x = coef**2 - p.x - p.x
        y = coef * (p.x - x) - p.y
        return CurvePoint(x, y)

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

    ############################
    # Computing with trace
    ############################

    def trace_add(self, trace, p_i=None, q_i=None):
        ap = len(trace)
        p = CurvePoint.from_trace(trace, ap - 6 if p_i is None else p_i)
        q = CurvePoint.from_trace(trace, ap - 3 if q_i is None else q_i)
        assert p != q
        coef = (q.y - p.y) / (q.x - p.x)
        if p == O:
            q.write(trace)
        elif q == O:
            p.write(trace)
        else:
            x = coef**2 - p.x - q.x
            y = coef * (p.x - x) - p.y
            CurvePoint(x, y).write(trace)

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
    def trace_mul(self, trace, k_i=None, p_i=None, max_bit_size=252):

        k = trace[k_i if k_i else -4]
        R1 = CurvePoint.from_trace(trace, p_i)
        R0 = O

        bits = []
        while k != 0:
            bits.append(k % 2)
            k //= 2
        while len(bits) < max_bit_size:
            bits.append(0)

        R1.write(trace)
        R0.write(trace)

        for bit in reversed(bits):

            self.trace_add(trace)
            added = CurvePoint.from_trace(trace)
            trace.append(bit)

            if bit == 0:
                R0.write(trace)
                self.trace_double(trace)
                doubled = CurvePoint.from_trace(trace)
                R1 = added
                R0 = doubled
            else:
                R1.write(trace)
                self.trace_double(trace)
                doubled = CurvePoint.from_trace(trace)
                R1 = doubled
                R0 = added

            R1.write(trace)
            R0.write(trace)

        return trace
