#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_CA_generate_voting_currency_file(const string &output_file, const string &input_file)
{
    ifstream infile(input_file);
    ofstream outfile(output_file);

    try
    {
        if (infile.is_open() && outfile.is_open())
        {
            string aline;
            int case_num = 0;
            while (getline(infile, aline))
            {
                case_num++;
                vector<string> tokens = tokeniser(aline);
                if (tokens.size() != 7)
                {
                    cerr << "Invalid input format in line " << case_num << endl;
                    continue;
                }

                StealthAddress sa;
                User receiver;

                hex_to_bytearray(receiver.pkS, tokens[0]);
                hex_to_bytearray(receiver.pkV, tokens[1]);
                hex_to_bytearray(receiver.skS, tokens[2]);
                hex_to_bytearray(receiver.skV, tokens[3]);
                hex_to_bytearray(sa.r, tokens[4]);
                hex_to_bytearray(sa.rG, tokens[5]);
                hex_to_bytearray(sa.pk, tokens[6]);

                Commitment commitment;
                try
                {
                    // Set up deterministic random number generation
                    memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed));
                    counter = 0;
                    randombytes_set_implementation(&deterministic_implementation);

                    CA_generate_voting_currency(commitment, sa, receiver);

                    // Reset random number generation to default implementation
                    randombytes_set_implementation(NULL);

                    string input_commitment, output_commitment, pseudo_output_commitment, amount_mask, sa_r, receiver_pkV;
                    to_string(input_commitment, commitment.inputs_commitments[0].data(), 32);
                    to_string(output_commitment, commitment.outputs_commitments[0].data(), 32);
                    to_string(pseudo_output_commitment, commitment.pseudoouts_commitments[0].data(), 32);
                    to_string(amount_mask, commitment.amount_masks[0].data(), 8);
                    to_string(sa_r, sa.r, 32);
                    to_string(receiver_pkV, receiver.pkV, 32);

                    outfile << input_commitment << " " 
                            << output_commitment << " " 
                            << pseudo_output_commitment << " " 
                            << amount_mask << " "
                            << sa_r << " "
                            << receiver_pkV << endl;
                }
                catch (const exception &e)
                {
                    cerr << "Test Case " << case_num << ": Failed - " << e.what() << endl;
                }
            }
            infile.close();
            outfile.close();

            cout << "Generated " << case_num << " test cases in " << output_file << endl;
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
