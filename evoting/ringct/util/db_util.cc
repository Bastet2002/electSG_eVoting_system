#include "db_util.h"
#include <nlohmann/json.hpp>
#include "fmt/format.h"

using namespace nlohmann;

/*
TODO : to implement it

DB ERROR CODES

301 - Failed to open connection to django db
302 - Failed to open connection to rct db
303 - return empty row
304 - return more than 1 row
*/

// can also get user by pk for function overloading
User get_voter(int32_t voter_id)
{
    pqxx::connection c_django{cnt_django};
    if (!c_django.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_django.dbname()));
    }

    // 1. get the pkV from the voter table in django db
    pqxx::nontransaction txn_d{c_django};
    pqxx::row r = txn_d.exec1("select pkV from voter where voter_id = " + to_string(voter_id) + ";");
    string pkV = r[0].as<string>();

    // 2. get all the keys with pkV in the rinct db
    pqxx::connection c_rct{cnt_rct};
    if(!c_rct.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_rct.dbname()));
    }
    pqxx::nontransaction txn_r{c_rct};
    r = txn_r.exec1("select * from voter_secretkey where pkV = '" + pkV + "';");

    return User(r["pkV"].as<string>(), r["skV"].as<string>(), r["pkS"].as<string>(), r["skS"].as<string>());
}

User get_candidate(int32_t candidate_id)
{
    pqxx::connection c_django{cnt_django};
    if (!c_django.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_django.dbname()));
    }

    // 1. get the pkV from the voter table in django db
    pqxx::nontransaction txn_d{c_django};
    pqxx::row r = txn_d.exec1("select pkV, pkS from candidate_publickey where candidate_id = " + to_string(candidate_id) + ";");

    return User(r["pkV"].as<string>(), r["pkS"].as<string>());
}

void write_voter(const int32_t district_id, const User &voter)
{
    // convert to hexstring
    string pkV, skV, pkS, skS;
    to_string(pkV, voter.pkV, 32);
    to_string(skV, voter.skV, 64);
    to_string(pkS, voter.pkS, 32);
    to_string(skS, voter.skS, 64);

    // write to candidate_secretkey
    pqxx::connection c_r(cnt_rct);
    if (!c_r.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_r.dbname()));
    }
    c_r.prepare("insert voter_secret", "insert into voter_secretkey (pkV, skV, pkS, skS) values ($1, $2, $3, $4);");

    pqxx::work txn_r(c_r);

    txn_r.exec_prepared("insert voter_secret", pkV, skV, pkS, skS);
    txn_r.commit();

    // write to voter_publickey
    pqxx::connection c_d(cnt_django);
    if (!c_d.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_d.dbname()));
    }
    c_d.prepare("insert voter_public", "insert into voter (district_id, pkV) values ($1, $2);");

    pqxx::work txn_d(c_d);
    txn_d.exec_prepared("insert voter_public", district_id, pkV);
    txn_d.commit();
}

void write_votercurrency(const int32_t district_id, const StealthAddress &sa, const Commitment &commitment)
{
    /**
     * json format
     * {
     *  "rG" : "hex",
     *  "commitment" : {
     *     "input_commitment" : "hex",
     *     "output_commitment" : "hex",
     *     "pseudo_output_commitment" : "hex",
     *     amount_mask: "hex"
     *   }
     * }
     */
    string stealth_address;
    to_string(stealth_address, sa.pk, 32);

    string rG, input_commitment, output_commitment, pseudo_output_commitment, amount_mask;
    to_string(rG, sa.rG, 32);
    to_string(input_commitment, commitment.inputs_commitments[0].data(), 32);
    to_string(output_commitment, commitment.outputs_commitments[0].data(), 32);
    to_string(pseudo_output_commitment, commitment.pseudoouts_commitments[0].data(), 32);
    // TODO amount mask not implemented
    // to_string(amount_mask, commitment.amount_masks[0].data(), 32);
    amount_mask = "0";

    string json = fmt::format(R"({{"rg": "{}", "commitment": {{"input_commitment": "{}", "output_commitment": "{}", "pseudo_output_commitment": "{}", "amount_mask": "{}"}}}})",
                              rG, input_commitment, output_commitment, pseudo_output_commitment, amount_mask);
    
    pqxx::connection C(cnt_django);

    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    C.prepare("insert vote_currency", "insert into voting_currency (district_id, stealth_address, commitment_record) values ($1, $2, $3);");
    pqxx::work W(C); 
    W.exec_prepared("insert vote_currency", district_id, stealth_address, json);
    W.commit();
}

void write_candidate(const int32_t candidate_id, const User &candidate)
{
    // convert to hexstring
    string pkV, skV, pkS, skS;
    to_string(pkV, candidate.pkV, 32);
    to_string(skV, candidate.skV, 64);
    to_string(pkS, candidate.pkS, 32);
    to_string(skS, candidate.skS, 64);

    // write to candidate_secretkey
    pqxx::connection c_r(cnt_rct);
    if (!c_r.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_r.dbname()));
    }
    c_r.prepare("insert candidate_secret", "insert into candidate_secretkey (pkV, skV, pkS, skS) values ($1, $2, $3, $4);");

    pqxx::work txn_r(c_r);

    txn_r.exec_prepared("insert candidate_secret", pkV, skV, pkS, skS);
    txn_r.commit();

    cout << "Candidate id:" << candidate_id << " written to candidate_secretkey" << endl;

    // write to candidate_publickey
    pqxx::connection c_d(cnt_django);
    if (!c_d.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_d.dbname()));
    }
    c_d.prepare("insert candidate_public", "insert into candidate_publickey (candidate_id, pkV, pkS) values ($1, $2, $3);");

    pqxx::work txn_d(c_d);
    txn_d.exec_prepared("insert candidate_public", candidate_id, pkV, pkS);
    txn_d.commit();

    cout << "Candidate id:" << candidate_id << " written to candidate_publickey" << endl;
}

void scan_for_stealthaddress(StealthAddress& sa, const int32_t district_id, const User & signer){

    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    pqxx::result r = W.exec("select stealth_address, commitment_record from voting_currency where district_id = " + to_string(district_id) + ";");

    // TODO : what if the record is too much 
    for (pqxx::result::const_iterator c = r.begin(); c != r.end(); ++c)
    {
        string stealth_address = c["stealth_address"].as<string>();
        json commitment_record = json::parse(c["commitment_record"].as<string>());
        string rG = commitment_record["rG"];

        StealthAddress sa_temp(stealth_address, rG);
        if (receiver_test_stealth_address(sa_temp, signer))
        {
            sa = sa_temp;
            return;
        }
    }

    throw runtime_error("Stealth address not found in scan_for_stealthaddress");
}

bool verify_double_voting(const int32_t district_id, const BYTE* key_image)
{
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);
    string key_image_str;

    to_string(key_image_str, key_image, 32);
    pqxx::row r = W.exec1("select sum(*) from vote_records where district_id=" + string(district_id) + " and key_image='" + key_image_str + "';");
    return !(r[0].as<int>() > 0);
}

void write_voterecord (const int32_t district_id, const blsagSig &blsagSig, const StealthAddress &sa, const Commitment &commitment)
{
    /*
    keyimage
    {
    "rg": "hex",
    "stealth_address": "hex",
    "commitment": {
        "input_commitment": "hex",
        "output_commitment": "hex",
        "pseudo_output_commitment": "hex",
        "amount_mask": "hex"
    },
    "blsagSig": {
        "c": "hex",
        "m": "hex",
        "r": ["hex"],
        "members": ["stealthaddress"]
    }
    }
    */


}

void grab_decoys(){

}

void verify_vote_record(){

}