#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include <bitset>
#include <vector>
#include "../test_util.h"

void gen_borromean_file(const string &output_file, const string &blinding_factors_file, const string &C1C2_file)
{
    ifstream infile_bf(blinding_factors_file);
    ifstream infile_C1C2(C1C2_file);
    ofstream outfile(output_file);

    try
    {
        if (infile_bf.is_open() && infile_C1C2.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input files and output file" << endl;

            string bf1_str, bf2_str;
            string C1_str, C2_str;
            int line_count = 0;

            while (getline(infile_bf, bf1_str) && getline(infile_bf, bf2_str) &&
                   getline(infile_C1C2, C1_str) && getline(infile_C1C2, C2_str))
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Convert blinding factors to BYTE arrays
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> x(8);
                    hex_to_bytearray(x[0].data(), bf1_str);
                    hex_to_bytearray(x[1].data(), bf2_str);

                    // Convert C1 and C2 to BYTE arrays
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8);
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);
                    for (int i = 0; i < 8; ++i) {
                        hex_to_bytearray(C1[i].data(), C1_str.substr(i * 64, 64));
                        hex_to_bytearray(C2[i].data(), C2_str.substr(i * 64, 64));
                    }

                    // Hardcode the amount to 30, and set indices accordingly
                    uint8_t amount = 30;
                    bitset<8> indices(amount);

                    // Prepare output variables
                    BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8);
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs1(8);

                    // Generate Borromean ring signature
                    generate_Borromean(x, C1, C2, indices, bbee, bbs0, bbs1);

                    // Convert results to strings and write to output file
                    string bbee_str;
                    to_string(bbee_str, bbee, crypto_core_ed25519_SCALARBYTES);
                    outfile << bbee_str << " ";

                    for (int i = 0; i < 8; i++) {
                        string bbs0_str, bbs1_str;
                        to_string(bbs0_str, bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                        to_string(bbs1_str, bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                        outfile << bbs0_str << " " << bbs1_str << " ";
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
            infile_C1C2.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "Borromean signatures generated and written to " << output_file << endl;
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
