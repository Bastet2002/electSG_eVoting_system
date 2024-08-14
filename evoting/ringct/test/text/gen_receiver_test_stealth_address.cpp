#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_receiver_test_stealth_address_file(const string &output_file, const string &input_file)
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
                // Create User object with all keys
                User receiver(pkV, skV, pkS, skS);

                // Create StealthAddress
                StealthAddress sa;
                hex_to_bytearray(sa.r, r);
                hex_to_bytearray(sa.rG, rG);
                hex_to_bytearray(sa.pk, pk);

                // Test if the stealth address belongs to the receiver
                bool result = receiver_test_stealth_address(sa, receiver);

                // Get the computed stealth address secret key
                string computed_sk;
                if (result) {
                    to_string(computed_sk, sa.sk, 32);
                } else {
                    computed_sk = "N/A";
                }

                // Write to file
                outfile << (result ? "valid" : "invalid") << " "
                        << skS << " "
                        << skV << " "
                        << rG << " "
                        << pkV << " "
                        << pkS << " "
                        << pk << " "
                        << computed_sk << "\n";
            }
            infile.close();
            outfile.close();

            cout << "Stealth address test results written to " << output_file << endl;
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
