#include <sodium.h>
#include <iostream>
#include <vector>
#include <numeric>
#include <stdexcept>
#include <array>

// Initialize libsodium
void initializeLibsodium() {
    if (sodium_init() < 0) {
        throw std::runtime_error("libsodium initialization failed");
    }
}

// Generate a random blinding factor
void generateBlindingFactor(unsigned char blindingFactor[crypto_core_ed25519_SCALARBYTES]) {
    randombytes_buf(blindingFactor, crypto_core_ed25519_SCALARBYTES);
}

// Convert a value to a scalar
void valueToScalar(uint64_t value, unsigned char scalar[crypto_core_ed25519_SCALARBYTES]) {
    memset(scalar, 0, crypto_core_ed25519_SCALARBYTES);
    memcpy(scalar, &value, sizeof(value));
}

// Calculate a Pedersen commitment
void calculateCommitment(const unsigned char blindingFactor[crypto_core_ed25519_SCALARBYTES], uint64_t value, unsigned char commitment[crypto_core_ed25519_BYTES]) {
    // Generate the point H (a fixed generator for the Pedersen commitment)
    unsigned char H[crypto_core_ed25519_BYTES];
    if (crypto_core_ed25519_from_uniform(H, blindingFactor) != 0) {
        throw std::runtime_error("Failed to generate H from blinding factor");
    }

    // Convert value to scalar
    unsigned char value_scalar[crypto_core_ed25519_SCALARBYTES];
    valueToScalar(value, value_scalar);

    // Calculate the commitment: C = r * G + v * H (where G is the base point)
    unsigned char rG[crypto_core_ed25519_BYTES];
    crypto_scalarmult_ed25519_base_noclamp(rG, blindingFactor);  // r * G

    unsigned char vH[crypto_core_ed25519_BYTES]; // v * H
    if (crypto_scalarmult_ed25519_noclamp(vH, value_scalar, H) != 0) {         
        throw std::runtime_error("Failed to compute vH");
    }

    crypto_core_ed25519_add(commitment, rG, vH);  // r * G + v * H
}

// Generate blinding factors ensuring the sum condition
void generateBlindingFactors(std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>>& pseudoOuts, std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>>& outputCommitments) {
    size_t numPseudoOuts = pseudoOuts.size();
    size_t numOutputCommitments = outputCommitments.size();

    // Generate random blinding factors for all but the last pseudo output
    for (size_t i = 0; i < numPseudoOuts - 1; ++i) {
        randombytes_buf(pseudoOuts[i].data(), crypto_core_ed25519_SCALARBYTES);
        // generateBlindingFactor(pseudoOuts[i].data());
    }

    // Generate random blinding factors for all output commitments
    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> sumOutputCommitments = {0};
    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < numOutputCommitments; ++i) {
        randombytes_buf(outputCommitments[i].data(), crypto_core_ed25519_SCALARBYTES);
        // generateBlindingFactor(outputCommitments[i].data());
        crypto_core_ed25519_scalar_add(temp.data(), outputCommitments[i].data(), sumOutputCommitments.data());
        // addScalars(sumOutputCommitments.data(), outputCommitments[i].data(), temp.data());
        sumOutputCommitments = temp;
    }

    // Calculate the sum of blinding factors for pseudo outputs (excluding the last one)
    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> sumPseudoOuts = {0};
    for (size_t i = 0; i < numPseudoOuts - 1; ++i) {
        crypto_core_ed25519_scalar_add(temp.data(), pseudoOuts[i].data(), sumPseudoOuts.data());
        // addScalars(sumPseudoOuts.data(), pseudoOuts[i].data(), temp.data());
        sumPseudoOuts = temp;
    }

    // Calculate the last blinding factor for the pseudo output
    crypto_core_ed25519_scalar_sub(pseudoOuts[numPseudoOuts - 1].data(), sumOutputCommitments.data(), sumPseudoOuts.data());
    // subtractScalars(sumOutputCommitments.data(), sumPseudoOuts.data(), pseudoOuts[numPseudoOuts - 1].data());
}

bool compareBlindingFactors(const std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>>& pseudoOuts, const std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>>& outputCommitments) {
    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> sumPseudoOuts = {0};
    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < pseudoOuts.size(); ++i) {
        crypto_core_ed25519_scalar_add(sumPseudoOuts.data(), pseudoOuts[i].data(), temp.data());
        // addScalars(sumPseudoOuts.data(), pseudoOuts[i].data(), temp.data());
        sumPseudoOuts = temp;
    }

    std::array<unsigned char, crypto_core_ed25519_SCALARBYTES> sumOutputCommitments = {0};
    for (size_t i = 0; i < outputCommitments.size(); ++i) {
        crypto_core_ed25519_scalar_add(sumOutputCommitments.data(), outputCommitments[i].data(), temp.data());
        // addScalars(sumOutputCommitments.data(), outputCommitments[i].data(), temp.data());
        sumOutputCommitments = temp;
    }

    return sumPseudoOuts == sumOutputCommitments;
}

int main() {
    try {
        // Initialize libsodium
        initializeLibsodium();

        // Define the number of pseudo outputs and output commitments
        size_t numPseudoOuts = 3; // Example
        size_t numOutputCommitments = 2; // Example

        // Vectors to store blinding factors
        std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>> pseudoOuts(numPseudoOuts);
        std::vector<std::array<unsigned char, crypto_core_ed25519_SCALARBYTES>> outputCommitments(numOutputCommitments);
        // std::vector<unsigned char[crypto_core_ed25519_SCALARBYTES]> outputCommitments(numOutputCommitments);

        // Generate blinding factors ensuring the sum condition
        generateBlindingFactors(pseudoOuts, outputCommitments);

        // Compare the sums of blinding factors
        if (compareBlindingFactors(pseudoOuts, outputCommitments)) {
            std::cout << "The sum of blinding factors for pseudo outputs is equal to the sum of blinding factors for output commitments.\n";
        } else {
            std::cout << "The sum of blinding factors for pseudo outputs is not equal to the sum of blinding factors for output commitments.\n";
        }

        // Define values for commitments (example values)
        std::vector<uint64_t> pseudoOutValues = {500, 1000, 1500};
        std::vector<uint64_t> outputCommitmentValues = {500, 2500};

        // Calculate and display pseudo output commitments
        std::cout << "Pseudo Output Commitments:\n";
        for (size_t i = 0; i < numPseudoOuts; ++i) {
            unsigned char commitment[crypto_core_ed25519_BYTES];
            calculateCommitment(pseudoOuts[i].data(), pseudoOutValues[i], commitment);
            std::cout << "PseudoOut[" << i << "]: ";
            for (int j = 0; j < crypto_core_ed25519_BYTES; ++j) {
                std::cout << std::hex << (int)commitment[j];
            }
            std::cout << std::endl;
        }

        // Calculate and display output commitments
        std::cout << "Output Commitments:\n";
        for (size_t i = 0; i < numOutputCommitments; ++i) {
            unsigned char commitment[crypto_core_ed25519_BYTES];
            calculateCommitment(outputCommitments[i].data(), outputCommitmentValues[i], commitment);
            std::cout << "OutputCommitment[" << i << "]: ";
            for (int j = 0; j < crypto_core_ed25519_BYTES; ++j) {
                std::cout << std::hex << (int)commitment[j];
            }
            std::cout << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    return 0;
}
