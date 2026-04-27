#define MyAppName      "Encryption System"
#define MyAppVersion   "1.0.2"
#define MyAppPublisher "Lux_"
#define MyAppExeName   "EncryptionSystem.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=EncryptionSystem_Setup
SetupIconFile=img\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\logo.ico
UninstallDisplayName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "french";    MessagesFile: "compiler:Languages\French.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "img\logo.ico";         DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Code]
var
  LanguageSelectionPage: TInputOptionWizardPage;
  SelectedLanguage: string;

procedure InitializeWizard;
begin
  // Create language selection page
  LanguageSelectionPage := CreateInputOptionPage(
    wpSelectTasks,
    'Sélection de la langue / Language Selection',
    'Choisissez votre langue préférée / Choose your preferred language',
    'La langue sélectionnée sera utilisée au prochain démarrage de l''application.' + #13#10 +
    'The selected language will be used when the application starts next time.',
    False,
    False
  );

  // Add language options
  LanguageSelectionPage.Add('Français (French)');
  LanguageSelectionPage.Add('English');

  // Set default based on installer language
  if CompareStr(ActiveLanguage, 'french') = 0 then
    LanguageSelectionPage.Values[0] := True
  else
    LanguageSelectionPage.Values[1] := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: string;
  ConfigFile: string;
  ConfigContent: string;
begin
  if CurStep = ssPostInstall then
  begin
    // Determine selected language
    if LanguageSelectionPage.Values[0] then
      SelectedLanguage := 'fr'
    else
      SelectedLanguage := 'en';

    // Create config directory if it doesn't exist
    ConfigDir := ExpandConstant('{userprofile}\.EncryptionSystem');
    if not DirExists(ConfigDir) then
      CreateDir(ConfigDir);

    // Write config file with selected language
    ConfigFile := ConfigDir + '\config.json';
    ConfigContent := '{"language": "' + SelectedLanguage + '", "theme": "dark"}';

    SaveStringToFile(ConfigFile, ConfigContent, False);
  end;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
