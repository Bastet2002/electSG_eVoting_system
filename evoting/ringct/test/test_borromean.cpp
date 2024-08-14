#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>
#include <bitset>

using namespace std;

// Helper function to split a string by spaces
std::vector<std::string> split_string(const std::string& str) {
    std::vector<std::string> result;
    std::istringstream iss(str);
    std::string token;
    while (iss >> token) {
        result.push_back(token);
    }
    return result;
}

SCENARIO("Test regeneration and validation of Borromean ring signatures based on blinding factors and C1C2 data", "[borromean]") {
    const string blinding_factors_file = filesystem::absolute("/app/test/text/blinding_factor.txt"); 
    const string C1C2_file = filesystem::absolute("/app/test/text/c1c2.txt");
    const string expected_output_file = filesystem::absolute("/app/test/text/borromean.txt"); 

    GIVEN("The blinding factors and C1C2 input files and the expected output file are accessible") {
        ifstream infile_bf(blinding_factors_file);
        ifstream infile_C1C2(C1C2_file);
        ifstream expected_output(expected_output_file);
        REQUIRE(infile_bf.is_open());
        REQUIRE(infile_C1C2.is_open());
        REQUIRE(expected_output.is_open());

        string bf_line, C1C2_line, expected_line;
        int line_count = 0;

        while (getline(infile_bf, bf_line) && getline(infile_C1C2, C1C2_line) && getline(expected_output, expected_line)) {
            line_count++;
            WHEN("Processing line " + to_string(line_count)) {
                auto bf_components = split_string(bf_line);
                auto C1C2_components = split_string(C1C2_line);
                auto expected_components = split_string(expected_line);

                // Initialize variables from input components
                array<BYTE, crypto_core_ed25519_SCALARBYTES> x;
                vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8), C2(8);
                hex_to_bytearray(x.data(), bf_components[0]); // Assuming the first component of bf_line is x

                // Assuming C1C2_components are alternately C1 and C2
                for (int i = 0; i < 8; i++) {
                    hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
                    hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
                }

                // Generate Borromean ring signature
                BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8), bbs1(8);
                bitset<8> indices(static_cast<unsigned long>(stoi(bf_components[1]))); // Assuming second component of bf_line are indices
                generate_Borromean({x}, C1, C2, indices, bbee, bbs0, bbs1);

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
