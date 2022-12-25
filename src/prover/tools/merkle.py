from tools.pedersen import pedersen_hash
from tools.field import FieldElement
from math import log2, ceil


class MerkleNode(object):
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right
        self.val = None

    def as_felt(self):
        return self.val if self.val else pedersen_hash(self.left, self.right)


class MerkleTree(object):
    """
    A simple and naive implementation of an immutable Merkle tree with pedersen hash.
    """

    def __init__(self, felt_arr):
        assert isinstance(felt_arr, list)
        assert len(felt_arr) > 0, "Cannot construct an empty Merkle Tree."
        num_leaves = 2 ** ceil(log2(len(felt_arr)))
        self.data = felt_arr + [FieldElement(-1)] * (num_leaves - len(felt_arr))
        self.height = int(log2(num_leaves))
        self.parents = {}
        self.root = self.build_tree()
        

    def get_merkle_proof(self, felt):
        proof = []
        while felt in self.parents:
            parent_node = self.parents[felt]
            if parent_node.left == felt:
                proof.append((False, parent_node.right))
            else:
                proof.append((True, parent_node.left))
            felt = parent_node.as_felt()
        return proof

    def build_tree(self):
        stage = []
        for i in range(len(self.data) // 2):
            a = self.data[2 * i]
            b = self.data[2 * i + 1]
            node = MerkleNode(a, b)
            self.parents[a] = node
            self.parents[b] = node
            stage.append(node)

        while len(stage) > 1:
            stage = self.parent_stage(stage)

        return stage[0]

    def parent_stage(self, stage):
        new_stage = []
        for node_id in range(len(stage) // 2):
            a = stage[2 * node_id].as_felt()
            b = stage[2 * node_id + 1].as_felt()
            node = MerkleNode(a, b)
            self.parents[a] = node
            self.parents[b] = node
            new_stage.append(node)
        return new_stage


def verify_proof(root_felt, felt, proof):

    for is_left, value in proof:
        if is_left:
            felt = pedersen_hash(value, felt)
        else:
            felt = pedersen_hash(felt, value)

    return felt == root_felt
