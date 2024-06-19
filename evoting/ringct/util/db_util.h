#ifndef DB_UTIL_H
#define DB_UTIL_H

#include "../rct/rctType.h"
#include <pqxx/pqxx>

// TODO change to separate db later
const string cnt_django = "postgresql://admin:password@djangodb:5432/mydb";
const string cnt_rct = "postgresql://admin:password@ringct-db:5432/ringct";

User get_voter(int32_t voter_id);
User get_candidate(int32_t& district_id, const int32_t candidate_id);
void write_candidate(const int32_t candidate_id, const User& candidate);
void write_voter(const int32_t district_id, const User& voter);
void write_votercurrency(const int32_t district_id, const StealthAddress &sa, const Commitment &commitment);
void scan_for_stealthaddress(StealthAddress& sa, const int32_t district_id, const User & signer);
bool verify_double_voting(const int32_t district_id, const BYTE* key_image);
void write_voterecord(const int32_t district_id, const blsagSig &blsagSig, const StealthAddress &sa, const Commitment &commitment);

#endif