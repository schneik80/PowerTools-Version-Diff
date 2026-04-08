# PowerTools: Version Diff for Autodesk Fusion

PowerTools Version Diff is an Autodesk Fusion add-in that compares two versions of a design document. It generates an interactive HTML report with a visual timeline overview, design property comparison, and a detailed two-column feature diff — detecting new features, deletions, XREF version changes, sketch modifications, parameter value changes, and feature health state changes.

## Prerequisites

Before you install and run this add-in, confirm that you have the following:

- **Autodesk Fusion** (any current subscription tier) with Python add-in support enabled
- **Windows 10/11** or **macOS**
- A design with at least **two saved versions** in the Autodesk Hub

## Installation

1. Download or clone this repository to your local machine.
2. In Autodesk Fusion, open the **Add-Ins** dialog by selecting **Utilities** > **Add-Ins**, or press **Shift+S**.
3. On the **Add-Ins** tab, click the green **+** icon.
4. Navigate to the folder where you placed the add-in files and select the `PowerTools-Version-Diff` folder.
5. Click **Open**.
6. Select **PowerTools Version Diff** in the list, then click **Run**.

To have the add-in load automatically each time Fusion starts, select **Run on Startup** before clicking **Run**.

## Commands

The following commands are included in this add-in:

| Command | Category | Location | Description |
|---|---|---|---|
| [Version Diff](./docs/Version%20Diff.md) | Analysis | Tools &rsaquo; PowerTools panel | Compares the timeline of the current document version against a selected earlier or later version and generates a side-by-side HTML diff report. |

---

## Analysis commands

### Version Diff

**[Version Diff](./docs/Version%20Diff.md)** compares the timeline of the active design against any other saved version of the same document. The command opens a dialog showing the current version metadata and a dropdown to select the comparison version.

After you select a version and click **OK**, the add-in:

- Walks the timeline of both versions to extract all features and their parameters.
- Detects new features, deleted features, unchanged features, XREF component version changes, sketch modifications (via `revisionId`), parameter value changes, and feature health state changes.
- Compares design-level properties: material, appearances, mass, volume, area, density, center of mass, and bounding box extents.
- Generates a visual timeline overview showing feature boxes with connection ribbons between versions.
- Produces a detailed two-column diff table with feature-type icons, change details, and interactive filter badges.
- Exports the raw diff data as a JSON file for programmatic access.

### Differences detected

| Status | Badge | Color | Detection method | Description |
|---|---|---|---|---|
| New | **NEW** | Green | Feature identity matching | Feature exists only in the newer version. |
| Deleted | **DEL** | Red | Feature identity matching | Feature exists only in the older version. |
| XREF Updated | **VER &Delta;** | Yellow | Component version comparison | XREF (Occurrence) feature references a different component version. Detail shows `v1 → v2`. |
| Sketch Modified | **SK &Delta;** | Amber | `Sketch.revisionId` comparison | Sketch content changed between versions. Detail shows element count deltas (lines, arcs, dimensions, etc.). |
| Params Changed | **PRM &Delta;** | Blue | Numeric value comparison with tolerance | Feature parameter values changed. Detail shows `d1: 10 mm → 15 mm`. |
| Health Changed | **HTH &Delta;** | Orange | `FeatureHealthStates` enum comparison | Feature health state changed (e.g., Healthy to Warning or Error) with no other modifications. Detail shows `Healthy → Error`. |
| Unchanged | **SAME** | Gray | All checks passed | Feature is identical in both versions. |

**Requirements:** The active product must be a Fusion 3D Design. The design must be saved, must use the parametric timeline, and must have at least two saved versions.

For full usage details, see [Version Diff](./docs/Version%20Diff.md).

---

## Support

This add-in is developed and maintained by IMA LLC.

---

## License

This project is released under the [MIT License](LICENSE).

---

*Copyright © 2026 IMA LLC. All rights reserved.*
