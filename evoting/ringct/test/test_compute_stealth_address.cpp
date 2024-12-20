#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the compute stealth address function", "[stealth_address]")
{
    const string stealth_address_file = filesystem::absolute("/app/test/text/stealth_address.txt");

    GIVEN("A set of inputs and expected outputs for computing the commitment mask")
    {
        ifstream infile(stealth_address_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            REQUIRE(tokens.size() == 7); // pkS, pkV, skS, skV, r, rG, pk

            string pkS = tokens[0];
            string pkV = tokens[1];
            string skS = tokens[2];
            string skV = tokens[3];
            User user(tokens[1], tokens[0]); // Use the constructor that takes all four parameters

            BYTE expected_r[32];
            BYTE expected_rG[32];
            BYTE expected_pk[32];
            hex_to_bytearray(expected_r, tokens[4]);
            hex_to_bytearray(expected_rG, tokens[5]);
            hex_to_bytearray(expected_pk, tokens[6]);

            i++;

            WHEN("The compute stealth address function is called" + to_string(i))
            {
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                StealthAddress computed_sa;
                compute_stealth_address(computed_sa, user);

                THEN("The computed output should match the expected output")
                {
                    bool is_equal_r = sodium_memcmp(computed_sa.r, expected_r, 32) == 0;
                    bool is_equal_rG = sodium_memcmp(computed_sa.rG, expected_rG, 32) == 0;
                    bool is_equal_pk = sodium_memcmp(computed_sa.pk, expected_pk, 32) == 0;
                    
                    cout << "Test case " << i << ":" << endl;
                    cout << "Input pkS: ";
                    print_hex(user.pkS, 32);
                    cout << "Input pkV: ";
                    print_hex(user.pkV, 32);
                    cout << "Computed r: ";
                    print_hex(computed_sa.r, 32);
                    cout << "Expected r: ";
                    print_hex(expected_r, 32);
                    cout << "Computed rG: ";
                    print_hex(computed_sa.rG, 32);
                    cout << "Expected rG: ";
                    print_hex(expected_rG, 32);
                    cout << "Computed pk: ";
                    print_hex(computed_sa.pk, 32);
                    cout << "Expected pk: ";
                    print_hex(expected_pk, 32);
                    cout << endl;

                    if (!is_equal_rG || !is_equal_pk || !is_equal_r)
                    {
                        cout << "Actual and expected output does not match" << endl;
                    }
                    
                    REQUIRE(is_equal_r);
                    REQUIRE(is_equal_rG);
                    REQUIRE(is_equal_pk);
                }
                randombytes_set_implementation(NULL);
            }
        }
    }
}
