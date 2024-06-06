#include "ringct.grpc.pb.h"
#include <grpcpp/grpcpp.h>
#include "evoting.h"
#include "core.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

// Include the proto file class
using ringct::Calculate_Total_Vote_Request;
using ringct::Calculate_Total_Vote_Response;
using ringct::Gen_Candidate_Request;
using ringct::Gen_Candidate_Response;
using ringct::Gen_VoterCurr_Request;
using ringct::Gen_VoterCurr_Response;
using ringct::RingCT_Service;
using ringct::Vote_Request;
using ringct::Vote_Response;

using namespace std;

// ------------------------------ conversion logic ------------------------------
// place all the conversion logic here

// convert vote_request to vote struct
void vote_request_to_vote(Vote &vote, const Vote_Request &request)
{
    vote.district_id = request.district_id();
    vote.candidate_id = request.candidate_id();
    vote.voter_id = request.voter_id();
}

void vote_to_vote_response(Vote_Response &response, const Vote &vote)
{
    response.set_district_id(vote.district_id);
    response.set_candidate_id(vote.candidate_id);
    response.set_voter_id(vote.voter_id);
    response.set_key_image(vote.key_image);
    response.set_test_output(vote.test_output);
}

void gen_votercurr_to_gen_votercurr_response(Gen_VoterCurr_Response &response, const Gen_VoterCurr &gen_user_curr)
{
    response.set_district_id(gen_user_curr.district_id);
    response.set_voter_num(gen_user_curr.voter_num);
    response.set_test_output(gen_user_curr.test_output);
}

void gen_votercurr_request_to_gen_votercurr(Gen_VoterCurr &gen_user_curr, const Gen_VoterCurr_Request &request)
{
    gen_user_curr.district_id = request.district_id();
    gen_user_curr.voter_num = request.voter_num();
}

void gen_candidate_request_to_gen_candidate(Gen_Candidate &gen_candidate, const Gen_Candidate_Request &request)
{
    gen_candidate.district_id = request.district_id();
    gen_candidate.candidate_id = request.candidate_id();
}

void gen_candidate_to_gen_candidate_response(Gen_Candidate_Response &response, const Gen_Candidate &gen_candidate)
{
    response.set_district_id(gen_candidate.district_id);
    response.set_candidate_id(gen_candidate.candidate_id);
    response.set_test_output(gen_candidate.test_output);
}

void compute_total_vote_request_to_compute_total_vote(Compute_Total_Vote &compute_total_vote, const Calculate_Total_Vote_Request &request)
{
    compute_total_vote.district_ids.insert(compute_total_vote.district_ids.end(), request.district_ids().begin(), request.district_ids().end());
}

void compute_total_vote_to_compute_total_vote_response(Calculate_Total_Vote_Response &response, const Compute_Total_Vote &compute_total_vote)
{
    for (int id : compute_total_vote.district_ids)
        response.add_district_ids(id);
    response.set_test_output(compute_total_vote.test_output);
}

// ------------------------------ server class logic ------------------------------
class RingCT_Service_Impl final : public RingCT_Service::Service
{
public:
    Status Compute_Vote(ServerContext *context, const Vote_Request *request, Vote_Response *response) override
    {
        // use the django defined one
        if (request->candidate_id() <= 0 || request->voter_id() <= 0 || request->district_id() <= 0)
        {
            return Status(grpc::INVALID_ARGUMENT, "Invalid field value for candidate_id, voter_id, or district_id");
        }

        Vote vote;
        vote_request_to_vote(vote, *request);

        try
        {
            voter_cast_vote(vote);
        }
        catch (const std::exception &e)
        {
            return Status(grpc::INTERNAL, e.what());
        }

        vote_to_vote_response(*response, vote);
        return Status::OK;
    }

    Status Generate_Voter_and_Voting_Currency(ServerContext *context, const Gen_VoterCurr_Request *request, Gen_VoterCurr_Response *response) override
    {
        if (request->district_id() <= 0 || request->voter_num() <= 0)
        {
            return Status(grpc::INVALID_ARGUMENT, "Invalid field value for district_id or voter_num");
        }

        Gen_VoterCurr gen_user_curr;
        gen_votercurr_request_to_gen_votercurr(gen_user_curr, *request);

        try
        {
            CA_generate_voter_keys_currency(gen_user_curr);
        }
        catch (const std::exception &e)
        {
            return Status(grpc::INTERNAL, e.what());
        }

        gen_votercurr_to_gen_votercurr_response(*response, gen_user_curr);
        return Status::OK;
    }

    Status Generate_CandidateKeys(ServerContext *context, const Gen_Candidate_Request *request, Gen_Candidate_Response *response) override
    {
        if (request->district_id() <= 0 || request->candidate_id() <= 0)
        {
            return Status(grpc::INVALID_ARGUMENT, "Invalid field value for district_id or candidate_id");
        }

        Gen_Candidate gen_candidate;
        gen_candidate_request_to_gen_candidate(gen_candidate, *request);

        try
        {
            CA_generate_candidate_keys(gen_candidate);
        }
        catch (const std::exception &e)
        {
            return Status(grpc::INTERNAL, e.what());
        }

        gen_candidate_to_gen_candidate_response(*response, gen_candidate);
        return Status::OK;
    }

    Status Calculate_Total_Vote(ServerContext *context, const Calculate_Total_Vote_Request *request, Calculate_Total_Vote_Response *response) override
    {
        if (request->district_ids().empty())
        {
            return Status(grpc::INVALID_ARGUMENT, "district_ids is empty");
        }

        Compute_Total_Vote compute_total_vote;
        compute_total_vote_request_to_compute_total_vote(compute_total_vote, *request);

        try
        {
            // compute_total_vote(compute_total_vote);
        }
        catch (const std::exception &e)
        {
            return Status(grpc::INTERNAL, e.what());
        }

        compute_total_vote_to_compute_total_vote_response(*response, compute_total_vote);
        return Status::OK;
    }
};

// ------------------------------ server run ------------------------------
void RunServer()
{
    // TODO update to the server address
    string server_address("0.0.0.0:50051");
    RingCT_Service_Impl service;

    ServerBuilder builder;
    // TODO temp run without enc
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);
    unique_ptr<Server> server(builder.BuildAndStart());
    cout << "Server listening on " << server_address << endl;
    server->Wait();
}

int main(int argc, char **argv)
{
    if (sodium_init() == -1)
    {
        cout << "sodium_init failed" << endl;
        return 1;
    }
    // Vote vote;
    // vote.voter_id = 1;
    // voter_cast_vote(vote);

    // test with blsag
    // for (int i = 0; i < 1; i++)
    // {
    //     vector<User> users_blsag(10);
    //     vector<StealthAddress> blsagSA; // decoy
    //     int secret_index = secret_index_gen(users_blsag.size());
    //     CA_generate_address(blsagSA, users_blsag);

    //     User signer;
    //     StealthAddress signerSA;
    //     compute_stealth_address(signerSA, signer);
    //     receiver_test_stealth_address(signerSA, signer);

    //     blsagSig blsagSig;
    //     BYTE m[32];
    //     crypto_core_ed25519_scalar_random(m);
    //     compute_key_image(blsagSig, signerSA);
    //     blsag_simple_gen(blsagSig, m, secret_index, signerSA, blsagSA);
    //     bool is_verified = blsag_simple_verify(blsagSig, m);
    //     if (!is_verified)
    //     {
    //         cout << "Verification fail" << endl;
    //         exit(1);
    //     }
    //     cout << "Verification success on " << i + 1 << endl;
    // }

    // // test
    // //  Define the number of pseudo outputs and output commitments
    // size_t numPseudoOuts = 3;        // Example
    // size_t numOutputCommitments = 2; // Example

    // // Vectors to store blinding factors
    // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> pseudoOutBfs(numPseudoOuts);
    // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> outputCommitmentBfs(numOutputCommitments);
    // // vector<BYTE[crypto_core_ed25519_SCALARBYTES]> outputCommitmentBfs(numOutputCommitments);

    // User receiver;
    // StealthAddress receiverSA;
    // BYTE r[crypto_core_ed25519_SCALARBYTES];
    // compute_stealth_address(receiverSA, receiver, r);

    // for (size_t i = 0; i < numOutputCommitments; ++i)
    // {
    //     compute_commitment_mask(outputCommitmentBfs[i].data(), r, receiver.pkV, i);
    // }
    // // Generate blinding factors ensuring the sum condition
    // generatePseudoBfs(pseudoOutBfs, outputCommitmentBfs);

    // // Compare the sums of blinding factors
    // if (compareBlindingFactors(pseudoOutBfs, outputCommitmentBfs))
    // {
    //     cout << "The sum of blinding factors for pseudo outputs is equal to the sum of blinding factors for output commitments.\n";
    // }
    // else
    // {
    //     cout << "The sum of blinding factors for pseudo outputs is not equal to the sum of blinding factors for output commitments.\n";
    // }

    // // Define values for commitments (example values)
    // vector<int> pseudoOutValues = {25, 50, 75};
    // vector<int> outputCommitmentValues = {50, 100};

    // // Vectors to store commitments
    // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> pseudoOuts(numPseudoOuts);
    // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> outputCommitments(numOutputCommitments);

    // BYTE H[crypto_core_ed25519_BYTES];
    // generate_H(H);
    // print_bytearray(H, 32);
    // compare_BYTE(H, H_point, 32);

    // for (size_t i = 0; i < numPseudoOuts; ++i)
    // {
    //     BYTE a[32] = {0};
    //     int_to_scalar_BYTE(a, pseudoOutValues[i]);
    //     add_key(pseudoOuts[i].data(), a, pseudoOutBfs[i].data(), H);
    // }

    // for (size_t i = 0; i < numOutputCommitments; ++i)
    // {
    //     BYTE b[32] = {0};
    //     int_to_scalar_BYTE(b, outputCommitmentValues[i]);
    //     add_key(outputCommitments[i].data(), b, outputCommitmentBfs[i].data(), H);
    // }

    // // verify commitment balancing
    // verify_commitment_balancing(outputCommitments, pseudoOuts);

    RunServer();

    return 0;
}