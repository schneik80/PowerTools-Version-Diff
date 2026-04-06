import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class TimelineFeature:
    """Represents a single feature in a Fusion 360 design timeline."""
    name: str
    feature_type: str
    index: int
    is_group: bool
    is_suppressed: bool
    is_rolled_back: bool
    health_state: str
    entity_type: str


@dataclass
class VersionInfo:
    """Metadata about a Fusion 360 document version."""
    version_number: int
    version_id: str
    name: str
    date_modified: str
    last_updated_by: str
    description: str


@dataclass
class DiffEntry:
    """A single entry in the timeline diff result."""
    name: str
    feature_type: str
    status: str  # "newer" | "deleted" | "unchanged"
    baseline_index: Optional[int]
    compare_index: Optional[int]


@dataclass
class DiffResult:
    """Complete diff output comparing two version timelines."""
    baseline: VersionInfo
    comparison: VersionInfo
    features: list = field(default_factory=list)  # list[DiffEntry]
    summary: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)
