#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include "../test_util.h"

void gen_rangeproof_file(const string &output_file, const string &commitment_input_file)
{
    ifstream infile(commitment_input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input file: " << commitment_input_file << endl;
            cout << "Successfully opened output file: " << output_file << endl;

            string amount_mask_str, output_blindingfactor_mask, pseudo_output_blindingfactor_mask;
            string output_commitment_str, pseudo_output_commitment_str, output_blindingfactor_str;
            int line_count = 0;

            while (infile >> amount_mask_str >> output_blindingfactor_mask >> pseudo_output_blindingfactor_mask 
                   >> output_commitment_str >> pseudo_output_commitment_str >> output_blindingfactor_str)
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Convert commitment data to Commitment structure
                    Commitment commitment;
                    hex_to_bytearray(commitment.output_blindingfactor, output_blindingfactor_str);

                    array<BYTE, 32> output_commitment;
                    hex_to_bytearray(output_commitment.data(), output_commitment_str);
                    commitment.outputs_commitments.push_back(output_commitment);

                    // Set bits to represent the value 30
                    uint8_t amount = 30;
                    bitset<8> bits(amount);

                    // Set random seed for deterministic behavior
                    memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                    counter = 0;
                    randombytes_set_implementation(&deterministic_implementation);

                    // Generate range proof
                    RangeProof rp;
                    rangeproof(rp, commitment, commitment.output_blindingfactor);

                    // Reset random implementation to default after proof generation
                    randombytes_set_implementation(NULL);
                    
                    // Convert rangeproof to string and write to output file
                    string bbee_str;
                    vector<string> bbs0_str(8), bbs1_str(8), C1_str(8), C2_str(8);

                    to_string(bbee_str, rp.bbee, crypto_core_ed25519_SCALARBYTES);
                    outfile << bbee_str << " ";

                    for (int i = 0; i < 8; ++i) {
                        to_string(bbs0_str[i], rp.bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                        to_string(bbs1_str[i], rp.bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                        to_string(C1_str[i], rp.C1[i].data(), crypto_core_ed25519_BYTES);
                        to_string(C2_str[i], rp.C2[i].data(), crypto_core_ed25519_BYTES);

                        outfile << bbs0_str[i] << " " << bbs1_str[i] << " " << C1_str[i] << " " << C2_str[i] << " ";
                    }
                    outfile << "\n";

                    cout << "Line " << line_count << " processed and written to output file" << endl;
                }
                catch (const exception &e)
                {
                    cerr << "Error processing line " << line_count << ": " << e.what() << endl;
                }
            }

            infile.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "Range proofs generated and written to " << output_file << endl;
        }
        else
        {
            cerr << "Failed to open input or output file" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
