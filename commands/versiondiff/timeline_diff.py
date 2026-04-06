import json
import os
import secrets
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import adsk.core
import adsk.fusion

from .timeline_model import TimelineFeature, VersionInfo, DiffEntry, DiffResult


def walk_timeline(timeline: adsk.fusion.Timeline) -> list:
    """Walk a Fusion 360 design timeline and extract all features.

    Args:
        timeline: The design's Timeline object.

    Returns:
        List of TimelineFeature dataclass instances.
    """
    features = []

    for i in range(timeline.count):
        item = timeline.item(i)

        # Extract short type name from entity objectType
        # Some timeline items have invalid/broken entities that raise RuntimeError
        try:
            entity = item.entity
        except RuntimeError:
            entity = None

        if entity is not None:
            full_type = entity.objectType  # e.g. "adsk::fusion::ExtrudeFeature"
            feature_type = full_type.split("::")[-1] if "::" in full_type else full_type
            entity_type = full_type
        else:
            feature_type = "Group" if item.isGroup else "Unknown"
            entity_type = ""

        # Map health state enum to string
        try:
            health_map = {
                adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState: "Healthy",
                adsk.fusion.FeatureHealthStates.WarningFeatureHealthState: "Warning",
                adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState: "Error",
            }
            health_str = health_map.get(item.healthState, "Unknown")
        except RuntimeError:
            health_str = "Unknown"

        features.append(TimelineFeature(
            name=item.name,
            feature_type=feature_type,
            index=item.index,
            is_group=item.isGroup,
            is_suppressed=item.isSuppressed,
            is_rolled_back=item.isRolledBack,
            health_state=health_str,
            entity_type=entity_type,
        ))

    return features


def get_version_info(data_file: adsk.core.DataFile) -> VersionInfo:
    """Extract version metadata from a Fusion DataFile.

    Args:
        data_file: The DataFile to read version info from.

    Returns:
        VersionInfo dataclass instance.
    """
    date_str = ""
    if data_file.dateModified:
        date_str = datetime.fromtimestamp(data_file.dateModified).strftime("%Y-%m-%d %H:%M:%S")

    updated_by = ""
    if data_file.lastUpdatedBy:
        updated_by = data_file.lastUpdatedBy.displayName

    return VersionInfo(
        version_number=data_file.versionNumber,
        version_id=data_file.versionId,
        name=data_file.name,
        date_modified=date_str,
        last_updated_by=updated_by,
        description=data_file.description or "",
    )


def compute_diff(baseline_features: list, compare_features: list) -> tuple:
    """Compare two timeline feature lists and produce a diff.

    Uses (name, feature_type) as the identity key for matching features.
    Baseline is the current/newer version; comparison is the older version.

    - "newer": feature exists in baseline but not in comparison (added after comparison)
    - "deleted": feature exists in comparison but not in baseline (removed since comparison)
    - "unchanged": feature exists in both

    Args:
        baseline_features: List of TimelineFeature from the current version.
        compare_features: List of TimelineFeature from the comparison version.

    Returns:
        Tuple of (list[DiffEntry], summary_dict).
    """
    # Build lookup dicts keyed by (name, feature_type)
    baseline_map = {}
    for f in baseline_features:
        key = (f.name, f.feature_type)
        baseline_map[key] = f

    compare_map = {}
    for f in compare_features:
        key = (f.name, f.feature_type)
        compare_map[key] = f

    diff_entries = []
    seen_keys = set()

    # Walk baseline features in order
    for f in baseline_features:
        key = (f.name, f.feature_type)
        seen_keys.add(key)

        if key in compare_map:
            status = "unchanged"
            compare_index = compare_map[key].index
        else:
            status = "newer"
            compare_index = None

        diff_entries.append(DiffEntry(
            name=f.name,
            feature_type=f.feature_type,
            status=status,
            baseline_index=f.index,
            compare_index=compare_index,
        ))

    # Walk comparison features for deleted items
    for f in compare_features:
        key = (f.name, f.feature_type)
        if key not in seen_keys:
            diff_entries.append(DiffEntry(
                name=f.name,
                feature_type=f.feature_type,
                status="deleted",
                baseline_index=None,
                compare_index=f.index,
            ))

    # Compute summary
    newer_count = sum(1 for e in diff_entries if e.status == "newer")
    deleted_count = sum(1 for e in diff_entries if e.status == "deleted")
    unchanged_count = sum(1 for e in diff_entries if e.status == "unchanged")

    summary = {
        "newer": newer_count,
        "deleted": deleted_count,
        "unchanged": unchanged_count,
        "total_baseline": len(baseline_features),
        "total_comparison": len(compare_features),
    }

    return diff_entries, summary


def save_diff_json(diff_result: DiffResult) -> str:
    """Save a DiffResult as a JSON file in the temp directory.

    Args:
        diff_result: The complete diff result to serialize.

    Returns:
        POSIX-style path to the saved JSON file.
    """
    temp_path = tempfile.gettempdir()
    report_name = secrets.token_urlsafe(8)
    filepath = os.path.join(temp_path, f"version_diff_{report_name}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(diff_result.to_json())

    return Path(filepath).as_posix()
