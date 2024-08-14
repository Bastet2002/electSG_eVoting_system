#include "db_util.h"
#include <nlohmann/json.hpp>
#include "fmt/format.h"

using namespace nlohmann;

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
    pqxx::row r = txn_d.exec1("select pkV from myapp_voter where voter_id = " + to_string(voter_id) + ";");
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
    pqxx::row r = txn_d.exec1("select pkV, pkS from myapp_candidatepublickey where candidate_id = " + to_string(candidate_id) + ";");
    string pkV = r["pkV"].as<string>();
    string pkS = r["pkS"].as<string>();

    // 2. get the district id from useraccount table
    r = txn_d.exec1("select district_id from myapp_useraccount where user_id = '" + to_string(candidate_id) + "';");
    district_id = r["district_id"].as<int>();

    return User(pkV, pkS);
}

User get_candidate_s(int32_t &district_id, const int32_t candidate_id)
{
    User candidate = get_candidate(district_id, candidate_id);
    string pkV;
    to_string(pkV, candidate.pkV, 32);

    pqxx::connection C{cnt_rct};
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::nontransaction W{C};
    C.prepare("get secret key", "select skv, sks from candidate_secretkey where pkv=$1;");
    pqxx::result r = W.exec_prepared("get secret key", pkV);

    string skV = r[0]["skv"].as<string>();
    string skS = r[0]["sks"].as<string>();

    hex_to_bytearray(candidate.skV, skV);
    hex_to_bytearray(candidate.skS, skS);
    return candidate;
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
    c_d.prepare("insert voter_public", "insert into myapp_voter (district_id, pkV) values ($1, $2);");

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
    to_string(amount_mask, commitment.amount_masks[0].data(), 8);

    string json = fmt::format(R"({{"rG": "{}", "commitment": {{"input_commitment": "{}", "output_commitment": "{}", "pseudoout_commitment": "{}", "amount_mask": "{}"}}}})",
                              rG, input_commitment, output_commitment, pseudo_output_commitment, amount_mask);

    pqxx::connection C(cnt_django);

    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    C.prepare("insert vote_currency", "insert into myapp_votingcurrency (district_id, stealth_address, commitment_record) values ($1, $2, $3);");
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
    c_d.prepare("insert candidate_public", "insert into myapp_candidatepublickey (candidate_id, pkV, pkS) values ($1, $2, $3);");

    pqxx::work txn_d(c_d);
    txn_d.exec_prepared("insert candidate_public", candidate_id, pkV, pkS);
    txn_d.commit();
}

void scan_for_stealthaddress(Commitment &receivedCmt, StealthAddress &sa, const int32_t district_id, const User &signer)
{
    cout << "scan for stealth address in district " << district_id << endl;

    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);
    int batch_size = 100;
    int offset = 0;
    bool more_page = true;

    while (more_page)
    {
        pqxx::result r = W.exec("select stealth_address, commitment_record->>'rG' as rG, commitment_record->'commitment'->>'output_commitment' as output_commitment,  commitment_record->'commitment'->>'amount_mask' as amount_mask from myapp_votingcurrency where district_id = " + to_string(district_id) + " order by stealth_address limit " + to_string(batch_size) + " offset " + to_string(offset) + ";");
        if (r.empty())
        {
            more_page = false;
        }
        else
        {
            for (const auto &row : r)
            {
                string stealth_address = row["stealth_address"].as<string>();
                string rG = row[1].as<string>();
                StealthAddress sa_temp(stealth_address, rG);
                if (receiver_test_stealth_address(sa_temp, signer))
                {
                    cout << "Stealth address found" << endl;
                    sa = sa_temp;
                    string output_commitment_str = row["output_commitment"].as<string>();

                    BYTE output_commitment[32];
                    hex_to_bytearray(output_commitment, output_commitment_str);

                    BYTE amount_mask[8];
                    hex_to_bytearray(amount_mask, row["amount_mask"].as<string>());

                    array<BYTE, 32> output_commitment_arr;
                    copy(begin(output_commitment), end(output_commitment), output_commitment_arr.begin());

                    array<BYTE, 8> amount_mask_arr;
                    copy(begin(amount_mask), end(amount_mask), amount_mask_arr.begin());

                    receivedCmt.outputs_commitments.push_back(output_commitment_arr);
                    receivedCmt.amount_masks.push_back(amount_mask_arr);
                    return; // Stealth address found and valid
                }
            }
            offset += batch_size;
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

    pqxx::result r = W.exec("select * from myapp_voterecords where district_id=" + to_string(district_id) + " and key_image='" + key_image_str + "';");

    return r.empty();
}

void write_voterecord(const int32_t district_id, const RangeProof& rangeproof,  const blsagSig &blsagSig, const StealthAddress &sa, const Commitment &commitment)
{
    /*
    keyimage
    {
    "rG": "hex",
    "stealth_address": "hex",
    "commitment": {
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
    "rangeproof":{
        "bbee": "hex",
        "bbs0": ["hex"],
        "bbs1": ["hex"],
        "C1": ["hex"],
        "C2": ["hex"],
    }
    */
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    string key_image;
    string rg, stealth_address, output_commitment, pseudout_commitment, amount_mask;
    string c, m;
    vector<string> r;
    vector<string> members;
    string bbee;
    vector<string> bbs0, bbs1, C1, C2;

    to_string(key_image, blsagSig.key_image, 32);
    to_string(rg, sa.rG, 32);
    to_string(stealth_address, sa.pk, 32);
    to_string(output_commitment, commitment.outputs_commitments[0].data(), 32);
    to_string(pseudout_commitment, commitment.pseudoouts_commitments[0].data(), 32);
    to_string(amount_mask, commitment.amount_masks[0].data(), 8);

    to_string(c, blsagSig.c, 32);
    to_string(m, blsagSig.m, 32);

    to_string(bbee, rangeproof.bbee, 32);

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
    for (int i = 0; i < rangeproof.bbs0.size(); i++)
    {
        string temp;
        to_string(temp, rangeproof.bbs0[i].data(), 32);
        bbs0.push_back(temp);
    }
    for (int i = 0; i < rangeproof.bbs1.size(); i++)
    {
        string temp;
        to_string(temp, rangeproof.bbs1[i].data(), 32);
        bbs1.push_back(temp);
    }
    for (int i = 0; i < rangeproof.C1.size(); i++)
    {
        string temp;
        to_string(temp, rangeproof.C1[i].data(), 32);
        C1.push_back(temp);
    }
    for (int i = 0; i < rangeproof.C2.size(); i++)
    {
        string temp;
        to_string(temp, rangeproof.C2[i].data(), 32);
        C2.push_back(temp);
    }

    json commit_json = {
        {"output_commitment", output_commitment},
        {"pseudoout_commitment", pseudout_commitment},
        {"amount_mask", amount_mask}};
    json blsag_json = {
        {"c", c},
        {"m", m},
        {"r", r},
        {"members", members}};
    json rangeproof_json = {
        {"bbee", bbee},
        {"bbs0", bbs0},
        {"bbs1", bbs1},
        {"C1", C1},
        {"C2", C2}};
    json record_json = {
        {"rG", rg},
        {"stealth_address", stealth_address},
        {"commitment", commit_json},
        {"blsagSig", blsag_json},
        {"rangeproof", rangeproof_json}};

    string record_str = record_json.dump();

    C.prepare("insert vote_record", "insert into myapp_voterecords (district_id, key_image, transaction_record) values ($1, $2, $3);");
    W.exec_prepared("insert vote_record", district_id, key_image, record_str);
    W.commit();
}

vector<int32_t> get_district_ids()
{
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    pqxx::result r = W.exec("select district_id from myapp_district;");

    vector<int> district_ids;
    for (const auto &row : r)
    {
        district_ids.push_back(row["district_id"].as<int32_t>());
    }

    return district_ids;
}

vector<int32_t> get_candidate_ids(const int32_t &district_id)
{
    pqxx::connection c_django{cnt_django};
    if (!c_django.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(c_django.dbname()));
    }
    pqxx::work W(c_django);

    c_django.prepare("get candidate ids in district", "select * from myapp_useraccount where district_id=$1;");
    pqxx::result r = W.exec_prepared("get candidate ids in district", district_id);

    vector<int32_t> candidate_ids;
    for (const auto &row : r)
    {
        candidate_ids.push_back(row["user_id"].as<int32_t>());
    }

    return candidate_ids;
}

vector<StealthAddress> grab_decoys(const int32_t district_id, const StealthAddress& signerSA)
{
    int decoy_size = 10;
    string signerSA_pk;
    to_string(signerSA_pk, signerSA.pk, 32);

    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);
    C.prepare("grab random stealth address", "select stealth_address from myapp_votingcurrency where district_id = $1 and stealth_address <> '"+ signerSA_pk +"' order by random() limit " + to_string(decoy_size) + ";");
    pqxx::result r = W.exec_prepared("grab random stealth address", district_id);

    vector<StealthAddress> decoys;
    for (const auto &row : r)
    {
        string stealth_address = row["stealth_address"].as<string>();
        StealthAddress temp;
        hex_to_bytearray(temp.pk, stealth_address);
        decoys.push_back(temp);
    }
    return decoys; 
}

void verify_vote_record()
{
}

void count_write_vote(const int32_t district_id, const int32_t candidate_id, const User &candidate)
{
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);
    // TODO do we need to test the performance for the query with or without pagination

    int batch_size = 100; // each page is 100 records
    int offset = 0;
    int total_vote = 0;
    bool more_page = true;
    while (more_page)
    {
        pqxx::result r = W.exec("select transaction_record->>'stealth_address' as stealth_address, transaction_record->>'rG' as rG, transaction_record->'commitment'->>'output_commitment' as output_commitment,  transaction_record->'commitment'->>'amount_mask' as amount_mask from myapp_voterecords where district_id = " + to_string(district_id) + " order by key_image limit " + to_string(batch_size) + " offset " + to_string(offset) + ";");

        if (r.empty())
        {
            more_page = false;
        }
        else
        {
            for (const auto &row : r)
            {
                string stealth_address = row["stealth_address"].as<string>();
                string rG = row["rG"].as<string>();
                StealthAddress sa_temp(stealth_address, rG);

                if (receiver_test_stealth_address(sa_temp, candidate))
                {
                    BYTE amount_mask_byte[8];
                    hex_to_bytearray(amount_mask_byte, row["amount_mask"].as<string>());
                    BYTE amount_byte[8];
                    XOR_amount_mask_receiver(amount_byte, amount_mask_byte, 0, sa_temp, candidate);
                    long long amount;
                    byte_to_int(amount, amount_byte, 8);
                    if (amount == 30)
                        total_vote += 1;
                }
            }
            offset += batch_size;
        }
    }

    pqxx::result d_row = W.exec("select * from myapp_voteresults where candidate_id = " + to_string(candidate_id) + ";");
    if (!d_row.empty())
    {
        C.prepare("update total vote", "update myapp_voteresults set total_vote = $1 where candidate_id = $2;");
        W.exec_prepared("update total vote", total_vote, candidate_id);
    }
    else
    {
        C.prepare("insert total vote", "insert into myapp_voteresults (candidate_id, total_vote) values ($1, $2);");
        W.exec_prepared("insert total vote", candidate_id, total_vote);
    }
    cout << "Total vote for candidate in district " << " is " << total_vote << endl;
    W.commit();
}

vector<int32_t> get_voter_ids(const int32_t district_id){
    pqxx::connection C(cnt_django);
    if (!C.is_open())
    {
        throw runtime_error("Failed to open connection to " + string(C.dbname()));
    }
    pqxx::work W(C);

    C.prepare("get voter ids in district", "select * from myapp_voter where district_id=$1 and hash_from_info<>'' and hash_from_info is not null;");
    pqxx::result r = W.exec_prepared("get voter ids in district", district_id);

    vector<int32_t> voter_ids;
    for (const auto &row : r)
    {
        voter_ids.push_back(row["voter_id"].as<int32_t>());
    }
    return voter_ids;
}