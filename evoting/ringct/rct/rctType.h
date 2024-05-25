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

#define H_String \
    ((const BYTE \
          *)"This is used as H string generation, no one knows this secret")
#define H_Len 61

void print_hex(const BYTE *key, const size_t n);

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
};

struct StealthAddress
{
    BYTE pk[32];
    BYTE rG[32];
    BYTE sk[32]; // can be null(0) depending on use case

    StealthAddress()
    {
        sodium_memzero(pk, crypto_core_ed25519_BYTES);
        sodium_memzero(rG, crypto_core_ed25519_BYTES);
        sodium_memzero(sk, crypto_core_ed25519_SCALARBYTES);
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
};

struct blsagSig
{
    BYTE c[32];
    vector<array<BYTE, 32>> r;
    BYTE key_image[32];
    vector<StealthAddress> members; // for verifier

    blsagSig()
    {
        sodium_memzero(c, 32);
        r.resize(0);
        sodium_memzero(key_image, 32);
    }
};

// util functions
void to_string(string *output, const BYTE *BYTE, const size_t n);
void compare_BYTE(const BYTE *a, const BYTE *b, const size_t n);
void int_to_scalar_BYTE(BYTE *out, const long long input);

// core functions
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
void blsag_simple_gen(blsagSig &blsagSig, const unsigned char *m, const size_t secret_index, const StealthAddress &signerSA, const vector<StealthAddress> &decoy);
bool blsag_simple_verify(const blsagSig &blsagSig, const unsigned char *m);

#endif