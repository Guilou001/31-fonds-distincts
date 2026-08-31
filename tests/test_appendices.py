"""Les trois appendices, éprouvés sur leur forme et sur ce que la ligne directrice en cite."""

from __future__ import annotations

import pytest

from fdg import appendices, reference


def test_la_grille_a_soixante_quinze_lignes_et_treize_colonnes():
    for base in ("terme", "comptant"):
        grille = appendices.table_des_chocs(base)
        assert len(grille) == 75
        assert all(len(ligne) == 13 for ligne in grille)


def test_les_volatilites_vont_de_un_a_soixante_quinze_sans_trou():
    assert appendices.volatilites() == list(range(1, 76))


def test_les_echeances_sont_croissantes_et_irregulieres():
    """L'irrégularité compte : interpoler entre 84 et 120 mois n'est pas interpoler entre deux
    points équidistants, et un code qui prendrait la moyenne simple se tromperait."""
    mois = appendices.mois()
    assert mois == sorted(mois)
    ecarts = [b - a for a, b in zip(mois, mois[1:], strict=False)]
    assert len(set(ecarts)) > 1


def test_les_vingt_cellules_citees_par_la_ligne_directrice_se_retrouvent():
    """C'est la première chose à établir quand on recopie une grille de mille nombres : que les
    lignes et les colonnes n'ont pas été interverties."""
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    for (v, m), citee in reference.CELLULES_CITEES.items():
        assert grille[vols.index(v)][mois.index(m)] == pytest.approx(citee)


def test_les_scenarios_partent_tous_de_cent():
    for pas in ("hebdomadaire", "mensuel"):
        assert appendices.scenarios(pas)[0] == [100.0] * 20


def test_les_deux_echantillonnages_finissent_au_meme_point():
    """Les tables hebdomadaire et mensuelle sont les mêmes vingt trajectoires, échantillonnées
    autrement. Leur dernier point doit donc coïncider, et il coïncide."""
    hebdo = appendices.scenarios("hebdomadaire")
    mensuel = appendices.scenarios("mensuel")
    assert len(hebdo) == 53
    assert len(mensuel) == 13
    assert hebdo[-1] == mensuel[-1]


def test_dix_scenarios_montent_et_dix_baissent():
    """Le jeu du régulateur est équilibré par construction, ce qui n'était pas annoncé mais se
    mesure : la moitié des trajectoires finit au-dessus de cent et l'autre en dessous."""
    fin = appendices.scenarios("hebdomadaire")[-1]
    assert sum(1 for p in fin if p > 100) == 10
    assert sum(1 for p in fin if p < 100) == 10


def test_la_source_est_declaree():
    assert "chapitre 7" in appendices.source()
