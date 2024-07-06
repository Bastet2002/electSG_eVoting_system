#include "../rct/rctType.h"
#include "../rct/rctOps.h"
// #include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

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

SCENARIO("Test the consistency of the add key function", "[aK+bH]")
{
    const string add_keys_file = filesystem::absolute("/app/test/text/add_keys.txt");

    GIVEN("Any inputs to the add key function")
    {
        ifstream infile(add_keys_file);

        REQUIRE(infile.is_open());

        string aline;
        int i = 0;
        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            vector<vector<BYTE>> input_hex_byte(4, vector<BYTE>(32));
            for (int j = 0; j < input_hex_byte.size(); j++) {
                hex_to_bytearray(input_hex_byte[j].data(), tokens[j+1]);
            }
            i++;
            // if you need to loop, you will need to provide different name for the when block
            WHEN("it produces the output key " + to_string(i))
            {
                BYTE aKbH[32];
                add_key(aKbH, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data(), input_hex_byte[3].data());
                
                THEN("the output should be a valid point on the curve") {
                    REQUIRE(crypto_core_ed25519_is_valid_point(aKbH) == 1);
                }

                WHEN("the same input is recomputed again " + to_string(i))
                {
                    BYTE aKbH_recomputed[32];
                    add_key(aKbH_recomputed, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data(), input_hex_byte[3].data());
                    THEN("both outputs should be equal")
                    {
                        REQUIRE(sodium_memcmp(aKbH, aKbH_recomputed, 32) == 0);
                    }
                }
            }
        }
    }

    GIVEN("The actual output should match the expected input")
    {
        ifstream infile(add_keys_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            BYTE expected[32];
            hex_to_bytearray(expected, tokens[0]);

            vector<vector<BYTE>> input_hex_byte(4, vector<BYTE>(32));
            for (int j = 0; j < input_hex_byte.size(); j++) {
                hex_to_bytearray(input_hex_byte[j].data(), tokens[j+1]);
            }

            i++;

            WHEN("the known input is passed to the function" + to_string(i))
            {
                BYTE actual[32];
                add_key(actual, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data(), input_hex_byte[3].data());

                THEN("the expected output is matched with output")
                {
                    bool is_equal = sodium_memcmp(actual, expected, 32) == 0;
                    if (!is_equal)
                    {
                        cout << "Actual and expected output does not match" << endl;
                        print_hex(actual, 32);
                        print_hex(expected, 32);
                    }
                    REQUIRE(is_equal);
                }
            }
        }
    }
}

SCENARIO("Test the consistency of the add key base function", "[aG+bH]")
{
    const string add_keys_base_file = filesystem::absolute("/app/test/text/add_keys_base.txt");

    GIVEN("Any inputs to the add key base function")
    {
        ifstream infile(add_keys_base_file);

        REQUIRE(infile.is_open());

        string aline;
        int i = 0;
        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            vector<vector<BYTE>> input_hex_byte(3, vector<BYTE>(32));
            for (int j = 0; j < input_hex_byte.size(); j++) {
                hex_to_bytearray(input_hex_byte[j].data(), tokens[j+1]);
            }
            i++;
            // if you need to loop, you will need to provide different name for the when block
            WHEN("it produces the output key " + to_string(i))
            {
                BYTE aGbH[32];
                add_key(aGbH, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data());

                THEN("the output should be a valid point on the curve") {
                    REQUIRE(crypto_core_ed25519_is_valid_point(aGbH) == 1);
                }

                WHEN("the same input is recomputed again " + to_string(i))
                {
                    BYTE aGbH_recomputed[32];
                    add_key(aGbH_recomputed, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data());
                    THEN("both outputs should be equal")
                    {
                        REQUIRE(sodium_memcmp(aGbH, aGbH_recomputed, 32) == 0);
                    }
                }
            }
        }
    }

    GIVEN("The actual output should match the expected input")
    {
        ifstream infile(add_keys_base_file);
        REQUIRE(infile.is_open());

        string aline;
        int i = 0;

        while (getline(infile, aline))
        {
            vector<string> tokens = tokeniser(aline);

            BYTE expected[32];
            hex_to_bytearray(expected, tokens[0]);

            vector<vector<BYTE>> input_hex_byte(3, vector<BYTE>(32));
            for (int j = 0; j < input_hex_byte.size(); j++) {
                hex_to_bytearray(input_hex_byte[j].data(), tokens[j+1]);
            }

            i++;

            WHEN("the known input is passed to the function" + to_string(i))
            {
                BYTE actual[32];
                add_key(actual, input_hex_byte[0].data(), input_hex_byte[1].data(), input_hex_byte[2].data());

                THEN("the expected output is matched with output")
                {
                    bool is_equal = sodium_memcmp(actual, expected, 32) == 0;
                    if (!is_equal)
                    {
                        cout << "Actual and expected output does not match" << endl;
                        print_hex(actual, 32);
                        print_hex(expected, 32);
                    }
                    REQUIRE(is_equal);
                }
            }
        }
    }
}