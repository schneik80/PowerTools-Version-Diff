[Setup]
AppName=PowerTools-Version-Diff
AppVersion=1.0
AppPublisher=IMA LLC
DefaultDirName={userappdata}\Autodesk\Autodesk Fusion 360\API\AddIns\PowerTools-Version-Diff
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputBaseFilename=PowerTools-Version-Diff-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayName=PowerTools-Version-Diff (Fusion Add-In)

[Files]
Source: "..\..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Excludes: ".git,*.git*,.github,installer"

[Code]
// No custom code needed - Inno Setup handles the copy
