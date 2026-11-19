"""Shared plain data types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeKind(str, Enum):
    KERNEL = "kernel"
    MEMCPY = "memcpy"
    MEMSET = "memset"
    EVENT = "event"
    OTHER = "other"


@dataclass(frozen=True)
class TimingRow:
    size: int
    eager_ms: float
    graph_ms: float


@dataclass(frozen=True)
class NcuRow:
    size: int
    ncu_ms_default: float
    ncu_ms_unlocked: float
