#ifndef CUSTOM_EXCEPTION_H
#define CUSTOM_EXCEPTION_H

#include <exception>
#include <sstream>

// enum class RingCTErrorCode {
//     CORE_DOUBLE_VOTING = 101,
// };

template<typename ErrorCode_T>
class CustomException : public exception {
    public:
    CustomException(const string&message, const ErrorCode_T& errorcode) : message_(message), errorcode_(errorcode) {
        ostringstream oss;
        oss << "Error code: " << errorcode_ << " >> " << message_;
        fullmessage_ = oss.str();
    }

    virtual const char* what() const noexcept override {
        return fullmessage_.c_str();
    }

    ErrorCode_T getErrorCode() const {
        return errorcode_;
    }

    private:
    string message_;
    ErrorCode_T errorcode_;
    string fullmessage_;
};

#endif