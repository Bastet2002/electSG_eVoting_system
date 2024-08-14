#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>

SCENARIO("Test the consistency of the gen_pseudo_bfs_file function", "[pseudo_bfs]")
{
    const string input_file = filesystem::absolute("/app/test/text/commitment_mask.txt");
    const string output_file = filesystem::absolute("/app/test/text/pseudoBF.txt");

    GIVEN("The input file containing r, pkV, and yt values")
    {
        REQUIRE(filesystem::exists(input_file));
        REQUIRE(filesystem::exists(output_file));

        ifstream infile(input_file);
        ifstream outfile(output_file);
        REQUIRE(infile.is_open());
        REQUIRE(outfile.is_open());

        string r, pkV, yt_hex;
        string yt_out, bf_out;
        int case_num = 0;

        while (infile >> r >> pkV >> yt_hex && outfile >> yt_out >> bf_out)
        {
            case_num++;

            WHEN("The generatePseudoBfs function is called for case " + to_string(case_num))
            {
                Commitment commitment;
                
                array<BYTE, 32> yt;
                hex_to_bytearray(yt.data(), yt_hex);
                commitment.outputs_blindingfactor_masks.push_back(yt);
                commitment.pseudoouts_blindingfactor_masks.resize(1);

                // Set up deterministic random number generation
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                generatePseudoBfs(commitment.pseudoouts_blindingfactor_masks, commitment.outputs_blindingfactor_masks);

                // Reset random number generation to default implementation
                randombytes_set_implementation(NULL);

                THEN("The generated pseudo blinding factor should match the expected output")
                {
                    string bf_generated;
                    to_string(bf_generated, commitment.pseudoouts_blindingfactor_masks[0].data(), crypto_core_ed25519_SCALARBYTES);

                    cout << "Test case " << case_num << endl;
                    cout << "Input r: " << r << endl;
                    cout << "Input pkV: " << pkV << endl;
                    cout << "Input yt: " << yt_hex << endl;
                    cout << "Generated bf: " << bf_generated << endl;
                    cout << "Expected bf: " << bf_out << endl;

                    REQUIRE(yt_hex == yt_out);
                    REQUIRE(bf_generated == bf_out);
                }
            }
        }

        infile.close();
        outfile.close();
    }
}
