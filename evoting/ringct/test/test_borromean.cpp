#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <vector>
#include <bitset>

using namespace std;

SCENARIO("Test regeneration and validation of Borromean ring signatures based on blinding factors and C1C2 data", "[borromean]") {
    const string blinding_factors_file = filesystem::absolute("/app/test/text/blinding_factor.txt"); 
    const string C1C2_file = filesystem::absolute("/app/test/text/c1c2.txt");
    const string expected_output_file = filesystem::absolute("/app/test/text/borromean.txt"); 

    cout << "Blinding factors file: " << blinding_factors_file << endl;
    cout << "C1C2 file: " << C1C2_file << endl;
    cout << "Expected output file: " << expected_output_file << endl;

    GIVEN("The blinding factors and C1C2 input files and the expected output") {
        ifstream infile_C1C2(C1C2_file);
        ifstream expected_output(expected_output_file);
        ifstream infile_bf(blinding_factors_file);
        REQUIRE(infile_bf.is_open());
        REQUIRE(infile_C1C2.is_open());
        REQUIRE(expected_output.is_open());

        string bf_line, C1C2_line, expected_line;
        int line_count = 0;

        while (getline(infile_bf, bf_line) && getline(infile_C1C2, C1C2_line) && getline(expected_output, expected_line)) {
            line_count++;
            WHEN("Processing line " + to_string(line_count)) {
                auto bf_components = tokeniser(bf_line, ' ');
                auto C1C2_components = tokeniser(C1C2_line, ' ');
                auto expected_components = tokeniser(expected_line, ' ');

                // Ensure the correct number of components are present
                REQUIRE(bf_components.size() == 2);
                REQUIRE(C1C2_components.size() == 16);
                REQUIRE(expected_components.size() == 17);  // 1 bbee + 8 pairs of bbs0 and bbs1

                // Initialize variables from input components
                array<BYTE, crypto_core_ed25519_SCALARBYTES> x;
                vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8), C2(8);
                hex_to_bytearray(x.data(), bf_components[0]);

                // Assuming C1C2_components are alternately C1 and C2
                for (int i = 0; i < 8; i++) {
                    hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
                    hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
                }

                // Generate Borromean ring signature
                BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8), bbs1(8);

                // Set the deterministic random seed and counter just before calling generate_Borromean
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed)); // Matching the seed with generation file
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                bitset<8> indices(static_cast<unsigned long>(30)); // Hardcoding amount to 30 to match generation file
                generate_Borromean({x}, C1, C2, indices, bbee, bbs0, bbs1);

                // Reset the random implementation to default
                randombytes_set_implementation(NULL);

                // Convert results to strings for comparison
                vector<string> regenerated_components;
                string component_str;
                to_string(component_str, bbee, crypto_core_ed25519_SCALARBYTES);
                regenerated_components.push_back(component_str);

                for (int i = 0; i < 8; i++) {
                    to_string(component_str, bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                    regenerated_components.push_back(component_str);
                    to_string(component_str, bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                    regenerated_components.push_back(component_str);
                }

                THEN("the regenerated output should match the expected output") {
                    REQUIRE(regenerated_components.size() == expected_components.size());
                    for (size_t i = 0; i < expected_components.size(); ++i) {
                        REQUIRE(regenerated_components[i] == expected_components[i]);
                    }
                }
            }
        }
    }
}
