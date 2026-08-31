"""L'exigence de capital, et la façon dont les deux chocs se rencontrent."""

from __future__ import annotations

from dataclasses import replace

import pytest

from fdg import chocs
from fdg.capital import FACTEUR_ACTIONS, contrat_choque, decomposer
from fdg.garantie import Contrat


def test_le_choc_d_actions_ne_touche_que_le_fonds():
    """La promesse ne bouge pas quand le marché baisse : c'est le principe du produit."""
    c = Contrat()
    d = contrat_choque(c, actions=True, volatilite=False)
    assert d.fonds == pytest.approx(c.fonds * (1 - FACTEUR_ACTIONS))
    assert d.garantie == pytest.approx(c.garantie)
    assert d.volatilite == pytest.approx(c.volatilite)


def test_le_facteur_d_actions_de_la_section_cinq_deux_retire_bien_un_tiers_du_fonds():
    """Un test qui comparerait FACTEUR_ACTIONS à son propre littéral ne vérifierait rien : changer
    les deux ensemble le laisserait vert. Celui-ci vérifie l'effet, sur un fonds de cent."""
    d = contrat_choque(Contrat(fonds=100.0), actions=True, volatilite=False)
    assert d.fonds == pytest.approx(65.0)
    assert d.fonds == pytest.approx(100.0 * (1 - 0.35))


def test_la_conversion_entre_points_et_fraction_se_fait_une_seule_fois():
    """La grille du régulateur travaille en points, le contrat en fraction. Confondre les deux
    multiplierait le choc par cent, ce qu'aucun test de forme ne verrait."""
    c = Contrat(volatilite=0.187, annees=115 / 12)
    d = contrat_choque(c, actions=False, volatilite=True)
    attendu = (18.7 + chocs.choc(18.7, 115)) / 100
    assert d.volatilite == pytest.approx(attendu)
    assert 0.3 < d.volatilite < 0.4


def test_les_deux_chocs_se_genent_au_lieu_de_s_additionner():
    """Une garantie poussée dans la monnaie par la baisse des actions devient moins sensible à la
    volatilité : l'exigence conjointe est donc plus petite que la somme des deux prises seules."""
    d = decomposer(Contrat())
    assert d.conjointe < d.somme_des_parts
    assert d.interaction < 0


def test_chaque_choc_pris_seul_augmente_le_passif():
    d = decomposer(Contrat())
    assert d.actions_seules > 0
    assert d.volatilite_seule > 0
    assert d.conjointe > max(d.actions_seules, d.volatilite_seule)


def test_la_part_de_la_volatilite_depasse_la_moitie_a_dix_ans():
    """C'est le résultat de tête du dépôt : sur le contrat type, le choc de volatilité pèse plus
    lourd que celui des actions."""
    d = decomposer(Contrat(annees=10.0))
    assert d.part_de_la_volatilite > 0.5
    assert d.volatilite_seule > d.actions_seules


def test_une_garantie_sans_valeur_exige_quand_meme_du_capital():
    """Un point de la méthode qui surprend et qui est bien voulu.

    Le passif reformulé est ce qu'on devra payer MOINS ce qu'on encaissera pour le porter. Faire
    baisser les actions de 35 % réduit l'assiette sur laquelle les frais se prélèvent, donc la
    valeur des frais futurs, donc augmente le passif. Une garantie qui ne vaut rien porte ainsi une
    exigence égale à la seule perte de frais.
    """
    from fdg.garantie import valeur_des_frais

    c = Contrat(garantie=1.0)
    d = decomposer(c)
    perte_de_frais = valeur_des_frais(c) - valeur_des_frais(
        contrat_choque(c, actions=True, volatilite=False))
    assert d.actions_seules > 1.0
    assert d.actions_seules == pytest.approx(perte_de_frais, rel=1e-9)
    # l'exigence conjointe est un cheveu plus grande : le choc de volatilité fait remonter la
    # garantie, qui ne valait rien, d'un montant infime mais positif
    assert d.conjointe > d.actions_seules


def test_l_exigence_augmente_avec_le_montant_garanti():
    c = Contrat()
    exigences = [decomposer(replace(c, garantie=g)).conjointe for g in (60.0, 100.0, 140.0)]
    assert exigences == sorted(exigences)
