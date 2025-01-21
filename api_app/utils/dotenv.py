"""
Environment operation functions are defined here.
"""

import os
from .config import UrbanApiConfig


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

def read_env() -> UrbanApiConfig:
    return UrbanApiConfig(
            host=os.getenv('host'),
            port=int(os.getenv('port')),
            api_key=os.getenv('api-key'),
           )
