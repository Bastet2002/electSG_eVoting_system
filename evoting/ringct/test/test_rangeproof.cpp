#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <vector>
#include <bitset>

using namespace std;

SCENARIO("Test regeneration and validation of Borromean ring signatures using rangeproof and commitment data", "[rangeproof]") {
    const string rangeproof_output_file = filesystem::absolute("/app/test/text/rangeproof_output.txt"); 
    const string commitment_input_file = filesystem::absolute("/app/test/text/commitment_simple.txt");

    cout << "Rangeproof output file: " << rangeproof_output_file << endl;
    cout << "Commitment input file: " << commitment_input_file << endl;

    GIVEN("The rangeproof and commitment input files are accessible") {
        ifstream infile_rangeproof(rangeproof_output_file);
        ifstream infile_commitment(commitment_input_file);
        REQUIRE(infile_rangeproof.is_open());
        REQUIRE(infile_commitment.is_open());

        string rangeproof_line, commitment_line;
        int line_count = 0;

        while (getline(infile_rangeproof, rangeproof_line) && getline(infile_commitment, commitment_line)) {
            line_count++;
            WHEN("Processing line " + to_string(line_count)) {
                auto rangeproof_components = tokeniser(rangeproof_line, ' ');
                auto commitment_components = tokeniser(commitment_line, ' ');

                // Ensure the correct number of components are present
                REQUIRE(rangeproof_components.size() == 33); // 1 bbee + 8 pairs of bbs0 and bbs1 + 8 C1 + 8 C2
                REQUIRE(commitment_components.size() == 6);

                // Initialize commitment from input components
                Commitment commitment;
                hex_to_bytearray(commitment.output_blindingfactor, commitment_components[5]);

                array<BYTE, 32> output_commitment;
                hex_to_bytearray(output_commitment.data(), commitment_components[3]);
                commitment.outputs_commitments.push_back(output_commitment);

                // Set random seed for deterministic behavior
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                // Generate range proof
                RangeProof rp;
                rangeproof(rp, commitment, commitment.output_blindingfactor);

                // Reset random implementation to default after proof generation
                randombytes_set_implementation(NULL);

                // Convert regenerated rangeproof to strings for comparison
                vector<string> regenerated_components;
                string component_str;
                to_string(component_str, rp.bbee, crypto_core_ed25519_SCALARBYTES);
                regenerated_components.push_back(component_str);
                
                cout << "Generated bbee: " << component_str << endl;

                for (int i = 0; i < 8; ++i) {
                    to_string(component_str, rp.bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                    regenerated_components.push_back(component_str);
                    cout << "Generated bbs0[" << i << "]: " << component_str << endl;

                    to_string(component_str, rp.bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                    regenerated_components.push_back(component_str);
                    cout << "Generated bbs1[" << i << "]: " << component_str << endl;

                    to_string(component_str, rp.C1[i].data(), crypto_core_ed25519_BYTES);
                    regenerated_components.push_back(component_str);
                    cout << "Generated C1[" << i << "]: " << component_str << endl;

                    to_string(component_str, rp.C2[i].data(), crypto_core_ed25519_BYTES);
                    regenerated_components.push_back(component_str);
                    cout << "Generated C2[" << i << "]: " << component_str << endl;
                }

                THEN("the regenerated rangeproof should match the expected rangeproof") {
                    REQUIRE(regenerated_components.size() == rangeproof_components.size());
                    for (size_t i = 0; i < rangeproof_components.size(); ++i) {
                        REQUIRE(regenerated_components[i] == rangeproof_components[i]);
                    }
                }
            }
        }
    }
}
