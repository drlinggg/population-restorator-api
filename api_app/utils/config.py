#todo desc

from dataclasses import dataclass

@dataclass
class UrbanApiConfig:
    #todo desc
    host: str
    port: int
    api_key: str   
    base_path: str = '/api/v1'

@dataclass
class DBConfig:
    #todo desc
    addr: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
