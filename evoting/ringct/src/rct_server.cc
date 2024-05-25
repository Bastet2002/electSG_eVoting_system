#include "ringct.grpc.pb.h"
#include <grpcpp/grpcpp.h>
#include "vote.h"
#include "core.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

// Include the proto file class
using ringct::RingCT_Service;
using ringct::Vote_Request;
using ringct::Vote_Response;

using namespace std;

// place all the conversion logic here
// convert vote_request to vote struct
void vote_request_to_vote(Vote &vote, const Vote_Request &request)
{
    vote.district_id = request.district_id();
    vote.candidate_id = request.candidate_id();
    vote.voter_id = request.voter_id();
}

class RingCT_Service_Impl final : public RingCT_Service::Service
{
public:
    Status Compute_Vote(ServerContext *context, const Vote_Request *request, Vote_Response *response) override
    {
        Vote vote;
        vote_request_to_vote(vote, *request);
        voter_cast_vote(vote);
        response->set_key_image(520);
        return Status::OK;
    }
};

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

    RunServer();

    return 0;
}