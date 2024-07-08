#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>

void gen_add_keys_file(const string &output_file, const string &input_file)
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

                BYTE a[32];
                hash_to_scalar(a, input_hex_byte.data(), input_hex_byte.size());

                BYTE b[32];
                hash_to_scalar(b, a, sizeof(a));

                BYTE k[32];
                hash_to_point(k, input_hex_byte.data(), input_hex_byte.size());

                BYTE h[32];
                generate_H(h);

                BYTE aKbH[32];
                add_key(aKbH, a, k, b, h);

                string aKbH_hex;
                to_string(aKbH_hex, aKbH, sizeof(aKbH));

                string a_hex;
                to_string(a_hex, a, sizeof(a));

                string b_hex;
                to_string(b_hex, b, sizeof(b));

                string k_hex;
                to_string(k_hex, k, sizeof(k));

                string h_hex;
                to_string(h_hex, h, sizeof(h));

                outfile << aKbH_hex << " " << a_hex << " " << k_hex << " " << b_hex << " " << h_hex << "\n";
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

void gen_add_keys_base_file(const string &output_file, const string &input_file)
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

                BYTE a[32];
                hash_to_scalar(a, input_hex_byte.data(), input_hex_byte.size());

                BYTE b[32];
                hash_to_scalar(b, a, sizeof(a));

                BYTE h[32];
                generate_H(h);

                BYTE aGbH[32];
                add_key(aGbH, a, b, h);

                string aGbH_hex;
                to_string(aGbH_hex, aGbH, sizeof(aGbH));

                string a_hex;
                to_string(a_hex, a, sizeof(a));

                string b_hex;
                to_string(b_hex, b, sizeof(b));

                string h_hex;
                to_string(h_hex, h, sizeof(h));

                outfile << aGbH_hex << " " << a_hex << " " << b_hex << " " << h_hex << "\n";
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