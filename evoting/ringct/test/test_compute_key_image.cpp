#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>

SCENARIO("Test the consistency of the gen_compute_key_image_file function", "[compute_key_image]")
{
    const string input_file = filesystem::absolute("/app/test/text/receiver_test_SA_signer.txt");
    const string output_file = filesystem::absolute("/app/test/text/key_image.txt");

    GIVEN("A set of inputs and expected outputs for computing the commitment key image")
    {
        REQUIRE(filesystem::exists(input_file));
        REQUIRE(filesystem::exists(output_file));

        ifstream infile(input_file);
        ifstream outfile(output_file);
        REQUIRE(infile.is_open());
        REQUIRE(outfile.is_open());

        string validity, skS, skV, rG, pkV, pkS, pk, computed_sk;
        string out_skS, out_skV, out_rG, out_pkV, out_pkS, out_pk, out_computed_sk, key_image;
        int case_num = 0;

        while (infile >> validity >> skS >> skV >> rG >> pkV >> pkS >> pk >> computed_sk &&
               outfile >> out_skS >> out_skV >> out_rG >> out_pkV >> out_pkS >> out_pk >> out_computed_sk >> key_image)
        {
            case_num++;
            WHEN("The gen_compute_key_image_file function is called and compared to the expected output" + to_string(case_num))
            {
                StealthAddress sa;
                hex_to_bytearray(sa.rG, rG);
                hex_to_bytearray(sa.pk, pk);

                if (validity == "valid" && computed_sk != "N/A") {
                    BYTE sk[32];
                    hex_to_bytearray(sk, computed_sk);
                    sa.set_stealth_address_secretkey(sk);
                }

                blsagSig blsagSig;
                string computed_key_image = "N/A";

                if (validity == "valid" && computed_sk != "N/A") {
                    compute_key_image(blsagSig, sa);
                    to_string(computed_key_image, blsagSig.key_image, 32);
                }

                cout << "Test case " << case_num << endl;
                cout << "Validity: " << validity << endl;
                cout << "Computed SK: " << computed_sk << endl;
                cout << "Computed key image: " << computed_key_image << endl;
                cout << "Expected key image: " << key_image << endl;

                THEN("The computed key image should match the expected output")
                {
                    REQUIRE(computed_key_image == key_image);
                }
            }
        }

        infile.close();
        outfile.close();

        // Debugging output for total lines processed
        cout << "Total lines processed: " << case_num << endl;
    }
}
