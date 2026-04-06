import os
import secrets
import tempfile
from pathlib import Path

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
    .version-card .detail {
        font-size: 12px;
        color: #636e72;
        margin-bottom: 3px;
    }
    .version-card .detail b {
        color: #2d3436;
    }

    /* Summary badges */
    .summary-row {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    .badge-newer {
        background: #d4edda;
        color: #155724;
    }
    .badge-deleted {
        background: #f8d7da;
        color: #721c24;
    }
    .badge-unchanged {
        background: #e2e3e5;
        color: #383d41;
    }
    .badge-version_changed {
        background: #fff3cd;
        color: #856404;
    }
    .badge .count {
        font-size: 16px;
        margin-right: 6px;
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
    td.older-idx, th.older-idx { width: 36px; text-align: right; color: #999; }
    td.older-name, th.older-name { }
    td.older-type, th.older-type { width: 140px; color: #636e72; }

    /* Newer side columns */
    td.newer-idx, th.newer-idx { width: 36px; text-align: left; color: #999; }
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
        background: #f6fff6;
        font-weight: 600;
    }

    tr.row-deleted td.older-name,
    tr.row-deleted td.older-type,
    tr.row-deleted td.older-idx {
        background: #fff6f6;
        font-weight: 600;
    }

    tr.row-version_changed td {
        background: #fffde7;
    }
    tr.row-version_changed td.older-name,
    tr.row-version_changed td.newer-name {
        font-weight: 600;
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

    /* Arrow indicator */
    .arrow {
        font-size: 14px;
        margin: 0 2px;
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
    return f"""<div class="version-card {css_class}">
    <div class="card-label">{label}</div>
    <div class="version-number">Version {info.version_number}</div>
    <div class="detail"><b>Date Saved:</b> {_escape_html(info.date_modified)}</div>
    <div class="detail"><b>Saved By:</b> {_escape_html(info.last_updated_by)}</div>
    <div class="detail"><b>Description:</b> {desc}</div>
</div>"""


def _build_summary_badges(summary: dict) -> str:
    """Build the summary badge row."""
    version_changed = summary.get('version_changed', 0)
    vc_badge = ""
    if version_changed > 0:
        vc_badge = f'<div class="badge badge-version_changed"><span class="count">{version_changed}</span> XREF Updated</div>'

    return f"""<div class="summary-row">
    <div class="badge badge-newer"><span class="count">{summary.get('newer', 0)}</span> Newer</div>
    <div class="badge badge-deleted"><span class="count">{summary.get('deleted', 0)}</span> Deleted</div>
    {vc_badge}
    <div class="badge badge-unchanged"><span class="count">{summary.get('unchanged', 0)}</span> Unchanged</div>
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
            older_name = _escape_html(ar.older.name)
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
            newer_name = _escape_html(ar.newer.name)
            newer_type = _escape_html(ar.newer.feature_type)
            # Show component version for XREFs
            if ar.newer.feature_type == "XREF" and ar.newer.component_version:
                newer_name += f'<span class="version-detail">{_escape_html(ar.newer.component_version)}</span>'
            newer_cls = ""
        else:
            newer_idx = ""
            newer_name = ""
            newer_type = ""
            newer_cls = " empty-cell"

        rows.append(
            f'<tr class="{row_class}">'
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

    return f"""<div class="diff-table-wrap">
    <h2>Timeline Comparison</h2>
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

    summary_badges = _build_summary_badges(diff_result.summary)
    feature_table = _build_two_column_table(diff_result)

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

    {summary_badges}

    {feature_table}

    <div class="report-footer">
        Power Tools Version Diff &middot; IMA LLC
    </div>
</body>
</html>"""

    temp_path = tempfile.gettempdir()
    report_name = secrets.token_urlsafe(8)
    html_filepath = os.path.join(temp_path, f"version_diff_{report_name}.html")

    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return Path(html_filepath).as_posix()
