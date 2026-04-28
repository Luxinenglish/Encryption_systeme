# Encryption Systeme — Site web

Site vitrine statique (HTML/CSS/JS) pour présenter l’application **Encryption Systeme**.

## Structure

- `index.html` : page d’accueil
- `features/` : fonctionnalités
- `download/` : téléchargement
- `security/` : sécurité
- `faq/` : FAQ
- `about/` : à propos
- `assets/` : images, CSS, JS

## Personnalisation rapide

1. Remplacer l’URL GitHub dans `download/index.html` (chercher `OWNER/REPO`).
2. Remplacer les liens GitHub dans `about/index.html`.
3. Ajouter une capture d’écran :
   - `assets/img/screenshot.png`

## Lancer en local

Depuis `Encryption_systeme_website` :

```powershell
python -m http.server 5173
```

Puis ouvrir : http://localhost:5173/

## Déploiement (GitHub Pages)

- Paramétrer GitHub Pages sur la branche qui contient ce dossier.
- Source : `/(root)`.

> Important : ce site utilise des chemins absolus (`/assets/...`).
> Sur GitHub Pages avec un *project site* (ex: `https://user.github.io/repo/`), il faut soit :
> - déployer en *user site* (racine du domaine), soit
> - remplacer les chemins par des chemins relatifs, soit
> - configurer un `base` (si vous passez à un bundler comme Vite).

