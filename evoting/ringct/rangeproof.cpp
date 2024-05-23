#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <bitset>
#include <sodium.h>
#include "rctType.h"

using namespace std;

// Convert a value to a scalar
void intToScalar(int value, BYTE scalar[crypto_core_ed25519_SCALARBYTES]) {
    memset(scalar, 0, crypto_core_ed25519_SCALARBYTES);
    memcpy(scalar, &value, sizeof(value));
}

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
            intToScalar(two_power_i, twoi);

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
            valueToScalar(pow(2, i), twoi);

            BYTE H[crypto_core_ed25519_BYTES];  // H
            generate_H(H);
            
            BYTE twoiH[crypto_core_ed25519_BYTES];  // 2^iH
            if (crypto_scalarmult_ed25519_noclamp(twoiH, twoi, H) !=0) {
                throw runtime_error("Failed to compute 2^iH");
            }

            crypto_core_ed25519_add(C1[i].data(), C2[i].data(), twoiH);  // Ci = xiG + 2^iH
        }
    }
}

void generateBlindingFactors(vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &blindingFactors, BYTE *outputCommitmentBf) {
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

// void testCheckBorromean(const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C1,
//                     const vector<array<BYTE, crypto_core_ed25519_BYTES>> &C2,
//                     const BYTE bbee[crypto_core_ed25519_SCALARBYTES],
//                     const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs0,
//                     const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &bbs1,
//                     const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &alpha,
//                     const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &x) {
//         BYTE bbs0G1[crypto_core_ed25519_BYTES];
//         crypto_scalarmult_ed25519_base_noclamp(bbs0G1, bbs0[0].data());

//         BYTE bbeeC11[crypto_core_ed25519_BYTES];
//         if (crypto_scalarmult_ed25519_noclamp(bbeeC11, bbee, C1[0].data()) != 0) {
//             throw runtime_error("Failed to compute bbee * C1");
//         }

//         BYTE LL1[crypto_core_ed25519_BYTES];
//         crypto_core_ed25519_add(LL1, bbs0G1, bbeeC11);



//         // BYTE LLa[crypto_core_ed25519_BYTES];
//         // if (crypto_scalarmult_ed25519_noclamp(LLa, alpha[0].data(), LL) != 0) {
//         //     throw runtime_error("Failed to compute LLa");
//         // }

//         // BYTE bbs0Ga[crypto_core_ed25519_BYTES];
//         // if (crypto_scalarmult_ed25519_noclamp(bbs0Ga, alpha[0].data(), bbs0G) != 0) {
//         //     throw runtime_error("Failed to compute bbs0Ga");
//         // }

//         // BYTE bbeeC1a[crypto_core_ed25519_BYTES];
//         // if (crypto_scalarmult_ed25519_noclamp(bbeeC1a, alpha[0].data(), bbeeC1) != 0) {
//         //     throw runtime_error("Failed to compute bbeeC1a");
//         // }

//         // BYTE LLL[crypto_core_ed25519_BYTES];
//         // crypto_core_ed25519_add(LLL, bbs0Ga, bbeeC1a);

//         // cout << "3: " << endl;
//         // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
//         //     cout << hex << static_cast<int>(LLa[i]);
//         // }
//         // cout << dec << endl;

//         // cout << "4: " << endl;
//         // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
//         //     cout << hex << static_cast<int>(LLL[i]);
//         // }
//         // cout << dec << endl;

//         BYTE chash[crypto_core_ed25519_SCALARBYTES];
//         hash_to_scalar(chash, LL1, crypto_core_ed25519_SCALARBYTES);

//         BYTE chashC2[crypto_core_ed25519_BYTES];
//         if (crypto_scalarmult_ed25519_noclamp(chashC2, chash, C2[0].data()) != 0) {
//             throw runtime_error("Failed to compute chash * C2");
//         }

//         BYTE bbs1G1[crypto_core_ed25519_BYTES];
//         crypto_scalarmult_ed25519_base_noclamp(bbs1G1, bbs1[0].data());

//         BYTE chashC2Plusbbs1G[crypto_core_ed25519_BYTES];
//         crypto_core_ed25519_add(chashC2Plusbbs1G, chashC2, bbs1G1);

        


//         BYTE aiG[crypto_core_ed25519_BYTES];
//         crypto_scalarmult_ed25519_base_noclamp(aiG, alpha[0].data()); // L[n][i] = a_i * G

//         BYTE c[crypto_core_ed25519_SCALARBYTES];
//         hash_to_scalar(c, aiG, crypto_core_ed25519_SCALARBYTES);

//         BYTE cC2[crypto_core_ed25519_BYTES];
//         if (crypto_scalarmult_ed25519_noclamp(cC2, c, C2[0].data()) != 0) {
//             throw runtime_error("Failed to compute c * C2");
//         }

//         BYTE bbs1G[crypto_core_ed25519_BYTES];
//         crypto_scalarmult_ed25519_base_noclamp(bbs1G, bbs1[0].data());

//         BYTE cC2bbs1G[crypto_core_ed25519_BYTES];
//         crypto_core_ed25519_add(cC2bbs1G, bbs1G, cC2);

//         cout << "1: " << endl;
//         for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
//             cout << hex << static_cast<int>(cC2bbs1G[i]);
//         }
//         cout << dec << endl;

//         cout << "2: " << endl;
//         for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
//             cout << hex << static_cast<int>(chashC2Plusbbs1G[i]);
//         }
//         cout << dec << endl;
// }

// int main() {
//     vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> blindingFactor(1);
//     vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> blindingFactors(8);

//     generateBlindingFactors(blindingFactors, blindingFactor);

//     uint8_t value = 9; // Example value
//     bitset<8> bits(value);
//     vector<array<BYTE, crypto_core_ed25519_BYTES>> C1(8); 
//     vector<array<BYTE, crypto_core_ed25519_BYTES>> C2(8);
    
//     // Generate C1 and C2 arrays
//     generateC1C2(blindingFactors, bits, C1, C2);

//     // Display C1 and C2 arrays
//     cout << "C1:" << endl;
//     for (const auto& C : C1) {
//         for (BYTE c : C) {
//             cout << hex << static_cast<int>(c) << " ";
//         }
//         cout << endl;
//     }

//     cout << "C2:" << endl;
//     for (const auto& CiMinus2iH : C2) {
//         for (BYTE c : CiMinus2iH) {
//             cout << hex << static_cast<int>(c) << " ";
//         }
//         cout << endl;
//     }
//     cout << "hello" << endl;

//     // Generate Borromean
//     BYTE bbee[crypto_core_ed25519_SCALARBYTES];
//     vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs0(8);
//     vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> bbs1(8);

//     // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> alpha(8);//test
//     generate_Borromean(blindingFactors, C1, C2, bits, bbee, bbs0, bbs1);

//     // Display bbee, bbs0 and bbs1
//     cout << "bbee: ";
//     for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
//         cout << hex << static_cast<int>(bbee[i]);
//     }
//     cout << dec << endl;

//     cout << "bbs0:" << endl;
//     for (const auto& b : bbs0) {
//         for (BYTE c : b) {
//             cout << hex << static_cast<int>(c) << " ";
//         }
//         cout << endl;
//     }

//     cout << "bbs1:" << endl;
//     for (const auto& b : bbs1) {
//         for (BYTE c : b) {
//             cout << hex << static_cast<int>(c) << " ";
//         }
//         cout << endl;
//     }
//     cout << "hello" << endl;

//     bool res = checkBorromean(C1, C2, bbee, bbs0, bbs1);

//     cout << res << endl;

    //-----------------------------------------------------
    //-----------------------------------------------------
    //-----------------------------------------------------

    // test hash to scalar
    // BYTE x1[crypto_core_ed25519_SCALARBYTES];
    // hash_to_scalar(x1, bbs0[1].data(), crypto_core_ed25519_SCALARBYTES);

    // BYTE x2[crypto_core_ed25519_SCALARBYTES];
    // hash_to_scalar(x2, bbs0[1].data(), crypto_core_ed25519_SCALARBYTES);

    // cout << "x1: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(x1[i]);
    // }
    // cout << dec << endl;

    // cout << "x2: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(x2[i]);
    // }
    // cout << dec << endl;

    // testing
    // testCheckBorromean(C1, C2, bbee, bbs0, bbs1, alpha, blindingFactors);

    // BYTE xbbee[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_mul(xbbee, blindingFactors[0].data(), bbee);
    // BYTE result[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_sub(result, alpha[0].data(), xbbee);

    // cout << "bbs0: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(bbs0[0][i]);
    // }
    // cout << dec << endl;

    // cout << "result: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(result[i]);
    // }
    // cout << dec << endl;

    // BYTE bbeeC1[crypto_core_ed25519_BYTES];
    // if (crypto_scalarmult_ed25519_noclamp(bbeeC1, bbee, C1[0].data()) != 0) {
    //     throw runtime_error("Failed to compute bbee * C1");
    // }

    // BYTE LL[crypto_core_ed25519_BYTES];
    // crypto_core_ed25519_add(LL, bbs0G, bbeeC1);

    // BYTE bbeeG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(bbeeG, bbee);

    // BYTE bbeeGx[crypto_core_ed25519_BYTES];
    // if (crypto_scalarmult_ed25519_noclamp(bbeeGx, blindingFactors[0].data(), bbeeG) != 0) {
    //     throw runtime_error("Failed to compute bbee * C1");
    // }

    // cout << "bbeeC1: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(bbeeC1[i]);
    // }
    // cout << dec << endl;

    // cout << "bbeexG: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(bbeeGx[i]);
    // }
    // cout << dec << endl;

    // BYTE xG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(xG, blindingFactors[0].data());

    // cout << "xG: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(xG[i]);
    // }
    // cout << dec << endl;

    // cout << "C1: ";
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(C1[0][i]);
    // }
    // cout << dec << endl;


    // BYTE bbs0G[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(bbs0G, bbs0[0].data());

    // BYTE LL[crypto_core_ed25519_BYTES];
    // crypto_core_ed25519_add(LL, bbs0G, bbeeC1);

    // BYTE aiG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(aiG, alpha[0].data()); // L[n][i] = a_i * G

    // cout << "1: " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(LL[i]);
    // }
    // cout << dec << endl;

    // cout << "2: " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(aiG[i]);
    // }
    // cout << dec << endl;

    // BYTE xbbee[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_mul(xbbee, blindingFactors[0].data(), bbee);

    // BYTE aminusxbbee[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_sub(aminusxbbee, alpha[0].data(), xbbee);

    // cout << "aminusxbbee: " << endl;
    // for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
    //     cout << hex << static_cast<int>(aminusxbbee[i]);
    // }
    // cout << dec << endl;

    // BYTE aiGMinus[crypto_core_ed25519_BYTES];
    // crypto_core_ed25519_sub(aiGMinus, aiG, bbeeGx);

    // BYTE aminusxbbeeG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(aminusxbbeeG, aminusxbbee);

    // cout << "aiGMinus:2 " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(aiGMinus[i]);
    // }
    // cout << dec << endl;

    // cout << "aminusxbbeeG: " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(aminusxbbeeG[i]);
    // }
    // cout << dec << endl;

    // Calculate bbeeGx = (x_i * bbee) * G
    // BYTE xbbee[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_mul(xbbee, blindingFactors[0].data(), bbee);

    // BYTE bbeeGx[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(bbeeGx, xbbee);

    // // Calculate aiG = alpha_i * G
    // BYTE aiG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(aiG, alpha[0].data());

    // // Calculate aiGMinus = aiG - bbeeGx
    // BYTE aiGMinus[crypto_core_ed25519_BYTES];
    // crypto_core_ed25519_sub(aiGMinus, aiG, bbeeGx);

    // // Calculate aminusxbbee = alpha_i - x_i * bbee
    // BYTE aminusxbbee[crypto_core_ed25519_SCALARBYTES];
    // crypto_core_ed25519_scalar_sub(aminusxbbee, alpha[0].data(), xbbee);

    // // Calculate aminusxbbeeG = aminusxbbee * G
    // BYTE aminusxbbeeG[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base_noclamp(aminusxbbeeG, aminusxbbee);

    // // Output results for comparison
    // cout << "aiGMinus:1 " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(aiGMinus[i]);
    // }
    // cout << dec << endl;

    // cout << "aminusxbbeeG: " << endl;
    // for (int i = 0; i < crypto_core_ed25519_BYTES; ++i) {
    //     cout << hex << static_cast<int>(aminusxbbeeG[i]);
    // }
    // cout << dec << endl;

//     size_t length = crypto_core_ed25519_BYTES + crypto_core_ed25519_SCALARBYTES; 
//     vector<BYTE> toHash(length);

//     string mask = "mask";
//     vector<BYTE> maskBytes(mask.begin(), mask.end());

//     cout << "mask: ";
//     for (int i = 0; i < crypto_core_ed25519_SCALARBYTES; ++i) {
//         cout << hex << static_cast<int>(maskBytes[i]);
//     }
//     cout << dec << endl;

//     cout << toHash.size() << endl;
//     cout << maskBytes.size() << endl;
//     cout << maskBytes.size()*sizeof(BYTE) << endl;
    
//     return 0;
// }
