#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_message_file(const string &output_file, const string &input_file_ki, const string &input_file_vc)
{
    ifstream infile_ki(input_file_ki);
    ifstream infile_vc(input_file_vc);
    ofstream outfile(output_file);

    try
    {
        if (infile_ki.is_open() && infile_vc.is_open() && outfile.is_open())
        {
            cout << "Successfully opened input files: " << input_file_ki << " and " << input_file_vc << endl;
            cout << "Successfully opened output file: " << output_file << endl;

            string validity, skS, skV, rG, pkV, pkS, pk, computed_sk, key_image;
            string input_commitment, output_commitment, pseudo_output_commitment, amount_mask, sa_r, receiver_pkV;
            int line_count = 0;

            while (infile_ki >> validity >> skS >> skV >> rG >> pkV >> pkS >> pk >> computed_sk >> key_image &&
                   infile_vc >> input_commitment >> output_commitment >> pseudo_output_commitment >> amount_mask >> sa_r >> receiver_pkV)
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                // Create StealthAddress object
                StealthAddress sa;
                hex_to_bytearray(sa.rG, rG);
                hex_to_bytearray(sa.pk, pk);
                hex_to_bytearray(sa.r, sa_r);

                // Debugging output for input values
                cout << "Validity: " << validity << endl;
                cout << "skS: " << skS << endl;
                cout << "skV: " << skV << endl;
                cout << "rG: " << rG << endl;
                cout << "pkV: " << pkV << endl;
                cout << "pkS: " << pkS << endl;
                cout << "pk: " << pk << endl;
                cout << "Computed SK: " << computed_sk << endl;
                cout << "Key Image: " << key_image << endl;

                // Set the SK if it's valid
                if (validity == "valid" && computed_sk != "N/A") {
                    BYTE sk[32];
                    hex_to_bytearray(sk, computed_sk);
                    sa.set_stealth_address_secretkey(sk);
                    cout << "SK set for valid stealth address" << endl;
                }

                // Set up Commitment
                Commitment commitment;
                array<BYTE, 32> input_commitment_arr, output_commitment_arr, pseudo_output_commitment_arr, output_blindingfactor_mask;
                array<BYTE, 8> amount_mask_arr;
                hex_to_bytearray(input_commitment_arr.data(), input_commitment);
                hex_to_bytearray(output_commitment_arr.data(), output_commitment);
                hex_to_bytearray(pseudo_output_commitment_arr.data(), pseudo_output_commitment);
                hex_to_bytearray(amount_mask_arr.data(), amount_mask);
                hex_to_bytearray(output_blindingfactor_mask.data(), computed_sk); // Assuming output_blindingfactor_mask is the same as computed_sk

                commitment.inputs_commitments.push_back(input_commitment_arr);
                commitment.outputs_commitments.push_back(output_commitment_arr);
                commitment.pseudoouts_commitments.push_back(pseudo_output_commitment_arr);
                commitment.amount_masks.push_back(amount_mask_arr);
                commitment.outputs_blindingfactor_masks.push_back(output_blindingfactor_mask);

                // Compute the message
                blsagSig blsagSig;
                hex_to_bytearray(blsagSig.key_image, key_image);
                string message = "N/A";

                if (validity == "valid" && computed_sk != "N/A") {
                    try
                    {
                        compute_message(blsagSig, sa, commitment);
                        to_string(message, blsagSig.m, 32);
                        cout << "Message computed successfully" << endl;
                    }
                    catch (const exception &e)
                    {
                        cerr << "Failed to compute message for line " << line_count << ": " << e.what() << endl;
                    }
                } else {
                    cout << "Skipping message computation for invalid or incomplete stealth address" << endl;
                }

                // Write results to the output file
                outfile << validity << " "
                        << skS << " "
                        << skV << " "
                        << rG << " "
                        << pkV << " "
                        << pkS << " "
                        << pk << " "
                        << computed_sk << " "
                        << key_image << " "
                        << message << "\n";
                
                cout << "Line " << line_count << " processed and written to output file" << endl;
            }

            infile_ki.close();
            infile_vc.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "Messages computed and written to " << output_file << endl;
        }
        else
        {
            if (!infile_ki.is_open()) cerr << "Failed to open input key image file: " << input_file_ki << endl;
            if (!infile_vc.is_open()) cerr << "Failed to open input voting currency file: " << input_file_vc << endl;
            if (!outfile.is_open()) cerr << "Failed to open output file: " << output_file << endl;
        }
    }
    catch (const exception &e)
    {
        cerr << "Exception: " << e.what() << endl;
    }
}
