"""Tests hors-ligne sur de petits jeux synthétiques (pas de réseau nécessaire)."""
import io
import zipfile

import pandas as pd

from src import ameli, insee
from src.build_dataset import merge_sources
from src.utils import normalise_dept, slugify


def test_normalise_dept():
    out = normalise_dept(pd.Series(["1", "01", "2a", "75", "971"]))
    assert out.tolist() == ["01", "01", "2A", "75", "971"]


def test_slugify():
    assert slugify("Cancer du poumon actif") == "cancer_du_poumon_actif"


def _fake_ameli():
    base = dict(annee="2024-01-01", sexe="9", cla_age_5="tsage", patho_niv1="Cancers")
    rows = [
        dict(base, patho_niv2="Cancer du poumon", patho_niv3="Cancer du poumon actif", dept="1", ntop="100", npop="10000"),
        dict(base, patho_niv2="Cancer du poumon", patho_niv3="Cancer du poumon actif", dept="2A", ntop="NS", npop="5000"),
        dict(base, patho_niv2="Cancer du sein", patho_niv3="Cancer du sein", dept="1", ntop="300", npop="10000"),
        dict(base, patho_niv2="Cancer du poumon", patho_niv3="Cancer du poumon actif", dept="999", ntop="9", npop="9"),
        dict(base, patho_niv2="Cancer du poumon", patho_niv3="Cancer du poumon actif", dept="1", ntop="1", npop="1", sexe="1"),
    ]
    return pd.DataFrame(rows)


def test_ameli_clean():
    out = ameli.clean(_fake_ameli(), year=2024)
    assert set(out["code_dep"]) == {"01", "2A"}            # agrégat national et autres cancers exclus
    row = out.set_index("code_dep").loc["01"]
    assert row["prev_pour_1000_cancer_du_poumon_actif"] == 10.0
    assert pd.isna(out.set_index("code_dep").loc["2A", "prev_pour_1000_cancer_du_poumon_actif"])  # NS -> NaN


def test_insee_load_and_clean(tmp_path):
    csv = "CODGEO;LIBGEO;MED21;TP6021\n1;Ain;24810;10,8\n2A;Corse-du-Sud;22000;18.0\n"
    path = tmp_path / "f.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("cc_filosofi_2021_COM.csv", "CODGEO;LIBGEO;MED21\n01001;X;1\n")
        zf.writestr("cc_filosofi_2021_DEP.csv", csv)
    out = insee.clean(insee.load_raw(path))
    assert out["code_dep"].tolist() == ["01", "2A"]
    assert out["taux_pauvrete"].tolist() == [10.8, 18.0]


def test_merge():
    cancer = ameli.clean(_fake_ameli(), year=2024)
    social = pd.DataFrame({"code_dep": ["01", "75"], "taux_pauvrete": [10.8, 15.0]})
    merged = merge_sources(cancer, social)
    assert merged["code_dep"].tolist() == ["01"]
