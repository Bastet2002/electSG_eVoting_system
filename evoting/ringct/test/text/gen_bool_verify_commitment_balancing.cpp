#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_verify_commitment_balancing_file(const string &output_file, const string &stealth_address_file, const string &bf_file)
{
    ifstream sa_file(stealth_address_file);
    ifstream bf_file_stream(bf_file);
    ofstream outfile(output_file);

    try
    {
        if (sa_file.is_open() && bf_file_stream.is_open() && outfile.is_open())
        {
            vector<array<BYTE, 32>> output_commitments;
            vector<array<BYTE, 32>> pseudo_output_commitments;
            Commitment commitment;

            BYTE H_point[32];
            generate_H(H_point);

            BYTE b[32];
            int_to_scalar_BYTE(b, vote_currency);

            string yt_hex, bf_hex;
            int case_num = 0;

            // Read stealth address information for each case
            string pkS, pkV, skS, skV, r, rG, pk;
            while (sa_file >> pkS >> pkV >> skS >> skV >> r >> rG >> pk && bf_file_stream >> yt_hex >> bf_hex)
            {
                case_num++;

                BYTE r_bytes[32];
                BYTE pkv_bytes[32];
                BYTE yt_computed[32];

                hex_to_bytearray(r_bytes, r);
                hex_to_bytearray(pkv_bytes, pkV);

                // Log the inputs to compute_commitment_mask
                std::string r_hex, pkv_hex;
                to_string(r_hex, r_bytes, 32);
                to_string(pkv_hex, pkv_bytes, 32);
                std::cout << "Case " << case_num << ":" << std::endl;
                std::cout << "r: " << r_hex << std::endl;
                std::cout << "pkV: " << pkv_hex << std::endl;

                // Compute commitment mask with index 0
                compute_commitment_mask(yt_computed, r_bytes, pkv_bytes, 0);

                string yt_computed_hex;
                to_string(yt_computed_hex, yt_computed, 32);

                cout << "Original yt: " << yt_hex << endl;
                cout << "Computed yt: " << yt_computed_hex << endl;

                // Create output commitment using the computed yt
                array<BYTE, 32> output_commitment;
                add_key(output_commitment.data(), yt_computed, b, H_point);
                commitment.outputs_commitments.push_back(output_commitment);
                output_commitments.push_back(output_commitment);

                // Convert bf from hex string to BYTE array
                array<BYTE, 32> bf;
                hex_to_bytearray(bf.data(), bf_hex);
                commitment.pseudoouts_blindingfactor_masks.push_back(bf);

                // Create pseudo-output commitment
                array<BYTE, 32> pseudoout_commitment;
                add_key(pseudoout_commitment.data(), bf.data(), b, H_point);
                commitment.pseudoouts_commitments.push_back(pseudoout_commitment);
                pseudo_output_commitments.push_back(pseudoout_commitment);

                // Verify commitment balancing for this case
                bool is_balanced = verify_commitment_balancing(output_commitments, pseudo_output_commitments);
                outfile << "Test Case " << case_num << ": " << (is_balanced ? "Balanced" : "Not Balanced") << endl;

                // Clear the vectors for the next case
                output_commitments.clear();
                pseudo_output_commitments.clear();
                commitment.outputs_commitments.clear();
                commitment.pseudoouts_commitments.clear();
                commitment.outputs_blindingfactor_masks.clear();
                commitment.pseudoouts_blindingfactor_masks.clear();
            }

            sa_file.close();
            bf_file_stream.close();
            outfile.close();
        }
        else
        {
            cerr << "Unable to open one or more files" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
