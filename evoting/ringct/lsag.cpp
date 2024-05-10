#include <algorithm>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <sodium.h>
#include <vector>
#include <array>

using namespace std;

#define H_String          \
    ((const unsigned char \
          *)"This is used as H string generation, no one knows this secret")
#define H_Len 61

struct User
{
    unsigned char skV[crypto_sign_SECRETKEYBYTES];
    unsigned char pkV[crypto_sign_PUBLICKEYBYTES];
    unsigned char skS[crypto_sign_SECRETKEYBYTES];
    unsigned char pkS[crypto_sign_PUBLICKEYBYTES];
    User()
    {
        crypto_sign_keypair(pkV, skV);
        crypto_sign_keypair(pkS, skS);
    }
};

struct AddressPair
{
    unsigned char stealth_address[crypto_core_ed25519_BYTES];
    unsigned char rG[crypto_core_ed25519_BYTES];
    unsigned char stealth_address_secretkey[crypto_core_ed25519_SCALARBYTES];

    AddressPair()
    {
        memset(stealth_address, 0, crypto_core_ed25519_BYTES);
        memset(rG, 0, crypto_core_ed25519_BYTES);
        memset(stealth_address_secretkey, 0, crypto_core_ed25519_SCALARBYTES);
    }
    void set_stealth_address(const unsigned char *scanned_stealth_address)
    {
        memcpy(stealth_address, scanned_stealth_address, crypto_core_ed25519_BYTES);
    }
    void set_rG(const unsigned char *scanned_rG)
    {
        memcpy(rG, scanned_rG, crypto_core_ed25519_BYTES);
    }
    void set_stealth_address_secretkey(const unsigned char *scanned_stealth_address_secretkey)
    {
        memcpy(stealth_address_secretkey, scanned_stealth_address_secretkey, crypto_core_ed25519_SCALARBYTES);
    }
};

void to_string(string *output, const unsigned char *key, const size_t n)
{
    ostringstream oss;
    for (size_t i = 0; i < n; i++)
    {
        oss << hex << setw(2) << setfill('0') << int(key[i]);
    }
}

void print_hex(const unsigned char *key, const size_t n)
{
    for (size_t i = 0; i < n; i++)
    {
        cout << hex << setw(2) << setfill('0') << int(key[i]);
    }
    cout << dec << endl;
}

void compare_byte(const unsigned char *a, const unsigned char *b, const size_t n)
{
    if (memcmp(a, b, n) == 0)
        cout << "Both byte strings equal" << endl;
    else
        cout << "WARNING>> Both byte strings are not equal" << endl;
}

// input long long is guaranteed at least 64bit == 8 byte, output in little endian
void int_to_scalar_byte(unsigned char *out, const long long input)
{
    memset(out, 0, crypto_core_ed25519_SCALARBYTES); // use 32 byte for now, if to use 8 byte, probably need to come up with own scalar multiplication funciton
    // overflow if > 32 byte, but not possible
    memcpy(out, &input, sizeof(input));
}

void generate_H(unsigned char *H)
{
    unsigned char hash[crypto_generichash_BYTES];
    unsigned char str_to_hash[H_Len + 4];
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

void hash_to_scalar(unsigned char *scalar, const unsigned char *key,
                    const size_t key_size)
{
    unsigned char hash[crypto_generichash_BYTES_MAX];
    crypto_generichash(hash, crypto_generichash_BYTES_MAX, key, key_size, NULL,
                       0);
    crypto_core_ed25519_scalar_reduce(scalar, hash);
}

void hash_to_point(unsigned char *point, const unsigned char *key, const size_t key_size)
{
    unsigned char hash[crypto_generichash_BYTES_MAX];
    crypto_generichash(hash, crypto_generichash_BYTES_MAX, key, key_size, NULL,
                       0);
    crypto_core_ed25519_from_uniform(point, hash);
}

void extract_scalar_from_sk(unsigned char *scalar, const unsigned char *seed)
{
    crypto_hash_sha512(scalar, seed, 32);
    scalar[0] &= 248;
    scalar[31] &= 127;
    scalar[31] |= 64;
}

// aGbH, where a and b are scalar, and G is the base point and B is the point
void add_key(unsigned char *aGbH, const unsigned char *a, const unsigned char *b,
             const unsigned char *H)
{
    unsigned char aG[crypto_scalarmult_ed25519_BYTES];
    unsigned char bH[crypto_scalarmult_ed25519_BYTES];

    // check value, skip for now

    int is_success_aG = crypto_scalarmult_ed25519_base_noclamp(aG, a);
    int is_success_bH = crypto_scalarmult_ed25519_noclamp(bH, b, H);
    if (is_success_aG != 0 || is_success_bH != 0)
        cout << "scalar multiplication fail on aG or bH" << endl;

    int is_success_add = crypto_core_ed25519_add(aGbH, aG, bH);
    if (is_success_add != 0)
        cout << "point addition aG + bH fail due to invalid points" << endl;
}

// aKbH, where a and b are scalar, and K and B are the points
void add_key(unsigned char *aKbH, const unsigned char *a, const unsigned char *K, const unsigned char *b,
             const unsigned char *H)
{
    unsigned char aK[crypto_scalarmult_ed25519_BYTES];
    unsigned char bH[crypto_scalarmult_ed25519_BYTES];

    // check value, skip for now

    int is_success_aK = crypto_scalarmult_ed25519_noclamp(aK, a, K);
    int is_success_bH = crypto_scalarmult_ed25519_noclamp(bH, b, H);
    if (is_success_aK != 0 || is_success_bH != 0)
        cout << "scalar multiplication fail on aK or bH" << endl;

    int is_success_add = crypto_core_ed25519_add(aKbH, aK, bH);
    if (is_success_add != 0)
        cout << "point addition aK + bH fail due to invalid points" << endl;
}

// input: the receiver public viewing key and public spending key
// output: stealth_address (one time public key)  and r (transaction secret key)
void compute_stealth_address(unsigned char *stealth_address, unsigned char *r,
                             const unsigned char *pkV_b, const unsigned char *pkS_b)
{
    crypto_core_ed25519_scalar_random(r);

    unsigned char r_pkV_b[crypto_scalarmult_ed25519_BYTES];
    int is_success = crypto_scalarmult_ed25519_noclamp(r_pkV_b, r, pkV_b);
    if (is_success != 0)
        cout << "Scalar operation on r * pkV_b fail" << endl;

    unsigned char hn_r_pkV_b[crypto_core_ed25519_SCALARBYTES];
    hash_to_scalar(hn_r_pkV_b, r_pkV_b, crypto_core_ed25519_SCALARBYTES);

    unsigned char G_hn_r_pkV_b[crypto_scalarmult_ed25519_BYTES];
    is_success = crypto_scalarmult_ed25519_base_noclamp(G_hn_r_pkV_b, hn_r_pkV_b);
    if (is_success != 0)
        cout << "Scalar operation of G with hash scalar fails" << endl;

    is_success = crypto_core_ed25519_add(stealth_address, G_hn_r_pkV_b, pkS_b);
    if (is_success != 0)
        cout << "Point addition for stealth address fail due to invalid point" << endl;
}

// assume sender could not access the receiver's private key
void sender_prep_address(unsigned char *rG, unsigned char *stealth_address, const User *receiver, const User *sender)
{
    unsigned char r[crypto_core_ed25519_SCALARBYTES];
    compute_stealth_address(stealth_address, r, receiver->pkV, receiver->pkS);
    crypto_scalarmult_ed25519_base_noclamp(rG, r);
}

// assume receiver scan through the network and try to compute does the stealth
// address belongs to receiver
void receiver_test_stealth_address(unsigned char *stealth_address_secretkey, const unsigned char *rG, const unsigned char *stealth_address, const User *receiver)
{
    unsigned char scalar_skV[crypto_core_ed25519_SCALARBYTES];
    extract_scalar_from_sk(scalar_skV, receiver->skV);
    unsigned char rG_skV[crypto_core_ed25519_BYTES];
    int is_success = crypto_scalarmult_ed25519_noclamp(rG_skV, scalar_skV, rG);
    if (is_success != 0)
        cout << "Scalar operation failure in rG_skV." << endl;

    unsigned char hn_rG_skV[crypto_core_ed25519_SCALARBYTES];
    hash_to_scalar(hn_rG_skV, rG_skV, crypto_core_ed25519_SCALARBYTES);

    unsigned char scalar_skS[crypto_core_ed25519_SCALARBYTES];
    extract_scalar_from_sk(scalar_skS, receiver->skS);
    crypto_core_ed25519_scalar_add(stealth_address_secretkey, scalar_skS, hn_rG_skV);

    // is the stealth address belongs to the receiver?
    unsigned char test_stealth_address[crypto_core_ed25519_BYTES];
    crypto_scalarmult_ed25519_base_noclamp(test_stealth_address, stealth_address_secretkey);

    cout << "Receiver comparing stealth address: " << endl;
    cout << "Stealth address: " << endl;
    print_hex(stealth_address, crypto_core_ed25519_BYTES);
    cout << "Test Stealth address: " << endl;
    print_hex(test_stealth_address, crypto_core_ed25519_BYTES);
    compare_byte(test_stealth_address, stealth_address, crypto_core_ed25519_BYTES);
}

void public_network_stealth_address_communication(AddressPair *receiver_address_pair, const User *receiver, const User *sender)
{
    // public info for the receiver
    unsigned char stealth_address[crypto_core_ed25519_BYTES];
    unsigned char rG[crypto_core_ed25519_BYTES];
    sender_prep_address(rG, stealth_address, receiver, sender);

    // assume sender cant see the stealth address secret key
    unsigned char stealth_address_secretkey[crypto_core_ed25519_SCALARBYTES];
    receiver_test_stealth_address(stealth_address_secretkey, rG, stealth_address, receiver);
    receiver_address_pair->set_stealth_address(stealth_address);
    receiver_address_pair->set_rG(rG);
    receiver_address_pair->set_stealth_address_secretkey(stealth_address_secretkey);
}

// ignore ring creation and m(commitment), mixing
// thus the index this sample construction serve no concealing purpose
// the purpose of this is to prove the calculation is correct and could be verified
// assume signer can access public key of all users only. Ignore it is struct for now
void blsag_simple_gen(vector<array<unsigned char, 32>> &signature, unsigned char *key_image, const unsigned char *m, const AddressPair *signer_ap, const User *signer, const vector<pair<User, AddressPair>> *decoy)
{
    cout << "BLSAG simple gen" << endl;

    // signer index = 1
    // decoy index = 0, 2
    int secret_index = 1;
    vector<pair<User, AddressPair>> all_members = {(*decoy)[0], {*signer, *signer_ap}, (*decoy)[1]};

    // 1. compute key image
    // unsigned char key_image[crypto_core_ed25519_BYTES];
    unsigned char Hp_stealth_address[crypto_core_ed25519_BYTES];
    hash_to_point(Hp_stealth_address, signer_ap->stealth_address, crypto_core_ed25519_BYTES);
    crypto_scalarmult_ed25519_noclamp(key_image, signer_ap->stealth_address_secretkey, Hp_stealth_address);

    cout << "Compute Key image: " << endl;
    print_hex(key_image, crypto_core_ed25519_BYTES);
    cout << endl;

    // 2.1 generate random alpha (scalar) for the ring signature
    unsigned char alpha[crypto_core_ed25519_SCALARBYTES];
    crypto_core_ed25519_scalar_random(alpha);

    cout << "Generating random Alpha: " << endl;
    print_hex(alpha, crypto_core_ed25519_SCALARBYTES);
    cout << endl;

    // 2.2 generate random r_i for each i except the secret index
    vector<array<unsigned char, crypto_core_ed25519_SCALARBYTES>> r(all_members.size()); // ady initialised
    for (int i = 0; i < all_members.size(); i++)
    {
        if (i == secret_index)
            continue; // use this to simulate null
        else
        {
            array<unsigned char, crypto_core_ed25519_SCALARBYTES> r_i;
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
    unsigned char c_initial[crypto_core_ed25519_SCALARBYTES];
    unsigned char alpha_G[crypto_core_ed25519_BYTES];
    unsigned char alpha_Hp_stealth_address[crypto_core_ed25519_BYTES];

    crypto_scalarmult_ed25519_base_noclamp(alpha_G, alpha);
    // use the secret index stealth address
    hash_to_point(Hp_stealth_address, all_members[secret_index].second.stealth_address, crypto_core_ed25519_BYTES);
    crypto_scalarmult_ed25519_noclamp(alpha_Hp_stealth_address, alpha, Hp_stealth_address);

    size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
    vector<unsigned char> to_hash(total_length);
    copy(m, m + crypto_core_ed25519_BYTES, to_hash.begin());
    copy(alpha_G, alpha_G + crypto_core_ed25519_BYTES, to_hash.begin() + crypto_core_ed25519_BYTES);
    // need to change the length when m is not random
    copy(alpha_Hp_stealth_address, alpha_Hp_stealth_address + crypto_core_ed25519_BYTES, to_hash.begin() + 2 * crypto_core_ed25519_BYTES);

    hash_to_scalar(c_initial, to_hash.data(), total_length);

    array<unsigned char, crypto_core_ed25519_SCALARBYTES> c_initial_arr;
    memcpy(c_initial_arr.data(), c_initial, crypto_core_ed25519_SCALARBYTES);

    int n = all_members.size();
    int challenge_index = secret_index + 1 == n ? 0 : secret_index + 1;
    int current_index = secret_index;
    vector<array<unsigned char, crypto_core_ed25519_SCALARBYTES>>
        c(n);

    if (secret_index >= n)
        cerr << "Error: secret index out of bound of n" << endl;
    c[challenge_index++] = c_initial_arr;
    current_index++;

    cout << "Initial challenge, i = 1, c_i = 2: " << endl;
    print_hex(c[2].data(), crypto_core_ed25519_SCALARBYTES);

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
        unsigned char ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        unsigned char Hp_Ki[crypto_core_ed25519_BYTES];
        unsigned char ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, r[current_index].data(), c[current_index].data(), all_members[current_index].second.stealth_address);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, all_members[current_index].second.stealth_address, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, r[current_index].data(), Hp_Ki, c[current_index].data(), key_image);

        // 3. concatenate and hash to scalar
        size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
        vector<unsigned char> to_hash(total_length);
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
    unsigned char c_stealth_address_secretkey[crypto_core_ed25519_SCALARBYTES];
    crypto_core_ed25519_scalar_mul(c_stealth_address_secretkey, c[secret_index].data(), all_members[secret_index].second.stealth_address_secretkey);
    crypto_core_ed25519_scalar_sub(r[secret_index].data(), alpha, c_stealth_address_secretkey);

    int k = 0;
    for (auto &r_i : r)
    {
        cout << "Response r: " << k++ << endl;
        print_hex(r_i.data(), crypto_core_ed25519_SCALARBYTES);
    }
    cout << endl;

    // 6. publish the ring
    signature[0] = c[0];
    copy(r.begin(), r.end(), signature.begin() + 1);
    for (auto &c : signature)
    {
        print_hex(c.data(), crypto_core_ed25519_SCALARBYTES);
    }
}

void blsag_simple_verify(const vector<array<unsigned char, 32>> &signature, const unsigned char *key_image, const unsigned char *m, const AddressPair &signer_ap, const User &signer, const vector<pair<User, AddressPair>> &decoy)
{
    cout << "BLSAG simple verify" << endl;

    // signer index = 1
    // decoy index = 0, 2
    int secret_index = 1;
    vector<pair<User, AddressPair>> all_members = {(decoy)[0], {signer, signer_ap}, (decoy)[1]};

    unsigned char received_c1[crypto_core_ed25519_SCALARBYTES];
    copy(signature[0].begin(), signature[0].end(), received_c1);
    vector<array<unsigned char, crypto_core_ed25519_SCALARBYTES>> r(signature.begin() + 1, signature.end());

    cout << "c 1 " << endl;
    print_hex(received_c1, crypto_core_ed25519_SCALARBYTES);
    cout << "r :" << endl;
    for (auto &r_i : r)
        print_hex(r_i.data(), crypto_core_ed25519_SCALARBYTES);
    cout << endl;

    // TODO
    int n = all_members.size();
    int loop_counter = all_members.size();
    int current_index = 0;
    int challenge_index = current_index + 1 == n ? 0 : current_index + 1;
    vector<array<unsigned char, crypto_core_ed25519_SCALARBYTES>> c(n);
    c[0] = signature[0]; // have to use the provided c1, then compare it against computed c1

    while (loop_counter > 0)
    {
        current_index = current_index == n ? 0 : current_index;
        challenge_index = challenge_index == n ? 0 : challenge_index;

        // compute every challenge
        unsigned char ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        unsigned char Hp_Ki[crypto_core_ed25519_BYTES];
        unsigned char ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, r[current_index].data(), c[current_index].data(), all_members[current_index].second.stealth_address);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, all_members[current_index].second.stealth_address, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, r[current_index].data(), Hp_Ki, c[current_index].data(), key_image);

        // 3. concatenate and hash to scalar
        size_t total_length = 2 * crypto_core_ed25519_BYTES + crypto_core_ed25519_BYTES; // TODO: last one is the rand m length
        vector<unsigned char> to_hash(total_length);
        copy(m, m + crypto_core_ed25519_BYTES, to_hash.begin());
        copy(ri_G_ci_Ki, ri_G_ci_Ki + crypto_core_ed25519_BYTES, to_hash.begin() + crypto_core_ed25519_BYTES);
        copy(ri_Hp_Ki_ci_Keyimage, ri_Hp_Ki_ci_Keyimage + crypto_core_ed25519_BYTES, to_hash.begin() + 2 * crypto_core_ed25519_BYTES);

        // on the last step compare if provided c_1 is equal to computed c_1
        if (loop_counter == 1)
        {
            unsigned char computed_c1[crypto_core_ed25519_SCALARBYTES];
            hash_to_scalar(computed_c1, to_hash.data(), total_length);
            cout << "Computed c_1: " << endl;
            print_hex(computed_c1, crypto_core_ed25519_SCALARBYTES);
            cout << "Comparison received c_1 and computed c_1" << endl;
            compare_byte(received_c1, computed_c1, crypto_core_ed25519_SCALARBYTES);
        }
        else
            hash_to_scalar(c[challenge_index].data(), to_hash.data(), total_length);

        // loop action
        current_index++;
        challenge_index++;
        loop_counter--;
    }
}

int main()
{
    cout << "C++ standard " << __cplusplus << endl;

    if (sodium_init() == -1)
        return 1;
    // test two user ring signature, i need at least 3 users to test
    // one user (CA) generates the stealth addresses for the other two users
    // one of the three users will be the sender/signer, the other users will be the decoy

    User alice, bob, charlie, danice; // assume alice is the CA
    AddressPair bob_address_pair, charlie_address_pair, danice_address_pair;
    public_network_stealth_address_communication(&bob_address_pair, &bob, &alice);
    public_network_stealth_address_communication(&charlie_address_pair, &charlie, &alice);
    public_network_stealth_address_communication(&danice_address_pair, &danice, &alice);

    cout << "======================" << endl;
    // for ring construction, let's put the m as random first
    // bob is the signer
    // random m
    unsigned char m[crypto_core_ed25519_BYTES];
    crypto_core_ed25519_random(m);
    vector<pair<User, AddressPair>> decoy = {{charlie, charlie_address_pair}, {danice, danice_address_pair}};
    vector<array<unsigned char, 32>> signature(4); // 1 challenge, 3 responses
    unsigned char key_image[crypto_core_ed25519_BYTES];

    blsag_simple_gen(signature, key_image, m, &bob_address_pair, &bob, &decoy);
    cout << "======================" << endl;

    blsag_simple_verify(signature, key_image, m, bob_address_pair, bob, decoy);
    cout << "======================" << endl;

    cout << "Size of various bytes: " << endl;
    cout << crypto_core_ed25519_BYTES << endl;
    cout << crypto_scalarmult_curve25519_BYTES << endl;
    cout << crypto_core_ed25519_SCALARBYTES << endl;
    cout << crypto_scalarmult_curve25519_SCALARBYTES << endl;
}

