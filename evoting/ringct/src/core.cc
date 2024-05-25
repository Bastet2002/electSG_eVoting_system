#include "core.h"

// TODO contains a lot hardcoded values without db interaction
void voter_cast_vote(const Vote &vote)
{
    // TODO change to real db
    User signer = get_user(vote.voter_id);

    // TODO scan for stealth address with db
    StealthAddress signerSA;
    compute_stealth_address(signerSA, signer);
    receiver_test_stealth_address(signerSA, signer);

    // TODO grab decoy from db
    vector<User> users_blsag(10);
    vector<StealthAddress> blsagSA; // decoy
    int secret_index = secret_index_gen(users_blsag.size());
    CA_generate_address(blsagSA, users_blsag);

    // blsag
    blsagSig blsagSig;
    // TODO change to real message from hash transaction data
    BYTE m[32];
    crypto_core_ed25519_scalar_random(m);

    blsag_simple_gen(blsagSig, m, secret_index, signerSA, blsagSA);
    bool is_verified = blsag_simple_verify(blsagSig, m);
    if (!is_verified)
    {
        cout << "Verification fail" << endl;
    }
}