import contextlib
import os

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class OwnersFileError(Exception):
    pass


def get_owner_data(category, organization, chart):
    path = os.path.join("charts", category, organization, chart, "OWNERS")
    success = True

    try:
        owner_content = get_owner_data_from_file(path)
    except OwnersFileError as e:
        print(f"Error getting OWNERS file data: {e}")
        success = False

    return success, owner_content


def get_owner_data_from_file(owner_path):
    try:
        with open(owner_path) as owner_data:
            owner_content = yaml.load(owner_data, Loader=Loader)
    except yaml.YAMLError as e:
        print(f"Exception loading OWNERS file: {e}")
        raise OwnersFileError from e
    except OSError as e:
        print(f"Error opening OWNERS file: {e}")
        raise OwnersFileError from e

    return owner_content


def get_vendor(owner_data):
    vendor_name = ""
    with contextlib.suppress(KeyError):
        vendor_name = owner_data["vendor"]["name"]
    return vendor_name


def get_vendor_label(owner_data):
    vendor_label = ""
    with contextlib.suppress(KeyError):
        vendor_label = owner_data["vendor"]["label"]
    return vendor_label


def get_chart(owner_data):
    chart = ""
    with contextlib.suppress(KeyError):
        chart = owner_data["chart"]["name"]
    return chart


def get_web_catalog_only(owner_data):
    return owner_data.get("web_catalog_only", False) or owner_data.get(
        "providerDelivery", False
    )


def get_users_included(owner_data):
    users = owner_data.get("users", list())
    return len(users) != 0


def get_pgp_public_key(owner_data):
    return owner_data.get("publicPgpKey", "")
