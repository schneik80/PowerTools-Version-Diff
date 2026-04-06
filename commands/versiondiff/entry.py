import adsk.core
import adsk.fusion
import os
import traceback

from ...lib import fusionAddInUtils as futil
from ... import config
from .timeline_diff import walk_timeline, get_version_info, compute_diff, save_diff_json
from .timeline_model import DiffResult
from .html_report import generate_html_report

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = "Version Diff"
CMD_ID = "PTVD-versiondiff"
CMD_Description = "Compare timeline differences between two versions of the active document"
IS_PROMOTED = True

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

# Resource location for command icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Maps dropdown item labels to DataFile objects for version selection
_version_map = {}


def start():
    """Initialize and register the Version Diff command."""
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    futil.add_handler(cmd_def.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    if not workspace:
        futil.log(f"Warning: Workspace {WORKSPACE_ID} not found")
        return

    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    control = panel.controls.addCommand(cmd_def)
    control.isPromoted = IS_PROMOTED

    futil.log(f"{CMD_NAME} command started successfully")


def stop():
    """Clean up and unregister the Version Diff command."""
    try:
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if not workspace:
            return

        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
        command_control = panel.controls.itemById(CMD_ID) if panel else None
        command_definition = ui.commandDefinitions.itemById(CMD_ID)

        if command_control:
            command_control.deleteMe()

        if command_definition:
            command_definition.deleteMe()

        if panel and panel.controls.count == 0:
            panel.deleteMe()

        if toolbar_tab and toolbar_tab.toolbarPanels.count == 0:
            toolbar_tab.deleteMe()

        futil.log(f"{CMD_NAME} command stopped successfully")

    except Exception as e:
        futil.log(f"Error stopping {CMD_NAME}: {e}")


def command_created(args: adsk.core.CommandCreatedEventArgs):
    """Handle command creation: validate document and build the dialog."""
    global _version_map
    _version_map = {}

    futil.log(f"{CMD_NAME} Command Created Event")

    try:
        # --- Phase 1: Validation ---

        # Check document is saved
        if not app.activeDocument.isSaved:
            ui.messageBox(
                "The active document must be saved before you can compare versions.",
                "Document Not Saved",
                0, 2,
            )
            args.command.doExecute(True)  # cancel
            return

        # Check active product is a Fusion 3D design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox(
                "Version Diff requires an active Fusion 3D design.",
                "No Design Found",
                0, 2,
            )
            args.command.doExecute(True)
            return

        # Check design is parametric (has timeline), not direct modeling
        if design.designType == adsk.fusion.DesignTypes.DirectDesignType:
            ui.messageBox(
                "Version Diff requires a parametric (timeline) design.\n"
                "Direct modeling designs do not have a timeline to compare.",
                "Direct Design Not Supported",
                0, 2,
            )
            args.command.doExecute(True)
            return

        # Check document has more than one version
        data_file = app.activeDocument.dataFile
        versions = data_file.versions
        if versions.count < 2:
            ui.messageBox(
                "This document has only one version.\n"
                "Save at least one more version before comparing.",
                "Insufficient Versions",
                0, 2,
            )
            args.command.doExecute(True)
            return

        # --- Phase 2: Build Dialog ---

        cmd = args.command
        inputs = cmd.commandInputs

        # Current version info group
        info_group = inputs.addGroupCommandInput("current_version_info", "Current Version")
        info_group.isEnabledCheckBoxDisplayed = False
        info_group.isExpanded = True

        group_inputs = info_group.children

        # Gather current version metadata
        version_num = data_file.versionNumber
        date_str = ""
        if data_file.dateModified:
            date_str = data_file.dateModified.strftime("%Y-%m-%d %H:%M:%S")
        updated_by = ""
        if data_file.lastUpdatedBy:
            updated_by = data_file.lastUpdatedBy.displayName
        description = data_file.description or "(no description)"

        group_inputs.addTextBoxCommandInput(
            "info_version", "Version",
            f"<b>Version {version_num}</b> of {data_file.latestVersionNumber}",
            1, True,
        )
        group_inputs.addTextBoxCommandInput(
            "info_date", "Date Saved",
            date_str,
            1, True,
        )
        group_inputs.addTextBoxCommandInput(
            "info_user", "Saved By",
            updated_by,
            1, True,
        )
        group_inputs.addTextBoxCommandInput(
            "info_desc", "Description",
            description,
            1, True,
        )

        # Comparison version dropdown
        dropdown = inputs.addDropDownCommandInput(
            "compare_version",
            "Compare With Version",
            adsk.core.DropDownStyles.TextListDropDownStyle,
        )

        current_version_num = data_file.versionNumber
        for i in range(versions.count):
            ver = versions.item(i)
            if ver.versionNumber == current_version_num:
                continue

            ver_date = ""
            if ver.dateModified:
                ver_date = ver.dateModified.strftime("%Y-%m-%d %H:%M")
            ver_user = ""
            if ver.lastUpdatedBy:
                ver_user = ver.lastUpdatedBy.displayName

            label = f"V{ver.versionNumber} - {ver_date} - {ver_user}"
            dropdown.listItems.add(label, i == 0)
            _version_map[label] = ver

        # Connect event handlers
        futil.add_handler(
            cmd.execute, command_execute, local_handlers=local_handlers
        )
        futil.add_handler(
            cmd.inputChanged, on_input_changed, local_handlers=local_handlers
        )
        futil.add_handler(
            cmd.destroy, command_destroy, local_handlers=local_handlers
        )

    except Exception as e:
        futil.log(f"Error in command_created: {e}\n{traceback.format_exc()}")
        ui.messageBox(f"Failed to initialize Version Diff:\n{str(e)}")


def on_input_changed(args: adsk.core.InputChangedEventArgs):
    """Handle input changes (stub for future use)."""
    pass


def command_execute(args: adsk.core.CommandEventArgs):
    """Execute the version diff: walk timelines, compute diff, generate report."""
    compare_doc = None

    try:
        # Resolve selected comparison version
        cmd_inputs = args.command.commandInputs
        dropdown = cmd_inputs.itemById("compare_version")
        selected_label = dropdown.selectedItem.name
        compare_data_file = _version_map.get(selected_label)

        if not compare_data_file:
            ui.messageBox("Could not resolve the selected version.", CMD_NAME, 0, 3)
            return

        # Walk baseline (current) timeline
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        baseline_features = walk_timeline(design.timeline)
        baseline_info = get_version_info(app.activeDocument.dataFile)

        futil.log(
            f"Baseline: V{baseline_info.version_number}, "
            f"{len(baseline_features)} timeline features"
        )

        # Open comparison version
        futil.log(f"Opening comparison version V{compare_data_file.versionNumber}...")
        compare_doc = app.documents.open(compare_data_file, True)

        if not compare_doc:
            ui.messageBox(
                "Failed to open the comparison version.",
                CMD_NAME, 0, 3,
            )
            return

        # Walk comparison timeline
        compare_product = compare_doc.products.itemByProductType("DesignProductType")
        compare_design = adsk.fusion.Design.cast(compare_product)

        if not compare_design:
            ui.messageBox(
                "The comparison version does not contain a valid design.",
                CMD_NAME, 0, 3,
            )
            return

        compare_features = walk_timeline(compare_design.timeline)
        compare_info = get_version_info(compare_data_file)

        futil.log(
            f"Comparison: V{compare_info.version_number}, "
            f"{len(compare_features)} timeline features"
        )

        # Close comparison document before generating report
        compare_doc.close(False)
        compare_doc = None

        # Compute diff
        diff_entries, summary = compute_diff(baseline_features, compare_features)

        diff_result = DiffResult(
            baseline=baseline_info,
            comparison=compare_info,
            features=diff_entries,
            summary=summary,
        )

        # Save JSON
        json_path = save_diff_json(diff_result)
        futil.log(f"Diff JSON saved to: {json_path}")

        # Generate and display HTML report
        html_path = generate_html_report(diff_result)
        futil.log(f"HTML report saved to: {html_path}")

        app.executeTextCommand(f"QTWebBrowser.Display file:///{html_path}")

        futil.log(
            f"Version Diff complete: "
            f"{summary['newer']} newer, "
            f"{summary['deleted']} deleted, "
            f"{summary['unchanged']} unchanged"
        )

    except Exception as e:
        error_msg = f"Version Diff failed: {str(e)}\n{traceback.format_exc()}"
        futil.log(error_msg)
        ui.messageBox(f"Version Diff failed:\n{str(e)}", CMD_NAME, 0, 3)

    finally:
        # Ensure comparison document is closed if still open
        if compare_doc:
            try:
                compare_doc.close(False)
            except:
                pass


def command_destroy(args: adsk.core.CommandEventArgs):
    """Clean up on command destruction."""
    global local_handlers, _version_map
    local_handlers = []
    _version_map = {}
    futil.log(f"{CMD_NAME} Command Destroy Event")
