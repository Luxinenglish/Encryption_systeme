# Build & Compilation

## 1. Compiler l'exe (PyInstaller)

```bash
pyinstaller EncryptionSystem.spec --noconfirm
```

Le résultat est dans `dist/EncryptionSystem.exe`.

---

## 2. Compiler l'installateur (Inno Setup)

### Via ligne de commande

```bash
C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### Via l'interface Inno Setup

1. Ouvrir `installer.iss` dans Inno Setup Compiler
2. `Build` → `Compile` (ou `Ctrl+F9`)

Le résultat est dans `installer_output/EncryptionSystem_Setup.exe`.

---

## Compilation complète (exe + installateur)

```bash
pyinstaller EncryptionSystem.spec --noconfirm && "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```
