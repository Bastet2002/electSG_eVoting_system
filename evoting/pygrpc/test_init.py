# initiate the grpc function to avoid manually input the data from the website
from ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
)

if __name__ == "__main__":
    grpc_generate_user_and_votingcurr_run(1, 10)
    grpc_generate_user_and_votingcurr_run(2, 10)

    grpc_generate_candidate_keys_run(2)

    grpc_compute_vote_run(2, 1)