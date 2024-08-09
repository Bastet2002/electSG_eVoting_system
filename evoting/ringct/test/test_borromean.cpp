#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <array>
#include "../rct/rctType.h"
#include "../rct/rctOps.h"

using namespace std;

// Function to split a string by spaces
std::vector<std::string> split_string(const std::string& str) {
    std::vector<std::string> result;
    std::istringstream iss(str);
    std::string token;
    while (iss >> token) {
        result.push_back(token);
    }
    return result;
}

SCENARIO("Test the generation of Borromean signatures", "[borromean]") {
    const string blinding_factors_file = "/app/test/text/blinding_factor.txt"; // Path to your existing file
    const string C1C2_file = "/app/test/text/c1c2.txt"; // Path to your existing file
    const string expected_output_file = "/app/test/text/borromean.txt"; // Path for the expected output file

    GIVEN("The input files are correctly formatted") {
        REQUIRE(filesystem::exists(blinding_factors_file));
        REQUIRE(filesystem::exists(C1C2_file));

        WHEN("The generate Borromean function is called") {
            // Initialize necessary variables
            ifstream infile_bf(blinding_factors_file);
            ifstream infile_C1C2(C1C2_file);
            REQUIRE(infile_bf.is_open());
            REQUIRE(infile_C1C2.is_open());

            string bf_str;
            string C1C2_str;
            int line_count = 0;

            vector<vector<string>> all_output_lines; // To store generated output for comparison

            while (getline(infile_bf, bf_str) && getline(infile_C1C2, C1C2_str)) {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Split the input strings into components
                    auto bf_components = split_string(bf_str);
                    auto C1C2_components = split_string(C1C2_str);

                    // Ensure each component has the expected length
                    REQUIRE(bf_components.size() == 2);
                    REQUIRE(C1C2_components.size() == 16);

                    // Convert blinding factor to BYTE array
                    array<BYTE, crypto_core_ed25519_SCALARBYTES> x;
                    hex_to_bytearray(x.data(), bf_components[0]);

                    // Convert C1 and C2 to BYTE arrays
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8);
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);
                    for (int i = 0; i < 8; ++i) {
                        hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
                        hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
                    }

                    // Hardcode the amount to 30, and set indices accordingly
                    uint8_t amount = 30;
                    bitset<8> indices(amount);

                    // Prepare output variables
                    BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8);
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs1(8);

                    // Generate Borromean ring signature
                    generate_Borromean({x}, C1, C2, indices, bbee, bbs0, bbs1);

                    // Convert results to strings and store them for comparison
                    vector<string> output_lines;
                    string bbee_str;
                    to_string(bbee_str, bbee, crypto_core_ed25519_SCALARBYTES);
                    output_lines.push_back(bbee_str); // Store bbee_str

                    for (int i = 0; i < 8; i++) {
                        string bbs0_str, bbs1_str;
                        to_string(bbs0_str, bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                        to_string(bbs1_str, bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                        output_lines.push_back(bbs0_str); // Store bbs0_str
                        output_lines.push_back(bbs1_str); // Store bbs1_str
                    }

                    all_output_lines.push_back(output_lines); // Store the output lines for the current iteration

                    cout << "Line " << line_count << " processed" << endl;
                }
                catch (const exception &e) {
                    cerr << "Error processing line " << line_count << ": " << e.what() << endl;
                }
            }

            infile_bf.close();
            infile_C1C2.close();

            // Now compare the output with the expected values
            REQUIRE(filesystem::exists(expected_output_file));

            ifstream expected_file(expected_output_file);
            REQUIRE(expected_file.is_open());

            string expected_line;
            int expected_line_count = 0;
            while (getline(expected_file, expected_line)) {
                // Split the expected line into components
                auto expected_components = split_string(expected_line);
                
                // Ensure we have enough generated output lines
                REQUIRE(expected_line_count < all_output_lines.size()); // Ensure we don't access out of bounds
                cout << "Comparing Output Line " << expected_line_count + 1 << endl;

                // Get the generated output components for the current line
                auto generated_components = all_output_lines[expected_line_count];

                // Compare each expected component with the corresponding generated component
                REQUIRE(generated_components.size() == expected_components.size()); // Ensure sizes match
                for (size_t i = 0; i < expected_components.size(); ++i) {
                    cout << "Comparing Component " << i + 1 << ": " << generated_components[i] << " with Expected: " << expected_components[i] << endl;
                    REQUIRE(generated_components[i] == expected_components[i]); // Compare each output component with expected component
                }
                
                expected_line_count++;
            }

            REQUIRE(expected_line_count == all_output_lines.size()); // Ensure all output lines have been compared
            expected_file.close();
        }
    }

    // Clean up test files if necessary
    // filesystem::remove(output_file); // Uncomment if you want to delete the output file after testing
}
