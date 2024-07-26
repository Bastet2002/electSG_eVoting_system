# initiate the grpc function to avoid manually input the data from the website
from ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    grpc_calculate_total_vote_run,
    GrpcError, 
)

from myapp.models import ElectionPhase

# if __name__ == "__main__":
    phase = ElectionPhase.objects.filter(phase_name='Polling Day')[0]
    phase.is_active = True
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