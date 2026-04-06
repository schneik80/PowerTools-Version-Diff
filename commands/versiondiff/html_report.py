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
    .version-card.baseline .card-label {
        color: #0984e3;
    }
    .version-card.comparison .card-label {
        color: #6c5ce7;
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
    .badge .count {
        font-size: 16px;
        margin-right: 6px;
    }

    /* Feature diff table */
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
    }
    table.diff-table th {
        text-align: left;
        padding: 10px 16px;
        background: #f8f9fa;
        color: #636e72;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        border-bottom: 2px solid #eee;
    }
    table.diff-table td {
        padding: 9px 16px;
        border-bottom: 1px solid #f0f0f0;
    }
    table.diff-table tr:last-child td {
        border-bottom: none;
    }

    /* Row status styles */
    tr.row-newer {
        border-left: 4px solid #28a745;
        background: #f6fff6;
    }
    tr.row-deleted {
        border-left: 4px solid #dc3545;
        background: #fff6f6;
    }
    tr.row-unchanged {
        border-left: 4px solid #dee2e6;
        background: #ffffff;
    }

    /* Status badge in table */
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
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
        color: #383d41;
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
    return f"""<div class="summary-row">
    <div class="badge badge-newer"><span class="count">{summary.get('newer', 0)}</span> Newer</div>
    <div class="badge badge-deleted"><span class="count">{summary.get('deleted', 0)}</span> Deleted</div>
    <div class="badge badge-unchanged"><span class="count">{summary.get('unchanged', 0)}</span> Unchanged</div>
</div>"""


def _build_feature_table(features: list) -> str:
    """Build the feature diff table HTML."""
    rows = []
    for entry in features:
        row_class = f"row-{entry.status}"
        status_class = f"status-{entry.status}"
        status_label = entry.status.capitalize()

        baseline_idx = str(entry.baseline_index) if entry.baseline_index is not None else "-"
        compare_idx = str(entry.compare_index) if entry.compare_index is not None else "-"

        rows.append(
            f'<tr class="{row_class}">'
            f'<td><span class="status-badge {status_class}">{status_label}</span></td>'
            f"<td>{_escape_html(entry.name)}</td>"
            f"<td>{_escape_html(entry.feature_type)}</td>"
            f"<td>{baseline_idx}</td>"
            f"<td>{compare_idx}</td>"
            f"</tr>"
        )

    table_rows = "\n        ".join(rows)

    return f"""<div class="diff-table-wrap">
    <h2>Timeline Feature Comparison</h2>
    <table class="diff-table">
        <thead>
            <tr>
                <th>Status</th>
                <th>Feature Name</th>
                <th>Feature Type</th>
                <th>Baseline #</th>
                <th>Compare #</th>
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

    baseline_card = _build_version_card(diff_result.baseline, "Current (Baseline)", "baseline")
    compare_card = _build_version_card(diff_result.comparison, "Comparison", "comparison")
    summary_badges = _build_summary_badges(diff_result.summary)
    feature_table = _build_feature_table(diff_result.features)

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
        <div class="subtitle">Version {diff_result.baseline.version_number} (current) vs Version {diff_result.comparison.version_number}</div>
    </div>

    <div class="version-cards">
        {baseline_card}
        {compare_card}
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
