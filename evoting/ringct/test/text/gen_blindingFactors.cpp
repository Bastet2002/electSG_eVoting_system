#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_blinding_factors_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input file: " << input_file << endl;
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
                    // Convert output commitment blinding factor to BYTE array
                    array<BYTE, 32> outputCommitmentBf;
                    hex_to_bytearray(outputCommitmentBf.data(), output_blindingfactor_str);

                    // Create vector of blinding factors (assuming 2 commitments: output and pseudo-output)
                    vector<array<BYTE, 32>> blindingFactors(2);

                    // Generate blinding factors
                    memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                    counter = 0;
                    randombytes_set_implementation(&deterministic_implementation);
                    generateBlindingFactors(blindingFactors, outputCommitmentBf.data());
                    randombytes_set_implementation(NULL);

                    // Convert blinding factors to strings and write to output file
                    string bf1_str, bf2_str;
                    to_string(bf1_str, blindingFactors[0].data(), 32);
                    to_string(bf2_str, blindingFactors[1].data(), 32);

                    outfile << bf1_str << " " << bf2_str << "\n";

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
            cout << "Blinding factors computed and written to " << output_file << endl;
        }
        else
        {
            cerr << "Failed to open one or more input files or the output file" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
