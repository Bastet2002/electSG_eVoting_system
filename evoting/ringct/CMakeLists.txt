cmake_minimum_required(VERSION 3.8)

project(RingCTServer C CXX)

include(./common.cmake)

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
    "src/vote.cc"
    "util/db_util.cc"
    "src/core.cc"
    "rct/lsag.cpp")

target_link_libraries(rct_server
    rct_grpc_proto
    ${_REFLECTION}
    ${_GRPC_GRPCPP}
    ${_PROTOBUF_LIBPROTOBUF}
    sodium)