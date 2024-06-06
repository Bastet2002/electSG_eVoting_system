#include "rctType.h"

// one to one
void compute_commitment_simple(){

}

// one to many
void compute_commitment(){

}

// TODO compute amount_t mask
void compute_amount_mask(){

}

void verify_commitment_balancing(const vector<array<BYTE, 32>> output_commitments, const vector<array<BYTE, 32>> pseudo_output_commitments)
{
    // sum output commitments
    BYTE sum_output_commitments[32] = {0};
    for (size_t i = 0; i < output_commitments.size(); ++i)
        crypto_core_ed25519_add(sum_output_commitments, output_commitments[i].data(), sum_output_commitments);

    // sum pseudo output commitments
    BYTE sum_pseudo_output_commitments[32] = {0};
    for (size_t i = 0; i < pseudo_output_commitments.size(); ++i)
        crypto_core_ed25519_add(sum_pseudo_output_commitments, pseudo_output_commitments[i].data(), sum_pseudo_output_commitments);

    // compare the sum of output commitments and pseudo output commitments
    if (memcmp(sum_output_commitments, sum_pseudo_output_commitments, 32) != 0){
        throw logic_error("The output commitments and pseudo output commitments are not balanced.");
    }
    else
        cout << "The output commitments and pseudo output commitments are balanced.\n";
}

void compute_commitment_mask(BYTE *yt, const BYTE *r, const BYTE *pkv, size_t index)
{
    BYTE rpkv[crypto_core_ed25519_BYTES];
    if (crypto_scalarmult_ed25519_noclamp(rpkv, r, pkv) != 0)
    {
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

    size_t length2 = crypto_core_ed25519_SCALARBYTES + (maskBytes.size() * sizeof(BYTE));
    vector<BYTE> toHash2(length);
    copy(maskBytes.begin(), maskBytes.end(), toHash2.begin());
    copy(hnrpkvt, hnrpkvt + crypto_core_ed25519_SCALARBYTES, toHash2.begin() + maskBytes.size());

    hash_to_scalar(yt, toHash2.data(), length2);
}

// Generate blinding factors ensuring the sum condition
void generatePseudoBfs(vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &pseudoOutBfs, vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &outputCommitmentBfs)
{
    size_t numPseudoOuts = pseudoOutBfs.size();
    size_t numOutputCommitments = outputCommitmentBfs.size();

    // Generate random blinding factors for all but the last pseudo output
    for (size_t i = 0; i < numPseudoOuts - 1; ++i)
    {
        crypto_core_ed25519_scalar_random(pseudoOutBfs[i].data());
    }

    // sum the output commitment blinding factors
    BYTE sumOutputCommitments[crypto_core_ed25519_SCALARBYTES] = {0};
    // array<BYTE, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < numOutputCommitments; ++i)
    {
        crypto_core_ed25519_scalar_add(sumOutputCommitments, outputCommitmentBfs[i].data(), sumOutputCommitments);
        // sumOutputCommitments = temp;
    }

    // Calculate the sum of blinding factors for pseudo outputs (excluding the last one)
    BYTE sumPseudoOuts[crypto_core_ed25519_SCALARBYTES] = {0};
    for (size_t i = 0; i < numPseudoOuts - 1; ++i)
    {
        crypto_core_ed25519_scalar_add(sumPseudoOuts, pseudoOutBfs[i].data(), sumPseudoOuts);
        // sumPseudoOuts = temp;
    }

    // Calculate the last blinding factor for the pseudo output
    crypto_core_ed25519_scalar_sub(pseudoOutBfs[numPseudoOuts - 1].data(), sumOutputCommitments, sumPseudoOuts);
}

bool compareBlindingFactors(const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &pseudoOutBfs, const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &outputCommitmentBfs)
{
    array<BYTE, crypto_core_ed25519_SCALARBYTES> sumPseudoOuts = {0};
    array<BYTE, crypto_core_ed25519_SCALARBYTES> temp = {0};
    for (size_t i = 0; i < pseudoOutBfs.size(); ++i)
    {
        crypto_core_ed25519_scalar_add(sumPseudoOuts.data(), pseudoOutBfs[i].data(), sumPseudoOuts.data());
        // addScalars(sumPseudoOuts.data(), pseudoOutBfs[i].data(), temp.data());
    }

    array<BYTE, crypto_core_ed25519_SCALARBYTES> sumOutputCommitments = {0};
    for (size_t i = 0; i < outputCommitmentBfs.size(); ++i)
    {
        crypto_core_ed25519_scalar_add(sumOutputCommitments.data(), outputCommitmentBfs[i].data(), sumOutputCommitments.data());
        // addScalars(sumOutputCommitments.data(), outputCommitmentBfs[i].data(), temp.data());
    }

    return sumPseudoOuts == sumOutputCommitments;
}