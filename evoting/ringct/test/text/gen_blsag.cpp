#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include "../test_util.h"

void gen_blsag_simple_file(const std::string &output_file, const std::string &signer_input_file, const std::string &decoy_input_file)
{
    std::ifstream infile_signer(signer_input_file);
    std::ifstream infile_decoy(decoy_input_file);
    std::ofstream outfile(output_file);

    try
    {
        if (infile_signer.is_open() && infile_decoy.is_open() && outfile.is_open())
        {
            std::string skS, skV, rG, pkV, pkS, pk, computed_sk, key_image_hex, r;
            StealthAddress signerSA, decoySA;

            // Loop over each line in the input files
            while (infile_signer >> skS >> skV >> rG >> pkV >> pkS >> pk >> computed_sk >> key_image_hex)
            {
                // Initialize the BLSAG signature structure
                blsagSig blsag;
                std::vector<StealthAddress> decoySA_vector; // Initialize an empty vector for each line

                hex_to_bytearray(signerSA.rG, rG);
                hex_to_bytearray(signerSA.pk, pk);

                // Set the SK if it's valid
                if (computed_sk != "N/A") {
                    BYTE sk[32];
                    hex_to_bytearray(sk, computed_sk);
                    signerSA.set_stealth_address_secretkey(sk);
                    std::cout << "SK set for valid stealth address" << std::endl;
                }

                // Convert the key image from hex to byte array and store it in the BLSAG signature
                hex_to_bytearray(blsag.key_image, key_image_hex);  // Use the key image from the input file

                // Read the decoy data (without secret key)
                if (infile_decoy >> pkS >> pkV >> skS >> skV >> r >> rG >> pk)
                {
                    hex_to_bytearray(decoySA.rG, rG);
                    hex_to_bytearray(decoySA.pk, pk);
                }

                // Initialize the decoy vector 9 times with the same decoy
                for (int i = 0; i < 10; ++i)
                {
                    decoySA_vector.push_back(decoySA);
                }

                // Add the signer as the 10th element
                size_t secret_index = decoySA_vector.size();

                // Generate the message m
                BYTE m[crypto_core_ed25519_BYTES];
                memset(m, 0xAA, sizeof(m)); // Example data

                memset(fixed_random_seed, 0x3c, sizeof(fixed_random_seed)); // you can set whatever you want for the seed
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                // Generate the BLSAG signature using the provided key image
                blsag_simple_gen(blsag, m, secret_index, signerSA, decoySA_vector);

                randombytes_set_implementation(NULL);


                // Write the key image, challenge, and responses to the output file in a straightforward format
                std::string key_image_str, challenge_str;
                to_string(key_image_str, blsag.key_image, crypto_core_ed25519_BYTES);
                to_string(challenge_str, blsag.c, crypto_core_ed25519_SCALARBYTES);

                outfile << key_image_str << " " << challenge_str;
                for (size_t i = 0; i < blsag.r.size(); ++i)
                {
                    std::string response_str;
                    to_string(response_str, blsag.r[i].data(), crypto_core_ed25519_SCALARBYTES);
                    outfile << " " << response_str;
                }
                outfile << "\n"; // End the line after each complete output
            }

            infile_signer.close();
            infile_decoy.close();
            outfile.close();
        }
        else
        {
            std::cerr << "Unable to open one or more files" << std::endl;
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << e.what() << std::endl;
    }
}
