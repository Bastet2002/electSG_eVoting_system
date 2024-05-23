#include <numeric>
#include <stdexcept>
#include "rctType.h"

using namespace std;

// Initialize libsodium
// void initializeLibsodium() {
//     if (sodium_init() < 0) {
//         throw runtime_error("libsodium initialization failed");
//     }
// }

// Convert a value to a scalar
void valueToScalar(int value, BYTE scalar[crypto_core_ed25519_SCALARBYTES]) {
    memset(scalar, 0, crypto_core_ed25519_SCALARBYTES);
    memcpy(scalar, &value, sizeof(value));
}

void computeMask(BYTE* yt, const BYTE *r, const BYTE *pkv, size_t index) {
    BYTE rpkv[crypto_core_ed25519_BYTES];
    if (crypto_scalarmult_ed25519_noclamp(rpkv, r, pkv) != 0) {
        throw runtime_error("Failed to compute rpkv");
    }

    BYTE t[crypto_core_ed25519_SCALARBYTES];
    int_to_scalar_BYTE(t, index);

    size_t length = crypto_core_ed25519_BYTES + crypto_core_ed25519_SCALARBYTES; 
    vector<BYTE> toHash(length);
    copy(rpkv, rpkv + crypto_core_ed25519_BYTES, toHash.begin());
    copy(t, t + crypto_core_ed25519_SCALARBYTES, toHash.begin() + crypto_core_ed25519_BYTES);

    BYTE hnrpkvt[crypto_core_ed25519_SCALARBYTES];
    hash_to_scalar(hnrpkvt, toHash.data(), length);

    string mask = "mask";
    vector<BYTE> maskBytes(mask.begin(), mask.end());

    size_t length2 = crypto_core_ed25519_SCALARBYTES + (maskBytes.size()*sizeof(BYTE));
    vector<BYTE> toHash2(length);
    copy(maskBytes.begin(), maskBytes.end(), toHash2.begin());
    copy(hnrpkvt, hnrpkvt + crypto_core_ed25519_SCALARBYTES, toHash2.begin() + maskBytes.size());

    hash_to_scalar(yt, toHash2.data(), length2);
}

// void computeAmount(BYTE* yt, const BYTE *r, const BYTE *pkv, int index) {
//     BYTE rpkv[crypto_core_ed25519_BYTES];
//     if (crypto_scalarmult_ed25519_noclamp(rpkv, r, pkv) != 0) {
//         throw runtime_error("Failed to compute rpkv");
//     }

//     BYTE t[crypto_core_ed25519_SCALARBYTES];
//     int_to_scalar_BYTE(t, index);

//     size_t length = crypto_core_ed25519_BYTES + crypto_core_ed25519_SCALARBYTES; 
//     vector<BYTE> toHash(length);
//     copy(rpkv, rpkv + crypto_core_ed25519_BYTES, toHash.begin());
//     copy(t, t + crypto_core_ed25519_SCALARBYTES, toHash.begin() + crypto_core_ed25519_BYTES);

//     BYTE hnrpkvt[crypto_core_ed25519_SCALARBYTES];
//     hash_to_scalar(hnrpkvt, toHash.data(), length);

//     string mask = "mask";
//     vector<BYTE> maskBytes(mask.begin(), mask.end());

//     size_t length2 = crypto_core_ed25519_SCALARBYTES + (maskBytes.size()*sizeof(BYTE));
//     vector<BYTE> toHash2(length);
//     copy(maskBytes, maskBytes + (maskBytes.size()*sizeof(BYTE)), toHash2.begin());
//     copy(hnrpkvt, hnrpkvt + crypto_core_ed25519_SCALARBYTES, toHash2.begin() + (maskBytes.size()*sizeof(BYTE)));

//     BYTE yt[crypto_core_ed25519_SCALARBYTES];
//     hash_to_scalar(yt, toHash2.data(), length2);
// }

// Calculate a Pedersen commitment
// void calculateCommitment(const BYTE blindingFactor[crypto_core_ed25519_SCALARBYTES], uint64_t value, BYTE commitment[crypto_core_ed25519_BYTES]) {
//     // Generate the point H (a fixed generator for the Pedersen commitment)
//     BYTE H[crypto_core_ed25519_BYTES];
//     if (crypto_core_ed25519_from_uniform(H, blindingFactor) != 0) {
//         throw runtime_error("Failed to generate H from blinding factor");
//     }

//     // Convert value to scalar
//     BYTE value_scalar[crypto_core_ed25519_SCALARBYTES];
//     valueToScalar(value, value_scalar);

//     // Calculate the commitment: C = r * G + v * H (where G is the base point)
//     BYTE rG[crypto_core_ed25519_BYTES];
//     crypto_scalarmult_ed25519_base_noclamp(rG, blindingFactor);  // r * G

//     BYTE vH[crypto_core_ed25519_BYTES]; // v * H
//     if (crypto_scalarmult_ed25519_noclamp(vH, value_scalar, H) != 0) {         
//         throw runtime_error("Failed to compute vH");
//     }

//     crypto_core_ed25519_add(commitment, rG, vH);  // r * G + v * H
// }

// Generate blinding factors ensuring the sum condition
void generatePseudoBfs(vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &pseudoOutBfs, vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &outputCommitmentBfs) {
    size_t numPseudoOuts = pseudoOutBfs.size();
    size_t numOutputCommitments = outputCommitmentBfs.size();

    // Generate random blinding factors for all but the last pseudo output
    for (size_t i = 0; i < numPseudoOuts - 1; ++i) {
        crypto_core_ed25519_scalar_random(pseudoOutBfs[i].data());
    }

    // Generate blinding factors for all output commitments
    BYTE sumOutputCommitments[crypto_core_ed25519_SCALARBYTES] = {0};
    // array<BYTE, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < numOutputCommitments; ++i) {
        crypto_core_ed25519_scalar_add(sumOutputCommitments, outputCommitmentBfs[i].data(), sumOutputCommitments);
        // sumOutputCommitments = temp;
    }

    // Calculate the sum of blinding factors for pseudo outputs (excluding the last one)
    BYTE sumPseudoOuts[crypto_core_ed25519_SCALARBYTES] = {0};
    for (size_t i = 0; i < numPseudoOuts - 1; ++i) {
        crypto_core_ed25519_scalar_add(sumPseudoOuts, pseudoOutBfs[i].data(), sumPseudoOuts);
        // sumPseudoOuts = temp;
    }

    // Calculate the last blinding factor for the pseudo output
    crypto_core_ed25519_scalar_sub(pseudoOutBfs[numPseudoOuts - 1].data(), sumOutputCommitments, sumPseudoOuts);
}

bool compareBlindingFactors(const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>>& pseudoOutBfs, const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>>& outputCommitmentBfs) {
    array<BYTE, crypto_core_ed25519_SCALARBYTES> sumPseudoOuts = {0};
    array<BYTE, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < pseudoOutBfs.size(); ++i) {
        crypto_core_ed25519_scalar_add(sumPseudoOuts.data(), pseudoOutBfs[i].data(), sumPseudoOuts.data());
        // addScalars(sumPseudoOuts.data(), pseudoOutBfs[i].data(), temp.data());
    }

    array<BYTE, crypto_core_ed25519_SCALARBYTES> sumOutputCommitments = {0};
    for (size_t i = 0; i < outputCommitmentBfs.size(); ++i) {
        crypto_core_ed25519_scalar_add(sumOutputCommitments.data(), outputCommitmentBfs[i].data(), sumOutputCommitments.data());
        // addScalars(sumOutputCommitments.data(), outputCommitmentBfs[i].data(), temp.data());
    }

    return sumPseudoOuts == sumOutputCommitments;
}

// int main() {
//     try {
//         // Initialize libsodium
//         initializeLibsodium();

//         // Define the number of pseudo outputs and output commitments
//         size_t numPseudoOuts = 3; // Example
//         size_t numOutputCommitments = 2; // Example

//         // Vectors to store blinding factors
//         vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> pseudoOutBfs(numPseudoOuts);
//         vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> outputCommitmentBfs(numOutputCommitments);
//         // vector<BYTE[crypto_core_ed25519_SCALARBYTES]> outputCommitmentBfs(numOutputCommitments);

//         for (size_t i = 0; i < numOutputCommitments; ++i) {
//             computeMask(outputCommitmentBfs[i].data(), r, receiver.pkv, i);
//         // Generate blinding factors ensuring the sum condition
//         generatePseudoBfs(pseudoOutBfs, outputCommitmentBfs);

//         // Compare the sums of blinding factors
//         if (compareBlindingFactors(pseudoOutBfs, outputCommitmentBfs)) {
//             cout << "The sum of blinding factors for pseudo outputs is equal to the sum of blinding factors for output commitments.\n";
//         } else {
//             cout << "The sum of blinding factors for pseudo outputs is not equal to the sum of blinding factors for output commitments.\n";
//         }

//         // Define values for commitments (example values)
//         vector<int> pseudoOutValues = {500, 1000, 1500};
//         vector<int> outputCommitmentValues = {500, 2500};


//         // Vectors to store commitments
//         vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> pseudoOuts(numPseudoOuts);
//         vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> outputCommitments(numOutputCommitments);

//         BYTE H[crypto_core_ed25519_BYTES];
//         generate_H(H);

//         // Calculate and display pseudo output commitments
//         cout << "Pseudo Output Commitments:\n";
//         for (size_t i = 0; i < numPseudoOuts; ++i) {

//             BYTE scalarValue[crypto_core_ed25519_SCALARBYTES];
//             valueToScalar(pseudoOutValues[i], scalarValue);

//             add_key(pseudoOuts[i].data(), pseudoOutBfs[i].data(), scalarValue, H);

//             cout << "PseudoOut[" << i << "]: ";
//             for (int j = 0; j < crypto_core_ed25519_BYTES; ++j) {
//                 cout << hex << (int)pseudoOuts[i][j];
//             }
//             cout << endl;
//         }

//         // Calculate and display output commitments
//         cout << "Output Commitments:\n";
//         for (size_t i = 0; i < numOutputCommitments; ++i) {

//             BYTE scalarValue[crypto_core_ed25519_SCALARBYTES];
//             valueToScalar(outputCommitmentValues[i], scalarValue);

//             add_key(outputCommitments[i].data(), outputCommitmentBfs[i].data(), scalarValue, H);

//             cout << "OutputCommitment[" << i << "]: ";
//             for (int j = 0; j < crypto_core_ed25519_BYTES; ++j) {
//                 cout << hex << (int)outputCommitments[i][j];
//             }
//             cout << endl;
//         }

//     } catch (const exception& e) {
//         cerr << e.what() << endl;
//         return 1;
//     }

//     return 0;
// }
