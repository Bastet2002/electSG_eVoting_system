#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the compute commitment mask function", "[commitment_mask]")
{
    const string test_cases_file = filesystem::absolute("/app/test/text/commitment_mask.txt");

    GIVEN("A set of inputs and expected outputs for computing the commitment mask")
    {
        ifstream infile(test_cases_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            REQUIRE(tokens.size() == 3); // r, pkV, yt

            string r = tokens[0];
            string pkV = tokens[1];
            string expected_yt = tokens[2];

            BYTE r_bytes[32];
            BYTE pkv_bytes[32];
            BYTE expected_yt_bytes[32];
            hex_to_bytearray(r_bytes, r);
            hex_to_bytearray(pkv_bytes, pkV);
            hex_to_bytearray(expected_yt_bytes, expected_yt);

            i++;

            WHEN("compute_commitment_mask is called with the given r and pkV for case " + to_string(i))
            {
                BYTE computed_yt[32];
                compute_commitment_mask(computed_yt, r_bytes, pkv_bytes, 0);

                THEN("the computed commitment mask should match the expected mask")
                {
                    bool is_equal_yt = sodium_memcmp(computed_yt, expected_yt_bytes, 32) == 0;
                    
                    cout << "Test case " << i << ":" << endl;
                    cout << "Input r: " << r << endl;
                    cout << "Input pkV: " << pkV << endl;
                    cout << "Computed yt: ";
                    print_hex(computed_yt, 32);
                    cout << "Expected yt: ";
                    print_hex(expected_yt_bytes, 32);
                    cout << endl;

                    if (!is_equal_yt)
                    {
                        cout << "Actual and expected output does not match" << endl;
                    }
                    
                    REQUIRE(is_equal_yt);
                }
            }
        }
    }
}
