#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <bitset>
#include "rctType.h"
#include "rctOps.h"

using namespace std;


// Function to generate C1 and C2 arrays
void generateC1C2(const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>>& blindingFactors,
                  const bitset<8> &bits,
                  vector<array<BYTE, crypto_core_ed25519_BYTES>>& C1,
                  vector<array<BYTE, crypto_core_ed25519_BYTES>>& C2) {
    
    cout << "--------------------------" << endl;
    cout << "------in generate C1 C2---" << endl;
    cout << "--------------------------" << endl;
    // bitset<8> bits(value);
    // Generate C1 and C2
    for (int i = 0; i < 8; ++i) {
        int ai = bits[i];
        if (ai == 0) {   // Ci = xiG, CiH = xiG - 2^iH
            crypto_scalarmult_ed25519_base_noclamp(C1[i].data(), blindingFactors[i].data());  // Ci = xiG
            
            BYTE twoi[crypto_core_ed25519_SCALARBYTES];  // 2^i
            int two_power_i = pow(2, i);
            // intToScalar(two_power_i, twoi);
            int_to_scalar_BYTE(twoi, two_power_i);

            BYTE H[crypto_core_ed25519_BYTES];  // H
            generate_H(H);
            
            BYTE twoiH[crypto_core_ed25519_BYTES];  // 2^iH
            if (crypto_scalarmult_ed25519_noclamp(twoiH, twoi, H) !=0) {
                throw runtime_error("Failed to compute 2^iH");
            }

            crypto_core_ed25519_sub(C2[i].data(), C1[i].data(), twoiH);  // Ci - 2^iH = xiG - 2^iH

        } else if (ai == 1) {   // Ci = xiG + 2^iH, Ci - 2^iH = xiG
            crypto_scalarmult_ed25519_base_noclamp(C2[i].data(), blindingFactors[i].data());  // Ci - 2^iH = xiG

            BYTE twoi[crypto_core_ed25519_SCALARBYTES];  // 2^i
            int_to_scalar_BYTE(twoi, pow(2, i));

            BYTE twoiH[crypto_core_ed25519_BYTES];  // 2^iH
            if (crypto_scalarmult_ed25519_noclamp(twoiH, twoi, H_point) !=0) {
                throw runtime_error("Failed to compute 2^iH");
            }

            crypto_core_ed25519_add(C1[i].data(), C2[i].data(), twoiH);  // Ci = xiG + 2^iH
        }
    }
}

void generateBlindingFactors(vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &blindingFactors, const BYTE *outputCommitmentBf) {
    size_t numCommitment = blindingFactors.size();

    // Generate random blinding factors for all but the last commitment
    for (size_t i = 0; i < numCommitment - 1; ++i) {
        crypto_core_ed25519_scalar_random(blindingFactors[i].data());
    }

    // Calculate the sum of blinding factors for commitments (excluding the last one)
    BYTE sumBlindingFactors[crypto_core_ed25519_SCALARBYTES] = {0};
    for (size_t i = 0; i < numCommitment - 1; ++i) {
        crypto_core_ed25519_scalar_add(sumBlindingFactors, blindingFactors[i].data(), sumBlindingFactors);
    }

    // Calculate the last blinding factor 
    crypto_core_ed25519_scalar_sub(blindingFactors[numCommitment - 1].data(), outputCommitmentBf, sumBlindingFactors);
}

void generate_Borromean(const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &x,
                        const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C1,
                        const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C2,
                        const bitset<8> &indices,
                        BYTE *bbee,
                        vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs0,
                        vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs1) {
    
    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> alpha(8);
    BYTE Lhash[crypto_core_ed25519_BYTES] = {0};
    array<array<array<BYTE, crypto_core_ed25519_BYTES>, 8>, 2> L;
    
    for (int i = 0; i < 8; ++i) {
        int n = indices[i];

        // randombytes_buf(alpha[i].data(), crypto_core_ed25519_SCALARBYTES); // a_i
        crypto_core_ed25519_scalar_random(alpha[i].data());

        crypto_scalarmult_ed25519_base_noclamp(L[n][i].data(), alpha[i].data()); // L[n][i] = a_i * G
        if (n == 0) {
            // randombytes_buf(bbs1[i].data(), crypto_core_ed25519_SCALARBYTES);
            crypto_core_ed25519_scalar_random(bbs1[i].data());

            BYTE c[crypto_core_ed25519_SCALARBYTES];
            hash_to_scalar(c, L[n][i].data(), crypto_core_ed25519_SCALARBYTES);

            BYTE cC2[crypto_core_ed25519_BYTES];
            if (crypto_scalarmult_ed25519_noclamp(cC2, c, C2[i].data()) != 0) {
                throw runtime_error("Failed to compute c * C2");
            }

            BYTE bbs1G[crypto_core_ed25519_BYTES];
            crypto_scalarmult_ed25519_base_noclamp(bbs1G, bbs1[i].data());

            crypto_core_ed25519_add(L[1][i].data(), bbs1G, cC2);
        }

        crypto_core_ed25519_add(Lhash, Lhash, L[1][i].data());
    }

    hash_to_scalar(bbee, Lhash, crypto_core_ed25519_SCALARBYTES);

    for (int j = 0; j < 8; ++j) {
        if (indices[j] == 0) {
            BYTE xbbee[crypto_core_ed25519_SCALARBYTES];
            crypto_core_ed25519_scalar_mul(xbbee, x[j].data(), bbee);

            crypto_core_ed25519_scalar_sub(bbs0[j].data(), alpha[j].data(), xbbee);

        } else {
            // randombytes_buf(bbs0[j].data(), crypto_core_ed25519_SCALARBYTES);
            crypto_core_ed25519_scalar_random(bbs0[j].data());

            BYTE bbs0G[crypto_core_ed25519_BYTES];
            crypto_scalarmult_ed25519_base_noclamp(bbs0G, bbs0[j].data());

            BYTE bbeeC1[crypto_core_ed25519_BYTES];
            if (crypto_scalarmult_ed25519_noclamp(bbeeC1, bbee, C1[j].data()) != 0) {
                throw runtime_error("Failed to compute bbee * C1[j]");
            }

            BYTE LL[crypto_core_ed25519_BYTES];
            crypto_core_ed25519_add(LL, bbs0G, bbeeC1);

            BYTE cc[crypto_core_ed25519_SCALARBYTES];
            hash_to_scalar(cc, LL, crypto_core_ed25519_SCALARBYTES);

            BYTE xcc[crypto_core_ed25519_SCALARBYTES];
            crypto_core_ed25519_scalar_mul(xcc, x[j].data(), cc);

            crypto_core_ed25519_scalar_sub(bbs1[j].data(), alpha[j].data(), xcc);
        }
    }
}

bool checkBorromean(const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C1,
                    const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C2,
                    const BYTE *bbee,
                    const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs0,
                    const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs1) {
    
    BYTE LV[crypto_core_ed25519_BYTES] = {0};
    for (int i = 0; i < 8; ++i) {
        BYTE Gbbs0[crypto_core_ed25519_BYTES];
        crypto_scalarmult_ed25519_base_noclamp(Gbbs0, bbs0[i].data());

        BYTE C1bbee[crypto_core_ed25519_BYTES];
        if (crypto_scalarmult_ed25519_noclamp(C1bbee, bbee, C1[i].data()) != 0) {
            throw runtime_error("Failed to compute bbee * C1");
        }

        BYTE LL[crypto_core_ed25519_BYTES];
        crypto_core_ed25519_add(LL, Gbbs0, C1bbee);

        BYTE chash[crypto_core_ed25519_SCALARBYTES];
        hash_to_scalar(chash, LL, crypto_core_ed25519_SCALARBYTES);

        BYTE chashC2[crypto_core_ed25519_BYTES];
        if (crypto_scalarmult_ed25519_noclamp(chashC2, chash, C2[i].data()) != 0) {
            throw runtime_error("Failed to compute chash * C2");
        }

        BYTE Gbbs1[crypto_core_ed25519_BYTES];
        crypto_scalarmult_ed25519_base_noclamp(Gbbs1, bbs1[i].data());

        BYTE chashC2Plusbbs1G[crypto_core_ed25519_BYTES];
        crypto_core_ed25519_add(chashC2Plusbbs1G, chashC2, Gbbs1);

        crypto_core_ed25519_add(LV, LV, chashC2Plusbbs1G);
    }
    BYTE eeComp[crypto_core_ed25519_SCALARBYTES];
    hash_to_scalar(eeComp, LV, crypto_core_ed25519_SCALARBYTES);

    cout << "eeComp: ";
    for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
        cout << hex << static_cast<int>(eeComp[i]);
    }
    cout << dec << endl;

    BYTE res[crypto_core_ed25519_SCALARBYTES];
    crypto_core_ed25519_scalar_sub(res, bbee, eeComp);

    cout << "res: ";
    for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
        cout << hex << static_cast<int>(res[i]);
    }
    cout << dec << endl;

    for (int j = 0; j < crypto_core_ed25519_SCALARBYTES; ++j) {
        if (res[j] != 0) {
            cout << "false" << endl;
            return false;
        } 
    }
    return true;
}

void rangeproof (RangeProof& rangeproof, const Commitment& commitment, const BYTE* output_blidingfactor) {
    // generate 8 bit blinding factor
    vector<array<BYTE, 32>> eight_bit_blindingFactors(8);
    generateBlindingFactors(eight_bit_blindingFactors, output_blidingfactor);
    cout << "after generateBlindingFactors" << endl;

    uint8_t value = static_cast<uint8_t>(commitment.amount); 
    bitset<8> bits(value);

    // generate C1 and C2
    generateC1C2(eight_bit_blindingFactors, bits, rangeproof.C1, rangeproof.C2);
    cout << "after generateC1C2" << endl;
    // generate Borromean
    generate_Borromean(eight_bit_blindingFactors, rangeproof.C1, rangeproof.C2, bits, rangeproof.bbee, rangeproof.bbs0, rangeproof.bbs1);
    cout << "after generate_Borromean" << endl;

    // check Borromean
    bool res = checkBorromean(rangeproof.C1, rangeproof.C2, rangeproof.bbee, rangeproof.bbs0, rangeproof.bbs1);
    cout << "after checkBorromean" << endl;
    if (res)
        cout << "Borromean is correct" << endl;
    else
        cout << "Borromean is incorrect" << endl;
}
