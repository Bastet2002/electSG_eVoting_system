#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
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
            string bf_str, C1C2_str;
            int line_count = 0;

            while (getline(infile_bf, bf_str) && getline(infile_C1C2, C1C2_str))
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                vector<string> bf_components = tokeniser(bf_str, ' ');
                vector<string> C1C2_components = tokeniser(C1C2_str, ' ');

                if (bf_components.size() != 2 || C1C2_components.size() != 16) {
                    cerr << "Error: Incorrect number of components in input strings at line " << line_count << endl;
                    continue;  // Skip this line and move to the next
                }

                // Convert blinding factors to BYTE arrays
                vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> x(2);
                for (int i = 0; i < 2; ++i) {
                    hex_to_bytearray(x[i].data(), bf_components[i]);
                }

                // Convert C1 and C2 to BYTE arrays
                vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8), C2(8);
                for (int i = 0; i < 8; ++i) {
                    hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
                    hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
                }

                uint8_t amount = 30;
                bitset<8> indices(amount);

                BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8), bbs1(8);

                // Ensure deterministic behavior by setting RNG right before the operation
                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                try {
                    generate_Borromean(x, C1, C2, indices, bbee, bbs0, bbs1);
                } catch (const exception &e) {
                    cerr << "Error generating Borromean signature at line " << line_count << ": " << e.what() << endl;
                    continue;  // Skip this line and move to the next
                }

                // Clear fixed randomness
                randombytes_set_implementation(NULL);

                // Convert and write the result to the output file
                string bbee_str;
                to_string(bbee_str, bbee, crypto_core_ed25519_SCALARBYTES);
                outfile << bbee_str << " ";

                for (int i = 0; i < 8; ++i) {
                    string bbs0_str, bbs1_str;
                    to_string(bbs0_str, bbs0[i].data(), crypto_core_ed25519_SCALARBYTES);
                    to_string(bbs1_str, bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
                    outfile << bbs0_str << " " << bbs1_str << " ";
                }
                outfile << "\n";
                cout << "Line " << line_count << " processed and written to output file" << endl;
            }

            infile_bf.close();
            infile_C1C2.close();
            outfile.close();

            cout << "Finished processing all lines." << endl;
        }
        else
        {
            cerr << "Unable to open input or output file" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
