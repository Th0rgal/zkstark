# My naive implementation of Elliptic curves over a finite field
# source: https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication#Point_addition

from tools.field import FieldElement


class CurvePoint:
    def __init__(self, x: FieldElement, y: FieldElement) -> None:
        self.x = x
        self.y = y

    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y

    def __str__(self):
        return "(" + repr(self.x) + ", " + repr(self.y) + ")"


class Curve:
    def __init__(self, alpha, beta) -> None:
        self.alpha = alpha
        self.beta = beta

    def negate(self, p: CurvePoint):
        if not p:
            return p
        return CurvePoint(p.x, -p.y)

    def add(self, p: CurvePoint, q: CurvePoint):
        if not p:
            return q
        if not q:
            return p
        if p == q:
            coef = (3 * (p.x**2) + self.alpha) / (2 * p.y)
        else:
            coef = (q.y - p.y) / (q.x - p.x)
        x = coef**2 - p.x - q.x
        y = coef * (p.x - x) - p.y
        return CurvePoint(x, y)

    def mul(self, k: int, p: CurvePoint):
        if k == 0:
            return None
        if k == 1:
            return p
        rec_call = self.mul(k // 2, p)
        duped = self.add(rec_call, rec_call)
        return self.add(duped, self.mul(k % 2, p))
