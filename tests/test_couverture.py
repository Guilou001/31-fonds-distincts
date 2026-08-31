"""La couverture dynamique, éprouvée sur l'exemple travaillé et sur les vingt scénarios."""

from __future__ import annotations

import pytest

from fdg import appendices, couverture
from fdg.garantie import Contrat


def test_l_exemple_travaille_du_regulateur_se_refait():
    """La ligne directrice déroule un pas de couverture, chiffre par chiffre. Les trois nombres
    qu'elle imprime se retrouvent."""
    r = couverture.refaire_l_exemple()
    assert r["variation_passif"] == pytest.approx(205.0)
    assert r["variation_actif"] == pytest.approx(178.0)
    assert r["perte"] == pytest.approx(27.0)
    assert r["coincide"]


def test_la_couverture_est_rejouee_sur_les_vingt_scenarios():
    r = couverture.exigence_avec_couverture(Contrat())
    assert r["scenarios"] == 20
    assert len(r["valeurs"]) == 20


def test_seules_les_valeurs_positives_comptent_dans_la_moyenne():
    """Le capital ne se réduit pas parce que la couverture a rapporté dans certains scénarios."""
    r = couverture.exigence_avec_couverture(Contrat())
    moyenne_brute = sum(r["valeurs"]) / 20
    moyenne_retenue = r["exigence"]
    assert moyenne_retenue >= moyenne_brute - 1e-12
    assert moyenne_retenue >= 0


def test_un_scenario_plat_ne_laisse_presque_rien_passer():
    """Sans mouvement de prix, une couverture rééquilibrée n'a rien à rattraper : ce qui reste est
    la seule érosion due au passage du temps."""
    c = Contrat()
    plat = [100.0] * 53
    r = couverture.rejouer_un_scenario(c, plat, c.taux)
    assert abs(r["valeur_actuelle"]) < 1.0


def test_la_couverture_reduit_l_exigence_sans_l_annuler():
    """Une couverture parfaite n'existe pas : le rééquilibrage discret laisse toujours passer
    quelque chose."""
    r = couverture.credit_de_couverture(Contrat())
    assert 0 < r["credit"] < r["exigence_sans_couverture"]
    assert 0.5 < r["part_reduite"] < 1.0


def test_rééquilibrer_plus_souvent_laisse_passer_moins():
    hebdo = couverture.credit_de_couverture(Contrat(), "hebdomadaire")
    mensuel = couverture.credit_de_couverture(Contrat(), "mensuel")
    assert hebdo["exigence_avec_couverture"] < mensuel["exigence_avec_couverture"]


def test_une_bande_de_non_intervention_large_laisse_passer_davantage():
    serre = couverture.credit_de_couverture(Contrat(), tolerance=0.0)
    lache = couverture.credit_de_couverture(Contrat(), tolerance=0.05)
    assert lache["exigence_avec_couverture"] > serre["exigence_avec_couverture"]


def test_les_scenarios_baissiers_coutent_plus_que_les_haussiers():
    """Un vendeur d'options qui se couvre en delta perd sur les grands mouvements, et les
    trajectoires baissières poussent la garantie vers la monnaie où sa sensibilité bouge le plus."""
    c = Contrat()
    r = couverture.exigence_avec_couverture(c)
    fin = appendices.scenarios("hebdomadaire")[-1]
    baissiers = [v for v, p in zip(r["valeurs"], fin, strict=True) if p < 100]
    haussiers = [v for v, p in zip(r["valeurs"], fin, strict=True) if p > 100]
    assert sum(baissiers) / len(baissiers) > sum(haussiers) / len(haussiers)
