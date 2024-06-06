# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ringct.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cringct.proto\x12\x06ringct\"?\n\x15Gen_VoterCurr_Request\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x11\n\tvoter_num\x18\x02 \x01(\x05\"4\n\x1c\x43\x61lculate_Total_Vote_Request\x12\x14\n\x0c\x64istrict_ids\x18\x01 \x03(\x05\"J\n\x1d\x43\x61lculate_Total_Vote_Response\x12\x14\n\x0c\x64istrict_ids\x18\x01 \x03(\x05\x12\x13\n\x0btest_output\x18\x02 \x01(\t\"U\n\x16Gen_VoterCurr_Response\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x11\n\tvoter_num\x18\x02 \x01(\x05\x12\x13\n\x0btest_output\x18\x03 \x01(\t\"B\n\x15Gen_Candidate_Request\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\"X\n\x16Gen_Candidate_Response\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\x12\x13\n\x0btest_output\x18\x03 \x01(\t\"K\n\x0cVote_Request\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\x12\x10\n\x08voter_id\x18\x03 \x01(\x05\"t\n\rVote_Response\x12\x13\n\x0b\x64istrict_id\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\x12\x10\n\x08voter_id\x18\x03 \x01(\x05\x12\x11\n\tkey_image\x18\x04 \x01(\t\x12\x13\n\x0btest_output\x18\x05 \x01(\t2\xf8\x02\n\x0eRingCT_Service\x12\x65\n\"Generate_Voter_and_Voting_Currency\x12\x1d.ringct.Gen_VoterCurr_Request\x1a\x1e.ringct.Gen_VoterCurr_Response\"\x00\x12Y\n\x16Generate_CandidateKeys\x12\x1d.ringct.Gen_Candidate_Request\x1a\x1e.ringct.Gen_Candidate_Response\"\x00\x12=\n\x0c\x43ompute_Vote\x12\x14.ringct.Vote_Request\x1a\x15.ringct.Vote_Response\"\x00\x12\x65\n\x14\x43\x61lculate_Total_Vote\x12$.ringct.Calculate_Total_Vote_Request\x1a%.ringct.Calculate_Total_Vote_Response\"\x00\x42\x06\xa2\x02\x03RCTb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ringct_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\242\002\003RCT'
  _globals['_GEN_VOTERCURR_REQUEST']._serialized_start=24
  _globals['_GEN_VOTERCURR_REQUEST']._serialized_end=87
  _globals['_CALCULATE_TOTAL_VOTE_REQUEST']._serialized_start=89
  _globals['_CALCULATE_TOTAL_VOTE_REQUEST']._serialized_end=141
  _globals['_CALCULATE_TOTAL_VOTE_RESPONSE']._serialized_start=143
  _globals['_CALCULATE_TOTAL_VOTE_RESPONSE']._serialized_end=217
  _globals['_GEN_VOTERCURR_RESPONSE']._serialized_start=219
  _globals['_GEN_VOTERCURR_RESPONSE']._serialized_end=304
  _globals['_GEN_CANDIDATE_REQUEST']._serialized_start=306
  _globals['_GEN_CANDIDATE_REQUEST']._serialized_end=372
  _globals['_GEN_CANDIDATE_RESPONSE']._serialized_start=374
  _globals['_GEN_CANDIDATE_RESPONSE']._serialized_end=462
  _globals['_VOTE_REQUEST']._serialized_start=464
  _globals['_VOTE_REQUEST']._serialized_end=539
  _globals['_VOTE_RESPONSE']._serialized_start=541
  _globals['_VOTE_RESPONSE']._serialized_end=657
  _globals['_RINGCT_SERVICE']._serialized_start=660
  _globals['_RINGCT_SERVICE']._serialized_end=1036
# @@protoc_insertion_point(module_scope)