#ifndef RCTOPS_H
#define RCTOPS_H

#include "rctType.h"

// util functions
void to_string(string &output, const BYTE *BYTE, const size_t n);
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