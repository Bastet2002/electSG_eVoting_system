import grpc
# import ringct_pb2_grpc
# import ringct_pb2
from pygrpc import ringct_pb2_grpc, ringct_pb2

import logging
import os
import json

# global variable for the channel
service_config = {
    "methodConfig": [{
        "name": [{"service": "YourServiceName"}],
        "retryPolicy": {
            "maxAttempts": 5,
            "initialBackoff": "0.1s",
            "maxBackoff": "1s",
            "backoffMultiplier": 2,
            "retryableStatusCodes": [
                "UNAVAILABLE"
            ]
        }
    }]
}

# Convert the service configuration to JSON string
service_config_json = json.dumps(service_config)
channel = grpc.insecure_channel(os.getenv("RINGCT_URL"), options=[('grpc.service_config', service_config_json)])
stub = ringct_pb2_grpc.RingCT_ServiceStub(channel)

class GrpcError(Exception):
    '''Error raised for the any grpc client error or grpc input error'''
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# ----------------- object conversion functions -----------------

# Dont use the grpc class in any django logic. Use the grpc class as data transfer object
# constructor for the django backend, so that can be used in grpc client to call the server
def grpc_construct_gen_votercurr_request(district_id, voter_num):
    gen_usercurr_request = ringct_pb2.Gen_VoterCurr_Request()
    gen_usercurr_request.district_id = district_id
    gen_usercurr_request.voter_num = voter_num
    return gen_usercurr_request

def grpc_construct_vote_request(candidate_id, voter_id, is_voting=True): # default is voting
    vote_request = ringct_pb2.Vote_Request()
    vote_request.candidate_id = candidate_id
    vote_request.voter_id = voter_id
    vote_request.is_voting = is_voting
    return vote_request

def grpc_construct_gen_candidate_request(candidate_id):
    gen_candidate_request = ringct_pb2.Gen_Candidate_Request()
    gen_candidate_request.candidate_id = candidate_id
    return gen_candidate_request

def grpc_construct_calculate_total_vote_request(district_ids):
    calculate_total_vote_request = ringct_pb2.Calculate_Total_Vote_Request()
    for district_id in district_ids:
        calculate_total_vote_request.district_ids.append(district_id)
    return calculate_total_vote_request

def grpc_construct_filter_non_voter_request(district_ids):
    filter_non_voter_request = ringct_pb2.Filter_Non_Voter_Request()
    for district_id in district_ids:
        filter_non_voter_request.district_ids.append(district_id)
    return filter_non_voter_request

# ----------------- grpc client functions -----------------
# assume the django backend only need to call these functions
# the other functions are suppliment to this function
# this will throw normal exception if the input is not correct
# this will throw grpc error if there is error in grpc server processing

def grpc_compute_vote_run(candidate_id, voter_id, is_voting=True):
    if not candidate_id or not voter_id:
        raise ValueError("Input error: district_id, candidate_id, voter_id cannot be empty")
    
    vote_request = grpc_construct_vote_request(candidate_id, voter_id, is_voting)

    try:
        print("-------------- ComputeVote --------------")
        vote_response = stub.Compute_Vote(vote_request)

        print("Vote Request: ", vote_request)
        print("Vote Response: ", vote_response)

        if vote_response.candidate_id != vote_request.candidate_id or vote_response.voter_id != vote_request.voter_id:
            raise grpc.RpcError("Input Output Mismatch: candidate_id, voter_id not matching after grpc_compute_vote_run")
        if is_voting and not vote_response.key_image:
            raise grpc.RpcError("Output Error: Key image not found in grpc_compute_vote")

    except grpc.RpcError as e:
        # print(e)
        raise GrpcError(f"Grpc error: {e.details()}")

    return vote_response

def grpc_generate_user_and_votingcurr_run(district_id, voter_num):
    if not district_id or not voter_num:
        raise ValueError("Input error: district_id, voter_num cannot be empty")
    
    gen_usercurr_request = grpc_construct_gen_votercurr_request(district_id, voter_num)

    try:
        print("-------------- GenerateUserCurr --------------")
        gen_usercurr_response = stub.Generate_Voter_and_Voting_Currency(gen_usercurr_request)

        print("Gen UserCurr Request: ", gen_usercurr_request)
        print("Gen UserCurr Response: ", gen_usercurr_response)

        if gen_usercurr_response.district_id != gen_usercurr_request.district_id or gen_usercurr_response.voter_num != gen_usercurr_request.voter_num:
            raise grpc.RpcError("Input output mismatch: district_id, voter_num not matching in grpc_generate_user_and_votingcurr_run")

    except grpc.RpcError as e:
        raise GrpcError(f"Grpc error: {e.details()}")

    return gen_usercurr_response

def grpc_generate_candidate_keys_run(candidate_id):
    if not candidate_id:
        raise ValueError("Input error: district_id, candidate_id cannot be empty")
    
    gen_candidate_request = grpc_construct_gen_candidate_request(candidate_id)

    try:
        print("-------------- GenerateCandidateKeys --------------")
        gen_candidate_response = stub.Generate_CandidateKeys(gen_candidate_request)

        print("Gen Candidate Request: ", gen_candidate_request)
        print("Gen Candidate Response: ", gen_candidate_response)

        if gen_candidate_response.candidate_id != gen_candidate_request.candidate_id:
            print(gen_candidate_response.candidate_id, gen_candidate_request.candidate_id)
            raise grpc.RpcError("Input output mismatch: candidate_id not matching in grpc_generate_candidate_keys_run")

    except grpc.RpcError as e:
        raise GrpcError(f"Grpc error: {e.details()}")

    return gen_candidate_response

def grpc_calculate_total_vote_run(district_ids):
    if not district_ids:
        raise ValueError("Input error: district_ids cannot be empty")
    
    calculate_total_vote_request = grpc_construct_calculate_total_vote_request(district_ids)

    print('calculate_total_vote_request', calculate_total_vote_request)

    try:
        print("-------------- CalculateTotalVote --------------")
        calculate_total_vote_response = stub.Calculate_Total_Vote(calculate_total_vote_request)

        print("Calculate Total Vote Request: ", calculate_total_vote_request)
        print("Calculate Total Vote Response: ", calculate_total_vote_response)

        if len(calculate_total_vote_response.district_ids) != len(calculate_total_vote_request.district_ids):
            raise grpc.RpcError("Input output mismatch: district_ids not matching in grpc_calculate_total_vote_run")

        for id in calculate_total_vote_response.district_ids:
            if id not in calculate_total_vote_request.district_ids:
                raise grpc.RpcError("Input output mismatch: district_ids not matching in grpc_calculate_total_vote_run")

    except grpc.RpcError as e:
        raise GrpcError(f"Grpc error: {e.details()}")

    return calculate_total_vote_response

def grpc_filter_non_voter_run(district_ids):
    if not district_ids:
        raise ValueError("Input error: district_ids cannot be empty")
    
    filter_non_voter_request = grpc_construct_filter_non_voter_request(district_ids)

    print('filter_non_voter_request', filter_non_voter_request)

    try:
        print("-------------- FilterNonVoter --------------")
        filter_non_voter_response = stub.Filter_Non_Voter(filter_non_voter_request)

        print("Filter Non Voter Request: ", filter_non_voter_request)
        print("Filter Non Voter Response: ", filter_non_voter_response)

        if len(filter_non_voter_response.district_ids) != len(filter_non_voter_request.district_ids):
            raise grpc.RpcError("Input output mismatch: district_ids not matching in grpc_filter_non_voter_run")
        
        for id in filter_non_voter_response.district_ids:
            if id not in filter_non_voter_request.district_ids:
                raise grpc.RpcError("Input output mismatch: district_ids not matching in grpc_filter_non_voter_run")
    
    except grpc.RpcError as e:
        raise GrpcError(f"Grpc error: {e.details()}")
    
    return filter_non_voter_response


# ----------------- test run function -----------------

if __name__ == "__main__":
    logging.basicConfig()
