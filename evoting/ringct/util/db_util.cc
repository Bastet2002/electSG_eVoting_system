#include "db_util.h"
#include "fmt/format.h"

// can also get user by pk for function overloading
User get_voter(int32_t voter_id)
{
    // pqxx::connection c_django{cnt_django};
    // pqxx::work txn_d{c_django};

    // pqxx:connection c_rct{cnt_rct};
    // pqxx::work txn_r{c_rct};

    // // 1. get the pkV from the voter table in django db
    // // can use prepared statement later
    // pqxx::result r = txn_d.exec("SELECT pkV FROM Voter WHERE voter_id = " + std::to_string(user_id) + ";");
    // auto[]

    // // 2. get all the keys with pkV in the rinct db
    // pqxx::row r = txn_r.exec("SELECT * FROM Voter_SecretKey WHERE pkV = " + pkV[0][0].c_str() + ";")[0];

    // // TODO interact with db and return the user

    // // random for now
    return User();
}

User get_candidate(int32_t candidate_id)
{
    // TODO interact with db and return the user

    // random for now
    return User();
}

void write_voter(const int32_t district_id, const User &voter)
{
    // convert to hexstring
    string pkV, skV, pkS, skS;
    to_string(pkV, voter.pkV, 32);
    to_string(skV, voter.skV, 32);
    to_string(pkS, voter.pkS, 32);
    to_string(skS, voter.skS, 32);

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
    // TODO
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
    to_string(skV, candidate.skV, 32);
    to_string(pkS, candidate.pkS, 32);
    to_string(skS, candidate.skS, 32);

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