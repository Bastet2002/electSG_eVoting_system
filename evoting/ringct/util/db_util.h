#ifndef DB_UTIL_H
#define DB_UTIL_H

#include "../rct/rctType.h"
#include <pqxx/pqxx>

// TODO change to separate db later
const string cnt_django = "postgresql://admin:password@db:5432/mydb";
const string cnt_rct = "postgresql://admin:password@db:5432/mydb";

User get_voter(int32_t voter_id);
User get_candidate(int32_t candidate_id);
void write_candidate(const int32_t candidate_id, const User& candidate);
void write_voter(const int32_t district_id, const User& voter);
void write_votercurrency(const int32_t district_id, const StealthAddress &sa, const Commitment &commitment);
#endif