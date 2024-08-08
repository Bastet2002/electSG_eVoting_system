#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include <bitset>
#include <vector>
#include "../test_util.h"

void gen_compute_C1C2_file(const string &output_file, const string &blinding_factors_file)
{
    ifstream infile_bf(blinding_factors_file);
    ofstream outfile(output_file);

    try
    {
        if (infile_bf.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input file: " << blinding_factors_file << endl;
            cout << "Successfully opened output file: " << output_file << endl;

            string bf1_str, bf2_str;
            int line_count = 0;

            while (infile_bf >> bf1_str >> bf2_str)
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Convert blinding factors to BYTE arrays
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> blindingFactors(8);
                    hex_to_bytearray(blindingFactors[0].data(), bf1_str);
                    hex_to_bytearray(blindingFactors[1].data(), bf2_str);

                    // Hardcode the amount to 30
                    uint8_t amount = 30;
                    bitset<8> bits(amount);

                    // Create vectors for C1 and C2
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8);
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);

                    // Generate C1 and C2
                    generateC1C2(blindingFactors, bits, C1, C2);

                    // Convert C1 and C2 to strings and write to output file
                    for (int i = 0; i < 8; ++i) {
                        string C1_str, C2_str;
                        to_string(C1_str, C1[i].data(), crypto_core_ed25519_BYTES);
                        to_string(C2_str, C2[i].data(), crypto_core_ed25519_BYTES);
                        outfile << C1_str << " " << C2_str << " ";
                    }
                    outfile << "\n";

                    cout << "Line " << line_count << " processed and written to output file" << endl;
                }
                catch (const exception &e)
                {
                    cerr << "Error processing line " << line_count << ": " << e.what() << endl;
                }
            }

            infile_bf.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "C1 and C2 values computed and written to " << output_file << endl;
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
