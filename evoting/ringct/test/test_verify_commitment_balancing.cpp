#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test commitment balancing for all stealth addresses", "[commitment_balancing]")
{
    const string stealth_address_file = filesystem::absolute("/app/test/text/stealth_address.txt");
    const string output_file = filesystem::absolute("/app/test/text/commitment_balancing.txt");

    GIVEN("The actual output should match the expected input")
    {
        REQUIRE(filesystem::exists(stealth_address_file));
        REQUIRE(filesystem::exists(output_file));

        ifstream sa_file(stealth_address_file);
        ifstream outfile(output_file);
        REQUIRE(sa_file.is_open());
        REQUIRE(outfile.is_open());

        BYTE H_point[32];
        generate_H(H_point);

        string aline;
        int i = 0;

        while (getline(sa_file, aline))
        {
            vector<string> tokens = tokeniser(aline);

            REQUIRE(tokens.size() == 7); // pkS, pkV, skS, skV, r, rG, pk

            string pkS = tokens[0];
            string pkV = tokens[1];
            string skS = tokens[2];
            string skV = tokens[3];
            string r = tokens[4];
            string rG = tokens[5];
            string pk = tokens[6];

            string output_line;
            REQUIRE(getline(outfile, output_line));

            i++;

            WHEN("the known input is passed to the function for case " + to_string(i))
            {
                Commitment commitment;
                BYTE b[32];
                int amount = 1; // You can adjust this as needed
                int_to_scalar_BYTE(b, static_cast<int>(amount));

                // Compute output commitment
                array<BYTE, 32> yt;
                array<BYTE, 32> output_commitment;
                BYTE r_bytes[32], pkv_bytes[32];
                hex_to_bytearray(r_bytes, r);
                hex_to_bytearray(pkv_bytes, pkV);

                compute_commitment_mask(yt.data(), r_bytes, pkv_bytes, 0);
                commitment.outputs_blindingfactor_masks.push_back(yt);
                add_key(output_commitment.data(), yt.data(), b, H_point);
                commitment.outputs_commitments.push_back(output_commitment);
                memcpy(commitment.output_blindingfactor, yt.data(), 32);

                // Compute pseudo-output commitment
                array<BYTE, 32> pseudoout_commitment;
                commitment.pseudoouts_blindingfactor_masks.resize(1);
                generatePseudoBfs(commitment.pseudoouts_blindingfactor_masks, commitment.outputs_blindingfactor_masks);

                add_key(pseudoout_commitment.data(), commitment.pseudoouts_blindingfactor_masks[0].data(), b, H_point);
                commitment.pseudoouts_commitments.push_back(pseudoout_commitment);

                THEN("the expected output is matched with the computed output")
                {
                    bool is_balanced = verify_commitment_balancing(commitment.outputs_commitments, commitment.pseudoouts_commitments);
                    
                    cout << "Test case " << i << ":" << endl;
                    cout << "Input r: " << r << endl;
                    cout << "Input pkV: " << pkV << endl;
                    cout << "Output Commitment: ";
                    print_hex(commitment.outputs_commitments[0].data(), 32);
                    cout << "Pseudo-Output Commitment: ";
                    print_hex(commitment.pseudoouts_commitments[0].data(), 32);
                    cout << "Computed balance: " << (is_balanced ? "Balanced" : "Not Balanced") << endl;
                    cout << "Expected output: " << output_line << endl;
                    cout << endl;

                    string expected_output = "Test Case " + to_string(i) + ": Balanced";
                    bool output_matches = (output_line == expected_output);

                    if (!is_balanced || !output_matches)
                    {
                        cout << "Actual and expected output does not match" << endl;
                    }
                    
                    REQUIRE(is_balanced);
                    REQUIRE(output_matches);
                }
            }
        }

        sa_file.close();
        outfile.close();
    }
}
