#ifndef TEST_UTIL_H
#define TEST_UTIL_H

#include <vector>
#include <string>
#include <sodium.h>

int sc25519_is_canonical(const unsigned char s[32]);
std::vector<std::string> tokeniser(const std::string &aline, const char delimeter = ' ');

extern unsigned char fixed_random_seed[randombytes_SEEDBYTES];
extern unsigned long long counter;

const char *get_implementation_name(void);
uint32_t deterministic_random(void);
void deterministic_buf(void *const buf, const size_t size);

extern randombytes_implementation deterministic_implementation;

#endif
