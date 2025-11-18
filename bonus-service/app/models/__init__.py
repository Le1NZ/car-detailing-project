"""Pydantic models for API requests and responses"""
from .bonus import (
    ApplyPromocodeRequest,
    PromocodeResponse,
    SpendBonusesRequest,
    SpendBonusesResponse,
)

__all__ = [
    "ApplyPromocodeRequest",
    "PromocodeResponse",
    "SpendBonusesRequest",
    "SpendBonusesResponse",
]
