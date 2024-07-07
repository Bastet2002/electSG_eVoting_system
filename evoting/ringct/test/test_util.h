#ifndef TEST_UTIL_H
#define TEST_UTIL_H

#include <vector>
#include <string>

int sc25519_is_canonical(const unsigned char s[32]);
std::vector<std::string> tokeniser(const std::string &aline, const char delimeter = ' ');

#endif