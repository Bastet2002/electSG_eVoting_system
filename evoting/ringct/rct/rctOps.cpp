#include "rctType.h"
#include "rctOps.h"


void to_string(string &output, const BYTE *key, const size_t n)
{
    ostringstream oss;
    for (size_t i = 0; i < n; i++)
    {
        oss << hex << setw(2) << setfill('0') << int(key[i]);
    }
    output = oss.str();
}

void hex_to_bytearray(BYTE *output, const string &input){
    if (input.size() % 2 != 0)
        throw invalid_argument("Input size must be even");

    for (size_t i = 0, j = 0; i < input.size(); i+=2, j++){
        output[j] = static_cast<BYTE>(stoul(input.substr(i, 2), nullptr, 16));
    }
}

void print_hex(const BYTE *key, const size_t n)
{
    for (size_t i = 0; i < n; i++)
    {
        cout << hex << setw(2) << setfill('0') << int(key[i]);
    }
    cout << dec << endl;
}

// for copying the H to as constant in header file
void print_bytearray(const BYTE *key, const size_t n)
{
    for (size_t i = 0; i < n; i++)
    {
        cout << "0x" << hex << setw(2) << setfill('0') << static_cast<int>(key[i]);
        if (i != n - 1)
            cout << ", ";
    }
    cout << dec << endl;
}

// input long long is guaranteed at least 64bit == 8 BYTE, output in little endian
void int_to_scalar_BYTE(BYTE *out, const long long input)
{
    memset(out, 0, crypto_core_ed25519_SCALARBYTES); // use 32 BYTE for now, if to use 8 BYTE, probably need to come up with own scalar multiplication funciton
    // overflow if > 32 BYTE, but not possible
    memcpy(out, &input, sizeof(input));
}

void byte_to_int(long long &output, const BYTE* input, const size_t n){
    memcpy(&output, input, n);
}

void generate_H(BYTE *H)
{
    BYTE hash[crypto_generichash_BYTES];
    BYTE str_to_hash[H_Len + 4];
    memmove(str_to_hash, "HSTR", 4); //  domain separation
    memmove(str_to_hash + 4, H_String, H_Len);

    crypto_generichash(hash, crypto_generichash_BYTES, H_String, H_Len, NULL, 0);

    crypto_core_ed25519_from_uniform(H, hash); // guarantee on main subgroup
    int is_success = crypto_core_ed25519_is_valid_point(
        H); // unnecessary, but to remind. Check on main subgroup, and dont have a
            // small order
    if (is_success != 1)
        exit(1);
}

void hash_to_scalar(BYTE *scalar, const BYTE *key, const size_t key_size)
{
    BYTE hash[crypto_generichash_BYTES_MAX];
    crypto_generichash(hash, crypto_generichash_BYTES_MAX, key, key_size, NULL,
                       0);
    crypto_core_ed25519_scalar_reduce(scalar, hash);
}

void hash_to_point(BYTE *point, const BYTE *key, const size_t key_size)
{
    BYTE hash[crypto_generichash_BYTES_MAX];
    crypto_generichash(hash, crypto_generichash_BYTES_MAX, key, key_size, NULL,
                       0);
    crypto_core_ed25519_from_uniform(point, hash);
}

// ensure seed is 32 BYTEs, need to copy the seed from sk to another intermediate buffer
void extract_scalar_from_sk(BYTE *scalar, const BYTE *seed)
{
    memset(scalar, 0, crypto_core_ed25519_SCALARBYTES);
    crypto_hash_sha512(scalar, seed, 32);
    scalar[0] &= 248;
    scalar[31] &= 127;
    scalar[31] |= 64;
}

// aGbH, where a and b are scalar, and G is the base point and B is the point
void add_key(BYTE *aGbH, const BYTE *a, const BYTE *b,
             const BYTE *H)
{
    BYTE aG[crypto_scalarmult_ed25519_BYTES];
    BYTE bH[crypto_scalarmult_ed25519_BYTES];

    // check value, skip for now

    int is_success_aG = crypto_scalarmult_ed25519_base_noclamp(aG, a);
    int is_success_bH = crypto_scalarmult_ed25519_noclamp(bH, b, H);
    if (is_success_aG != 0 || is_success_bH != 0)
        throw logic_error("Scalar multiplication fail on aG or bH");

    int is_success_add = crypto_core_ed25519_add(aGbH, aG, bH);
    if (is_success_add != 0)
        throw logic_error("Point addition aG + bH fail due to invalid points");
}

// aKbH, where a and b are scalar, and K and B are the points
void add_key(BYTE *aKbH, const BYTE *a, const BYTE *K, const BYTE *b,
             const BYTE *H)
{
    BYTE aK[crypto_scalarmult_ed25519_BYTES];
    BYTE bH[crypto_scalarmult_ed25519_BYTES];

    // check value, skip for now

    int is_success_aK = crypto_scalarmult_ed25519_noclamp(aK, a, K);
    int is_success_bH = crypto_scalarmult_ed25519_noclamp(bH, b, H);
    if (is_success_aK != 0 || is_success_bH != 0)
        throw logic_error("Scalar multiplication fail on aK or bH");

    int is_success_add = crypto_core_ed25519_add(aKbH, aK, bH);
    if (is_success_add != 0)
        throw logic_error("Point addition aK + bH fail due to invalid points");
}

// input: user with public key (the private key is present here but is no harm as long CA is not compromised)
// output: stealth_address (one time public key)  and rG (transaction public key)
void compute_stealth_address(StealthAddress &stealth_address, const User &receiver)
{
    crypto_core_ed25519_scalar_random(stealth_address.r);

    BYTE r_pkV_b[32];
    int is_success = crypto_scalarmult_ed25519_noclamp(r_pkV_b, stealth_address.r, receiver.pkV);

    if (is_success != 0)
    {
        cout << "Scalar operation on r * pkV_b fail" << endl;
        return;
    }

    BYTE hn_r_pkV_b[32];
    hash_to_scalar(hn_r_pkV_b, r_pkV_b, crypto_core_ed25519_SCALARBYTES);

    BYTE G_hn_r_pkV_b[32];
    is_success = crypto_scalarmult_ed25519_base_noclamp(G_hn_r_pkV_b, hn_r_pkV_b);

    if (is_success != 0)
        throw logic_error("Scalar operation of G with hash scalar fails");

    is_success = crypto_core_ed25519_add(stealth_address.pk, G_hn_r_pkV_b, receiver.pkS);

    if (is_success != 0)
        throw logic_error("Point addition for stealth address fail due to invalid point");

    // compute rG
    crypto_scalarmult_ed25519_base_noclamp(stealth_address.rG, stealth_address.r);
}

// when store the stealth address in the db, need to mix up the order of the stealth address
// as people could conclude the address belongs to the same person
void CA_generate_address(vector<StealthAddress> &address_list, const vector<User> &users)
{
    // Modify to pass r
    // vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>> r(users.size());
    for (int i = 0; i < users.size(); i++)
    {
        StealthAddress address;
        compute_stealth_address(address, users[i]);
        address_list.push_back(address);
    }
}

// assume receiver scan through the network and try to compute does the stealth
// address belongs to receiver
bool receiver_test_stealth_address(StealthAddress &stealth_address, const User &receiver)
{
    BYTE rG_skV[32];
    BYTE scalar_skV[32];
    BYTE seed_skV[32];
    // prevent buffer overflow
    memcpy(seed_skV, receiver.skV, 32);
    extract_scalar_from_sk(scalar_skV, seed_skV);

    int is_success = crypto_scalarmult_ed25519_noclamp(rG_skV, scalar_skV, stealth_address.rG);
    if (is_success != 0)
        cout << "Scalar operation failure in rG_skV." << endl;

    BYTE hn_rG_skV[32];
    hash_to_scalar(hn_rG_skV, rG_skV, 32);

    BYTE stealth_address_sk[32];
    BYTE scalar_skS[32];
    BYTE seed_skS[32];
    // prevent buffer overflow
    memcpy(seed_skS, receiver.skS, 32);
    extract_scalar_from_sk(scalar_skS, seed_skS);

    crypto_core_ed25519_scalar_add(stealth_address_sk, scalar_skS, hn_rG_skV);

    // is the stealth address belongs to the receiver?
    StealthAddress test_stealth_address;
    crypto_scalarmult_ed25519_base_noclamp(test_stealth_address.pk, stealth_address_sk);

    // set the sk if the stealth address belongs to the receiver
    if (memcmp(stealth_address.pk, test_stealth_address.pk, crypto_core_ed25519_BYTES) == 0)
    {
        cout << "Stealth address belongs to the receiver" << endl;
        stealth_address.set_stealth_address_secretkey(stealth_address_sk);
        return true;
    }
    return false;
}

// using a secured pseudo random number generator to shuffle the vector
// performing swap operation based on the random number generated
void mix_address(vector<StealthAddress> &vec)
{
    // perform 5 times of shuffling
    for (int shuffle = 0; shuffle < 5; shuffle++)
    {
        for (int i = vec.size() - 1; i > 0; i--)
        {
            int random_index = randombytes_uniform(i + 1); // mod i + 1 to get the range
            swap(vec[i], vec[random_index]);
        }
    }
}

// use a secured pseudo random number generator to generate the secret index
// using /dev/urandom
int secret_index_gen(size_t n)
{
    return randombytes_uniform(n);
}

// compute m
// H(tx_prefix) = H(keyiamge || candidate stealth address || ringmember stealth address || rG)
// H(ss) = H(pseduout_commitment || amount mask || output blindingfactor mask || output commitment)
// H(rangeproof)
// m = H(H(tx_prefix) || H(ss) || H(rangeproof))
void compute_message(blsagSig& blsag, const StealthAddress& sa, const Commitment& commitment){

    string keyimage, candidate_stealth_address, rG;


    to_string(keyimage, blsag.key_image, 32);
    to_string(candidate_stealth_address, sa.pk, 32);
    to_string(rG, sa.rG, 32);
    // TODO missing ring member stealth address


    // TODO need change if in the future one to many
    string pseudout_commitment, amount_mask, output_blindingfactor_mask, output_commitment;
    to_string(pseudout_commitment, commitment.pseudoouts_commitments[0].data(), 32);
    to_string(amount_mask, commitment.amount_masks[0].data(), 8);
    to_string(output_blindingfactor_mask, commitment.outputs_blindingfactor_masks[0].data(), 32);
    to_string(output_commitment, commitment.outputs_commitments[0].data(), 32);

    string tx_prefix = keyimage + candidate_stealth_address + rG;
    string ss = pseudout_commitment + amount_mask + output_blindingfactor_mask + output_commitment;

    // TODO missing rangeproof


    vector<BYTE> tx_prefix_byte(tx_prefix.begin(), tx_prefix.end());
    vector<BYTE> ss_byte(ss.begin(), ss.end());

    BYTE H_tx_prefix[32];
    BYTE H_ss[32];


    crypto_generichash(H_tx_prefix, 32, tx_prefix_byte.data(), tx_prefix_byte.size(), NULL, 0);
    crypto_generichash(H_ss, 32, ss_byte.data(), ss_byte.size(), NULL, 0);


    BYTE H_tx_prefix_H_ss[64];
    memcpy(H_tx_prefix_H_ss, H_tx_prefix, 32);
    memcpy(H_tx_prefix_H_ss + 32, H_ss, 32);

    crypto_generichash(blsag.m, 32, H_tx_prefix_H_ss, 64, NULL, 0);
}

void compute_key_image(blsagSig &blsagSig, const StealthAddress &signerSA)
{
    BYTE Hp_stealth_address[crypto_core_ed25519_BYTES];
    hash_to_point(Hp_stealth_address, signerSA.pk, crypto_core_ed25519_BYTES);
    if (crypto_scalarmult_ed25519_noclamp(blsagSig.key_image, signerSA.sk, Hp_stealth_address) != 0)
    {
        throw logic_error("Failed to compute key image");
    }
}

// ignore ring creation and m(commitment), mixing
// thus the index this sample construction serve no concealing purpose
// the purpose of this is to prove the calculation is correct and could be verified
// in implementation, only the signerap has the secret key
// the rest of the members only have the public key for the Stealthaddress
// m is random, default to 32 BYTE
void blsag_simple_gen(blsagSig &blsagSig, const BYTE *m, const size_t secret_index, const StealthAddress &signerSA, const vector<StealthAddress> &decoy)
{
    cout << "======================" << endl;
    cout << "BLSAG simple gen" << endl;
    // TODO check each parameter

    // 0. mix the decoy
    vector<StealthAddress> all_members(decoy);
    mix_address(all_members);

    insertAtIndex(all_members, secret_index, signerSA);
    cout << "All members: " << all_members.size() << endl;

    // 1. compute key image
    // BYTE key_image[crypto_core_ed25519_BYTES];
    BYTE Hp_stealth_address[crypto_core_ed25519_BYTES];
    BYTE test_key_image[crypto_core_ed25519_BYTES];
    hash_to_point(Hp_stealth_address, signerSA.pk, crypto_core_ed25519_BYTES);
    if (crypto_scalarmult_ed25519_noclamp(test_key_image, signerSA.sk, Hp_stealth_address) != 0)
    {
        throw std::runtime_error("Failed to compute test key image");
    }
    if (sodium_memcmp(test_key_image, blsagSig.key_image, crypto_core_ed25519_BYTES) != 0)
    {
        throw logic_error("Key image comparison mismatch");
    }

    // 2.1 generate random alpha (scalar) for the ring signature
    BYTE alpha[crypto_core_ed25519_SCALARBYTES];
    crypto_core_ed25519_scalar_random(alpha);

    cout << "Generating random Alpha: " << endl;
    print_hex(alpha, crypto_core_ed25519_SCALARBYTES);
    cout << endl;

    // 2.2 generate random r_i for each i except the secret index
    vector<array<BYTE, 32>> r(all_members.size()); // ady initialised
    for (int i = 0; i < all_members.size(); i++)
    {
        if (i == secret_index)
            continue; // use this to simulate null
        else
        {
            array<BYTE, 32> r_i;
            crypto_core_ed25519_scalar_random(r_i.data());
            r[i] = r_i;
        }
    }

    int r_index = 0;
    for (auto &r_i : r)
    {
        cout << "Random r" << r_index++ << ": " << endl;
        print_hex(r_i.data(), crypto_core_ed25519_SCALARBYTES);
    }
    cout << endl;

    // 3. compute initial challenge, i = secret index, c_pi_+1 = H(m || alpha_G || alpha_Hp_stealth_address)
    BYTE c_initial[crypto_core_ed25519_SCALARBYTES];
    BYTE alpha_G[crypto_core_ed25519_BYTES];
    BYTE alpha_Hp_stealth_address[crypto_core_ed25519_BYTES];

    crypto_scalarmult_ed25519_base_noclamp(alpha_G, alpha);
    // use the secret index stealth address
    hash_to_point(Hp_stealth_address, all_members[secret_index].pk, crypto_core_ed25519_BYTES);
    if (crypto_scalarmult_ed25519_noclamp(alpha_Hp_stealth_address, alpha, Hp_stealth_address) != 0)
    {
        throw std::runtime_error("Failed to compute alpha_Hp_stealth_address");
    }

    size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
    vector<BYTE> to_hash(total_length);
    copy(m, m + crypto_core_ed25519_BYTES, to_hash.begin());
    copy(alpha_G, alpha_G + crypto_core_ed25519_BYTES, to_hash.begin() + crypto_core_ed25519_BYTES);
    // need to change the length when m is not random
    copy(alpha_Hp_stealth_address, alpha_Hp_stealth_address + crypto_core_ed25519_BYTES, to_hash.begin() + 2 * crypto_core_ed25519_BYTES);

    hash_to_scalar(c_initial, to_hash.data(), total_length);

    array<BYTE, 32> c_initial_arr;
    memcpy(c_initial_arr.data(), c_initial, crypto_core_ed25519_SCALARBYTES);

    int n = all_members.size();
    int challenge_index = secret_index + 1 == n ? 0 : secret_index + 1;
    int current_index = secret_index;
    vector<array<BYTE, crypto_core_ed25519_SCALARBYTES>>
        c(n);

    if (secret_index >= n)
        cerr << "Error: secret index out of bound of n" << endl;
    c[challenge_index++] = c_initial_arr;
    current_index++;

    // 4. compute c_i for each i
    // pair.first is the index, pair.second is the challenge
    while (n > 0)
    {
        // if secret index is the last one
        if (challenge_index == n)
            challenge_index = 0;

        if (current_index == n)
            current_index = 0;

        // TODO when does it stop, is it challenge index  or member index???
        if (current_index == secret_index)
            break;

        if (challenge_index > n)
            cerr << "Error: current index exceed n" << endl;

        // compute subsequent challenge
        BYTE ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        BYTE Hp_Ki[crypto_core_ed25519_BYTES];
        BYTE ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, r[current_index].data(), c[current_index].data(), all_members[current_index].pk);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, all_members[current_index].pk, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, r[current_index].data(), Hp_Ki, c[current_index].data(), blsagSig.key_image);

        // 3. concatenate and hash to scalar
        size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
        vector<BYTE> to_hash(total_length);
        copy(m, m + crypto_core_ed25519_BYTES, to_hash.begin());
        copy(ri_G_ci_Ki, ri_G_ci_Ki + crypto_core_ed25519_BYTES, to_hash.begin() + crypto_core_ed25519_BYTES);
        copy(ri_Hp_Ki_ci_Keyimage, ri_Hp_Ki_ci_Keyimage + crypto_core_ed25519_BYTES, to_hash.begin() + 2 * crypto_core_ed25519_BYTES);
        hash_to_scalar(c[challenge_index].data(), to_hash.data(), total_length);

        // loop action
        current_index++;
        challenge_index++;
    }

    int j = 0;
    for (auto &c_i : c)
    {
        cout << "Challenge " << j << ": " << endl;
        print_hex(c_i.data(), crypto_core_ed25519_SCALARBYTES);
        j++;
    }
    cout << endl;

    // 5. define real response r_secret_index = alpha - c_secret_index * sk_secret_index mod l
    BYTE c_stealth_address_secretkey[crypto_core_ed25519_SCALARBYTES];
    crypto_core_ed25519_scalar_mul(c_stealth_address_secretkey, c[secret_index].data(), all_members[secret_index].sk);
    crypto_core_ed25519_scalar_sub(r[secret_index].data(), alpha, c_stealth_address_secretkey);

    int k = 0;
    for (auto &r_i : r)
    {
        cout << "Response r: " << k++ << endl;
        print_hex(r_i.data(), crypto_core_ed25519_SCALARBYTES);
    }
    cout << endl;

    // 6. publish the ring
    memcpy(blsagSig.c, c[0].data(), 32);
    blsagSig.r.clear();
    blsagSig.r.assign(r.begin(), r.end());

    for (auto &mem : all_members)
        sodium_memzero(mem.sk, 32);

    blsagSig.members.assign(all_members.begin(), all_members.end());

    cout << "BLSAG Signature: " << endl;
    cout << "Key image: " << endl;
    print_hex(blsagSig.key_image, crypto_core_ed25519_BYTES);
    cout << "Challenge: " << endl;
    print_hex(blsagSig.c, crypto_core_ed25519_SCALARBYTES);
    cout << "Response: " << endl;
    for (auto &res : blsagSig.r)
    {
        print_hex(res.data(), crypto_core_ed25519_SCALARBYTES);
    }
}

bool blsag_simple_verify(const blsagSig &blsagSig, const BYTE *m)
{
    cout << "BLSAG simple verify" << endl;

    cout << "c 1 " << endl;
    print_hex(blsagSig.c, crypto_core_ed25519_SCALARBYTES);
    cout << "r :" << endl;
    for (auto &r_i : blsagSig.r)
        print_hex(r_i.data(), crypto_core_ed25519_SCALARBYTES);
    cout << endl;

    int n = blsagSig.members.size();
    int loop_counter = n;
    int current_index = 0;
    int challenge_index = current_index + 1 == n ? 0 : current_index + 1;
    vector<array<BYTE, 32>> c(n);
    array<BYTE, 32> received_c1;
    memcpy(received_c1.data(), blsagSig.c, 32);
    c[0] = received_c1; // have to use the provided c1, then compare it against computed c1

    while (loop_counter > 0)
    {
        current_index = current_index == n ? 0 : current_index;
        challenge_index = challenge_index == n ? 0 : challenge_index;

        // compute every challenge
        BYTE ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        BYTE Hp_Ki[crypto_core_ed25519_BYTES];
        BYTE ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, blsagSig.r[current_index].data(), c[current_index].data(), blsagSig.members[current_index].pk);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, blsagSig.members[current_index].pk, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, blsagSig.r[current_index].data(), Hp_Ki, c[current_index].data(), blsagSig.key_image);

        // 3. concatenate and hash to scalar
        size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
        vector<BYTE> to_hash(total_length);
        copy(m, m + crypto_core_ed25519_BYTES, to_hash.begin());
        copy(ri_G_ci_Ki, ri_G_ci_Ki + crypto_core_ed25519_BYTES, to_hash.begin() + crypto_core_ed25519_BYTES);
        copy(ri_Hp_Ki_ci_Keyimage, ri_Hp_Ki_ci_Keyimage + crypto_core_ed25519_BYTES, to_hash.begin() + 2 * crypto_core_ed25519_BYTES);

        // on the last step compare if provided c_1 is equal to computed c_1
        if (loop_counter == 1)
        {
            BYTE computed_c1[crypto_core_ed25519_SCALARBYTES];
            hash_to_scalar(computed_c1, to_hash.data(), total_length);
            cout << "Computed c_1: " << endl;
            print_hex(computed_c1, crypto_core_ed25519_SCALARBYTES);
            cout << "Comparison received c_1 and computed c_1" << endl;
            if (memcmp(blsagSig.c, computed_c1, crypto_core_ed25519_SCALARBYTES) == 0)
            {
                cout << "c_1 is equal to computed c_1" << endl;
                return true;
            }
            else
            {
                cout << "c_1 is not equal to computed c_1" << endl;
                return false;
            }
        }
        else
            hash_to_scalar(c[challenge_index].data(), to_hash.data(), total_length);

        // loop action
        current_index++;
        challenge_index++;
        loop_counter--;
    }
    cout << "Verification fail" << endl;
    return false;
}
