import os
import secrets
import tempfile
from pathlib import Path

from .feature_icons import icon_img_tag
from .timeline_model import DiffResult


HTML_CSS = """<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: #f5f6fa;
        color: #2d3436;
        line-height: 1.5;
        padding: 24px;
    }

    /* Header */
    .report-header {
        background: #1a1a2e;
        color: #ffffff;
        padding: 20px 28px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .report-header h1 {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .report-header .subtitle {
        font-size: 13px;
        color: #b2bec3;
    }

    /* Version cards */
    .version-cards {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
    }
    .version-card {
        flex: 1;
        background: #ffffff;
        border-radius: 8px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .version-card .card-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    .version-card.older .card-label {
        color: #6c5ce7;
    }
    .version-card.newer .card-label {
        color: #0984e3;
    }
    .version-card .version-number {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .version-card .card-body {
        display: flex;
        gap: 14px;
        align-items: flex-start;
    }
    .card-thumb {
        width: 104px;
        height: 78px;
        object-fit: contain;
        border-radius: 4px;
        border: 1px solid #eee;
        background: #f8f9fa;
        flex-shrink: 0;
    }
    .card-details {
        flex: 1;
        min-width: 0;
    }
    .version-card .detail {
        font-size: 12px;
        color: #636e72;
        margin-bottom: 3px;
    }
    .version-card .detail b {
        color: #2d3436;
    }

    /* Filter badges */
    .filter-row {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    .filter-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        user-select: none;
        border: 2px solid transparent;
        transition: opacity 0.15s, border-color 0.15s;
    }
    .filter-badge:hover {
        border-color: rgba(0,0,0,0.15);
    }
    .filter-badge.inactive {
        opacity: 0.35;
    }
    .filter-badge.inactive:hover {
        opacity: 0.55;
    }
    .filter-badge .count {
        font-size: 16px;
        margin-right: 6px;
    }
    .filter-badge-newer {
        background: #d4edda;
        color: #155724;
    }
    .filter-badge-deleted {
        background: #f8d7da;
        color: #721c24;
    }
    .filter-badge-unchanged {
        background: #e2e3e5;
        color: #383d41;
    }
    .filter-badge-version_changed {
        background: #fff3cd;
        color: #856404;
    }
    .filter-badge-sketch_modified {
        background: #fde8d0;
        color: #8a4b08;
    }
    .filter-badge-params_changed {
        background: #d6eaf8;
        color: #1a5276;
    }

    /* Two-column diff table */
    .diff-table-wrap {
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .diff-table-wrap h2 {
        font-size: 15px;
        font-weight: 600;
        padding: 14px 22px;
        border-bottom: 1px solid #eee;
    }
    table.diff-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        table-layout: fixed;
    }
    table.diff-table th {
        text-align: left;
        padding: 10px 12px;
        background: #f8f9fa;
        color: #636e72;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        border-bottom: 2px solid #eee;
    }
    table.diff-table td {
        padding: 7px 12px;
        border-bottom: 1px solid #f0f0f0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    table.diff-table tr:last-child td {
        border-bottom: none;
    }

    /* Column header groups */
    th.col-older {
        background: #f3f0ff;
        color: #6c5ce7;
    }
    th.col-newer {
        background: #eef6ff;
        color: #0984e3;
    }
    th.col-status {
        width: 80px;
        text-align: center;
    }

    /* Center divider between the two version columns */
    td.col-divider, th.col-divider {
        width: 80px;
        text-align: center;
        background: #fafafa;
        border-left: 2px solid #eee;
        border-right: 2px solid #eee;
    }

    /* Older side columns */
    td.older-idx, th.older-idx { width: 50px; text-align: right; color: #999; }
    td.older-name, th.older-name { }
    td.older-type, th.older-type { width: 140px; color: #636e72; }

    /* Newer side columns */
    td.newer-idx, th.newer-idx { width: 50px; text-align: left; color: #999; }
    td.newer-name, th.newer-name { }
    td.newer-type, th.newer-type { width: 140px; color: #636e72; }

    /* Row status styles */
    tr.row-newer td.col-divider {
        background: #d4edda;
    }
    tr.row-deleted td.col-divider {
        background: #f8d7da;
    }
    tr.row-unchanged td.col-divider {
        background: #f0f0f0;
    }
    tr.row-version_changed td.col-divider {
        background: #fff3cd;
    }

    tr.row-newer td.newer-name,
    tr.row-newer td.newer-type,
    tr.row-newer td.newer-idx {
        background: #ecfaee;
        font-weight: 600;
    }

    tr.row-deleted td.older-name,
    tr.row-deleted td.older-type,
    tr.row-deleted td.older-idx {
        background: #fdedee;
        font-weight: 600;
    }

    tr.row-version_changed td.newer-idx,
    tr.row-version_changed td.newer-name,
    tr.row-version_changed td.newer-type {
        background: #fffde7;
        font-weight: 600;
    }

    /* Sketch modified rows — only highlight the newer (changed) side */
    tr.row-sketch_modified td.col-divider {
        background: #fde8d0;
    }
    tr.row-sketch_modified td.newer-name,
    tr.row-sketch_modified td.newer-type,
    tr.row-sketch_modified td.newer-idx {
        background: #fef5eb;
        font-weight: 600;
    }

    /* Parameter changed rows — only highlight the newer (changed) side */
    tr.row-params_changed td.col-divider {
        background: #d6eaf8;
    }
    tr.row-params_changed td.newer-name,
    tr.row-params_changed td.newer-type,
    tr.row-params_changed td.newer-idx {
        background: #ebf5fb;
        font-weight: 600;
    }

    /* Sketch change detail text (shown under feature name) */
    .sketch-detail {
        display: block;
        font-size: 10px;
        color: #8a4b08;
        font-weight: 400;
        margin-top: 1px;
        white-space: normal;
        line-height: 1.3;
    }

    /* Parameter change detail text (shown under feature name) */
    .params-detail {
        display: block;
        font-size: 10px;
        color: #1a5276;
        font-weight: 400;
        margin-top: 1px;
        white-space: normal;
        line-height: 1.3;
    }

    /* Version change detail text */
    .version-detail {
        display: block;
        font-size: 10px;
        color: #856404;
        font-weight: 400;
        margin-top: 1px;
    }

    /* Empty cell styling */
    td.empty-cell {
        background: #fafafa;
    }

    /* Status badge in divider */
    .status-badge {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 8px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .status-newer {
        background: #d4edda;
        color: #155724;
    }
    .status-deleted {
        background: #f8d7da;
        color: #721c24;
    }
    .status-unchanged {
        background: #e2e3e5;
        color: #6b7075;
    }
    .status-version_changed {
        background: #fff3cd;
        color: #856404;
    }
    .status-sketch_modified {
        background: #fde8d0;
        color: #8a4b08;
    }
    .status-params_changed {
        background: #d6eaf8;
        color: #1a5276;
    }

    /* Arrow indicator */
    .arrow {
        font-size: 14px;
        margin: 0 2px;
    }

    /* Design Properties table */
    .props-table-wrap {
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
        margin-bottom: 20px;
    }
    .props-table-wrap h2 {
        font-size: 15px;
        font-weight: 600;
        padding: 14px 22px;
        border-bottom: 1px solid #eee;
    }
    table.props-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        table-layout: fixed;
    }
    table.props-table th {
        text-align: left;
        padding: 10px 12px;
        background: #f8f9fa;
        color: #636e72;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        border-bottom: 2px solid #eee;
    }
    table.props-table th.prop-col-older { background: #f3f0ff; color: #6c5ce7; width: 35%; }
    table.props-table th.prop-col-label { width: 30%; text-align: center; }
    table.props-table th.prop-col-newer { background: #eef6ff; color: #0984e3; width: 35%; }
    table.props-table td {
        padding: 7px 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    table.props-table td.prop-label {
        text-align: center;
        font-weight: 600;
        color: #636e72;
        background: #fafafa;
    }
    table.props-table td.prop-changed {
        background: #fef5eb;
        font-weight: 600;
    }
    table.props-table tr:last-child td {
        border-bottom: none;
    }

    /* Table heading summary */
    .table-summary {
        font-size: 12px;
        font-weight: 400;
        color: #636e72;
    }

    /* Footer */
    .report-footer {
        margin-top: 20px;
        text-align: center;
        font-size: 11px;
        color: #b2bec3;
    }
</style>
"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _build_version_card(info, label: str, css_class: str) -> str:
    """Build HTML for a version info card."""
    desc = _escape_html(info.description) if info.description else "<i>No description</i>"

    # Thumbnail (embedded as base64 data URI)
    thumb_html = ""
    if getattr(info, "thumbnail_b64", ""):
        thumb_html = (
            f'<img class="card-thumb" '
            f'src="data:image/png;base64,{info.thumbnail_b64}" '
            f'alt="Version {info.version_number} thumbnail" />'
        )

    return f"""<div class="version-card {css_class}">
    <div class="card-label">{label}</div>
    <div class="card-body">
        {thumb_html}
        <div class="card-details">
            <div class="version-number">Version {info.version_number}</div>
            <div class="detail"><b>Date Saved:</b> {_escape_html(info.date_modified)}</div>
            <div class="detail"><b>Saved By:</b> {_escape_html(info.last_updated_by)}</div>
            <div class="detail"><b>Description:</b> {desc}</div>
        </div>
    </div>
</div>"""


def _build_filter_badges(summary: dict) -> str:
    """Build the clickable filter badge row."""
    version_changed = summary.get('version_changed', 0)
    vc_badge = ""
    if version_changed > 0:
        vc_badge = (
            f'<span class="filter-badge filter-badge-version_changed" '
            f'data-filter="version_changed" onclick="toggleFilter(this)">'
            f'<span class="count">{version_changed}</span> XREF Updated</span>'
        )

    sketch_modified = summary.get('sketch_modified', 0)
    sk_badge = ""
    if sketch_modified > 0:
        sk_badge = (
            f'<span class="filter-badge filter-badge-sketch_modified" '
            f'data-filter="sketch_modified" onclick="toggleFilter(this)">'
            f'<span class="count">{sketch_modified}</span> Sketch Modified</span>'
        )

    params_changed = summary.get('params_changed', 0)
    prm_badge = ""
    if params_changed > 0:
        prm_badge = (
            f'<span class="filter-badge filter-badge-params_changed" '
            f'data-filter="params_changed" onclick="toggleFilter(this)">'
            f'<span class="count">{params_changed}</span> Params Changed</span>'
        )

    return f"""<div class="filter-row">
    <span class="filter-badge filter-badge-newer" data-filter="newer" onclick="toggleFilter(this)"><span class="count">{summary.get('newer', 0)}</span> Newer</span>
    <span class="filter-badge filter-badge-deleted" data-filter="deleted" onclick="toggleFilter(this)"><span class="count">{summary.get('deleted', 0)}</span> Deleted</span>
    {vc_badge}
    {sk_badge}
    {prm_badge}
    <span class="filter-badge filter-badge-unchanged" data-filter="unchanged" onclick="toggleFilter(this)"><span class="count">{summary.get('unchanged', 0)}</span> Unchanged</span>
</div>"""


def _build_properties_table(diff_result: DiffResult) -> str:
    """Build the Design Properties comparison table.

    Shows material, appearances, mass properties and extents side-by-side
    for the older and newer versions, highlighting changed values.
    """
    older_props = (
        diff_result.comparison_properties
        if diff_result.older_is_comparison
        else diff_result.baseline_properties
    )
    newer_props = (
        diff_result.baseline_properties
        if diff_result.older_is_comparison
        else diff_result.comparison_properties
    )

    if not older_props and not newer_props:
        return ""

    older_info = (
        diff_result.comparison if diff_result.older_is_comparison else diff_result.baseline
    )
    newer_info = (
        diff_result.baseline if diff_result.older_is_comparison else diff_result.comparison
    )

    def _fmt(val, decimals=3):
        """Format a float to fixed decimals."""
        if val is None:
            return "—"
        return f"{val:.{decimals}f}"

    def _fmt_tuple(t, decimals=3):
        """Format a 3-tuple of floats."""
        if not t:
            return "—"
        return f"({_fmt(t[0], decimals)}, {_fmt(t[1], decimals)}, {_fmt(t[2], decimals)})"

    def _extents(bbox_min, bbox_max, decimals=3):
        """Compute extents string from bbox min/max."""
        if not bbox_min or not bbox_max:
            return "—"
        w = abs(bbox_max[0] - bbox_min[0])
        h = abs(bbox_max[1] - bbox_min[1])
        d = abs(bbox_max[2] - bbox_min[2])
        return f"{_fmt(w, decimals)} × {_fmt(h, decimals)} × {_fmt(d, decimals)}"

    def _row(label, older_val, newer_val, unit=""):
        """Build a table row, highlighting only the newer column if values differ."""
        o_str = _escape_html(str(older_val)) + (f" {unit}" if unit and older_val != "—" else "")
        n_str = _escape_html(str(newer_val)) + (f" {unit}" if unit and newer_val != "—" else "")
        changed = str(older_val) != str(newer_val)
        n_cls = ' class="prop-changed"' if changed else ""
        return (
            f"<tr>"
            f"<td>{o_str}</td>"
            f'<td class="prop-label">{_escape_html(label)}</td>'
            f'<td{n_cls}>{n_str}</td>'
            f"</tr>"
        )

    # Prepare values (use safe defaults if a side is missing)
    op = older_props or type(newer_props)()
    np_ = newer_props or type(older_props)()

    rows = []
    rows.append(_row("Material", op.material or "—", np_.material or "—"))
    rows.append(_row("Appearances",
                     ", ".join(op.body_appearances) if op.body_appearances else "—",
                     ", ".join(np_.body_appearances) if np_.body_appearances else "—"))
    rows.append(_row("Bodies", op.body_count, np_.body_count))
    rows.append(_row("Mass", _fmt(op.mass, 6), _fmt(np_.mass, 6), "kg"))
    rows.append(_row("Volume", _fmt(op.volume, 3), _fmt(np_.volume, 3), "cm³"))
    rows.append(_row("Area", _fmt(op.area, 3), _fmt(np_.area, 3), "cm²"))
    rows.append(_row("Density", _fmt(op.density, 6), _fmt(np_.density, 6), "kg/cm³"))
    rows.append(_row("Center of Mass", _fmt_tuple(op.center_of_mass, 4), _fmt_tuple(np_.center_of_mass, 4), "cm"))
    rows.append(_row("Extents (W × H × D)",
                     _extents(op.bbox_min, op.bbox_max),
                     _extents(np_.bbox_min, np_.bbox_max), "cm"))

    table_rows = "\n        ".join(rows)

    # Build a plain-English summary of what changed
    changed_props = []
    if (op.material or "—") != (np_.material or "—"):
        changed_props.append("material")
    if (op.body_appearances or []) != (np_.body_appearances or []):
        changed_props.append("appearance")
    if _fmt(op.mass, 6) != _fmt(np_.mass, 6):
        changed_props.append("mass")
    if _fmt(op.volume, 3) != _fmt(np_.volume, 3):
        changed_props.append("volume")
    if _fmt(op.area, 3) != _fmt(np_.area, 3):
        changed_props.append("area")
    if _fmt(op.density, 6) != _fmt(np_.density, 6):
        changed_props.append("density")
    if _fmt_tuple(op.center_of_mass, 4) != _fmt_tuple(np_.center_of_mass, 4):
        changed_props.append("center of mass")
    if _extents(op.bbox_min, op.bbox_max) != _extents(np_.bbox_min, np_.bbox_max):
        changed_props.append("extents")
    if op.body_count != np_.body_count:
        changed_props.append("body count")

    if changed_props:
        props_summary = _escape_html(", ".join(changed_props)) + " changed"
    else:
        props_summary = "no changes detected"

    return f"""<div class="props-table-wrap">
    <h2>Design Properties <span class="table-summary">&mdash; {props_summary}</span></h2>
    <table class="props-table">
        <thead>
            <tr>
                <th class="prop-col-older">V{older_info.version_number} (Older)</th>
                <th class="prop-col-label">Property</th>
                <th class="prop-col-newer">V{newer_info.version_number} (Newer)</th>
            </tr>
        </thead>
        <tbody>
        {table_rows}
        </tbody>
    </table>
</div>"""


def _build_two_column_table(diff_result: DiffResult) -> str:
    """Build the two-column aligned diff table.

    Left column = older version, right column = newer version.
    The comparison version goes left if it's older, right if newer.
    Empty cells appear where a feature doesn't exist in that version.
    """
    older_is_comparison = diff_result.older_is_comparison

    if older_is_comparison:
        older_info = diff_result.comparison
        newer_info = diff_result.baseline
    else:
        older_info = diff_result.baseline
        newer_info = diff_result.comparison

    older_label = f"V{older_info.version_number} (Older)"
    newer_label = f"V{newer_info.version_number} (Newer)"

    # Status label mapping for display
    status_labels = {
        "newer": "NEW",
        "deleted": "DEL",
        "unchanged": "SAME",
        "version_changed": "VER \u0394",
        "sketch_modified": "SK \u0394",
        "params_changed": "PRM \u0394",
    }

    rows = []
    for ar in diff_result.aligned_rows:
        row_class = f"row-{ar.status}"
        status_class = f"status-{ar.status}"
        status_label = status_labels.get(ar.status, ar.status.upper())

        # For version_changed rows, append version detail to the divider
        divider_extra = ""
        if ar.status == "version_changed" and ar.detail:
            divider_extra = f'<br><span class="version-detail">{_escape_html(ar.detail)}</span>'

        # Older side cells
        if ar.older:
            older_idx = str(ar.older.index)
            older_icon = icon_img_tag(ar.older.feature_type)
            older_name = older_icon + _escape_html(ar.older.name)
            older_type = _escape_html(ar.older.feature_type)
            # Show component version for XREFs
            if ar.older.feature_type == "XREF" and ar.older.component_version:
                older_name += f'<span class="version-detail">{_escape_html(ar.older.component_version)}</span>'
            older_cls = ""
        else:
            older_idx = ""
            older_name = ""
            older_type = ""
            older_cls = " empty-cell"

        # Newer side cells
        if ar.newer:
            newer_idx = str(ar.newer.index)
            newer_icon = icon_img_tag(ar.newer.feature_type)
            newer_name = newer_icon + _escape_html(ar.newer.name)
            newer_type = _escape_html(ar.newer.feature_type)
            # Show component version for XREFs
            if ar.newer.feature_type == "XREF" and ar.newer.component_version:
                newer_name += f'<span class="version-detail">{_escape_html(ar.newer.component_version)}</span>'
            # Show sketch change detail under the name
            if ar.status == "sketch_modified" and ar.sketch_detail:
                newer_name += f'<span class="sketch-detail">{_escape_html(ar.sketch_detail)}</span>'
            # Show parameter change detail under the name
            if ar.status == "params_changed" and ar.params_detail:
                newer_name += f'<span class="params-detail">{_escape_html(ar.params_detail)}</span>'
            newer_cls = ""
        else:
            newer_idx = ""
            newer_name = ""
            newer_type = ""
            newer_cls = " empty-cell"

        rows.append(
            f'<tr class="{row_class}" data-status="{ar.status}">'
            f'<td class="older-idx{older_cls}">{older_idx}</td>'
            f'<td class="older-name{older_cls}">{older_name}</td>'
            f'<td class="older-type{older_cls}">{older_type}</td>'
            f'<td class="col-divider"><span class="status-badge {status_class}">{status_label}</span>{divider_extra}</td>'
            f'<td class="newer-idx{newer_cls}">{newer_idx}</td>'
            f'<td class="newer-name{newer_cls}">{newer_name}</td>'
            f'<td class="newer-type{newer_cls}">{newer_type}</td>'
            f"</tr>"
        )

    table_rows = "\n        ".join(rows)

    # Build a plain-English summary of changes by feature type
    changed_statuses = {"newer", "deleted", "version_changed", "sketch_modified", "params_changed"}
    type_counts: dict[str, int] = {}
    total_changed = 0
    for ar in diff_result.aligned_rows:
        if ar.status in changed_statuses:
            total_changed += 1
            # Use the feature type from whichever side exists
            ft = (ar.newer or ar.older).feature_type if (ar.newer or ar.older) else "Unknown"
            # Normalize to readable names
            if ft == "Sketch":
                label = "sketch"
            elif ft == "XREF":
                label = "component ref"
            elif ft in ("Joint", "AsBuiltJoint", "JointOrigin"):
                label = "joint"
            elif ft in ("ConstructionAxis", "ConstructionPlane", "ConstructionPoint"):
                label = "construction"
            elif ft.endswith("Feature"):
                label = "feature"
            else:
                label = "feature"
            type_counts[label] = type_counts.get(label, 0) + 1

    if total_changed == 0:
        timeline_summary = "no changes"
    else:
        parts = []
        parts.append(f"{total_changed} total")
        for label in ["feature", "sketch", "component ref", "joint", "construction"]:
            if label in type_counts:
                count = type_counts[label]
                plural = label + ("es" if label.endswith("ch") else "s")
                parts.append(f"{count} {plural if count != 1 else label}")
        timeline_summary = ", ".join(parts)

    return f"""<div class="diff-table-wrap">
    <h2>Timeline Comparison <span class="table-summary">&mdash; {_escape_html(timeline_summary)}</span></h2>
    <table class="diff-table">
        <thead>
            <tr>
                <th class="older-idx col-older">#</th>
                <th class="older-name col-older">{_escape_html(older_label)}</th>
                <th class="older-type col-older">Type</th>
                <th class="col-divider col-status">Status</th>
                <th class="newer-idx col-newer">#</th>
                <th class="newer-name col-newer">{_escape_html(newer_label)}</th>
                <th class="newer-type col-newer">Type</th>
            </tr>
        </thead>
        <tbody>
        {table_rows}
        </tbody>
    </table>
</div>"""


def generate_html_report(diff_result: DiffResult) -> str:
    """Generate a complete HTML diff report and save to a temp file.

    Args:
        diff_result: The complete DiffResult to render.

    Returns:
        POSIX-style path to the generated HTML file.
    """
    doc_name = _escape_html(diff_result.baseline.name)

    # Cards ordered left=older, right=newer to match the table columns
    if diff_result.older_is_comparison:
        left_card = _build_version_card(diff_result.comparison, "Older (Comparison)", "older")
        right_card = _build_version_card(diff_result.baseline, "Newer (Current)", "newer")
    else:
        left_card = _build_version_card(diff_result.baseline, "Older (Current)", "older")
        right_card = _build_version_card(diff_result.comparison, "Newer (Comparison)", "newer")

    filter_badges = _build_filter_badges(diff_result.summary)
    properties_table = _build_properties_table(diff_result)
    feature_table = _build_two_column_table(diff_result)

    filter_js = """<script>
function toggleFilter(badge) {
    badge.classList.toggle('inactive');
    applyFilters();
}
function applyFilters() {
    var badges = document.querySelectorAll('.filter-badge');
    var hidden = {};
    for (var i = 0; i < badges.length; i++) {
        if (badges[i].classList.contains('inactive')) {
            hidden[badges[i].getAttribute('data-filter')] = true;
        }
    }
    var rows = document.querySelectorAll('tr[data-status]');
    for (var j = 0; j < rows.length; j++) {
        var status = rows[j].getAttribute('data-status');
        rows[j].style.display = hidden[status] ? 'none' : '';
    }
}
</script>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{doc_name} - Version Diff Report</title>
    {HTML_CSS}
</head>
<body>
    <div class="report-header">
        <h1>{doc_name} - Version Diff Report</h1>
        <div class="subtitle">Version {diff_result.baseline.version_number} (current) vs Version {diff_result.comparison.version_number} <span class="arrow">&larr; older</span></div>
    </div>

    <div class="version-cards">
        {left_card}
        {right_card}
    </div>

    {properties_table}

    {filter_badges}
    <div style="font-size:11px;color:#999;margin:-14px 0 16px 2px;">Click a badge to show or hide those rows</div>

    {feature_table}

    <div class="report-footer">
        Power Tools Version Diff &middot; IMA LLC
    </div>
    {filter_js}
</body>
</html>"""

    temp_path = tempfile.gettempdir()
    report_name = secrets.token_urlsafe(8)
    html_filepath = os.path.join(temp_path, f"version_diff_{report_name}.html")

    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return Path(html_filepath).as_posix()
