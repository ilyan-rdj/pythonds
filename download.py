"""Téléchargement avec cache local : base de la reproductibilité.

Les données brutes sont téléchargées depuis leur URL publique une seule fois,
stockées dans data/ (ignoré par Git) puis relues depuis le disque.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "projet-cancer-poumon (projet etudiant ENSAE)"}


def _session() -> requests.Session:
    """Session HTTP avec relances automatiques en cas d'erreur transitoire."""
    retry = Retry(total=4, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504))
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(HEADERS)
    return session


def download_file(url: str, dest: Path, params: dict | None = None, force: bool = False) -> Path:
    """Télécharge `url` vers `dest` (sauf si déjà présent) et trace la provenance.

    Un fichier `<dest>.meta.json` garde l'URL, les paramètres et la date de
    téléchargement : utile pour documenter les données dans le rapport.
    """
    dest = Path(dest)
    if dest.exists() and not force:
        logger.info("Cache utilisé : %s", dest)
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    logger.info("Téléchargement : %s", url)
    with _session().get(url, params=params, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(dest)  # écriture atomique : pas de fichier à moitié téléchargé

    meta = {
        "url": resp.url,
        "params": params,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "size_bytes": dest.stat().st_size,
    }
    dest.with_suffix(dest.suffix + ".meta.json").write_text(json.dumps(meta, indent=2))
    return dest
