#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_pseudo_bfs_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            string r, pkV, yt_hex;
            int case_num = 0;

            // Set up deterministic random number generation
            memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
            counter = 0;
            randombytes_set_implementation(&deterministic_implementation);

            while (infile >> r >> pkV >> yt_hex)
            {
                case_num++;
                
                Commitment commitment;
                
                // Step 1 & 2: Create yt and add to outputs_blindingfactor_masks
                array<BYTE, 32> yt;
                hex_to_bytearray(yt.data(), yt_hex);
                commitment.outputs_blindingfactor_masks.push_back(yt);

                // Step 3: Resize pseudoouts_blindingfactor_masks to 1
                commitment.pseudoouts_blindingfactor_masks.resize(1);

                // Step 4: Generate pseudo blinding factors
                generatePseudoBfs(commitment.pseudoouts_blindingfactor_masks, commitment.outputs_blindingfactor_masks);

                // Write results to output file
                string pseudo_bf_hex;
                to_string(pseudo_bf_hex, commitment.pseudoouts_blindingfactor_masks[0].data(), crypto_core_ed25519_SCALARBYTES);
                outfile << yt_hex << " " << pseudo_bf_hex << "\n";
            }

            // Reset random number generation to default implementation
            randombytes_set_implementation(NULL);

            infile.close();
            outfile.close();

            cout << "Generated " << case_num << " test cases in " << output_file << endl;
        }
        else
        {
            cerr << "Unable to open file" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
