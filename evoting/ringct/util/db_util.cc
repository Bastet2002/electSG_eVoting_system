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
    cout << "get voter id: " << voter_id << endl;
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
    if (!c_rct.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_rct.dbname()));
    }
    pqxx::nontransaction txn_r{c_rct};
    r = txn_r.exec1("select * from voter_secretkey where pkV = '" + pkV + "';");

    return User(r["pkV"].as<string>(), r["skV"].as<string>(), r["pkS"].as<string>(), r["skS"].as<string>());
}

User get_candidate(int32_t &district_id, const int32_t candidate_id)
{
    cout << "get candidate id: " << candidate_id << endl;
    pqxx::connection c_django{cnt_django};
    if (!c_django.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_django.dbname()));
    }

    // 1. get the pkV from the voter table in django db
    pqxx::nontransaction txn_d{c_django};
    pqxx::row r = txn_d.exec1("select pkV, pkS from candidate_publickey where candidate_id = " + to_string(candidate_id) + ";");
    string pkV = r["pkV"].as<string>();
    string pkS = r["pkS"].as<string>();

    cout << "candidate id " << candidate_id << endl;
    cout << "pkV: " << pkV << endl;

    // 2. get the district id from useraccount table
    r = txn_d.exec1("select district_id from myapp_useraccount where id = '" + to_string(candidate_id) + "';");
    district_id = r["district_id"].as<int>();

    return User(pkV, pkS);
}

void write_voter(const int32_t district_id, const User &voter)
{
    cout << "write voter in " << district_id << endl;
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
    cout << "write vote currency in " << district_id << endl;
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
    amount_mask = "10";

    string json = fmt::format(R"({{"rG": "{}", "commitment": {{"input_commitment": "{}", "output_commitment": "{}", "pseudoout_commitment": "{}", "amount_mask": "{}"}}}})",
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
    cout << "write candidate id:" << candidate_id << endl;
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

void scan_for_stealthaddress(StealthAddress &sa, const int32_t district_id, const User &signer)
{
    cout << "scan for stealth address in district " << district_id << endl;

    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    pqxx::result r = W.exec("select stealth_address, commitment_record->>'rG' as rG from voting_currency where district_id = " + to_string(district_id) + ";");

    // TODO : what if the record is too much
    for (const auto &row : r)
    {
        string stealth_address = row["stealth_address"].as<string>();
        string rG = row[1].as<string>();
        StealthAddress sa_temp(stealth_address, rG);
        if (receiver_test_stealth_address(sa_temp, signer))
        {
            cout << "Stealth address found" << endl;
            sa = sa_temp;
            return; // Stealth address found and valid
        }
    }

    throw runtime_error("Stealth address not found in scan_for_stealthaddress");
}

bool verify_double_voting(const int32_t district_id, const BYTE *key_image)
{
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);
    string key_image_str;
    to_string(key_image_str, key_image, 32);

    cout << "verify double voting in " << district_id << " with key image " << key_image_str << endl;

    pqxx::result r = W.exec("select * from vote_records where district_id=" + to_string(district_id) + " and key_image='" + key_image_str + "';");

    return r.empty();
}

void write_voterecord(const int32_t district_id, const blsagSig &blsagSig, const StealthAddress &sa, const Commitment &commitment)
{
    // TODO right one for one, for the simplicity
    /*
    keyimage
    {
    "rG": "hex",
    "stealth_address": "hex",
    "commitment": {
        "input_commitment": "hex",
        "output_commitment": "hex",
        "pseudoout_commitment": "hex",
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
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    string key_image;
    string rg, stealth_address, input_commitment, output_commitment, pseudout_commitment, amount_mask;
    string c, m;
    vector<string> r;
    vector<string> members;

    to_string(key_image, blsagSig.key_image, 32);
    to_string(rg, sa.rG, 32);
    to_string(stealth_address, sa.pk, 32);
    // to_string(input_commitment, commitment.inputs_commitments[0].data(), 32);
    // to_string(output_commitment, commitment.outputs_commitments[0].data(), 32);
    // to_string(pseudoout_commitment, commitment.pseudoouts_commitments[0].data(), 32);

    // to_string(amount_mask, commitment.amount_masks[0].data(), 32);

    // TODO amount mask not implemented
    input_commitment = "10";
    output_commitment = "10";
    pseudout_commitment = "10";
    amount_mask = "10";

    to_string(c, blsagSig.c, 32);
    to_string(m, blsagSig.m, 32);
    for (int i = 0; i < blsagSig.r.size(); i++)
    {
        string temp;
        to_string(temp, blsagSig.r[i].data(), 32);
        r.push_back(temp);
    }
    for (int i = 0; i < blsagSig.members.size(); i++)
    {
        string temp;
        to_string(temp, blsagSig.members[i].pk, 32);
        members.push_back(temp);
    }

    json commit_json = {
        {"input_commitment", input_commitment},
        {"output_commitment", output_commitment},
        {"pseudoout_commitment", pseudout_commitment},
        {"amount_mask", amount_mask}};
    json blsag_json = {
        {"c", c},
        {"m", m},
        {"r", r},
        {"members", members}};
    json record_json = {
        {"rG", rg},
        {"stealth_address", stealth_address},
        {"commitment", commit_json},
        {"blsagSig", blsag_json}};

    string record_str = record_json.dump();

    C.prepare("insert vote_record", "insert into vote_records (district_id, key_image, transaction_record) values ($1, $2, $3);");
    W.exec_prepared("insert vote_record", district_id, key_image, record_str);
    W.commit();
}

void grab_decoys()
{
}

void verify_vote_record()
{
}