"""La valeur de la garantie, éprouvée par ses limites connues et par la simulation."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from fdg.garantie import (
    Contrat,
    delta,
    passif_reformule,
    valeur_de_la_garantie,
    valeur_des_frais,
    valeur_par_simulation,
)


def test_la_forme_fermee_et_la_simulation_se_rejoignent():
    """Une formule fermée mal transcrite passe tous les tests d'unité et se trompe quand même.
    Deux chemins indépendants qui tombent sur le même nombre, c'est autre chose."""
    c = Contrat()
    ferme = valeur_de_la_garantie(c)
    simule = valeur_par_simulation(c, tirages=400_000)
    ecart = abs(ferme - simule["valeur"]) / simule["erreur_type"]
    assert ecart < 3.0


def test_une_garantie_nulle_ne_vaut_rien():
    assert valeur_de_la_garantie(Contrat(garantie=0.0)) == pytest.approx(0.0)


def test_une_garantie_vaut_plus_cher_quand_le_marche_s_agite():
    """C'est le fait qui justifie le choc de volatilité du chapitre 7 : l'assureur a vendu une
    option, et une option vaut plus cher quand l'incertitude monte."""
    c = Contrat()
    valeurs = [valeur_de_la_garantie(replace(c, volatilite=v)) for v in (0.10, 0.18, 0.30, 0.45)]
    assert valeurs == sorted(valeurs)


def test_une_garantie_vaut_plus_cher_quand_le_fonds_baisse():
    c = Contrat()
    valeurs = [valeur_de_la_garantie(replace(c, fonds=f)) for f in (140.0, 100.0, 70.0)]
    assert valeurs == sorted(valeurs)


def test_a_volatilite_nulle_la_garantie_vaut_sa_valeur_intrinseque_actualisee():
    """Sans incertitude, le fonds croît au taux de swap diminué des frais, et le paiement est
    connu d'avance."""
    c = Contrat(volatilite=1e-9, deces=0.0, decheance=0.0)
    attendu = max(c.garantie - c.fonds * math.exp((c.taux - c.frais) * c.annees), 0.0)
    attendu *= math.exp(-c.taux * c.annees)
    assert valeur_de_la_garantie(c) == pytest.approx(attendu, abs=1e-6)


def test_la_survie_diminue_la_garantie_proportionnellement():
    """Un contrat racheté ne réclame plus rien : doubler la force de sortie réduit la garantie
    exactement comme la survie qu'elle implique."""
    c = Contrat(deces=0.0, decheance=0.0)
    d = replace(c, decheance=0.05)
    rapport = valeur_de_la_garantie(d) / valeur_de_la_garantie(c)
    assert rapport == pytest.approx(math.exp(-0.05 * c.annees))


def test_les_frais_valent_zero_sans_part_affectee_a_la_garantie():
    assert valeur_des_frais(Contrat(part_frais_garantie=0.0)) == pytest.approx(0.0)


def test_le_passif_reformule_peut_etre_negatif():
    """Une garantie très en dehors de la monnaie rapporte plus de frais qu'elle ne coûte, et le
    dépôt ne l'écrête pas : un passif négatif est un actif, pas une erreur."""
    c = Contrat(garantie=40.0)
    assert passif_reformule(c) < 0


def test_le_delta_du_passif_est_negatif():
    """Le passif baisse quand le fonds monte : c'est ce qui fait qu'on se couvre en VENDANT des
    actions, et non en en achetant."""
    assert delta(Contrat()) < 0


def test_le_delta_tend_vers_moins_un_quand_la_garantie_est_certaine():
    """Une garantie très dans la monnaie sera payée à coup sûr : chaque dollar perdu par le fonds
    est un dollar de plus à verser, à la survie et à l'actualisation près."""
    c = Contrat(garantie=400.0, volatilite=0.05, annees=1.0, deces=0.0, decheance=0.0)
    assert delta(c) == pytest.approx(-math.exp(-c.frais * c.annees), abs=0.02)
