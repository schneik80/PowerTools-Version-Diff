# PowerTools: Version Diff for Autodesk Fusion

PowerTools Version Diff is an Autodesk Fusion add-in that compares timeline feature differences between two versions of a design document. It generates an interactive HTML report showing which features were added, deleted, or modified — including external reference (XREF) version changes — in a two-column side-by-side view.

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

- Walks the timeline of both versions to extract all features.
- Detects new features, deleted features, unchanged features, and XREF component version changes.
- Generates an interactive HTML report with a two-column aligned view (older version on the left, newer version on the right).
- Exports the raw diff data as a JSON file for programmatic access.

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
