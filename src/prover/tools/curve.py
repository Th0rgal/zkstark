# My naive implementation of Elliptic curves over a finite field
# source: https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication#Point_addition

from tools.field import FieldElement


class CurvePoint:
    def __init__(
        self, x: FieldElement, y: FieldElement, infinity: FieldElement = FieldElement(0)
    ) -> None:
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
        return (
            "O" if self.infinity.val else "(" + repr(self.x) + ", " + repr(self.y) + ")"
        )

    def write(self, registers, step, first_register_id):
        registers[first_register_id][step] = self.x
        registers[first_register_id + 1][step] = self.y
        registers[first_register_id + 2][step] = self.infinity


O = CurvePoint(FieldElement(0), FieldElement(1), FieldElement(1))


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
    def mul(self, k: FieldElement, p: CurvePoint):
        R0 = O
        R1 = p
        bits = []
        k_val = k.val
        while k_val != 0:
            bits.append(k_val % 2)
            k_val //= 2

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

    def verifiable_add(self, p: CurvePoint, q: CurvePoint):
        assert p != q
        coef = (q.y - p.y) / (q.x - p.x)

        if p == O:
            return coef, q
        elif q == O:
            return coef, p
        else:
            x = coef**2 - p.x - q.x
            y = coef * (p.x - x) - p.y
            return coef, CurvePoint(x, y)

    def verifiable_double(self, p: CurvePoint):

        coef = (FieldElement(3) * (p.x**2) + self.alpha) / (FieldElement(2) * p.y)

        if p.infinity.val:
            return coef, O
        else:
            x = coef**2 - p.x - p.x
            y = coef * (p.x - x) - p.y
            return coef, CurvePoint(x, y)

    # multiplication implemented with montgomery ladder
    def trace_mul(self, registers, k, R1, R0, max_bit_size=16):

        bits = []
        while k != 0:
            bits.append(k % 2)
            k //= 2
        while len(bits) < max_bit_size:
            bits.append(0)

        for i, bit in enumerate(reversed(bits)):

            # we write in the id register
            registers[0][i + 1] = FieldElement(i + 1)
            # in the bit one
            registers[1][i + 1] = FieldElement(bit)

            # in the add ones
            coef, added = self.verifiable_add(R1, R0)
            registers[2][i + 1] = coef
            added.write(registers, i + 1, 3)

            if bit == 0:
                R0.write(registers, i + 1, 6)
                coef, doubled = self.verifiable_double(R0)
                R1 = added
                R0 = doubled
            else:
                R1.write(registers, i + 1, 6)
                coef, doubled = self.verifiable_double(R1)
                R1 = doubled
                R0 = added
            registers[9][i + 1] = coef
            doubled.write(registers, i + 1, 10)

            R1.write(registers, i + 1, 13)
            R0.write(registers, i + 1, 16)


curve = Curve(
    FieldElement(44499),
    FieldElement(24688),
)
G = CurvePoint(FieldElement(72051298), FieldElement(2007892845))
