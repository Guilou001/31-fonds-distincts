"""La couverture dynamique, éprouvée sur l'exemple travaillé et sur les vingt scénarios."""

from __future__ import annotations

from dataclasses import replace

import pytest

from fdg import appendices, couverture
from fdg.garantie import Contrat, passif_reformule


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
    """Le capital ne se réduit pas parce que la couverture a rapporté dans certains scénarios.

    La règle s'éprouve sur une entrée qui la déclenche, et non sur le contrat par défaut. Les
    vingt erreurs de suivi y sont toutes positives. Retirer le plancher ne changerait donc aucun
    nombre publié, et laisserait un test vert.
    """
    assert couverture.moyenne_des_valeurs_positives([1.0, -3.0, 2.0, -4.0]) == pytest.approx(0.75)
    assert couverture.moyenne_des_valeurs_positives([-1.0, -2.0]) == pytest.approx(0.0)
    moyenne_ordinaire = (1.0 - 3.0 + 2.0 - 4.0) / 4
    assert couverture.moyenne_des_valeurs_positives([1.0, -3.0, 2.0, -4.0]) > moyenne_ordinaire


def test_un_scenario_plat_laisse_passer_exactement_le_passage_du_temps():
    """Sans mouvement de prix, une couverture en delta n'a rigoureusement rien à rattraper.

    Ce qui reste est le passage du temps sur le passif reformulé, décroissance de la garantie et
    frais de garantie encaissés confondus. Le seuil est donc cette dérive elle-même, et non une
    borne lâche : à moins de 1,0, le test tolérait 83 % de l'exigence publiée du § 5.4 et un défaut
    qui aurait doublé la part des frais serait resté invisible.
    """
    c = Contrat()
    r = couverture.rejouer_un_scenario(c, [100.0] * 53, c.taux)
    attendu = passif_reformule(replace(c, annees=9.0)) - passif_reformule(c)
    assert r["valeur_actuelle"] == pytest.approx(attendu, rel=0.05)
    assert r["valeur_actuelle"] == pytest.approx(couverture.derive_du_chemin_plat(c))


def test_la_derive_du_chemin_plat_est_publiee_et_pese_plus_de_la_moitie():
    """Le nombre de tête du § 5.4 contient cette dérive, et le README le dit. Le test le tient :
    si l'exigence cessait de la contenir, le README devrait changer avec le code."""
    c = Contrat()
    r = couverture.credit_de_couverture(c)
    assert r["derive_du_chemin_plat"] > 0.5 * r["exigence_avec_couverture"]
    assert r["derive_du_chemin_plat"] < r["exigence_avec_couverture"]


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
