#ifndef RCTTYPE_H
#define RCTTYPE_H

#include <sodium.h>
#include <cstring>
#include <vector>
#include <algorithm>
#include <string>
#include <iostream>
#include <iomanip>
#include <array>

using namespace std;
typedef unsigned char BYTE;

template <typename T>
void insertAtIndex(vector<T> &v, int index, const T &t)
{
    if (index <= v.size())
    {
        auto it = v.begin() + index;
        v.insert(it, t);
    }
    else
    {
        cout << "Index out of range" << endl;
        v.push_back(t);
    }
}

// Could change to something else, take note to change the length as well, and copy output to H_point
#define H_String \
    ((const BYTE \
          *)"This is used as H string generation, no one knows this secret")
#define H_Len 61

// to save on computation, so precompute H
// it is the same as the result from the generate_H 
const BYTE H_point[] = {0x9f, 0xac, 0xd9, 0x67, 0x6d, 0x4d, 0xd5, 0x68, 0x90, 0xf9, 0x2c, 0xf4, 0xca, 0x6d, 0x38, 0x9d, 0x24, 0xa1, 0x1f, 0xd2, 0x05, 0x79, 0xfc, 0xab, 0x6b, 0x28, 0xe5, 0x28, 0x30, 0x52, 0x28, 0x20};

void hex_to_bytearray(BYTE *output, const string &input);

// TODO : create one more user type with public key only??
// when do we need sk?
// 1. verify the stealth address
// sign ring is with stealth_address_secretkey
struct User
{
    BYTE skV[64];
    BYTE pkV[32];
    BYTE skS[64];
    BYTE pkS[32];
    User()
    {
        sodium_memzero(skV, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkV, crypto_sign_PUBLICKEYBYTES);
        sodium_memzero(skS, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkS, crypto_sign_PUBLICKEYBYTES);
        crypto_sign_keypair(pkV, skV);
        crypto_sign_keypair(pkS, skS);
    }

    // for voter from db
    User(string r_pkV, string r_skV, string r_pkS, string r_skS)
    {
        sodium_memzero(skV, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkV, crypto_sign_PUBLICKEYBYTES);
        sodium_memzero(skS, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkS, crypto_sign_PUBLICKEYBYTES);
        hex_to_bytearray(this->pkV, r_pkV);
        hex_to_bytearray(this->skV, r_skV);
        hex_to_bytearray(this->pkS, r_pkS);
        hex_to_bytearray(this->skS, r_skS);
    }

    // for candidate from db
    User(string r_pkV, string r_pkS)
    {
        sodium_memzero(skV, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkV, crypto_sign_PUBLICKEYBYTES);
        sodium_memzero(skS, crypto_sign_SECRETKEYBYTES);
        sodium_memzero(pkS, crypto_sign_PUBLICKEYBYTES);
        hex_to_bytearray(this->pkV, r_pkV);
        hex_to_bytearray(this->pkS, r_pkS);
    }
};

struct StealthAddress
{
    BYTE pk[32];
    BYTE rG[32];
    BYTE sk[32]; // can be null(0) depending on use case
    BYTE r[32];  // can be null(0), the r is set in compute_stealth_address,
    // so the commitment mask calculation must done after this function 

    StealthAddress()
    {
        sodium_memzero(pk, crypto_core_ed25519_BYTES);
        sodium_memzero(rG, crypto_core_ed25519_BYTES);
        sodium_memzero(sk, crypto_core_ed25519_SCALARBYTES);
        sodium_memzero(r, crypto_core_ed25519_SCALARBYTES);
    }

    StealthAddress(const string &r_pk, const string &r_rG)
    {
        sodium_memzero(pk, crypto_core_ed25519_BYTES);
        sodium_memzero(rG, crypto_core_ed25519_BYTES);
        sodium_memzero(sk, crypto_core_ed25519_SCALARBYTES);
        sodium_memzero(r, crypto_core_ed25519_SCALARBYTES);
        hex_to_bytearray(this->pk, r_pk);
        hex_to_bytearray(this->rG, r_rG);
    }

    void set_stealth_address(const BYTE *scanned_stealth_address)
    {
        memcpy(sk, scanned_stealth_address, crypto_core_ed25519_BYTES);
    }
    void set_rG(const BYTE *scanned_rG)
    {
        memcpy(rG, scanned_rG, crypto_core_ed25519_BYTES);
    }
    void set_stealth_address_secretkey(const BYTE *scanned_stealth_address_secretkey)
    {
        memcpy(sk, scanned_stealth_address_secretkey, crypto_core_ed25519_SCALARBYTES);
    }
    void set_r(const BYTE *rand)
    {
        memcpy(r, rand, crypto_core_ed25519_SCALARBYTES);
    }
};

struct blsagSig
{
    BYTE c[32];
    BYTE m[32];
    vector<array<BYTE, 32>> r; // response, not the r from r in mask and rG
    BYTE key_image[32];
    vector<StealthAddress> members; // for verifier

    blsagSig()
    {
        sodium_memzero(c, 32);
        sodium_memzero(m, 32);
        sodium_memzero(key_image, 32);
        r.resize(0);
    }
};

struct Commitment{
    vector<array<BYTE,32>> pseudoouts_commitments;
    vector<array<BYTE,32>> outputs_commitments;
    vector<array<BYTE,32>> inputs_commitments; // no need to store in db, if need to verify, can be searched

    vector<array<BYTE,32>> pseudoouts_blindingfactor_masks;
    vector<array<BYTE,32>> outputs_blindingfactor_masks;
    vector<array<BYTE,8>> amount_masks;

    Commitment(){
        pseudoouts_commitments.resize(0);
        outputs_commitments.resize(0);
        inputs_commitments.resize(0);
        pseudoouts_blindingfactor_masks.resize(0);
        outputs_blindingfactor_masks.resize(0);
        amount_masks.resize(0);
    }
};

// util functions
void to_string(string &output, const BYTE *BYTE, const size_t n);
void compare_BYTE(const BYTE *a, const BYTE *b, const size_t n);
void int_to_scalar_BYTE(BYTE *out, const long long input);
void byte_to_int(long long &output, const BYTE* input, const size_t n);
void print_bytearray(const BYTE *key, const size_t n);
void print_hex(const BYTE *key, const size_t n);

// core functions
void extract_scalar_from_sk(BYTE *scalar, const BYTE *seed);
void generate_H(BYTE *H);
void hash_to_scalar(BYTE *scalar, const BYTE *key, const size_t key_size);
void hash_to_point(BYTE *point, const BYTE *BYTE, const size_t key_size);
void add_key(BYTE *aGbH, const BYTE *a, const BYTE *b, const BYTE *H);
void add_key(BYTE *aKbH, const BYTE *a, const BYTE *K, const BYTE *b, const BYTE *H);
void compute_stealth_address(StealthAddress &stealth_address, const User &receiver);
void CA_generate_address(vector<StealthAddress> &address_list, const vector<User> &users);
bool receiver_test_stealth_address(StealthAddress &stealth_address, const User &receiver);
void public_network_stealth_address_communication(vector<StealthAddress> &address_list, const vector<User> &users);
void mix_address(vector<StealthAddress> &vec);
int secret_index_gen(size_t n);
void compute_key_image(blsagSig &blsagSig, const StealthAddress &signerSA);
void compute_message(blsagSig& blsag, const StealthAddress& sa, const Commitment& commitment);
void blsag_simple_gen(blsagSig &blsagSig, const unsigned char *m, const size_t secret_index, const StealthAddress &signerSA, const vector<StealthAddress> &decoy);
bool blsag_simple_verify(const blsagSig &blsagSig, const BYTE *m);


void CA_generate_voting_currency(Commitment& commitment, const StealthAddress& sa, const User& receiver);
bool verify_commitment_balancing(const vector<array<BYTE, 32>> output_commitments, const vector<array<BYTE, 32>> pseudo_output_commitments);
void compute_commitment_simple(Commitment& commitment, const StealthAddress& sa, const User& receiver, const Commitment& received_commitment, const StealthAddress& received_sa, const User& signer);

void XOR_amount_mask_signer(BYTE* out, const BYTE* in, const size_t t, const StealthAddress& sa, const User& receiver);
void XOR_amount_mask_receiver(BYTE* out, const BYTE* in, const size_t t, const StealthAddress& sa, const User& receiver);
void compute_commitment_mask(BYTE *yt, const BYTE *r, const BYTE *pkv, size_t index);
void generatePseudoBfs(vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &pseudoOutBfs, vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &outputCommitmentBfs);
bool compareBlindingFactors(const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &pseudoOutBfs, const vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> &outputCommitmentBfs);

#endif