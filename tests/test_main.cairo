%lang starknet
from src.verifier.main import deposit, get_commitments, get_commitments_amount
from starkware.cairo.common.cairo_builtins import HashBuiltin

@external
func test_commiting{syscall_ptr: felt*, range_check_ptr, pedersen_ptr: HashBuiltin*}() {
    deposit(1);
    deposit(2);
    deposit(3);

    let (commitments_len, commitments) = get_commitments();
    assert commitments_len = 3;
    assert commitments[0] = 1;
    assert commitments[1] = 2;
    assert commitments[2] = 3;

    let (amount) = get_commitments_amount();
    assert amount = commitments_len;

    return ();
}
