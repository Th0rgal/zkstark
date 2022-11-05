%lang starknet
from starkware.cairo.common.math import assert_nn
from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.bool import TRUE, FALSE
from starkware.cairo.common.alloc import alloc

@storage_var
func commitments(id: felt) -> (commitment: felt) {
}

@storage_var
func commitments_amount() -> (res: felt) {
}

@storage_var
func blacklisted_beta(beta: felt) -> (blacklisted: felt) {
}

@storage_var
func deposited() -> (deposited: felt) {
}

@external
func deposit{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(commitment) {
    // deposits 1 token
    let (currently_deposited) = deposited.read();
    deposited.write(currently_deposited + 1);

    let (commited) = commitments_amount.read();
    // writes a commitment to redeem this token
    commitments.write(commited, commitment);
    // increases commitment amount (could be improved with a hint like system but this is a poc)
    commitments_amount.write(commited + 1);

    return ();
}

@external
func withdraw{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(proof, beta) {
    // ensures beta is not blacklisted
    let (is_beta_blacklisted) = blacklisted_beta.read(beta);
    assert is_beta_blacklisted = FALSE;

    // todo: Uses proof to check that caller knows alpha such that
    // hash(alpha, beta) ∈ commitments

    // blacklists beta
    blacklisted_beta.write(beta, TRUE);

    // withdraws 1 token
    let (currently_deposited) = deposited.read();
    deposited.write(currently_deposited - 1);

    return ();
}

@view
func get_commitments_amount{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    amount: felt
) {
    let (amount) = commitments_amount.read();
    return (amount,);
}

@view
func get_commitments{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    arr_len: felt, arr: felt*
) {
    let (arr_len) = commitments_amount.read();
    return rec_get_commitments(arr_len);
}

func rec_get_commitments{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    arr_len
) -> (arr_len: felt, arr: felt*) {
    if (arr_len == 0) {
        let (arr) = alloc();
        return (0, arr);
    }
    let (i: felt, arr: felt*) = rec_get_commitments(arr_len - 1);
    let (value) = commitments.read(i);
    assert arr[i] = value;
    return (arr_len, arr);
}
