#include "rctType.h"

void to_string(string *output, const BYTE *key, const size_t n)
{
    ostringstream oss;
    for (size_t i = 0; i < n; i++)
    {
        oss << hex << setw(2) << setfill('0') << int(key[i]);
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

void compare_BYTE(const BYTE *a, const BYTE *b, const size_t n)
{
    if (memcmp(a, b, n) == 0)
        cout << "Both BYTE strings equal" << endl;
    else
        cout << "WARNING>> Both BYTE strings are not equal" << endl;
}

// input long long is guaranteed at least 64bit == 8 BYTE, output in little endian
void int_to_scalar_BYTE(BYTE *out, const long long input)
{
    memset(out, 0, crypto_core_ed25519_SCALARBYTES); // use 32 BYTE for now, if to use 8 BYTE, probably need to come up with own scalar multiplication funciton
    // overflow if > 32 BYTE, but not possible
    memcpy(out, &input, sizeof(input));
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
        cout << "scalar multiplication fail on aG or bH" << endl;

    int is_success_add = crypto_core_ed25519_add(aGbH, aG, bH);
    if (is_success_add != 0)
        cout << "point addition aG + bH fail due to invalid points" << endl;
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
        cout << "scalar multiplication fail on aK or bH" << endl;

    int is_success_add = crypto_core_ed25519_add(aKbH, aK, bH);
    if (is_success_add != 0)
        cout << "point addition aK + bH fail due to invalid points" << endl;
}

// use by CA
// TODO do i need another one for normal voter
// input: user with public key (the private key is present here but is no harm as long CA is not compromised)
// output: stealth_address (one time public key)  and rG (transaction public key)
void compute_stealth_address(StealthAddress &stealth_address, const User &receiver)
{
    cout << "======================" << endl;
    cout << "Inside compute_stealth_address" << endl;
    BYTE r[32];
    crypto_core_ed25519_scalar_random(r);
    cout << "r " << endl;
    print_hex(r, crypto_core_ed25519_SCALARBYTES);
    cout << "pkV " << endl;
    print_hex(receiver.pkV, crypto_core_ed25519_BYTES);

    BYTE r_pkV_b[32];
    int is_success = crypto_scalarmult_ed25519_noclamp(r_pkV_b, r, receiver.pkV);
    cout << "r_pkV_b: " << endl;
    print_hex(r_pkV_b, crypto_core_ed25519_BYTES);

    if (is_success != 0)
    {
        cout << "Scalar operation on r * pkV_b fail" << endl;
        return;
    }

    BYTE hn_r_pkV_b[32];
    hash_to_scalar(hn_r_pkV_b, r_pkV_b, crypto_core_ed25519_SCALARBYTES);

    BYTE G_hn_r_pkV_b[32];
    is_success = crypto_scalarmult_ed25519_base_noclamp(G_hn_r_pkV_b, hn_r_pkV_b);

    cout << "G_hn_r_pkV_b: " << endl;
    print_hex(G_hn_r_pkV_b, crypto_core_ed25519_BYTES);

    if (is_success != 0)
        cout << "Scalar operation of G with hash scalar fails" << endl;

    is_success = crypto_core_ed25519_add(stealth_address.pk, G_hn_r_pkV_b, receiver.pkS);
    if (is_success != 0)
        cout << "Point addition for stealth address fail due to invalid point" << endl;

    // compute rG
    crypto_scalarmult_ed25519_base_noclamp(stealth_address.rG, r);

    cout << "rG " << endl;
    print_hex(stealth_address.rG, crypto_core_ed25519_BYTES);

    cout << "======================" << endl;
}

// TODO when store the stealth address in the db, need to mix up the order of the stealth address
// as people could conclude the address belongs to the same person
void CA_generate_address(vector<StealthAddress> &address_list, const vector<User> &users)
{
    for (const User &user : users)
    {
        StealthAddress address;
        compute_stealth_address(address, user);
        address_list.push_back(address);
    }
}

// assume receiver scan through the network and try to compute does the stealth
// address belongs to receiver
bool receiver_test_stealth_address(StealthAddress &stealth_address, const User &receiver)
{
    cout << "======================" << endl;
    cout << "Inside receiver test stealth addrss" << endl;
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

    cout << "Stealth address secret key: " << endl;
    print_hex(stealth_address_sk, crypto_core_ed25519_SCALARBYTES);

    // is the stealth address belongs to the receiver?
    StealthAddress test_stealth_address;
    crypto_scalarmult_ed25519_base_noclamp(test_stealth_address.pk, stealth_address_sk);

    cout << "Stealth address : " << endl;
    print_hex(stealth_address.pk, crypto_core_ed25519_BYTES);
    cout << "Test stealth address: " << endl;
    print_hex(test_stealth_address.pk, crypto_core_ed25519_BYTES);

    // set the sk if the stealth address belongs to the receiver
    if (memcmp(stealth_address.pk, test_stealth_address.pk, crypto_core_ed25519_BYTES) == 0)
    {
        cout << "Stealth address belongs to the receiver" << endl;
        stealth_address.set_stealth_address_secretkey(stealth_address_sk);
        return true;
    }
    return false;
}

void public_network_stealth_address_communication(vector<StealthAddress> address_list, const vector<User> &users)
{
    for (int i = 0; i < users.size(); i++)
    {
        cout << "User " << i << " test stealth address" << endl;
        for (int j = 0; j < address_list.size(); j++)
        {
            if (receiver_test_stealth_address(address_list[j], users[i]))
            {
                cout << "stealth address " << j << " belongs to user " << i << endl;
                break;
            }
        }
        cout << "=====================" << endl;
    }
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

// ignore ring creation and m(commitment), mixing
// thus the index this sample construction serve no concealing purpose
// the purpose of this is to prove the calculation is correct and could be verified
// in implementation, only the signerap has the secret key
// the rest of the members only have the public key for the Stealthaddress
// m is random, default to 32 BYTE
void blsag_simple_gen(blsagSig &blsagSig, const unsigned char *m, const size_t secret_index, const StealthAddress &signerSA, const vector<StealthAddress> &decoy)
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
    // unsigned char key_image[crypto_core_ed25519_BYTES];
    BYTE Hp_stealth_address[crypto_core_ed25519_BYTES];
    hash_to_point(Hp_stealth_address, signerSA.pk, crypto_core_ed25519_BYTES);
    crypto_scalarmult_ed25519_noclamp(blsagSig.key_image, signerSA.sk, Hp_stealth_address);

    cout << "Compute Key image: " << endl;
    print_hex(blsagSig.key_image, crypto_core_ed25519_BYTES);
    cout << endl;

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
    crypto_scalarmult_ed25519_noclamp(alpha_Hp_stealth_address, alpha, Hp_stealth_address);

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
    vector<array<unsigned char, crypto_core_ed25519_SCALARBYTES>>
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
        unsigned char ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        unsigned char Hp_Ki[crypto_core_ed25519_BYTES];
        unsigned char ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, r[current_index].data(), c[current_index].data(), all_members[current_index].pk);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, all_members[current_index].pk, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, r[current_index].data(), Hp_Ki, c[current_index].data(), blsagSig.key_image);

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

bool blsag_simple_verify(const blsagSig &blsagSig, const unsigned char *m)
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
        unsigned char ri_G_ci_Ki[crypto_core_ed25519_BYTES];
        unsigned char Hp_Ki[crypto_core_ed25519_BYTES];
        unsigned char ri_Hp_Ki_ci_Keyimage[crypto_core_ed25519_BYTES];

        // 1. compute ri_G + ci_Ki
        add_key(ri_G_ci_Ki, blsagSig.r[current_index].data(), c[current_index].data(), blsagSig.members[current_index].pk);

        // 2. compute ri_Hp_Ki + ci_Keyimage
        hash_to_point(Hp_Ki, blsagSig.members[current_index].pk, crypto_core_ed25519_BYTES);
        add_key(ri_Hp_Ki_ci_Keyimage, blsagSig.r[current_index].data(), Hp_Ki, c[current_index].data(), blsagSig.key_image);

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

int main()
{
    if (sodium_init() == -1)
    {
        cout << "Sodium Init failed" << endl;
        return 1;
    }

    // User user1;

    // BYTE scalar_skS[crypto_core_ed25519_SCALARBYTES];
    // BYTE seed_skS[crypto_core_ed25519_BYTES];
    // // need to input the seed from the user instead of using the skS(seed + pk)
    // // will result in buffer overflow
    // memcpy(seed_skS, user1.skS, crypto_core_ed25519_BYTES);
    // extract_scalar_from_sk(scalar_skS, seed_skS);
    // BYTE computed_pkS[crypto_core_ed25519_BYTES];
    // crypto_scalarmult_ed25519_base(computed_pkS, scalar_skS);
    // cout << "User1 pkS: " << endl;
    // print_hex(user1.pkS, crypto_core_ed25519_BYTES);
    // cout << "User1 computed pkS: " << endl;
    // print_hex(computed_pkS, crypto_core_ed25519_BYTES);
    // compare_BYTE(user1.pkS, computed_pkS, crypto_core_ed25519_BYTES);

    // // test compute_stealth_address
    // User CA, bob, charlie;
    // StealthAddress bob_stealth_address, charlie_stealth_address;
    // compute_stealth_address(bob_stealth_address, bob);

    // cout << "bob test stealth address" << endl;
    // receiver_test_stealth_address(bob_stealth_address, bob);

    // // test with many user
    // vector<User> users(11);
    // vector<StealthAddress> address_list;

    // CA_generate_address(address_list, users);
    // public_network_stealth_address_communication(address_list, users);

    // test with blsag
    for (int i = 0; i < 1000; i++)
    {
        vector<User> users_blsag(10);
        vector<StealthAddress> blsagSA; // decoy
        int secret_index = secret_index_gen(users_blsag.size());
        CA_generate_address(blsagSA, users_blsag);

        User signer;
        StealthAddress signerSA;
        compute_stealth_address(signerSA, signer);
        receiver_test_stealth_address(signerSA, signer);

        blsagSig blsagSig;
        BYTE m[32];
        crypto_core_ed25519_scalar_random(m);

        blsag_simple_gen(blsagSig, m, secret_index, signerSA, blsagSA);
        bool is_verified = blsag_simple_verify(blsagSig, m);
        if (!is_verified)
        {
            cout << "Verification fail" << endl;
            exit(1);
        }
        cout << "Verification success on " << i + 1 << endl;
    }

    return 0;
}