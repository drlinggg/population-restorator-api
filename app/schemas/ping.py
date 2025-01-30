"""
Ping response is defined here
"""

from pydantic import BaseModel, Field


class PingResponse(BaseModel):
    message: str = Field(default="Pong!", examples=["Pong!"])
