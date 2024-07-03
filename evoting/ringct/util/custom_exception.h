#ifndef CUSTOM_EXCEPTION_H
#define CUSTOM_EXCEPTION_H

#include <exception>
#include <sstream>

#define ENUM_TO_STRING(x) case x: return #x;

enum class RingCTErrorCode {
    CORE_DOUBLE_VOTING = 101,
    NO_CANDIDATE_IN_DISTRICT = 201,
};

template<typename ErrorCode_T>
class CustomException : public std::exception {
    public:
    CustomException(const std::string&message, const ErrorCode_T& errorcode) : message_(message), errorcode_(errorcode) {
        std::ostringstream oss;
        oss << errorcode_ << " " << message_;
        fullmessage_ = oss.str();
    }

    virtual const char* what() const noexcept override {
        return fullmessage_.c_str();
    }

    ErrorCode_T getErrorCode() const {
        return errorcode_;
    }

    private:
    std::string message_;
    ErrorCode_T errorcode_;
    std::string fullmessage_;
};

std::string enumToString (RingCTErrorCode errorCode);
#endif