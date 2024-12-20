# initiate the grpc function to avoid manually input the data from the website
from ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    grpc_calculate_total_vote_run,
    grpc_filter_non_voter_run,
    GrpcError, 
)

if __name__ == "__main__":
    # # grpc_generate_user_and_votingcurr_run(1, 10)
    # # grpc_generate_user_and_votingcurr_run(2, 10)
    # grpc_generate_candidate_keys_run(2)

    # try: 
    #     grpc_compute_vote_run(2, 1)
    #     grpc_compute_vote_run(2, 1)
    # except GrpcError as e:   
    #     print(e)
    
    # try: 
    #     grpc_compute_vote_run(2, 2)
    # except GrpcError as e:   
    #     print(e)

    # try:
    #     grpc_calculate_total_vote_run([1, 2])
    # except GrpcError as e:   
    #     print(e)

    for i in range(1, 1500):
        try:
            grpc_compute_vote_run(2, i)
        except GrpcError as e:
            print(e)

    # try:
    #     grpc_filter_non_voter_run([1, 2, 3])
    # except GrpcError as e:
    #     print(e)