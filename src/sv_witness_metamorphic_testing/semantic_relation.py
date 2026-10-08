"""Semantic relation labels established by transformation theorems."""

from enum import StrEnum


class BaseRelation(StrEnum):
    """Base semantic relation supplied by an established transformation theorem."""

    EXACT = "exact"
    BROADENING = "broadening"
