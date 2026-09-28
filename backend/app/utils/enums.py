from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    VERIFIER = "VERIFIER"
    ADMIN = "ADMIN"
