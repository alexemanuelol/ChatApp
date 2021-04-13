#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# Package type
P_TYPE = {
    "command"           : 0,
    "message"           : 1,
    "notify"            : 2,
    "error"             : 3
}

# Commands
CLIENT_COMMANDS = {
    "setNickname"       : 0,
    "getUsers"          : 1
}

SERVER_COMMANDS = {
    "updateUsers"       : 0,
    "password"          : 1
}


# Package template
P_TMPL = {
    "type"              : None,
    "data"              : None,
    "info"              : None,
    "initiator"         : None
}

def create_package(pType, pData, pInfo=None, pInitiator=None, encode=True):
    """ Creates a package and returns it. """
    package = P_TMPL
    package["type"] = pType
    package["data"] = pData
    package["info"] = pInfo
    package["initiator"] = pInitiator

    valid_package(package)

    if encode:
        package = json.dumps(package).encode("utf-8")

    return package


def valid_package(package, exception=True):
    """ Validates a input package against the package template.
        Arguments:
            package         - package in the format of P_TEMPLATE       (dict)
            exception       - If true, exception is raised              (bool)
    """
    if not isinstance(package, dict):
        if exception:
            raise Exception(f"package is not of type dict.")
        else:
            return False

    if not len(package) == 4:
        if exception:
            raise Exception(f"package length is not of length {len(P_TEMPLATE)}.")
        else:
            return False

    if not all(x in package for x in P_TMPL):
        if exception:
            raise Exception(f"Package keys are missing.")
        else:
            return False

    if not (package["type"] in P_TYPE.values()):
        if exception:
            raise Exception(f"Type {package['type']} does not exist in P_TYPE")
        else:
            return False

    return True



if __name__ == "__main__":
    a = {
    "type"              : 3,
    "command"           : None,
    "initiator"         : None,
    "data"              : None
    }

    print(valid_package(a, False))
