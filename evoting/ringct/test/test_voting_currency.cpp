#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the CA_generate_voting_currency function", "[voting_currency]")
{
    const string input_file = filesystem::absolute("/app/test/text/stealth_address.txt");
    const string output_file = filesystem::absolute("/app/test/text/voting_currency.txt");

    GIVEN("A set of inputs and expected outputs for generating the voting currency")
    {
        // Generate the output file
        ifstream infile(input_file);
        ifstream outfile(output_file);
        REQUIRE(infile.is_open());
        REQUIRE(outfile.is_open());

        string input_line, output_line;
        int i = 0;

        while (getline(infile, input_line) && getline(outfile, output_line))
        {
            vector<string> input_tokens = tokeniser(input_line);
            vector<string> output_tokens = tokeniser(output_line);

            REQUIRE(input_tokens.size() == 7);  // pkS, pkV, skS, skV, r, rG, pk
            REQUIRE(output_tokens.size() == 6); // input_commitment, output_commitment, pseudo_output_commitment, amount_mask, sa_r, receiver_pkV

            StealthAddress sa;
            User receiver;

            hex_to_bytearray(receiver.pkS, input_tokens[0]);
            hex_to_bytearray(receiver.pkV, input_tokens[1]);
            hex_to_bytearray(receiver.skS, input_tokens[2]);
            hex_to_bytearray(receiver.skV, input_tokens[3]);
            hex_to_bytearray(sa.r, input_tokens[4]);
            hex_to_bytearray(sa.rG, input_tokens[5]);
            hex_to_bytearray(sa.pk, input_tokens[6]);

            i++;

            WHEN("The generate voting currency function is called and compared to the expected output" + to_string(i))
            {
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                Commitment computed_commitment;
                CA_generate_voting_currency(computed_commitment, sa, receiver);

                string computed_input_commitment, computed_output_commitment, computed_pseudo_output_commitment, computed_amount_mask;
                to_string(computed_input_commitment, computed_commitment.inputs_commitments[0].data(), 32);
                to_string(computed_output_commitment, computed_commitment.outputs_commitments[0].data(), 32);
                to_string(computed_pseudo_output_commitment, computed_commitment.pseudoouts_commitments[0].data(), 32);
                to_string(computed_amount_mask, computed_commitment.amount_masks[0].data(), 8);

                bool is_equal_input_commitment = (computed_input_commitment == output_tokens[0]);
                bool is_equal_output_commitment = (computed_output_commitment == output_tokens[1]);
                bool is_equal_pseudo_output_commitment = (computed_pseudo_output_commitment == output_tokens[2]);
                bool is_equal_amount_mask = (computed_amount_mask == output_tokens[3]);
                bool is_equal_sa_r = (input_tokens[4] == output_tokens[4]);
                bool is_equal_receiver_pkV = (input_tokens[1] == output_tokens[5]);
                
                cout << "Test case " << i << ":" << endl;
                cout << "Computed input commitment: " << computed_input_commitment << endl;
                cout << "Expected input commitment: " << output_tokens[0] << endl;
                cout << "Computed output commitment: " << computed_output_commitment << endl;
                cout << "Expected output commitment: " << output_tokens[1] << endl;
                cout << "Computed pseudo-output commitment: " << computed_pseudo_output_commitment << endl;
                cout << "Expected pseudo-output commitment: " << output_tokens[2] << endl;
                cout << "Computed amount mask: " << computed_amount_mask << endl;
                cout << "Expected amount mask: " << output_tokens[3] << endl;
                cout << endl;

                if (!is_equal_input_commitment || !is_equal_output_commitment || 
                    !is_equal_pseudo_output_commitment || !is_equal_amount_mask || 
                    !is_equal_sa_r || !is_equal_receiver_pkV)
                {
                    cout << "Actual and expected output does not match" << endl;
                }

                THEN("The generated output should match the expected output")
                {
                    REQUIRE(is_equal_input_commitment);
                    REQUIRE(is_equal_output_commitment);
                    REQUIRE(is_equal_pseudo_output_commitment);
                    REQUIRE(is_equal_amount_mask);
                    REQUIRE(is_equal_sa_r);
                    REQUIRE(is_equal_receiver_pkV);
                }
                randombytes_set_implementation(NULL);
            }
        }
    }
}
