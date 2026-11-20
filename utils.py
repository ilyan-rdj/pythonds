"""Fonctions utilitaires partagées entre les sources."""
import re
import unicodedata

import pandas as pd


def normalise_dept(code: pd.Series) -> pd.Series:
    """Normalise les codes département : '1' -> '01', '2a' -> '2A', '971' inchangé.

    C'est la clé de jointure commune à toutes les sources.
    """
    code = code.astype(str).str.strip().str.upper()
    return code.where(~code.str.fullmatch(r"\d{1,2}"), code.str.zfill(2))


def slugify(text: str) -> str:
    """'Cancer du poumon actif' -> 'cancer_du_poumon_actif' (noms de colonnes propres)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def to_numeric(s: pd.Series) -> pd.Series:
    """Convertit en nombre (virgule décimale acceptée) ; 'NS', 's', etc. -> NaN."""
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")
