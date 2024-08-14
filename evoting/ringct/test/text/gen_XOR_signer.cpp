#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_XOR_amount_mask_signer_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);
    const int c = vote_currency;

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            string pkS, pkV, skS, skV, r, rG, pk;
            while (infile >> pkS >> pkV >> skS >> skV >> r >> rG >> pk)
            {
                User receiver(pkV, pkS);

                // Create Stealthaddress
                StealthAddress sa;
                hex_to_bytearray(sa.r, r);
                hex_to_bytearray(sa.rG, rG);
                hex_to_bytearray(sa.pk, pk);

                size_t t = 0;

                // Generate input based on vote_currency
                BYTE b[32];
                int_to_scalar_BYTE(b, vote_currency);
                BYTE in[8];
                memcpy(in, b, 8);  // We only need the first 8 bytes

                // Call function
                BYTE out[8];
                XOR_amount_mask_signer(out, in, t, sa, receiver);

                // Write to file
                string out_hex;
                to_string(out_hex, out, 8);
                
                outfile << out_hex << " " << r << " " << pkV << "\n";
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

