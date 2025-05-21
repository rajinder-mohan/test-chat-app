from enum import Enum

class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    BRANCH = "branch"

class MessageType(str, Enum):
    TEXT = "text"
    CODE = "code"
    LINK = "link"

class ErrorMessages:
    CHAT_NOT_FOUND = "Chat not found"
    MESSAGE_NOT_FOUND = "Message not found"
    UNAUTHORIZED = "Not authorized to access this resource"
    BRANCH_NOT_FOUND = "Branch not found"
    INVALID_PARENT_MESSAGE = "Invalid parent message for branching" 