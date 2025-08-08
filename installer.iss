[Setup]
AppName=YT Playlist Sorter & Tracker
AppVersion=1.0
DefaultDirName={pf}\YTPlaylistSorter
DefaultGroupName=YT Playlist Sorter & Tracker
UninstallDisplayIcon={app}\main_app.exe
OutputDir=.
OutputBaseFilename=YTPlaylistSorterSetup
SetupIconFile=installer_files\logo\logo.ico

[Files]
Source: "installer_files\main_app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_files\helpers.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_files\config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_files\logo\logo.png"; DestDir: "{app}\logo"; Flags: ignoreversion

[Icons]
Name: "{group}\YT Playlist Sorter & Tracker"; Filename: "{app}\main_app.exe"
Name: "{userdesktop}\YT Playlist Sorter & Tracker"; Filename: "{app}\main_app.exe"; Tasks: desktopicon
Name: "{group}\YT Playlist Sorter & Tracker"; Filename: "{app}\main_app.exe"; IconFilename: "{app}\logo\logo.ico"
Name: "{userdesktop}\YT Playlist Sorter & Tracker"; Filename: "{app}\main_app.exe"; IconFilename: "{app}\logo\logo.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"