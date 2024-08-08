#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_commitment_mask_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            string pkS, pkV, skS, skV, r, rG, pk;
            while (infile >> pkS >> pkV >> skS >> skV >> r >> rG >> pk)
            {
                BYTE r_bytes[32];
                BYTE pkv_bytes[32];
                BYTE yt[32];

                hex_to_bytearray(r_bytes, r);
                hex_to_bytearray(pkv_bytes, pkV);

                // Compute commitment mask with index 0
                compute_commitment_mask(yt, r_bytes, pkv_bytes, 0);

                string yt_hex;
                to_string(yt_hex, yt, 32);

                outfile << r << " " << pkV << " " << yt_hex << "\n";
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
        cerr << "Exception: " << e.what() << endl;
    }
}

