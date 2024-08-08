#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the compute_commitment_simple function", "[compute_commitment_simple]")
{
    const string input_file_receiver = filesystem::absolute("/app/test/text/stealth_address_signer.txt");
    const string input_file_signer = filesystem::absolute("/app/test/text/stealth_address.txt");
    const string input_file_received_commitment = filesystem::absolute("/app/test/text/voting_currency.txt");
    const string expected_output_file = filesystem::absolute("/app/test/text/commitment_simple.txt");

    GIVEN("The input files and expected output")
    {
        ifstream infile_receiver(input_file_receiver);
        ifstream infile_signer(input_file_signer);
        ifstream infile_received_commitment(input_file_received_commitment);
        ifstream expected_output(expected_output_file);
        REQUIRE(infile_receiver.is_open());
        REQUIRE(infile_signer.is_open());
        REQUIRE(infile_received_commitment.is_open());
        REQUIRE(expected_output.is_open());

        string pkS_r, pkV_r, skS_r, skV_r, r_r, rG_r, pk_r;
        string pkS_s, pkV_s, skS_s, skV_s, r_s, rG_s, pk_s;
        string input_commitment, output_commitment, pseudo_output_commitment, amount_mask, sa_r, receiver_pkV;
        string expected_line;
        int line_count = 0;

        while (infile_receiver >> pkS_r >> pkV_r >> skS_r >> skV_r >> r_r >> rG_r >> pk_r &&
               infile_signer >> pkS_s >> pkV_s >> skS_s >> skV_s >> r_s >> rG_s >> pk_s &&
               infile_received_commitment >> input_commitment >> output_commitment >> pseudo_output_commitment >> amount_mask >> sa_r >> receiver_pkV &&
               getline(expected_output, expected_line))
        {
            line_count++;

            WHEN("processing input line " + to_string(line_count))
            {
                // Set up StealthAddress objects
                StealthAddress receiverSA, signerSA;
                hex_to_bytearray(receiverSA.r, r_r);
                hex_to_bytearray(receiverSA.rG, rG_r);
                hex_to_bytearray(receiverSA.pk, pk_r);
                hex_to_bytearray(signerSA.r, r_s);
                hex_to_bytearray(signerSA.rG, rG_s);
                hex_to_bytearray(signerSA.pk, pk_s);

                // Set up User objects
                User receiver(pkV_r, skV_r, pkS_r, skS_r);
                User signer(pkV_s, skV_s, pkS_s, skS_s);

                // Create receivedCmt from imported data
                Commitment receivedCmt;
                array<BYTE, 32> received_output_commitment;
                array<BYTE, 8> received_amount_mask;
                hex_to_bytearray(received_output_commitment.data(), output_commitment);
                hex_to_bytearray(received_amount_mask.data(), amount_mask);

                receivedCmt.outputs_commitments.push_back(received_output_commitment);
                receivedCmt.amount_masks.push_back(received_amount_mask);

                // Debugging output for received commitment
                cout << "in test file" << endl;
                string debug_str;
                // cout << "Received Commitment:" << endl;
                // to_string(debug_str, received_output_commitment.data(), 32);
                // cout << "output_commitment: " << debug_str << endl;
                to_string(debug_str, received_amount_mask.data(), 8);
                cout << "singer received sa.rg" << endl;
                print_hex(signerSA.rG, 32);
                cout << "signer skV" << endl;
                print_hex(signer.skV, 64);

                // Set up candidate Commitment
                Commitment candidateCmt;

                // Call compute_commitment_simple
                try {
                    compute_commitment_simple(candidateCmt, receiverSA, receiver, receivedCmt, signerSA, signer);
                } catch (const std::exception& e) {
                    cerr << "Exception caught: " << e.what() << endl;
                    FAIL("Exception caught: " << e.what());
                }

                // Convert commitment fields to strings
                string amount_mask_str, output_blindingfactor_mask, pseudo_output_blindingfactor_mask;
                string output_commitment_str, pseudo_output_commitment_str, output_blindingfactor_str;

                to_string(amount_mask_str, candidateCmt.amount_masks[0].data(), 8);
                to_string(output_blindingfactor_mask, candidateCmt.outputs_blindingfactor_masks[0].data(), 32);
                to_string(pseudo_output_blindingfactor_mask, candidateCmt.pseudoouts_blindingfactor_masks[0].data(), 32);
                to_string(output_commitment_str, candidateCmt.outputs_commitments[0].data(), 32);
                to_string(pseudo_output_commitment_str, candidateCmt.pseudoouts_commitments[0].data(), 32);
                to_string(output_blindingfactor_str, candidateCmt.output_blindingfactor, 32);

                // Construct the computed output string
                string computed_output = amount_mask_str + " " +
                                         output_blindingfactor_mask + " " +
                                         pseudo_output_blindingfactor_mask + " " +
                                         output_commitment_str + " " +
                                         pseudo_output_commitment_str + " " +
                                         output_blindingfactor_str;

                THEN("the computed output should match the expected output")
                {
                    REQUIRE(computed_output == expected_line);
                }
            }
        }
    }
}
