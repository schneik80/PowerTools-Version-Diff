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
class AlignedRow:
    """A single row in the two-column aligned diff view.

    Each row has an older side and a newer side. One side may be None
    when a feature only exists in one version.
    """
    older: Optional[TimelineFeature]
    newer: Optional[TimelineFeature]
    status: str  # "newer" | "deleted" | "unchanged"


@dataclass
class DiffResult:
    """Complete diff output comparing two version timelines."""
    baseline: VersionInfo
    comparison: VersionInfo
    features: list = field(default_factory=list)      # list[DiffEntry]
    aligned_rows: list = field(default_factory=list)   # list[AlignedRow]
    summary: dict = field(default_factory=dict)
    older_is_comparison: bool = True  # True when comparison is older than baseline

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)
