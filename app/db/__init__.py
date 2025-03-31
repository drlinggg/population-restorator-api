"""
Connection manager class and entities are defined here.
"""

from sqlalchemy import MetaData

from .conn_manager import PostgresConnectionManager


metadata = MetaData()
