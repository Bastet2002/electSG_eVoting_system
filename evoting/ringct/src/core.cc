#include "core.h"
#include "../util/custom_exception.h"
#include "fmt/format.h"

// All error related to core logic should be handled by CustomException
// The error core prefix is "1"
/*
101 CORE_DOUBLE_VOTING
201 NO_CANIDATE_IN_DISTRICT

maybe all sql error in 5xx
*/

// CA generate all the voters keys, currency and store in db without signature and decoys
// Would need to separate with district
// if would like to increase the anonymity in the future, can generate more keys, and put in decoys with signature
void CA_generate_voter_keys_currency(Gen_VoterCurr &gen_user_curr)
{
    int count = 0;
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
        try
        {
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

        cout << "I have generated voter " << i + 1 << " for district " << gen_user_curr.district_id << " stealthAddress and commitment and stored in db" << endl;
        count += 1;
    }
    // TODO: remove test output
    gen_user_curr.test_output = "I have looped for " + to_string(count) + " times";
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
    StealthAddress receivedSA;
    StealthAddress candidateSA;
    blsagSig blsagSig;
    int32_t district_id;
    Commitment receivedCmt;
    Commitment candidateCmt;

    // get from db
    User signer = get_voter(vote.voter_id);
    User candidate = get_candidate(district_id, vote.candidate_id);

    // the r is set in compute_stealth_address,
    try
    {
        scan_for_stealthaddress(receivedCmt, receivedSA, district_id, signer);
    }
    catch (pqxx::sql_error &e)
    {
        throw runtime_error("SQL error: " + string(e.what()));
    }
    catch (exception &e)
    {
        throw runtime_error(e.what());
    }

    compute_stealth_address(candidateSA, candidate);

    // check the keyimage against the voted table in db
    compute_key_image(blsagSig, receivedSA);

    // for printing the status early
    if (!vote.is_voting)
    {
        vote.has_voted = false;
        if (!verify_double_voting(district_id, blsagSig.key_image))
        {
            vote.has_voted = true;
        }
        return;
    }

    if (!verify_double_voting(district_id, blsagSig.key_image))
    {
        RingCTErrorCode errorCode = RingCTErrorCode::CORE_DOUBLE_VOTING;
        string msg = fmt::format("{} Double voting detected for district {} and voter id {}", enumToString(errorCode), district_id, vote.voter_id);
        cerr << msg << endl;
        throw CustomException(msg, static_cast<int>(errorCode));
    }

    // extract amount, compute commitment, mask, and verify commitment balancing
    compute_commitment_simple(candidateCmt, candidateSA, candidate, receivedCmt, receivedSA, signer);

    // rangeproof
    RangeProof rp;
    rangeproof(rp, candidateCmt, candidateCmt.output_blindingfactor);

    // grab decoys from db
    vector<StealthAddress> decoySA = grab_decoys(district_id, receivedSA); // decoy
    int secret_index = secret_index_gen(decoySA.size());

    // blsag
    compute_message(blsagSig, candidateSA, candidateCmt);

    // The reason is to compare double voting, and move it to earlier step for efficiency
    blsag_simple_gen(blsagSig, blsagSig.m, secret_index, receivedSA, decoySA);
    bool is_verified = blsag_simple_verify(blsagSig, blsagSig.m);
    if (!is_verified)
    {
        throw logic_error("Ring signature Verification fail");
    }

    // need to wipe r, sk in stealth address before store in db
    sodium_memzero(candidateSA.r, 32);
    sodium_memzero(candidateSA.sk, 32);
    sodium_memzero(candidateCmt.output_blindingfactor, 32); // for rangeproof

    // blsag -> c, r, keyimage, membersSA.pk/index in db
    // stealth address -> pk, rG
    // commitment -> output, pseudo output, outputmask, amount mask
    try
    {
        write_voterecord(district_id, rp, blsagSig, candidateSA, candidateCmt);
    }
    catch (const pqxx::sql_error &e)
    {
        throw runtime_error("SQL error: " + string(e.what()));
    }
    catch (const exception &e)
    {
        throw runtime_error(e.what());
    }

    // assign the string keyimage and test_output here
    to_string(vote.key_image, blsagSig.key_image, 32);

    string msg = fmt::format("TEST OUTPUT:: Voter {} has casted vote in district {}", vote.voter_id, district_id);
    cout << msg << endl;
}

void CA_compute_result(Compute_Total_Vote &compute_total_vote)
{
    vector<int32_t> district_ids = get_district_ids();

    // TODO remove
    cout << "I have gotten all the district ids" << endl;
    cout << "The district ids are: ";
    for (const int32_t &district_id : district_ids)
    {
        cout << district_id << " ";
    }
    cout << endl;

    // check against all district matches the one django sent
    // if (compute_total_vote.district_ids != district_ids)
    // {
    //     throw logic_error("District ids do not match");
    // }

    // TODO: might need to do stg with it
    if (district_ids.size() == 0)
        return;

    for (const int32_t &district_id : district_ids)
    {
        vector<int32_t> candidate_ids = get_candidate_ids(district_id);

        // TODO remove
        cout << "I have gotten all the candidate ids for district " << district_id << endl;
        cout << "The candidate ids are: ";

        for (const int32_t &candidate_id : candidate_ids)
        {
            cout << candidate_id << " ";
        }
        cout << endl;

        for (const int32_t &candidate_id : candidate_ids)
        {
            int32_t test_district_id;
            User candidate = get_candidate_s(test_district_id, candidate_id);

            if (test_district_id != district_id)
            {
                cerr << "Candidate " + to_string(candidate_id) + " is not in district " + to_string(district_id) << endl;
            }

            cout << "Counting the total vote of candidate " << candidate_id << " in district " << district_id << endl;
            count_write_vote(district_id, candidate_id, candidate);
        }
        // verify the total vote match with the number of vote record
        // if (!verify_total_vote(district_id)){
        //     throw logic_error("Total vote does not match with the number of vote record in district " + to_string(district_id));
        // }
    }
}

void CA_filter_non_voter(Filter_voter &filter_non_voter)
{
    vector<int32_t> district_ids = get_district_ids();

    if (district_ids.size() == 0)
        return;

    for (const int32_t &district_id : district_ids)
    {
        vector<int32_t> voter_ids = get_voter_ids(district_id);

        for (const int32_t &voter_id : voter_ids)
        {
            cout << "Checking for is_non_voter for voter " << voter_id << " in district " << district_id << endl;
            User voter = get_voter(voter_id);
            StealthAddress voterSA;
            Commitment receivedCmt;
            blsagSig blsagSig;

            try
            {
                scan_for_stealthaddress(receivedCmt, voterSA, district_id, voter);
            }
            catch (pqxx::sql_error &e)
            {
                throw runtime_error("SQL error: " + string(e.what()));
            }
            catch (exception &e)
            {
                throw runtime_error(e.what());
            }

            compute_key_image(blsagSig, voterSA);

            // if the key image is not found in the voted table, then it is a non-voter
            if (verify_double_voting(district_id, blsagSig.key_image))
            {
                cout << "Voter " << voter_id << " is a non voter" << endl;
                filter_non_voter.voter_ids.push_back(voter_id);
            }
        }
    }
}