from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Gen_VoterCurr_Request(_message.Message):
    __slots__ = ("district_id", "voter_num")
    DISTRICT_ID_FIELD_NUMBER: _ClassVar[int]
    VOTER_NUM_FIELD_NUMBER: _ClassVar[int]
    district_id: int
    voter_num: int
    def __init__(self, district_id: _Optional[int] = ..., voter_num: _Optional[int] = ...) -> None: ...

class Calculate_Total_Vote_Request(_message.Message):
    __slots__ = ("district_ids",)
    DISTRICT_IDS_FIELD_NUMBER: _ClassVar[int]
    district_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, district_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class Calculate_Total_Vote_Response(_message.Message):
    __slots__ = ("district_ids", "test_output")
    DISTRICT_IDS_FIELD_NUMBER: _ClassVar[int]
    TEST_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    district_ids: _containers.RepeatedScalarFieldContainer[int]
    test_output: str
    def __init__(self, district_ids: _Optional[_Iterable[int]] = ..., test_output: _Optional[str] = ...) -> None: ...

class Gen_VoterCurr_Response(_message.Message):
    __slots__ = ("district_id", "voter_num", "test_output")
    DISTRICT_ID_FIELD_NUMBER: _ClassVar[int]
    VOTER_NUM_FIELD_NUMBER: _ClassVar[int]
    TEST_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    district_id: int
    voter_num: int
    test_output: str
    def __init__(self, district_id: _Optional[int] = ..., voter_num: _Optional[int] = ..., test_output: _Optional[str] = ...) -> None: ...

class Gen_Candidate_Request(_message.Message):
    __slots__ = ("candidate_id",)
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    def __init__(self, candidate_id: _Optional[int] = ...) -> None: ...

class Gen_Candidate_Response(_message.Message):
    __slots__ = ("candidate_id", "test_output")
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    TEST_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    test_output: str
    def __init__(self, candidate_id: _Optional[int] = ..., test_output: _Optional[str] = ...) -> None: ...

class Vote_Request(_message.Message):
    __slots__ = ("candidate_id", "voter_id", "is_voting")
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    VOTER_ID_FIELD_NUMBER: _ClassVar[int]
    IS_VOTING_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    voter_id: int
    is_voting: bool
    def __init__(self, candidate_id: _Optional[int] = ..., voter_id: _Optional[int] = ..., is_voting: bool = ...) -> None: ...

class Vote_Response(_message.Message):
    __slots__ = ("candidate_id", "voter_id", "key_image", "has_voted", "test_output")
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    VOTER_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_IMAGE_FIELD_NUMBER: _ClassVar[int]
    HAS_VOTED_FIELD_NUMBER: _ClassVar[int]
    TEST_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    voter_id: int
    key_image: str
    has_voted: bool
    test_output: str
    def __init__(self, candidate_id: _Optional[int] = ..., voter_id: _Optional[int] = ..., key_image: _Optional[str] = ..., has_voted: bool = ..., test_output: _Optional[str] = ...) -> None: ...

class Filter_Non_Voter_Request(_message.Message):
    __slots__ = ("district_ids",)
    DISTRICT_IDS_FIELD_NUMBER: _ClassVar[int]
    district_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, district_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class Filter_Non_Voter_Response(_message.Message):
    __slots__ = ("district_ids", "voter_ids", "test_output")
    DISTRICT_IDS_FIELD_NUMBER: _ClassVar[int]
    VOTER_IDS_FIELD_NUMBER: _ClassVar[int]
    TEST_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    district_ids: _containers.RepeatedScalarFieldContainer[int]
    voter_ids: _containers.RepeatedScalarFieldContainer[int]
    test_output: str
    def __init__(self, district_ids: _Optional[_Iterable[int]] = ..., voter_ids: _Optional[_Iterable[int]] = ..., test_output: _Optional[str] = ...) -> None: ...
