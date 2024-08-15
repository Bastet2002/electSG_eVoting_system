#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the XOR_amount_mask_signer function", "[XOR_amount_mask_signer]")
{
    const string test_cases_file = filesystem::absolute("/app/test/text/XOR_signer.txt");

    GIVEN("A set of inputs and expected outputs for testing the XOR amout mask Signer")
    {
        ifstream infile(test_cases_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            REQUIRE(tokens.size() == 3); // out_hex, r, pkV

            string out_hex = tokens[0];
            string r = tokens[1];
            string pkV = tokens[2];

            // Create User object
            User receiver(pkV, ""); // pkV

            // Create StealthAddress object
            StealthAddress sa;
            hex_to_bytearray(sa.r, r);

            size_t t = 0;

            // Generate input based on vote_currency
            BYTE b[32];
            int_to_scalar_BYTE(b, vote_currency);
            BYTE in[8];
            memcpy(in, b, 8);  // We only need the first 8 bytes

            i++;

            WHEN("The XOR_amount_mask_signer is called and compared to the expected outputs " + to_string(i))
            {
                // Call function
                BYTE out[8];
                XOR_amount_mask_signer(out, in, t, sa, receiver);

                // Convert output to hex string
                string computed_out_hex;
                to_string(computed_out_hex, out, 8);

                // Debug output
                cout << "Test case " << i << ":" << endl;
                cout << "Input r: " << r << endl;
                cout << "Input pkV: " << pkV << endl;
                cout << "Computed out: " << computed_out_hex << endl;
                cout << "Expected out: " << out_hex << endl;
                cout << endl;

                THEN("The generated output should match the expected outputs")
                {
                    REQUIRE(computed_out_hex == out_hex);


                }
            }
        }
    }
}
