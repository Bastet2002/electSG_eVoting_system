#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_message_file(const std::string &output_file, const std::string &key_image_file, const std::string &commitment_input_file)
{
    std::ifstream infile_key_image(key_image_file);
    std::ifstream infile_commitment(commitment_input_file);
    std::ofstream outfile(output_file);

    try
    {
        if (infile_key_image.is_open() && infile_commitment.is_open() && outfile.is_open())
        {
            std::cout << "Successfully opened input files and output file" << std::endl;

            std::string skS_str, skV_str, rG_str, pkV_str, pkS_str, pk_str, computed_sk_str, key_image_str;
            std::string pseudout_commitment_str, amount_mask_str, output_blindingfactor_mask_str, output_commitment_str;
            int line_count = 0;

            while (infile_key_image >> skS_str >> skV_str >> rG_str >> pkV_str >> pkS_str >> pk_str >> computed_sk_str >> key_image_str &&
                   infile_commitment >> pseudout_commitment_str >> amount_mask_str >> output_blindingfactor_mask_str >> output_commitment_str)
            {
                line_count++;
                std::cout << "Processing line " << line_count << std::endl;

                try {
                    // Set up StealthAddress using values from the key image file
                    StealthAddress sa;
                    hex_to_bytearray(sa.rG, rG_str);
                    hex_to_bytearray(sa.pk, pk_str);

                    if (computed_sk_str != "N/A") {
                        BYTE sk[32];
                        hex_to_bytearray(sk, computed_sk_str);
                        sa.set_stealth_address_secretkey(sk);
                    }

                    // Set up Commitment using the provided structure
                    Commitment commitment;

                    // Instead of resizing, use push_back
                    array<BYTE, 32> pseudoout_commitment;
                    array<BYTE, 32> output_commitment;
                    array<BYTE, 32> output_blindingfactor_mask;
                    array<BYTE, 8> amount_mask;

                    hex_to_bytearray(pseudoout_commitment.data(), pseudout_commitment_str);
                    hex_to_bytearray(amount_mask.data(), amount_mask_str);
                    hex_to_bytearray(output_blindingfactor_mask.data(), output_blindingfactor_mask_str);
                    hex_to_bytearray(output_commitment.data(), output_commitment_str);

                    // Add elements to the vectors
                    commitment.pseudoouts_commitments.push_back(pseudoout_commitment);
                    commitment.outputs_commitments.push_back(output_commitment);
                    commitment.outputs_blindingfactor_masks.push_back(output_blindingfactor_mask);
                    commitment.amount_masks.push_back(amount_mask);

                    // Set up blsagSig
                    blsagSig blsag;
                    hex_to_bytearray(blsag.key_image, key_image_str);  // Use the key image from the input file

                    // Compute the message
                    compute_message(blsag, sa, commitment);

                    // Convert the result to a string and write to the output file
                    std::string message_str;
                    to_string(message_str, blsag.m, 32);
                    outfile << message_str << "\n";

                    std::cout << "Line " << line_count << " processed and written to output file" << std::endl;
                }
                catch (const std::exception &e)
                {
                    std::cerr << "Error processing line " << line_count << ": " << e.what() << std::endl;
                }
            }

            infile_key_image.close();
            infile_commitment.close();
            outfile.close();

            std::cout << "Processed " << line_count << " lines" << std::endl;
            std::cout << "Messages computed and written to " << output_file << std::endl;
        }
        else
        {
            std::cerr << "Failed to open one or more input files or the output file" << std::endl;
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << "Exception: " << e.what() << std::endl;
    }
}
