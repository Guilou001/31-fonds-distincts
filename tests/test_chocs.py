"""Le choc de volatilité, éprouvé sur les neuf exemples travaillés de la ligne directrice."""

from __future__ import annotations

import pytest

from fdg import appendices, chocs, etudes, reference


def test_les_neuf_chocs_publies_se_retrouvent():
    """Neuf sur neuf, à la décimale que la ligne directrice imprime."""
    for e in reference.EXEMPLES:
        assert chocs.choc(e.volatilite, e.mois) == pytest.approx(e.choc_publie, abs=0.05)


def test_huit_totaux_sur_neuf_se_retrouvent_et_le_neuvieme_est_faux():
    """C'est le constat du dépôt, et il est mesuré plutôt qu'affirmé.

    La ligne directrice écrit, pour 54,0 % à 115 mois, un choc de −3,6 puis une volatilité choquée
    de 51,4. Or 54,0 moins 3,6 fait 50,4. Le choc, lui, est juste.
    """
    table = etudes.exemples_du_regulateur()
    assert bool(table["choc_coincide"].all())
    faux = table[~table["total_coincide"]]
    assert len(faux) == 1
    ligne = faux.iloc[0]
    assert ligne["volatilite"] == pytest.approx(54.0)
    assert ligne["mois"] == 115
    assert ligne["total_publie"] == pytest.approx(51.4)
    assert ligne["total_recalcule"] == pytest.approx(50.4)


def test_sur_un_point_de_la_grille_l_interpolation_rend_la_case():
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    for v in (1, 18, 40, 75):
        for m in (1, 60, 1200):
            attendu = grille[vols.index(v)][mois.index(m)]
            assert chocs.choc(float(v), float(m)) == pytest.approx(attendu)


def test_l_interpolation_en_volatilite_suit_la_regle_du_regulateur():
    """L'exemple à 18,7 % l'écrit : 0,3 fois la ligne 18 plus 0,7 fois la ligne 19."""
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    j = mois.index(1)
    attendu = 0.3 * grille[vols.index(18)][j] + 0.7 * grille[vols.index(19)][j]
    assert chocs.choc(18.7, 1) == pytest.approx(attendu)
    assert attendu == pytest.approx(22.3)


def test_l_interpolation_en_mois_suit_la_regle_du_regulateur():
    """L'exemple à 115 mois l'écrit : (5 × la colonne 84 + 31 × la colonne 120) ÷ 36."""
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    i = vols.index(5)
    attendu = (5 * grille[i][mois.index(84)] + 31 * grille[i][mois.index(120)]) / 36
    assert chocs.choc(5.0, 115) == pytest.approx(attendu)


def test_hors_de_la_grille_on_retient_le_bord_plutot_que_d_extrapoler():
    """Extrapoler inventerait un choc que le régulateur n'a pas publié."""
    assert chocs.choc(0.2, 60) == pytest.approx(chocs.choc(1.0, 60))
    assert chocs.choc(120.0, 60) == pytest.approx(chocs.choc(75.0, 60))
    assert chocs.choc(20.0, 5000) == pytest.approx(chocs.choc(20.0, 1200))
    assert chocs.choc(20.0, 0.5) == pytest.approx(chocs.choc(20.0, 1.0))


def test_le_tres_court_terme_est_epingle_a_quarante_et_un():
    """Quelle que soit la volatilité de départ, le choc d'un mois y ajoute ce qu'il faut pour
    arriver à 41 %. La ligne directrice ne l'écrit nulle part."""
    for v in (1.0, 5.0, 18.0, 40.0, 54.0, 75.0):
        assert chocs.volatilite_choquee(v, 1) == pytest.approx(41.0, abs=0.11)


def test_le_tres_long_terme_est_epingle_a_vingt_cinq():
    for v in (1.0, 5.0, 18.0, 40.0, 54.0, 75.0):
        for m in (360, 1200):
            assert chocs.volatilite_choquee(v, m) == pytest.approx(25.0, abs=1e-9)


def test_au_dela_du_pivot_le_choc_devient_une_baisse():
    """Un assureur déjà très agité voit sa volatilité RÉDUITE par le scénario de tension, ce qui
    est la conséquence directe de l'épinglage."""
    pivots = {p["mois"]: p["pivot"] for p in chocs.volatilite_pivot("terme")}
    for m, pivot in pivots.items():
        assert pivot is not None
        assert chocs.choc(pivot - 5.0, m) > 0
        assert chocs.choc(pivot + 5.0, m) < 0
