from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    INPUT_UNREADABLE = 1
    INVALID_INPUT = 3
    UNSUPPORTED_PROBLEM = 4
    VERIFICATION_NOT_PASSED = 5
