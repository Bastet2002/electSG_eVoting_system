#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>
#include <bitset>
#include <cstdio>

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

SCENARIO("Test the computation of C1 and C2 values based on blinding factors", "[compute_C1C2]") {
    GIVEN("A set of blinding factors and the expected C1 and C2 values") {
        // Define the paths to the input and expected output files
        const string test_blinding_factors_file = "/app/test/text/blinding_factor.txt";
        const string expected_output_file = "/app/test/text/c1c2.txt";

        // Prepare the input file with blinding factors
        ifstream infile_bf(test_blinding_factors_file);
        ifstream expected_file(expected_output_file);
        REQUIRE(infile_bf.is_open());
        REQUIRE(expected_file.is_open());

        string bf1_str, bf2_str;
        string expected_line;
        int line_count = 0;

        // Define the amount (hardcoded as 30)
        uint8_t amount = 30;
        bitset<8> bits(amount);

        while (infile_bf >> bf1_str >> bf2_str && getline(expected_file, expected_line)) {
            line_count++;
            
            WHEN("THe generateC1C2 function is called and compared to the expected output " + to_string(line_count)) {
                // Convert blinding factors to BYTE arrays
                vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> blindingFactors(8);
                hex_to_bytearray(blindingFactors[0].data(), bf1_str);
                hex_to_bytearray(blindingFactors[1].data(), bf2_str);

                // Create vectors for C1 and C2
                vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8);
                vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);

                // Generate C1 and C2
                generateC1C2(blindingFactors, bits, C1, C2);

                // Convert C1 and C2 to strings for comparison
                vector<string> computed_components;
                for (int i = 0; i < 8; ++i) {
                    string C1_str, C2_str;
                    to_string(C1_str, C1[i].data(), crypto_core_ed25519_BYTES);
                    to_string(C2_str, C2[i].data(), crypto_core_ed25519_BYTES);
                    computed_components.push_back(C1_str);
                    computed_components.push_back(C2_str);
                }

                // Split the expected line into components
                auto expected_components = split_string(expected_line);
                REQUIRE(computed_components.size() == expected_components.size());

                THEN("The computed C1 and C2 values should match the expected values") {
                    for (size_t i = 0; i < computed_components.size(); ++i) {
                        REQUIRE(computed_components[i] == expected_components[i]);
                    }

                    // Output debugging information
                    cout << "Test case " << line_count << ":" << endl;
                    cout << "Computed C1 and C2 values:" << endl;
                    for (const auto& comp : computed_components) {
                        cout << comp << " ";
                    }
                    cout << endl;
                    cout << "Expected C1 and C2 values:" << endl;
                    for (const auto& exp : expected_components) {
                        cout << exp << " ";
                    }
                    cout << endl;
                }
            }
        }

        infile_bf.close();
        expected_file.close();

        // Debugging output for total lines processed
        cout << "Total lines processed: " << line_count << endl;
    }
}
