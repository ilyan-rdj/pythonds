"""Source 2 : indicateurs sociaux par département (Insee, Filosofi 2021)."""
import io
import logging
import zipfile
from pathlib import Path

import pandas as pd

from . import config
from .download import download_file
from .utils import normalise_dept, to_numeric

logger = logging.getLogger(__name__)

# Noms Insee -> noms lisibles (seules les colonnes présentes sont conservées)
RENAME = {
    "CODGEO": "code_dep",
    "LIBGEO": "departement",
    "NBMENFISC21": "nb_menages_fiscaux",
    "NBPERSMENFISC21": "nb_personnes",
    "MED21": "niveau_vie_median",
    "TP6021": "taux_pauvrete",
    "PIMP21": "part_menages_imposes",
    "PCHO21": "part_indemnites_chomage",
    "PPEN21": "part_pensions_retraites",
    "PPSOC21": "part_prestations_sociales",
    "D121": "decile1_niveau_vie",
    "D921": "decile9_niveau_vie",
    "RD21": "rapport_interdecile",
}


def download_raw(force: bool = False) -> Path:
    return download_file(config.INSEE_FILOSOFI_URL, config.RAW_DIR / "insee_filosofi_2021.zip", force=force)


def load_raw(path: Path) -> pd.DataFrame:
    """Lit, dans le zip, le fichier au niveau département (le zip en contient un par niveau)."""
    with zipfile.ZipFile(path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        dep = [n for n in members if "dep" in n.lower().rsplit("/", 1)[-1]]
        if not dep:
            raise FileNotFoundError(f"Pas de fichier département dans le zip : {members}")
        with zf.open(dep[0]) as f:
            return pd.read_csv(io.BytesIO(f.read()), sep=";", dtype=str)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par département, colonnes renommées et converties en numérique."""
    df = raw.rename(columns=RENAME)
    if "code_dep" not in df.columns or "niveau_vie_median" not in df.columns:
        raise ValueError(f"Colonnes Insee inattendues : {list(raw.columns)}")
    keep = [c for c in RENAME.values() if c in df.columns]
    df = df[keep].copy()
    df["code_dep"] = normalise_dept(df["code_dep"])
    for col in keep:
        if col not in ("code_dep", "departement"):
            df[col] = to_numeric(df[col])
    return df.drop_duplicates("code_dep")
