#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

/*
template

// normal test case without BDD
TEST_CASE( "test case", "[tag]" ) {
    SECTION( "section" ) {
        // Arrange
        int var = 5;
        REQUIRE( var == 5 );

        // Action
        var = 10;

        // Assert
        REQUIRE( var == 10 );
    }
}


// Behaviour-driven development
SCENARIO( "test case scenario ", "[tag]" ) {
    GIVEN( "Given the arranged variable" ) {

        // Arrange variables with assertions
        var = 5
        REQUIRE( var == 5 );

        WHEN( "When the action is taken" ) {
            // var will be reinitiated in every when block
            // you can also nested when block

            // Action
            var = 10

            THEN( "Then the expected result should be" ) {
                // Assert
                REQUIRE( var == 10 );
            }
        }
    }
}
*/

vector<string> tokeniser(const string &aline, const char delimeter = ' ')
{
    vector<string> tokens;
    string token;
    istringstream input(aline);
    while (getline(input, token, delimeter))
    {
        tokens.push_back(token);
    }
    return tokens;
}

SCENARIO("Test the consistency of the hash to point function", "[hash]")
{
    // base hex string of variety length for use
    const string base_file = filesystem::absolute("./test/text/hash_infile");
    // contain expected output
    const string h2p_file = filesystem::absolute("./test/text/h2p.txt");

    GIVEN("Any inputs to the hash to point function")
    {
        ifstream infile(base_file);

        REQUIRE(infile.is_open());

        string aline;
        int i = 0;
        while (getline(infile, aline))
        {
            vector<BYTE> input_hex_byte;
            input_hex_byte.resize(aline.size() / 2);

            if (aline == "x")
            {
                input_hex_byte.resize(1);
                hex_to_bytearray(input_hex_byte.data(), "00");
            }
            else
            {
                hex_to_bytearray(input_hex_byte.data(), aline);
            }
            i++;
            // if you need to loop, you will need to provide different name for the when block
            WHEN("it produces the output point " + to_string(i))
            {
                BYTE h2p[32];
                hash_to_point(h2p, input_hex_byte.data(), input_hex_byte.size());

                THEN("the output should lies within the curve ed25519")
                {
                    REQUIRE(crypto_core_ed25519_is_valid_point(h2p) == 1);
                }

                WHEN("the same input is recomputed again " + to_string(i))
                {
                    BYTE h2p_recomputed[32];
                    hash_to_point(h2p_recomputed, input_hex_byte.data(), input_hex_byte.size());
                    THEN("both outputs should be equal")
                    {
                        REQUIRE(sodium_memcmp(h2p, h2p_recomputed, 32) == 0);
                    }
                }
            }
        }
    }

    GIVEN("The actual output should match the expected input")
    {
        ifstream infile(h2p_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            BYTE expected[32];
            hex_to_bytearray(expected, tokens[0]);
            i++;

            vector<BYTE> input_hex_byte;
            input_hex_byte.resize(tokens[1].size() / 2);
            if (tokens[1] == "x")
            {
                input_hex_byte.resize(0);
            }
            else
            {
                hex_to_bytearray(input_hex_byte.data(), tokens[1]);
            }

            WHEN("the known input is passed to the function" + to_string(i))
            {
                BYTE actual[32];
                hash_to_point(actual, input_hex_byte.data(), input_hex_byte.size());

                THEN("the expected output is matched with output")
                {
                    bool is_equal = sodium_memcmp(actual, expected, 32) == 0;
                    if (!is_equal)
                    {
                        cout << "Actual and expected output does not match" << endl;
                        cout << "String: " << tokens[1] << endl;
                        print_hex(actual, 32);
                        print_hex(expected, 32);
                    }
                    REQUIRE(is_equal);
                }
            }
        }
    }
}
