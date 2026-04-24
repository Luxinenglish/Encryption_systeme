import json
import platform
import re
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass
class UpdateCheckResult:
    update_available: bool
    message: str
    latest_version: str | None = None
    release_notes: str = ""
    release_url: str | None = None
    asset: ReleaseAsset | None = None
    error: str | None = None


class UpdateService:
    def __init__(self, repo: str, current_version: str, timeout: float = 10.0):
        self.repo = repo.strip()
        self.current_version = current_version.strip()
        self.timeout = timeout

    def check_for_updates(self) -> UpdateCheckResult:
        if not self.repo or "/" not in self.repo:
            return UpdateCheckResult(
                update_available=False,
                message="Depot GitHub non configure.",
                error="Configuration GitHub invalide.",
            )

        try:
            release = self._fetch_latest_release()
        except urllib.error.URLError as exc:
            return UpdateCheckResult(
                update_available=False,
                message="Impossible de verifier les mises a jour.",
                error=str(exc),
            )
        except Exception as exc:
            return UpdateCheckResult(
                update_available=False,
                message="Erreur inattendue pendant la verification des mises a jour.",
                error=str(exc),
            )

        latest_tag = str(release.get("tag_name") or "").strip()
        latest_version = _normalize_version(latest_tag)
        current_version = _normalize_version(self.current_version)

        if not _is_newer(latest_version, current_version):
            return UpdateCheckResult(
                update_available=False,
                message=f"Vous etes deja a jour ({self.current_version}).",
                latest_version=latest_version,
                release_notes=str(release.get("body") or ""),
                release_url=str(release.get("html_url") or ""),
            )

        asset = self._select_asset(release.get("assets") or [])
        if asset is None:
            return UpdateCheckResult(
                update_available=False,
                message=f"Version {latest_version} disponible, mais aucun fichier compatible trouve.",
                latest_version=latest_version,
                release_notes=str(release.get("body") or ""),
                release_url=str(release.get("html_url") or ""),
            )

        return UpdateCheckResult(
            update_available=True,
            message=f"Nouvelle version {latest_version} disponible.",
            latest_version=latest_version,
            release_notes=str(release.get("body") or ""),
            release_url=str(release.get("html_url") or ""),
            asset=asset,
        )

    def download_asset(self, asset: ReleaseAsset, target_dir: Path | None = None) -> Path:
        if target_dir is None:
            default_downloads = Path.home() / "Downloads"
            target_dir = default_downloads if default_downloads.exists() else Path(tempfile.gettempdir())

        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / asset.name

        req = urllib.request.Request(
            asset.download_url,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": "EncryptionSystem-Updater",
            },
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            with destination.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 64)
                    if not chunk:
                        break
                    output.write(chunk)

        return destination

    def _fetch_latest_release(self) -> dict:
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "EncryptionSystem-Updater",
            },
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            payload = response.read().decode("utf-8")

        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Reponse GitHub invalide.")
        return data

    def _select_asset(self, assets: list[dict]) -> ReleaseAsset | None:
        if not assets:
            return None

        ext_preferences = self._extension_preferences()
        arch_tokens = _arch_tokens()

        best_score = -1
        best_asset: ReleaseAsset | None = None

        for item in assets:
            name = str(item.get("name") or "")
            url = str(item.get("browser_download_url") or "")
            if not name or not url:
                continue

            score = _extension_score(name, ext_preferences)
            if score <= 0:
                continue

            lowered = name.lower()
            if arch_tokens and any(token in lowered for token in arch_tokens):
                score += 20

            if score > best_score:
                best_score = score
                best_asset = ReleaseAsset(
                    name=name,
                    download_url=url,
                    size=int(item.get("size") or 0),
                )

        return best_asset

    def _extension_preferences(self) -> list[str]:
        system_name = platform.system().lower()
        if system_name == "windows":
            return [".exe", ".msi", ".zip"]
        if system_name == "darwin":
            return [".dmg", ".pkg", ".zip"]

        # Linux: Debian en priorite, sinon alternatives courantes.
        if _is_debian_like_linux():
            return [".deb", ".appimage", ".tar.gz", ".zip", ".rpm"]
        return [".rpm", ".appimage", ".tar.gz", ".zip", ".deb"]


def _normalize_version(raw: str) -> str:
    return raw.strip().lstrip("vV")


def _version_key(version: str) -> tuple[list[int], bool]:
    normalized = _normalize_version(version)
    digits = [int(x) for x in re.findall(r"\d+", normalized)]
    prerelease = bool(re.search(r"[a-zA-Z]", normalized))
    return digits or [0], prerelease


def _is_newer(candidate: str, current: str) -> bool:
    cand_nums, cand_pre = _version_key(candidate)
    curr_nums, curr_pre = _version_key(current)

    max_len = max(len(cand_nums), len(curr_nums))
    cand_nums = cand_nums + [0] * (max_len - len(cand_nums))
    curr_nums = curr_nums + [0] * (max_len - len(curr_nums))

    if cand_nums != curr_nums:
        return cand_nums > curr_nums

    # A numeros egaux, une version stable est plus recente qu'une prerelease.
    if curr_pre and not cand_pre:
        return True
    return False


def _extension_score(filename: str, preferences: list[str]) -> int:
    lowered = filename.lower()
    for index, ext in enumerate(preferences):
        if lowered.endswith(ext):
            return len(preferences) - index
    return 0


def _arch_tokens() -> list[str]:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return ["x86_64", "amd64", "x64", "win64"]
    if machine in {"arm64", "aarch64"}:
        return ["arm64", "aarch64"]
    if machine in {"x86", "i386", "i686"}:
        return ["x86", "i386", "i686", "win32"]
    return []


def _is_debian_like_linux() -> bool:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return False

    try:
        content = os_release.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False

    return "debian" in content or "ubuntu" in content

