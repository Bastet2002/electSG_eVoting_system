#include "../../rct/rctOps.h"
#include "../../rct/rctType.h"
#include <fstream>
#include <iostream>
#include <string>
#include <filesystem>
#include "../test_util.h"

void gen_compute_commitment_simple_file(const string &output_file, const string &input_file_receiver, const string &input_file_signer, const string &input_file_received_commitment)
{
    ifstream infile_receiver(input_file_receiver);
    ifstream infile_signer(input_file_signer);
    ifstream infile_received_commitment(input_file_received_commitment);
    ofstream outfile(output_file);

    try
    {
        if (infile_receiver.is_open() && infile_signer.is_open() && infile_received_commitment.is_open() && outfile.is_open())
        {
            cout << "Successfully opened all input files and output file" << endl;

            string pkS_r, pkV_r, skS_r, skV_r, r_r, rG_r, pk_r;
            string pkS_s, pkV_s, skS_s, skV_s, r_s, rG_s, pk_s;
            string input_commitment, output_commitment, pseudo_output_commitment, amount_mask, sa_r, receiver_pkV;
            int line_count = 0;

            while (infile_receiver >> pkS_r >> pkV_r >> skS_r >> skV_r >> r_r >> rG_r >> pk_r &&
                   infile_signer >> pkS_s >> pkV_s >> skS_s >> skV_s >> r_s >> rG_s >> pk_s &&
                   infile_received_commitment >> input_commitment >> output_commitment >> pseudo_output_commitment >> amount_mask >> sa_r >> receiver_pkV)
            {
                line_count++;
                cout << "Processing line " << line_count << endl;

                try {
                    // Set up StealthAddress objects
                    StealthAddress receiverSA, signerSA;
                    hex_to_bytearray(receiverSA.r, r_r);
                    hex_to_bytearray(receiverSA.rG, rG_r);
                    hex_to_bytearray(receiverSA.pk, pk_r);
                    hex_to_bytearray(signerSA.r, r_s);
                    hex_to_bytearray(signerSA.rG, rG_s);
                    hex_to_bytearray(signerSA.pk, pk_s);

                    // Set up User objects
                    User receiver(pkV_r, skV_r, pkS_r, skS_r);
                    User signer(pkV_s, skV_s, pkS_s, skS_s);

                    // Create receivedCmt from imported data
                    Commitment receivedCmt;
                    array<BYTE, 32> received_output_commitment;
                    array<BYTE, 8> received_amount_mask;
                    hex_to_bytearray(received_output_commitment.data(), output_commitment);
                    hex_to_bytearray(received_amount_mask.data(), amount_mask);

                    receivedCmt.outputs_commitments.push_back(received_output_commitment);
                    receivedCmt.amount_masks.push_back(received_amount_mask);

                    // Debugging output for received commitment
                    string debug_str;
                    cout << "Received Commitment:" << endl;
                    to_string(debug_str, received_output_commitment.data(), 32);
                    cout << "output_commitment: " << debug_str << endl;
                    to_string(debug_str, received_amount_mask.data(), 8);
                    cout << "amount_mask: " << debug_str << endl;

                    // Set up candidate Commitment
                    Commitment candidateCmt;

                    // Call compute_commitment_simple
                    cout << "Computing commitment..." << endl;
                    compute_commitment_simple(candidateCmt, receiverSA, receiver, receivedCmt, signerSA, signer);
                    cout << "Commitment computed successfully." << endl;

                    // Convert commitment fields to strings
                    string amount_mask_str, output_blindingfactor_mask, pseudo_output_blindingfactor_mask;
                    string output_commitment_str, pseudo_output_commitment_str, output_blindingfactor_str;

                    to_string(amount_mask_str, candidateCmt.amount_masks[0].data(), 8);
                    to_string(output_blindingfactor_mask, candidateCmt.outputs_blindingfactor_masks[0].data(), 32);
                    to_string(pseudo_output_blindingfactor_mask, candidateCmt.pseudoouts_blindingfactor_masks[0].data(), 32);
                    to_string(output_commitment_str, candidateCmt.outputs_commitments[0].data(), 32);
                    to_string(pseudo_output_commitment_str, candidateCmt.pseudoouts_commitments[0].data(), 32);
                    to_string(output_blindingfactor_str, candidateCmt.output_blindingfactor, 32);

                    // Write results to the output file
                    outfile << amount_mask_str << " "
                            << output_blindingfactor_mask << " "
                            << pseudo_output_blindingfactor_mask << " "
                            << output_commitment_str << " "
                            << pseudo_output_commitment_str << " "
                            << output_blindingfactor_str << "\n";

                    cout << "Line " << line_count << " processed and written to output file" << endl;
                }
                catch (const exception &e)
                {
                    cerr << "Error processing line " << line_count << ": " << e.what() << endl;
                }
            }

            infile_receiver.close();
            infile_signer.close();
            infile_received_commitment.close();
            outfile.close();

            cout << "Processed " << line_count << " lines" << endl;
            cout << "Commitments computed and written to " << output_file << endl;
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
