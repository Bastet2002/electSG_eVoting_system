#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

SCENARIO("Test the consistency of the compute message function", "[compute_message]")
{
    const std::string compute_message_file = std::filesystem::absolute("/app/test/text/messages.txt");

    GIVEN("The actual output should match the expected input")
    {
        std::ifstream infile(compute_message_file);
        REQUIRE(infile.is_open());

        std::string aline;
        int i = 0;

        while (std::getline(infile, aline))
        {
            std::istringstream iss(aline);
            std::string keyimage, candidate_stealth_address, rG;
            std::string pseudout_commitment, amount_mask, output_blindingfactor_mask, output_commitment, expected_m;

            iss >> keyimage >> candidate_stealth_address >> rG 
                >> pseudout_commitment >> amount_mask >> output_blindingfactor_mask >> output_commitment >> expected_m;

            blsagSig blsag;
            StealthAddress sa;
            Commitment commitment;

            // Initialize structures using hex_to_bytearray
            hex_to_bytearray(blsag.key_image, keyimage);
            hex_to_bytearray(sa.pk, candidate_stealth_address);
            hex_to_bytearray(sa.rG, rG);
            hex_to_bytearray(commitment.pseudoouts_commitments[0].data(), pseudout_commitment);
            hex_to_bytearray(commitment.amount_masks[0].data(), amount_mask);
            hex_to_bytearray(commitment.outputs_blindingfactor_masks[0].data(), output_blindingfactor_mask);
            hex_to_bytearray(commitment.outputs_commitments[0].data(), output_commitment);

            i++;

            WHEN("the known input is passed to the function" + std::to_string(i))
            {
                compute_message(blsag, sa, commitment);

                THEN("the expected output is matched with output")
                {
                    std::string computed_m;
                    to_string(computed_m, blsag.m, 32);

                    bool is_equal_m = computed_m == expected_m;

                    std::cout << "Test case " << i << ":" << std::endl;
                    std::cout << "Input keyimage: " << keyimage << std::endl;
                    std::cout << "Input candidate_stealth_address: " << candidate_stealth_address << std::endl;
                    std::cout << "Input rG: " << rG << std::endl;
                    std::cout << "Input pseudout_commitment: " << pseudout_commitment << std::endl;
                    std::cout << "Input amount_mask: " << amount_mask << std::endl;
                    std::cout << "Input output_blindingfactor_mask: " << output_blindingfactor_mask << std::endl;
                    std::cout << "Input output_commitment: " << output_commitment << std::endl;
                    std::cout << "Computed m: " << computed_m << std::endl;
                    std::cout << "Expected m: " << expected_m << std::endl;
                    std::cout << std::endl;

                    if (!is_equal_m)
                    {
                        std::cout << "Actual and expected output does not match" << std::endl;
                    }

                    REQUIRE(is_equal_m);
                }
            }
        }
    }
}
