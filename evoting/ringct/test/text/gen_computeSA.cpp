#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_stealth_address_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            string aline;
            while (getline(infile, aline))
            {
                vector<BYTE> input_hex_byte;
                input_hex_byte.resize(aline.size() / 2);

                if (aline == "x")
                {
                    input_hex_byte.resize(0);
                }
                else
                {
                    hex_to_bytearray(input_hex_byte.data(), aline);
                }

                User user;

                string pkS, pkV, skS, skV;
                to_string(pkS, user.pkS, 32);
                to_string(pkV, user.pkV, 32);
                to_string(skS, user.skS, 64);
                to_string(skV, user.skV, 64);

                outfile <<  pkS << " " << pkV << " " << skS << " " << skV << " ";

                memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed)); // you can set whatever you want for the seed
                counter = 0;
                randombytes_set_implementation(&deterministic_implementation);

                StealthAddress sa;
                compute_stealth_address(sa, user);

                // clear fixed randomness
                randombytes_set_implementation(NULL);

                string r, rG, pk;
                to_string(r, sa.r, 32);
                to_string(rG, sa.rG, 32);
                to_string(pk, sa.pk, 32);

                outfile <<  r << " " << rG << " " << pk << "\n";
            }
            infile.close();
            outfile.close();
        }
        else
        {
            cerr << "Unable to open file" << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << e.what() << endl;
    }
}
