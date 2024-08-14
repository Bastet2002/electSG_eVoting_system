#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <bitset>
#include "../test_util.h"

// Function to split a string by spaces
std::vector<std::string> split_string(const std::string& str) {
    std::vector<std::string> result;
    std::istringstream iss(str);
    std::string token;
    while (iss >> token) {
        result.push_back(token);
    }
    return result;
}

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

            string bf_str;
            string C1C2_str;
            int line_count = 0;

            while (getline(infile_bf, bf_str) && getline(infile_C1C2, C1C2_str))
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Split the input strings into components
                    auto bf_components = split_string(bf_str);
                    auto C1C2_components = split_string(C1C2_str);

                    // Debugging output for component counts
                    cout << "bf_components: " << bf_components.size() << endl;
                    cout << "C1C2_components: " << C1C2_components.size() << endl;

                    // Ensure each component has the expected length
                    if (bf_components.size() != 2 || C1C2_components.size() != 16) {
                        throw std::invalid_argument("Incorrect number of components in input strings");
                    }

                    // Convert blinding factor to BYTE array
                    array<BYTE, crypto_core_ed25519_SCALARBYTES> x;
                    hex_to_bytearray(x.data(), bf_components[0]);

                    // Convert C1 and C2 to BYTE arrays
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8);
                    vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);
                    for (int i = 0; i < 8; ++i) {
                        hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
                        hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
                    }

                    // Hardcode the amount to 30, and set indices accordingly
                    uint8_t amount = 30;
                    bitset<8> indices(amount);

                    // Prepare output variables
                    BYTE bbee[crypto_core_ed25519_SCALARBYTES];
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8);
                    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs1(8);

                    // Generate Borromean ring signature
                    memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed)); // you can set whatever you want for the seed
                    counter = 0;
                    randombytes_set_implementation(&deterministic_implementation);
                    generate_Borromean({x}, C1, C2, indices, bbee, bbs0, bbs1);
                    randombytes_set_implementation(NULL);

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
