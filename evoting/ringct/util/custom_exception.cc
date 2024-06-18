#include "custom_exception.h"
#include <string>

using namespace std;

string enumToString (RingCTErrorCode errorCode){
    switch (errorCode)
    {
        ENUM_TO_STRING(RingCTErrorCode::CORE_DOUBLE_VOTING)
        default: return "Unknown error code";
    }
}