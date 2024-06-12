#include "core.h"

// TODO CA generate all the voters keys, currency and store in db without signature and decoys
// Would need to separate with district
// if would like to increase the anonymity in the future, can generate more keys, and put in decoys with signature
void CA_generate_voter_keys_currency(Gen_VoterCurr &gen_user_curr)
{
    for (int i = 0; i < gen_user_curr.voter_num; i++)
    {
        User user;

        try
        {
            write_voter(gen_user_curr.district_id, user);
        }
        catch (const pqxx::sql_error &e)
        {
            throw runtime_error("SQL error: " + string(e.what()));
        }
        catch (const exception &e)
        {
            throw runtime_error(e.what());
        }

        // What to be stored in db?
        // stealth address -> pk, rG
        // commitment -> output, pseudo output, outputmask, amount mask
        StealthAddress userSA;
        compute_stealth_address(userSA, user);

        // Commitment commitment;
        Commitment commitment;
        CA_generate_voting_currency(commitment, userSA, user);

        // store in db
        try {
            write_votercurrency(gen_user_curr.district_id, userSA, commitment);
        }
        catch (const pqxx::sql_error &e)
        {
            throw runtime_error("SQL error: " + string(e.what()));
        }
        catch (const exception &e)
        {
            throw runtime_error(e.what());
        }

        cout << "I have generated voter "<< i << " for district " << gen_user_curr.district_id << " stealthAddress and commitment and stored in db" << endl;
    }
    // TODO: remove test output
    gen_user_curr.test_output = "I have looped for " + to_string(gen_user_curr.voter_num) + " times";
    // TODO mix the order of the voters/stealth address in the db
}

// Candidate is generated one by one, as what django does
// The createCandidate in django would make request to generate the candidate keys
void CA_generate_candidate_keys(Gen_Candidate &gen_candidate)
{
    User candidate;

    try
    {
        write_candidate(gen_candidate.candidate_id, candidate);
    }
    catch (const pqxx::sql_error &e)
    {
        throw runtime_error("SQL error: " + string(e.what()));
    }
    catch (const exception &e)
    {
        throw runtime_error(e.what());
    }

    // TODO remove test output
    gen_candidate.test_output = "I have generated candidate with id " + to_string(gen_candidate.candidate_id);
    string pkV;
    to_string(pkV, candidate.pkV, 32);
    gen_candidate.test_output += " with pkV " + pkV;

    cout << gen_candidate.test_output << endl;
}

// TODO contains a lot hardcoded values without db interaction
// ignore all the db interaction first, prioritize the core logic of the voting
// focus on building the object that is gonna store in the db
// store the data at the end of the function
void voter_cast_vote(Vote &vote)
{
    StealthAddress signerSA;
    blsagSig blsagSig;

    // TODO change to real db
    User signer = get_voter(vote.voter_id);

    // TODO grab candidate public key from db
    User candidate = get_candidate(vote.candidate_id);

    // TODO scan for stealth address with db
    // the r is set in compute_stealth_address,
    compute_stealth_address(signerSA, signer);
    receiver_test_stealth_address(signerSA, signer);

    // TODO after grab the stealth address from db
    // check the keyimage against the voted table in db
    compute_key_image(blsagSig, signerSA);
    // verify_double_voting(blsagSig.key_image);

    // TODO after having stealth address, decode amount_t from the output

    // TODO compute commitment and masks (amount and yt)
    // commitment balancing

    // TODO grab decoy from db
    vector<User> users_blsag(10);
    vector<StealthAddress> blsagSA; // decoy
    int secret_index = secret_index_gen(users_blsag.size());
    CA_generate_address(blsagSA, users_blsag); // when storing in db, only store the stealthAddress.pk of the decoy and signer

    // blsag
    // TODO change to real message from hash transaction data
    BYTE m[32];
    crypto_core_ed25519_scalar_random(m);

    // TODO need to move the key image out from blsag simple gen.
    // The reason is to compare double voting, and move it to earlier step for efficiency
    blsag_simple_gen(blsagSig, m, secret_index, signerSA, blsagSA);
    bool is_verified = blsag_simple_verify(blsagSig, m);
    if (!is_verified)
    {
        throw logic_error("Ring signature Verification fail");
    }

    // need to wipe r, sk in stealth address before store in db
    sodium_memzero(signerSA.r, 32);
    sodium_memzero(signerSA.sk, 32);

    // TODO store in db, the vote record
    // blsag -> c, r, keyimage, membersSA.pk/index in db
    // stealth address -> pk, rG
    // commitment -> output, pseudo output, outputmask, amount mask

    // assign the string keyimage and test_output here
    to_string(vote.key_image, blsagSig.key_image, 32);
}

void CA_compute_result(Compute_Total_Vote &compute_total_vote)
{
    // get all district_id
    // vector<int> district_ids = get_district_ids();

    // check against all district matches the one django sent
    // if (compute_total_vote.district_ids != district_ids)
    // {
    //     throw logic_error("District ids do not match");
    // }

    // for (const int &district_id :district_ids){
    // vector<int> candidate_ids = get_candidate_ids(district_id);

    //     if (candidate_ids.size() == 0){
    //         throw logic_error("No candidate in district " + to_string(district_id));
    //     }

    //     // automatically win
    //     if (candidate_ids.size() == 1){
    //         continue;
    //     }

    //     for (const int &candidate_id :candidate_ids){
    //         // compute the total vote for each candidate
    //         // store in db
    //         // store_candidate_total_vote(district_id, candidate_id, total_vote);
    //         compute_candidate_total_vote(district_id, candidate_id);
    //     }
    // verify the total vote match with the number of vote record
    // if (!verify_total_vote(district_id)){
    //     throw logic_error("Total vote does not match with the number of vote record in district " + to_string(district_id));
    // }
    // }

    // TODO remove test output
}