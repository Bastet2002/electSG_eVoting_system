#include "../rct/rctType.h"
#include "../rct/rctOps.h"
#include "test_util.h"
#include <catch2/catch_all.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>

static unsigned char fixed_random_seed[randombytes_SEEDBYTES];
static unsigned long long counter = 0;

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

// https://github.com/jedisct1/libsodium/blob/master/src/libsodium/include/sodium/randombytes.h#L19
// it utilise function pointer to set the randomness
static randombytes_implementation deterministic_implementation = {
    .implementation_name = get_implementation_name,
    .random = deterministic_random,
    .stir = NULL,
    .uniform = NULL,
    .buf = deterministic_buf,
    .close = NULL,
};

SCENARIO("Test fixed randomness", "[test]")
{
    // The test will always have a fixed r throughout the test
    GIVEN("Given the fixed randomness, does the r result the same if rerun?")
    {
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
}