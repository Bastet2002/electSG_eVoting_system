#include "../src/core.h"
#include "../util/db_util.h"
#include "../util/custom_exception.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

void init_test(){
    // Prepare the data for the integration test 
    pqxx::connection conn{cnt_django};
    if (!conn.is_open())
    {
        cout << "Can't open database" << endl;
        return;
    }
    pqxx::work txn{conn};
    // A district with id 1
    txn.exec("INSERT INTO myapp_district (district_id, district_name, num_of_people) VALUES (1, 'district1', 20)");
    // A party with id 1
    txn.exec("INSERT INTO myapp_party (party_id, party_name, description) VALUES (1, 'PAP', 'PAP')");
    // A candidate profile with id 1
    txn.exec("INSERT INTO myapp_profile (profile_id, profile_name, description) VALUES (1, 'candidate', 'desc')");
    // A candidate with id 1 in district 1
    txn.exec("INSERT INTO public.myapp_useraccount (user_id, last_login,username, password, full_name, date_of_birth, district_id,party_id,role_id,first_login) VALUES(1, '2024-08-13 10:30:00+00','johndoe123','hashed_password_here','John Doe','1985-05-15',1,1,1,true) ");
    // A candidate with id 2 in district 1
    txn.exec("INSERT INTO public.myapp_useraccount (user_id, last_login,username, password, full_name, date_of_birth, district_id,party_id,role_id,first_login) VALUES(2, '2024-08-13 10:30:00+00','kenny123','hashed_password_here','Kenny','1985-05-15',1,1,1,true) ");
    // A voter with id 1 in district 1
    txn.commit();

    Gen_VoterCurr gen_voter_curr;
    gen_voter_curr.district_id = 1;
    gen_voter_curr.voter_num = 20;

    Gen_Candidate gen_candidate;
    gen_candidate.candidate_id = 1;

    Gen_Candidate gen_candidate2;
    gen_candidate2.candidate_id = 2;

    CA_generate_voter_keys_currency(gen_voter_curr);
    CA_generate_candidate_keys(gen_candidate);
    CA_generate_candidate_keys(gen_candidate2);

    pqxx::connection conn2{cnt_django};
    if (!conn2.is_open())
    {
        cout << "Can't open database" << endl;
        return;
    }
    pqxx::work txn2{conn2};
    txn2.exec("UPDATE myapp_voter set hash_from_info='integration_test_v1' where voter_id = 1");
    txn2.exec("UPDATE myapp_voter set hash_from_info='integration_test_v2' where voter_id = 2");
    txn2.exec("UPDATE myapp_voter set hash_from_info='integration_test_v3' where voter_id = 3");
    txn2.exec("UPDATE myapp_voter set hash_from_info='integration_test_v4' where voter_id = 4");
    txn2.commit();
}

void clean_test(){
    pqxx::connection conn{cnt_django};
    if (!conn.is_open())
    {
        cout << "Can't open database" << endl;
        return;
    }
    pqxx::work txn{conn};
    txn.exec("TRUNCATE TABLE myapp_voterecords, myapp_voteresults, candidate_secretkey, myapp_candidatepublickey, myapp_votingcurrency, voter_secretkey, myapp_useraccount, myapp_party, myapp_profile, myapp_voter, myapp_district RESTART IDENTITY CASCADE");
    txn.commit();
}

SCENARIO("Voter Login into the voter home", "[integration test]")
{
    GIVEN("Voter 1 has not voted before")
    {
        init_test();
        // voter 1 visit the voter home
        Vote vote_voterhome;
        vote_voterhome.voter_id = 1;
        vote_voterhome.candidate_id = 1;
        vote_voterhome.is_voting = false;
        THEN("Voter 1 status has_voted should be false") {
            voter_cast_vote(vote_voterhome);
            REQUIRE(vote_voterhome.has_voted == false);
        }
        clean_test();
    }

    GIVEN("Voter 2 has voted")
    {
        // Voter 2 cast his/her vote
        init_test();
        Vote vote;
        vote.voter_id = 2;
        vote.candidate_id = 1;
        vote.is_voting = true;
        voter_cast_vote(vote);
        cout << "Voter 2 visit the voter home" << endl;

        // Voter 2 visit the voter home
        Vote vote_voterhome;
        vote_voterhome.voter_id = 2;
        vote_voterhome.candidate_id = 1;
        vote_voterhome.is_voting = false;
        THEN("Voter 1 status has_voted should be false") {
            voter_cast_vote(vote_voterhome);
            REQUIRE(vote_voterhome.has_voted == true);
        }
        clean_test();
    }
}

SCENARIO("Voter in the ballot paper and cast his/her vote", "[integration test]")
{

    GIVEN("Voter 1 has not voted before, and cast his/her vote")
    {
        init_test();
        // voter 1 visit the voter home
        Vote vote_voterhome;
        vote_voterhome.voter_id = 1;
        vote_voterhome.candidate_id = 1;
        vote_voterhome.is_voting = true;
        THEN("There should no exception thrown as voter 1 is not double voting") {
           REQUIRE_NOTHROW(voter_cast_vote(vote_voterhome));
        }
        clean_test();
    }

    GIVEN("Voter 2 has voted, and would like to double vote")
    {
        init_test();
        Vote vote;
        vote.voter_id = 2;
        vote.candidate_id = 1;
        vote.is_voting = true;
        voter_cast_vote(vote);

        // Voter 2 visit the voter home
        Vote vote_voterhome;
        vote_voterhome.voter_id = 2;
        vote_voterhome.candidate_id = 1;
        vote_voterhome.is_voting = true;
        THEN("There should be an double voting exception thrown") {
            REQUIRE_THROWS(voter_cast_vote(vote_voterhome));
        }
        clean_test();
    }
}

SCENARIO("Filter out non-voter", "[integration test]")
{
    GIVEN("2 out of 4 voters have voted in district 1")
    {
        init_test();

        Vote vote1;
        vote1.voter_id = 1;
        vote1.candidate_id = 1;
        vote1.is_voting = true;
        voter_cast_vote(vote1);

        Vote vote2;
        vote2.voter_id = 2;
        vote2.candidate_id = 1;
        vote2.is_voting = true;
        voter_cast_vote(vote2);

        Filter_voter filter_voter;
        filter_voter.district_ids.push_back(1);

        THEN("There should be no exception thrown") {
            CA_filter_non_voter(filter_voter);
            cout << "Filter non-voter in district 1" << endl;
            for (const int32_t &voter_id : filter_voter.voter_ids)
            {
                cout << "Voter " << voter_id << " is a non voter" << endl;
            }
            // check if voter 3 and 4 are in the non-voter list
            REQUIRE(filter_voter.voter_ids.size() == 2);
            REQUIRE(find(filter_voter.voter_ids.begin(), filter_voter.voter_ids.end(), 3) != filter_voter.voter_ids.end());
            REQUIRE(find(filter_voter.voter_ids.begin(), filter_voter.voter_ids.end(), 4) != filter_voter.voter_ids.end());
        }
        clean_test();
    }
}

SCENARIO("End of Election", "[integration test]")
{
    GIVEN("Candidate 1 is given 2 votes and Candidate 2 is given 0 vote")
    {
        init_test();
        Vote vote1;
        vote1.voter_id = 1;
        vote1.candidate_id = 1;
        vote1.is_voting = true;
        voter_cast_vote(vote1);

        Vote vote2;
        vote2.voter_id = 2;
        vote2.candidate_id = 1;
        vote2.is_voting = true;
        voter_cast_vote(vote2);

        Compute_Total_Vote compute_total_vote;
        compute_total_vote.district_ids.push_back(1);
        try{
            CA_compute_result(compute_total_vote);
        } catch (const exception &e) {
            cout << e.what() << endl;
        }

        THEN("The record in the database should be updated") {
            // check if the result is updated in the database
            pqxx::connection conn{cnt_django};
            pqxx::work txn{conn};
            pqxx::row r = txn.exec1("select total_vote from myapp_voteresults where candidate_id=1");
            REQUIRE(r[0].as<int>() == 2);
            pqxx::row r2 = txn.exec1("select total_vote from myapp_voteresults where candidate_id=2");
            REQUIRE(r2[0].as<int>() == 0);
        }
        clean_test();
    }
}