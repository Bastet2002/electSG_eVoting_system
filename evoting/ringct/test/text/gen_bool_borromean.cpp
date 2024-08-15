// void validate_borromean_from_files(const string &C1C2_file, const string &borromean_file, const string &output_file)
// {
//     ifstream infile_C1C2(C1C2_file);
//     ifstream infile_borromean(borromean_file);
//     ofstream outfile(output_file);

//     try
//     {
//         if (infile_C1C2.is_open() && infile_borromean.is_open() && outfile.is_open())
//         {
//             string C1C2_str, borromean_str;
//             int line_count = 0;

//             while (getline(infile_C1C2, C1C2_str) && getline(infile_borromean, borromean_str))
//             {
//                 line_count++;
//                 cout << "Processing line " << line_count << endl;

//                 vector<string> C1C2_components = tokeniser(C1C2_str, ' ');
//                 vector<string> borromean_components = tokeniser(borromean_str, ' ');

//                 if (C1C2_components.size() != 16 || borromean_components.size() != 17) {
//                     cerr << "Error: Incorrect number of components in input strings at line " << line_count << endl;
//                     continue;  // Skip this line and move to the next
//                 }

//                 // Debug: Print original C1 and C2 strings
//                 for (int i = 0; i < 8; ++i) {
//                     cout << "Original C1[" << i << "]: " << C1C2_components[2 * i] << endl;
//                     cout << "Original C2[" << i << "]: " << C1C2_components[2 * i + 1] << endl;
//                 }

//                 // Convert C1 and C2 to BYTE arrays
//                 vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8), C2(8);
//                 for (int i = 0; i < 8; ++i) {
//                     hex_to_bytearray(C1[i].data(), C1C2_components[2 * i]);
//                     hex_to_bytearray(C2[i].data(), C1C2_components[2 * i + 1]);
//                 }

//                 // Debug: Print converted C1 and C2 byte arrays
//                 for (int i = 0; i < 8; ++i) {
//                     cout << "Converted C1[" << i << "]: ";
//                     print_hex(C1[i].data(), crypto_core_ed25519_BYTES);
//                     cout << endl;
//                     cout << "Converted C2[" << i << "]: ";
//                     print_hex(C2[i].data(), crypto_core_ed25519_BYTES);
//                     cout << endl;
//                 }

//                 // Extract Borromean signature components from the input
//                 BYTE bbee[crypto_core_ed25519_SCALARBYTES];
//                 vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8), bbs1(8);

//                 hex_to_bytearray(bbee, borromean_components[0]);
//                 for (int i = 0; i < 8; ++i) {
//                     hex_to_bytearray(bbs0[i].data(), borromean_components[1 + 2 * i]);
//                     hex_to_bytearray(bbs1[i].data(), borromean_components[2 + 2 * i]);
//                 }

//                 // Validate the Borromean ring signature
//                 bool is_valid = false;
//                 try {
//                     is_valid = checkBorromean(C1, C2, bbee, bbs0, bbs1);
//                 } catch (const exception &e) {
//                     cerr << "Error validating Borromean signature at line " << line_count << ": " << e.what() << endl;
//                     outfile << "Line " << line_count << ": Exception occurred during validation\n";
//                     continue;
//                 }

//                 // Write the result to the output file
//                 outfile << "Line " << line_count << ": " << (is_valid ? "Valid" : "Invalid") << "\n";
//                 cout << "Line " << line_count << " validation result written to output file" << endl;
//             }

//             infile_C1C2.close();
//             infile_borromean.close();
//             outfile.close();

//             cout << "Finished processing all lines." << endl;
//         }
//         else
//         {
//             cerr << "Unable to open input or output file" << endl;
//         }
//     }
//     catch (const exception &e)
//     {
//         cerr << "Exception: " << e.what() << endl;
//     }
// }
