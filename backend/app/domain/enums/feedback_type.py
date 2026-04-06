from enum import Enum


class FeedbackType(str, Enum):
    REVISION_REQUEST = "revision_request"
    APPROVE = "approve"
