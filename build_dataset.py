"""Pipeline complet : télécharge, nettoie et fusionne les sources par département.

Usage :  python -m src.build_dataset [--year 2024] [--force]
"""
import argparse
import logging

import pandas as pd

from . import ameli, config, insee

logger = logging.getLogger(__name__)


def merge_sources(cancer: pd.DataFrame, social: pd.DataFrame) -> pd.DataFrame:
    """Jointure sur le code département, avec un diagnostic des non-appariés."""
    merged = social.merge(cancer, on="code_dep", how="outer", indicator=True)
    for side, label in (("left_only", "Insee seul"), ("right_only", "Ameli seul")):
        codes = merged.loc[merged["_merge"] == side, "code_dep"].tolist()
        if codes:
            logger.warning("%s (%d) : %s", label, len(codes), codes)
    return merged[merged["_merge"] == "both"].drop(columns="_merge").reset_index(drop=True)


def build(year: int = config.AMELI_YEAR, force: bool = False) -> pd.DataFrame:
    cancer = ameli.clean(ameli.load_raw(ameli.download_raw(year, force)), year)
    social = insee.clean(insee.load_raw(insee.download_raw(force)))
    df = merge_sources(cancer, social)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROCESSED_DIR / "departements.csv"
    df.to_csv(out, index=False)
    logger.info("Table finale : %d départements, %d colonnes -> %s", *df.shape, out)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=config.AMELI_YEAR)
    parser.add_argument("--force", action="store_true", help="re-télécharge même si en cache")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    df = build(args.year, args.force)
    prev = next((c for c in df.columns if c.startswith("prev_pour_1000")), None)
    print(df.shape, "\nValeurs manquantes :\n", df.isna().sum()[lambda s: s > 0])
    if prev and "taux_pauvrete" in df.columns:
        print(f"\nCorrélation de Spearman ({prev} vs taux de pauvreté) :",
              round(df[prev].corr(df["taux_pauvrete"], method="spearman"), 2))


if __name__ == "__main__":
    main()
