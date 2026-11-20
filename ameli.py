"""Source 1 : cancer du poumon par département (Assurance Maladie, data.ameli.fr).

L'indicateur est une *prévalence traitée* (patients pris en charge dans l'année),
pas une incidence ni une mortalité. Il n'est pas standardisé sur l'âge ici.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .download import download_file
from .utils import normalise_dept, slugify, to_numeric

logger = logging.getLogger(__name__)

NATIONAL_DEPT = "999"  # code des lignes d'agrégat (France entière)
REQUIRED = {"annee", "patho_niv1", "patho_niv2", "patho_niv3", "dept", "ntop", "npop"}


def download_raw(year: int = config.AMELI_YEAR, force: bool = False) -> Path:
    """Télécharge via l'API le sous-ensemble utile : une année, tous sexes, tous âges.

    Le filtrage se fait côté serveur (langage ODSQL). Les filtres sont revérifiés
    dans `clean`, car l'API ignore silencieusement un paramètre mal reconnu.
    """
    params = {
        "where": f'year(annee)={year} AND sexe=9 AND cla_age_5="tsage"',
        "use_labels": "false",
        "delimiter": ";",
    }
    dest = config.RAW_DIR / f"ameli_effectifs_{year}.csv"
    return download_file(config.AMELI_EXPORT_URL, dest, params=params, force=force)


def load_raw(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", dtype=str)


def clean(raw: pd.DataFrame, year: int = config.AMELI_YEAR) -> pd.DataFrame:
    """Une ligne par département : effectifs et prévalence (pour 1 000) du cancer du poumon."""
    df = raw.rename(columns=str.lower).copy()
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes absentes {sorted(missing)} ; colonnes reçues : {list(df.columns)}")

    # Garde-fous : on revérifie les filtres demandés à l'API
    df = df[df["annee"].astype(str).str[:4] == str(year)]
    if "sexe" in df.columns:
        df = df[to_numeric(df["sexe"]) == 9]
    if "cla_age_5" in df.columns:
        df = df[df["cla_age_5"] == "tsage"]
    df = df[df["dept"].astype(str).str.strip() != NATIONAL_DEPT]  # on garde les départements

    # Lignes « poumon » : le niveau de la nomenclature varie selon la ligne
    levels = ["patho_niv3", "patho_niv2", "patho_niv1"]
    is_lung = {c: df[c].str.contains("poumon", case=False, na=False) for c in levels}
    df = df[is_lung["patho_niv3"] | is_lung["patho_niv2"] | is_lung["patho_niv1"]].copy()
    df["pathologie"] = np.select(
        [is_lung["patho_niv3"].loc[df.index], is_lung["patho_niv2"].loc[df.index]],
        [df["patho_niv3"], df["patho_niv2"]],
        default=df["patho_niv1"],
    )

    df["code_dep"] = normalise_dept(df["dept"])
    df["ntop"] = to_numeric(df["ntop"])  # patients ('NS' si < 11 -> NaN)
    df["npop"] = to_numeric(df["npop"])  # population de référence
    df = df.drop_duplicates(["code_dep", "pathologie"])

    # Passage en format large : une colonne par catégorie de cancer du poumon
    wide = df.pivot(index="code_dep", columns="pathologie", values=["ntop", "npop"])
    wide.columns = [f"{var}_{slugify(patho)}" for var, patho in wide.columns]
    out = wide.reset_index()
    for col in [c for c in out.columns if c.startswith("ntop_")]:
        suffix = col.removeprefix("ntop_")
        out[f"prev_pour_1000_{suffix}"] = 1000 * out[col] / out[f"npop_{suffix}"]
    return out
