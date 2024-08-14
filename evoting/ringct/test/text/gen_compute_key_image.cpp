#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_key_image_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input file: " << input_file << endl;
            cout << "Successfully opened output file: " << output_file << endl;

            string validity, skS, skV, rG, pkV, pkS, pk, computed_sk;
            int line_count = 0;

            while (infile >> validity >> skS >> skV >> rG >> pkV >> pkS >> pk >> computed_sk)
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                // Create StealthAddress object
                StealthAddress sa;
                hex_to_bytearray(sa.rG, rG);
                hex_to_bytearray(sa.pk, pk);

                // Debugging output for input values
                cout << "Validity: " << validity << endl;
                cout << "skS: " << skS << endl;
                cout << "skV: " << skV << endl;
                cout << "rG: " << rG << endl;
                cout << "pkV: " << pkV << endl;
                cout << "pkS: " << pkS << endl;
                cout << "pk: " << pk << endl;
                cout << "Computed SK: " << computed_sk << endl;

                // Set the SK if it's validAV
                if (validity == "valid" && computed_sk != "N/A") {
                    BYTE sk[32];
                    hex_to_bytearray(sk, computed_sk);
                    sa.set_stealth_address_secretkey(sk);
                    cout << "SK set for valid stealth address" << endl;
                }

                // Compute the key image
                blsagSig blsagSig;
                string key_image = "N/A";

                if (validity == "valid" && computed_sk != "N/A") {
                    try
                    {
                        compute_key_image(blsagSig, sa);
                        to_string(key_image, blsagSig.key_image, 32);
                        cout << "Key image computed successfully" << endl;
                    }
                    catch (const exception &e)
                    {
                        cerr << "Failed to compute key image for line " << line_count << ": " << e.what() << endl;
                    }
                } else {
                    cout << "Skipping key image computation for invalid or incomplete stealth address" << endl;
                }

                // Write results to the output file
                outfile << skS << " "
                        << skV << " "
                        << rG << " "
                        << pkV << " "
                        << pkS << " "
                        << pk << " "
                        << computed_sk << " "
                        << key_image << "\n";
                
                cout << "Line " << line_count << " processed and written to output file" << endl;
            }

            infile.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "Key images computed and written to " << output_file << endl;
        }
        else
        {
            if (!infile.is_open()) cerr << "Failed to open input file: " << input_file << endl;
            if (!outfile.is_open()) cerr << "Failed to open output file: " << output_file << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
