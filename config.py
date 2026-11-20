"""Paramètres centraux du projet (URL des sources, chemins, millésimes)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"              # données brutes téléchargées (non versionnées)
PROCESSED_DIR = ROOT / "data" / "processed"  # tables nettoyées (non versionnées)

# --- Source 1 : Assurance Maladie (API Opendatasoft, licence ODbL) -------------
# Patients pris en charge pour cancer du poumon, par département.
# L'API filtre côté serveur : on ne télécharge que le millésime voulu
# (le fichier complet fait ~1 Go).
AMELI_EXPORT_URL = (
    "https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv"
)
AMELI_YEAR = 2024

# --- Source 2 : Insee, Filosofi 2021 (revenus et pauvreté), fichier plat -------
INSEE_FILOSOFI_URL = (
    "https://www.insee.fr/fr/statistiques/fichier/7756729/"
    "base-cc-filosofi-2021-geo2025_csv.zip"
)
