@echo off
pyinstaller EncryptionSystem.spec --noconfirm && "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss && echo =================================================================== && echo 1. Ouvrir `installer.iss` dans Inno Setup Compiler && echo 2. `Build` → `Compile` (ou `Ctrl+F9`) && echo Le résultat est dans `installer_output/EncryptionSystem_Setup.exe`.
