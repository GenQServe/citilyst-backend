from enum import Enum
from permissions.model_permission import *


class Role(str, Enum):
    ADMINISTRATOR = "admin"
    USER = "user"

    @classmethod
    def get_roles(cls):
        values = []
        for member in cls:
            values.append(f"{member.value}")
        return values


ROLE_PERMISSIONS = {
    Role.ADMINISTRATOR: [
        [
            Users.permissions.CREATE,
            Users.permissions.READ,
            Users.permissions.UPDATE,
            Users.permissions.DELETE,
        ],
        [
            Reports.permissions.READ,
            Reports.permissions.UPDATE,
            Reports.permissions.DELETE,
        ],
        [
            Districts.permissions.CREATE,
            Districts.permissions.READ,
            Districts.permissions.UPDATE,
            Districts.permissions.DELETE,
        ],
        [
            Villages.permissions.CREATE,
            Villages.permissions.READ,
            Villages.permissions.UPDATE,
            Villages.permissions.DELETE,
        ],
    ],
    Role.USER: [
        [
            Reports.permissions.CREATE,
            Reports.permissions.READ,
        ],
        [
            Users.permissions.UPDATE,
            UsersProfile.permissions.READ,
            UsersProfile.permissions.UPDATE,
        ],
        [
            Districts.permissions.READ,
        ],
        [
            Villages.permissions.READ,
        ],
    ],
}


def get_role_permissions(role: Role):
    permissions = set()
    for permissions_group in ROLE_PERMISSIONS[role]:
        for permission in permissions_group:
            permissions.add(str(permission))
    return list(permissions)
