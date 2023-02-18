from tools.field import FieldElement
from tools.pedersen import pedersen_hash

class Channel:

    def __init__(self) -> None:
        self.state = FieldElement(1)
        self.commitments = []

    def send(self, note: str, felt : FieldElement):
        self.commitments.append((note, felt))
        self.state = pedersen_hash(self.state, felt)

    def get_random_felt(self):
        self.state = pedersen_hash(self.state, FieldElement(1))
        return self.state