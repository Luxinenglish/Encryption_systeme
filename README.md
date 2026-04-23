# Encryption Systeme

Application desktop Python pour chiffrer et déchiffrer des fichiers/dossiers avec une interface graphique Tkinter.

## Fonctionnalités

- Chiffrement d'un **fichier** ou d'un **dossier**
- Déchiffrement d'un **fichier** ou d'un **dossier**
- Support de plusieurs algorithmes :
    - Fernet (AES-128-CBC)
    - AES-256-GCM
    - ChaCha20-Poly1305
- Glisser-déposer (si `tkinterdnd2` est disponible)
- Gestion locale des clés (sauvegarde JSON)

## Technologies

- Python 3
- Tkinter
- `cryptography`
- `tkinterdnd2` (optionnel mais recommandé pour le drag-and-drop)
- PyInstaller (build `.exe`)
- Inno Setup (build installateur)

## Installation (mode développement)

1. Créer un environnement virtuel
2. Installer les dépendances
3. Lancer l'application

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
