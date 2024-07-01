#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>

void gen_h2p_file(const string &output_file, const string &input_file)
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
                BYTE h2p[32];


                if (aline == "x")
                {
                    input_hex_byte.resize(0);
                }
                else
                {
                    hex_to_bytearray(input_hex_byte.data(), aline);
                }

                hash_to_point(h2p, input_hex_byte.data(), input_hex_byte.size());

                string h2p_hex;
                to_string(h2p_hex, h2p, sizeof(h2p));

                outfile << h2p_hex << " " << aline << "\n";
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

void gen_h2s_file(const string &output_file, const string &input_file)
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

                BYTE h2s[32];
                hash_to_scalar(h2s, input_hex_byte.data(), input_hex_byte.size());

                string h2s_hex;
                to_string(h2s_hex, h2s, sizeof(h2s));

                outfile << h2s_hex << " " << aline << "\n";
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