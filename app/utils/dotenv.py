"""
Environment operation functions are defined here.
"""

import os

from .config import DBConfig, UrbanApiConfig


def try_load_envfile(envfile: str) -> bool:
    """
    Parse given file as envfile with PARAM=VALUE lines and set them to `os.env`.

    Returns true if file exists and read attempt was performed, false otherwise.
    """
    if not os.path.isfile(envfile):
        return False
    with open(envfile, "rt", encoding="utf-8") as file:
        for name, value in (
            tuple((line[len("export ") :] if line.startswith("export ") else line).strip().split("=", 1))
            for line in file.readlines()
            if not line.startswith("#") and "=" in line
        ):
            if name not in os.environ:
                if " #" in value:
                    value = value[: value.index(" #")]
                os.environ[name] = value.strip()
    return True


def read_api_env() -> UrbanApiConfig:
    # todo desc
    return UrbanApiConfig(
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        api_key=os.getenv("API_KEY"),
    )


def read_db_env() -> DBConfig:
    # todo desc
    # todo
    return DBConfig("1", "2", "3", "4", "5", "6")


# todo fix path because it doesnt work if run from anything but population-restorator-api/
try_load_envfile(os.environ.get("ENVFILE", "urban_api.env"))
try_load_envfile(os.environ.get("ENVFILE", "db.env"))
urban_api_config = read_api_env()
db_config = read_db_env()
