#include "test_util.h"
#include <sstream>
#include <vector>
#include <string>
using namespace std;

unsigned char fixed_random_seed[randombytes_SEEDBYTES];
unsigned long long counter = 0;

randombytes_implementation deterministic_implementation = {
    get_implementation_name,
    deterministic_random,
    NULL,
    NULL,
    deterministic_buf,
    NULL
};

int sc25519_is_canonical(const unsigned char s[32])
{
    /* 2^252+27742317777372353535851937790883648493 */
    static const unsigned char L[32] = {
        0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7,
        0xa2, 0xde, 0xf9, 0xde, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10
    };
    unsigned char c = 0;
    unsigned char n = 1;
    unsigned int  i = 32;

    do {
        i--;
        c |= ((s[i] - L[i]) >> 8) & n;
        n &= ((s[i] ^ L[i]) - 1) >> 8;
    } while (i != 0);

    return (c != 0);
}

vector<string> tokeniser(const string &aline, const char delimeter)
{
    vector<string> tokens;
    string token;
    istringstream input(aline);
    while (getline(input, token, delimeter))
    {
        tokens.push_back(token);
    }
    return tokens;
}

const char *get_implementation_name(void)
{
    return "deterministic_random";
}

uint32_t deterministic_random(void)
{
    uint32_t result;
    unsigned char tmp[4];

    for (int i = 0; i < 4; i++)
    {
        if (counter % 64 == 0)
        {
            crypto_stream_chacha20(tmp, sizeof tmp, (unsigned char *)&counter, fixed_random_seed);
        }
        ((unsigned char *)&result)[i] = tmp[counter % 64];
        counter++;
    }

    return result;
}

void deterministic_buf(void *const buf, const size_t size)
{
    unsigned char tmp[64];
    size_t i;

    for (i = 0; i < size; i++)
    {
        if (counter % 64 == 0)
        {
            crypto_stream_chacha20(tmp, sizeof tmp, (unsigned char *)&counter, fixed_random_seed);
        }
        ((unsigned char *)buf)[i] = tmp[counter % 64];
        counter++;
    }
}

// Sample usage
/**     {
        // set fixed randomness
        memset(fixed_random_seed, 0x4f, sizeof(fixed_random_seed)); // you can set whatever you want for the seed
        counter = 0;
        randombytes_set_implementation(&deterministic_implementation);

        cout << "inside test randomness" << endl;
        BYTE r[32];
        crypto_core_ed25519_scalar_random(r);
        print_hex(r, 32);

        // clear fixed randomness
        randombytes_set_implementation(NULL);
    }
*/
