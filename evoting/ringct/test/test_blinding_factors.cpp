#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the generate blinding factors function", "[blinding_factors]")
{
    const string input_file = filesystem::absolute("/app/test/text/commitment_simple.txt");
    const string output_file = filesystem::absolute("/app/test/text/blinding_factor.txt");

    GIVEN("A set of input and expected output blinding factors")
    {
        REQUIRE(filesystem::exists(input_file));
        REQUIRE(filesystem::exists(output_file));

        ifstream infile(input_file);
        ifstream outfile(output_file);
        REQUIRE(infile.is_open());
        REQUIRE(outfile.is_open());

        string amount_mask_str, output_blindingfactor_mask, pseudo_output_blindingfactor_mask;
        string output_commitment_str, pseudo_output_commitment_str, output_blindingfactor_str;
        string bf1_str, bf2_str;
        int line_count = 0;

        while (infile >> amount_mask_str >> output_blindingfactor_mask >> pseudo_output_blindingfactor_mask 
               >> output_commitment_str >> pseudo_output_commitment_str >> output_blindingfactor_str &&
               outfile >> bf1_str >> bf2_str)
        {
            line_count++;

            // Convert output commitment blinding factor to BYTE array
            array<BYTE, 32> outputCommitmentBf;
            hex_to_bytearray(outputCommitmentBf.data(), output_blindingfactor_str);

            // Create vector of blinding factors (assuming 2 commitments: output and pseudo-output)
            vector<array<BYTE, 32>> expected_blindingFactors(2);
            hex_to_bytearray(expected_blindingFactors[0].data(), bf1_str);
            hex_to_bytearray(expected_blindingFactors[1].data(), bf2_str);

            WHEN("The generateBlindingFactors function is called and compared to the expected blinding factors" + to_string(line_count))
            {
                // Generate blinding factors
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);
                vector<array<BYTE, 32>> computed_blindingFactors(2);
                generateBlindingFactors(computed_blindingFactors, outputCommitmentBf.data());
                randombytes_set_implementation(NULL);

                THEN("The computed blinding factors should match the expected blinding factors")
                {
                    bool is_equal_bf1 = sodium_memcmp(computed_blindingFactors[0].data(), expected_blindingFactors[0].data(), 32) == 0;
                    bool is_equal_bf2 = sodium_memcmp(computed_blindingFactors[1].data(), expected_blindingFactors[1].data(), 32) == 0;
                    
                    cout << "Test case " << line_count << ":" << endl;
                    cout << "Input output_blindingfactor: ";
                    print_hex(outputCommitmentBf.data(), 32);
                    cout << "Computed blinding factor 1: ";
                    print_hex(computed_blindingFactors[0].data(), 32);
                    cout << "Expected blinding factor 1: ";
                    print_hex(expected_blindingFactors[0].data(), 32);
                    cout << "Computed blinding factor 2: ";
                    print_hex(computed_blindingFactors[1].data(), 32);
                    cout << "Expected blinding factor 2: ";
                    print_hex(expected_blindingFactors[1].data(), 32);
                    cout << endl;

                    if (!is_equal_bf1 || !is_equal_bf2)
                    {
                        cout << "Actual and expected output does not match" << endl;
                    }
                    
                    REQUIRE(is_equal_bf1);
                    REQUIRE(is_equal_bf2);
                }
            }
        }

        infile.close();
        outfile.close();

        // Debugging output for total lines processed
        cout << "Total lines processed: " << line_count << endl;
    }
}
