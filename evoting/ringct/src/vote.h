#ifndef VOTE_H
#define VOTE_H
#include "../rct/rctType.h"

struct Vote
{
    int32_t district_id;
    int32_t candidate_id;
    int32_t voter_id;
};

#endif