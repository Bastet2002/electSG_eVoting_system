#ifndef EVOTING_H
#define EVOTING_H
#include "../rct/rctType.h"

struct Vote
{
    int32_t candidate_id;
    int32_t voter_id;
    bool is_voting;
    bool has_voted;
    string key_image;
    string test_output; // TODO temporary for testing
};

struct Gen_VoterCurr{
    int32_t district_id;
    int32_t voter_num;
    string test_output; // TODO temporary for testing
};

struct Gen_Candidate{
    int32_t candidate_id;
    string test_output; // TODO temporary for testing
};

struct Compute_Total_Vote{
    vector<int32_t> district_ids;
    string test_output; // TODO temporary for testing
};

#endif

// table draft

// voter
// voter_id | district_id | pkV

// voter secret
// voter_id | pkV | skV | pkS | skS

// candidatate
// candidate_id | district_id | pkV | pkS

// candidate secret
// candidate_id | pkV | skV | pkS | skS

// 