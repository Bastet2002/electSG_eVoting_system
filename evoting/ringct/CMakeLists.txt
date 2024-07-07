cmake_minimum_required(VERSION 3.10)

project(RingCTServer C CXX)

include(./common.cmake)

# libpqxx 7 requires at least C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF) # ensure code adheres to the C++17 standard without non-standard extensions

# for libsodium
find_library(sodium_library NAMES sodium)
find_path(sodium_include_dir NAMES sodium.h)

if (sodium_library AND sodium_include_dir)
    message(STATUS "Found libsodium: ${sodium_library}")
    message(STATUS "Found libsodium include dir: ${sodium_include_dir}")
else()
    message(FATAL_ERROR "libsodium not found")
endif()

include_directories(${sodium_include_dir})

# for git repo download on the /libpqxx
add_subdirectory(/libpqxx build-pqxx)
target_link_libraries(pqxx)

# fmt using fetch to avoid long rebuilding time in docker
include(FetchContent)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.2.1 
)
FetchContent_MakeAvailable(fmt)

# include nlohmann/json for json parsing
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)

# catch 2 for cpp unit, integration test
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.4.0 # or a later release
)
FetchContent_MakeAvailable(Catch2)


# proto file
get_filename_component(rct_proto "./proto/ringct.proto" ABSOLUTE)
get_filename_component(rct_proto_path "${rct_proto}" PATH)

# generated sources
set(rg_proto_srcs "${CMAKE_CURRENT_BINARY_DIR}/ringct.pb.cc")
set(rg_proto_hdrs "${CMAKE_CURRENT_BINARY_DIR}/ringct.pb.h")
set(rg_grpc_srcs "${CMAKE_CURRENT_BINARY_DIR}/ringct.grpc.pb.cc")
set(rg_grpc_hdrs "${CMAKE_CURRENT_BINARY_DIR}/ringct.grpc.pb.h")

add_custom_command(
    OUTPUT "${rg_proto_srcs}" "${rg_proto_hdrs}" "${rg_grpc_srcs}" "${rg_grpc_hdrs}"
    COMMAND ${_PROTOBUF_PROTOC}
    ARGS --grpc_out "${CMAKE_CURRENT_BINARY_DIR}"
    --cpp_out "${CMAKE_CURRENT_BINARY_DIR}"
    -I "${rct_proto_path}"
    --plugin=protoc-gen-grpc="${_GRPC_CPP_PLUGIN_EXECUTABLE}"
    "${rct_proto}"
    DEPENDS "${rct_proto}")


# inlcude generated *.pb.h files
include_directories("${CMAKE_CURRENT_BINARY_DIR}")

# rg_grpc_proto
add_library(rct_grpc_proto
    "${rg_proto_srcs}"
    "${rg_proto_hdrs}"
    "${rg_grpc_srcs}"
    "${rg_grpc_hdrs}")
target_link_libraries(rct_grpc_proto
    ${_REFLECTION}
    ${_GRPC_GRPCPP}
    ${_PROTOBUF_LIBPROTOBUF})

# 
add_executable(rct_server
    "src/rct_server.cc"
    "util/db_util.cc"
    "util/custom_exception.cc"
    "src/core.cc"
    "rct/rctOps.cpp"
    "rct/commitment.cpp")

target_link_libraries(rct_server
    rct_grpc_proto
    ${_REFLECTION}
    ${_GRPC_GRPCPP}
    sodium
    fmt::fmt
    nlohmann_json::nlohmann_json
    Catch2::Catch2WithMain
    pqxx)

add_executable(test_rct
    "util/custom_exception.cc"
    "rct/rctOps.cpp"
    "rct/commitment.cpp"
    "test/test_hash.cpp"
    "test/test_util.cc"
    "test/test_compute_stealth_address.cpp"
    "test/test_add_keys.cpp")

target_link_libraries(test_rct
    sodium
    fmt::fmt
    nlohmann_json::nlohmann_json
    Catch2::Catch2WithMain
    )