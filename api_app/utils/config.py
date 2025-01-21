#todo desc

import os
from dataclasses import dataclass, field

@dataclass
class UrbanApiConfig:
    host: str
    port: int
    api_key: str   
    base_path: str = '/api/v1'

@dataclass
class DBConfig:
    addr: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
