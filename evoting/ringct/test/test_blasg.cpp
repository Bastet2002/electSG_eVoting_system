#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <vector>
#include <sstream>

using namespace std;

SCENARIO ("Test generation and validation of BLSAG signatures based on key images, challenges, and responses", "[blsag]"){
    GIVEN("random voter and random decoy members") {
        for (size_t i = 0; i < 100; ++i) {
            WHEN("The BLSAG signature is generated and verified " + to_string(i)){
                cout << "Test " << i << ": ";
                StealthAddress voter_sa; 
                blsagSig blsag;
                User voter;
                compute_stealth_address(voter_sa, voter);
                receiver_test_stealth_address(voter_sa, voter);
                compute_key_image(blsag, voter_sa);

                vector<User> decoy_members{10};
                vector<StealthAddress> decoy_sa;
                CA_generate_address(decoy_sa, decoy_members);

                BYTE m[32];
                crypto_core_ed25519_scalar_random(m);

                cout << "decoy number seized: " << decoy_members.size() << endl;
                int secret_index = secret_index_gen(decoy_members.size());

                cout << "secret index: " << secret_index << endl;
                blsag_simple_gen(blsag, m, secret_index, voter_sa, decoy_sa);
                THEN("The verification should pass"){
                    REQUIRE(blsag_simple_verify(blsag, m));
                }
            }
        }
    }
}



// SCENARIO("Test generation and validation of BLSAG signatures based on key images, challenges, and responses", "[blsag]") {
//     const string signer_input_file = filesystem::absolute("/app/test/text/key_image.txt"); 
//     const string decoy_input_file = filesystem::absolute("/app/test/text/stealth_address_decoy.txt");
//     const string expected_output_file = filesystem::absolute("/app/test/text/blsag_signature.txt");

//     cout << "Signer input file: " << signer_input_file << endl;
//     cout << "Decoy input file: " << decoy_input_file << endl;
//     cout << "Expected output file: " << expected_output_file << endl;

//     GIVEN("The signer and decoy input files to generate BLSAG signatures") {
//         ifstream infile_signer(signer_input_file);
//         ifstream infile_decoy(decoy_input_file);
//         ifstream infile_expected_output(expected_output_file);

//         REQUIRE(infile_signer.is_open());
//         REQUIRE(infile_decoy.is_open());
//         REQUIRE(infile_expected_output.is_open());

//         vector<string> expected_outputs;
//         string expected_output_line;

//         // Read all expected output lines into a vector
//         while (getline(infile_expected_output, expected_output_line)) {
//             expected_outputs.push_back(expected_output_line);
//         }

//         string skS, skV, rG, pkV, pkS, pk, computed_sk, key_image_hex, r;
//         int line_count = 0;

//         while (getline(infile_signer, skS, ' ') && getline(infile_signer, skV, ' ') && 
//                getline(infile_signer, rG, ' ') && getline(infile_signer, pkV, ' ') && 
//                getline(infile_signer, pkS, ' ') && getline(infile_signer, pk, ' ') && 
//                getline(infile_signer, computed_sk, ' ') && getline(infile_signer, key_image_hex)) {
//             line_count++;

//             // Make sure we don't exceed the expected output count
//             REQUIRE(line_count <= expected_outputs.size());

//             WHEN("The BLSAG signature is generated and compared to the expected output for line " + to_string(line_count)) {
//                 // Initialize the BLSAG signature structure
//                 blsagSig blsag;
//                 StealthAddress signerSA, decoySA;
//                 vector<StealthAddress> decoySA_vector;

//                 hex_to_bytearray(signerSA.rG, rG);
//                 hex_to_bytearray(signerSA.pk, pk);

//                 // Set the SK if it's valid
//                 if (computed_sk != "N/A") {
//                     BYTE sk[32];
//                     hex_to_bytearray(sk, computed_sk);
//                     signerSA.set_stealth_address_secretkey(sk);
//                     cout << "SK set for valid stealth address" << endl;
//                 }

//                 // Convert the key image from hex to byte array and store it in the BLSAG signature
//                 hex_to_bytearray(blsag.key_image, key_image_hex);

//                 // Read the decoy data (without secret key)
//                 REQUIRE(getline(infile_decoy, pkS, ' '));
//                 REQUIRE(getline(infile_decoy, pkV, ' '));
//                 REQUIRE(getline(infile_decoy, skS, ' '));
//                 REQUIRE(getline(infile_decoy, skV, ' '));
//                 REQUIRE(getline(infile_decoy, r, ' '));
//                 REQUIRE(getline(infile_decoy, rG, ' '));
//                 REQUIRE(getline(infile_decoy, pk));

//                 hex_to_bytearray(decoySA.rG, rG);
//                 hex_to_bytearray(decoySA.pk, pk);

//                 // Initialize the decoy vector 9 times with the same decoy
//                 for (int i = 0; i < 10; ++i) {
//                     decoySA_vector.push_back(decoySA);
//                 }

//                 // Add the signer as the 10th element
//                 size_t secret_index = decoySA_vector.size();

//                 // Generate the message m
//                 BYTE m[crypto_core_ed25519_BYTES];
//                 memset(m, 0xAA, sizeof(m)); // Example data

//                 // Set deterministic random seed for reproducible tests
//                 memset(fixed_random_seed, 0x3c, sizeof(fixed_random_seed));
//                 counter = 0;
//                 randombytes_set_implementation(&deterministic_implementation);

//                 // Generate the BLSAG signature using the provided key image
//                 blsag_simple_gen(blsag, m, secret_index, signerSA, decoySA_vector);

//                 // Reset to default random implementation
//                 randombytes_set_implementation(NULL);

//                 THEN("The computed output should match the expected output") {
//                     // Convert the generated output to string format
//                     string key_image_str, challenge_str;
//                     to_string(key_image_str, blsag.key_image, crypto_core_ed25519_BYTES);
//                     to_string(challenge_str, blsag.c, crypto_core_ed25519_SCALARBYTES);

//                     string generated_output = key_image_str + " " + challenge_str;
//                     for (size_t i = 0; i < blsag.r.size(); ++i) {
//                         string response_str;
//                         to_string(response_str, blsag.r[i].data(), crypto_core_ed25519_SCALARBYTES);
//                         generated_output += " " + response_str;
//                     }

//                     // Get the expected output for the current line
//                     string expected_output_line = expected_outputs[line_count - 1];

//                     // Print the generated and expected output lines for comparison
//                     cout << "Generated Output:\n" << generated_output << endl;
//                     cout << "Expected Output:\n" << expected_output_line << endl;

//                     // Ensure the generated output matches the expected output
//                     REQUIRE(generated_output == expected_output_line);
//                 }
//             }
//         }

//         infile_signer.close();
//         infile_decoy.close();
//     }
// }
