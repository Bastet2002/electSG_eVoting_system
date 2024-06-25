#ifndef CORE_H
#define CORE_H

#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "../util/db_util.h"
#include "evoting.h"

void CA_generate_voter_keys_currency(Gen_VoterCurr &gen_user_curr);
void voter_cast_vote(Vote &vote);
void CA_generate_candidate_keys(Gen_Candidate &gen_candidate);
#endif