"""Configs are defined here"""

from dataclasses import dataclass


@dataclass
class ApiConfig:
    """defaut api config"""

    host: str
    port: int
    api_key: str
    base_path: str


@dataclass
class DBConfig:
    # todo desc
    addr: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
