"""Le crédit de capital qu'une couverture dynamique fait gagner, sur les scénarios du régulateur.

**L'idée, en mots simples.** Un assureur qui a vendu des garanties peut se couvrir : il vend des
actions à découvert dans la proportion exacte où son passif monte quand le marché baisse. Si la
couverture était parfaite, son exigence de capital tomberait à zéro. Elle ne l'est jamais, parce que
la proportion à vendre change à chaque mouvement et qu'on ne rééquilibre qu'à intervalles.

**Ce que le régulateur mesure.** Il ne croit pas l'assureur sur parole : il lui impose vingt
trajectoires de prix d'actions, publiées dans l'appendice 7-C, et lui demande de rejouer sa
couverture dessus semaine après semaine. À chaque pas, on compare la variation du passif à la
variation de la couverture ; ce qui reste est l'erreur de suivi. L'exigence avec couverture est la
**moyenne des valeurs actuelles positives** sur les vingt scénarios, ce qui revient à ignorer les
scénarios où la couverture a rapporté.

**Ce que le régulateur fige pendant la projection.** La volatilité implicite reste celle du départ,
et seul le prix des actions bouge. C'est écrit noir sur blanc, et cela veut dire que ce test mesure
le risque de rééquilibrage, pas le risque de volatilité, lequel est déjà chargé ailleurs.
"""

from __future__ import annotations

import math
from dataclasses import replace

from . import appendices
from .garantie import Contrat, delta, passif_reformule


def rejouer_un_scenario(c: Contrat, prix: list[float], taux: float,
                        tolerance: float = 0.0) -> dict:
    """La couverture rejouée pas à pas sur une trajectoire, et l'erreur de suivi qu'elle laisse.

    `tolerance` est la bande de non-intervention, mesurée en points de sensibilité et non en
    proportion : on ne rééquilibre que si la sensibilité a bougé de plus que cet écart absolu. Une
    tolérance de 0,05 laisse donc la sensibilité s'écarter de cinq points de part et d'autre de
    celle qui est détenue, soit une fenêtre de dix points. À zéro, on rééquilibre à chaque pas, ce
    qui est le cas le plus favorable à l'assureur et donc le plancher de l'exigence.
    """
    pas = len(prix) - 1
    duree = 1.0 / pas                       # les scénarios couvrent un an
    contrat = c
    passif = passif_reformule(contrat)
    sensibilite = delta(contrat)
    # la couverture part de zéro : on vend le nombre d'actions qui annule la sensibilité du passif
    quantite = sensibilite
    actif = 0.0
    ecarts = []
    for k in range(1, pas + 1):
        rendement = prix[k] / prix[k - 1]
        contrat = replace(contrat, fonds=contrat.fonds * rendement,
                          annees=max(c.annees - k * duree, 1e-9))
        nouveau_passif = passif_reformule(contrat)
        # l'actif de couverture suit le prix des actions, dans la quantité détenue
        nouvel_actif = actif + quantite * (prix[k] - prix[k - 1]) / prix[0] * c.fonds
        variation_passif = nouveau_passif - passif
        variation_actif = nouvel_actif - actif
        ecart = variation_passif - variation_actif
        ecarts.append(ecart * math.exp(-taux * k * duree))
        nouvelle_sensibilite = delta(contrat)
        if abs(nouvelle_sensibilite - quantite) > tolerance:
            quantite = nouvelle_sensibilite
        passif, actif = nouveau_passif, nouvel_actif
    return {"valeur_actuelle": float(sum(ecarts)), "pas": pas,
            "ecart_maximal": float(max(ecarts, key=abs)) if ecarts else 0.0}


def moyenne_des_valeurs_positives(valeurs: list[float]) -> float:
    """La règle d'agrégation du régulateur : les scénarios gagnants comptent pour zéro.

    C'est ce qui distingue l'exigence d'une moyenne ordinaire. Un scénario où la couverture a
    rapporté ne réduit pas le capital, et il ne le réduit pas non plus « un peu ». Il est écrasé à
    zéro avant la moyenne, et le diviseur reste le nombre total de scénarios.
    """
    return sum(max(v, 0.0) for v in valeurs) / len(valeurs)


def derive_du_chemin_plat(c: Contrat, pas: str = "hebdomadaire",
                          tolerance: float = 0.0) -> float:
    """Ce que la mesure compte quand le prix d'actions ne bouge pas d'un cent.

    Sur une trajectoire strictement plate, une couverture en delta n'a rigoureusement rien à
    rattraper : l'actif de couverture ne bouge pas. Ce qui reste est le passage du temps sur le
    passif reformulé. Deux morceaux le composent, la décroissance temporelle de la garantie et les
    frais de garantie qui sortent du passif parce que l'assureur les a encaissés dans l'année.

    Cet encaissement, `rejouer_un_scenario` ne le crédite nulle part au compte de couverture. La
    dérive est donc un plancher déterministe de l'erreur de suivi, présent dans les vingt
    scénarios. Le § 5.4 du README la publie à côté de l'exigence, pour que le lecteur sache ce que
    le nombre contient.
    """
    depart = appendices.scenarios(pas)[0][0]
    n = len(appendices.scenarios(pas))
    return rejouer_un_scenario(c, [depart] * n, c.taux, tolerance)["valeur_actuelle"]


def exigence_avec_couverture(c: Contrat, pas: str = "hebdomadaire",
                             tolerance: float = 0.0) -> dict:
    """L'exigence de risque d'actions d'un assureur qui se couvre, sur les vingt scénarios publiés.

    La règle du régulateur retient la moyenne des valeurs actuelles **positives**. Les scénarios où
    la couverture a rapporté comptent donc pour zéro et non pour un gain : le capital ne se réduit
    pas parce qu'on a eu de la chance ailleurs.
    """
    table = appendices.scenarios(pas)
    n = len(table[0])
    resultats = []
    for j in range(n):
        prix = [ligne[j] for ligne in table]
        resultats.append(rejouer_un_scenario(c, prix, c.taux, tolerance))
    valeurs = [r["valeur_actuelle"] for r in resultats]
    return {"scenarios": n, "pas": pas,
            "exigence": float(moyenne_des_valeurs_positives(valeurs)),
            "valeurs": valeurs,
            "scenarios_perdants": int(sum(1 for v in valeurs if v > 0)),
            "pire_scenario": float(max(valeurs)), "meilleur_scenario": float(min(valeurs))}


def credit_de_couverture(c: Contrat, pas: str = "hebdomadaire",
                         tolerance: float = 0.0) -> dict:
    """De combien la couverture réduit l'exigence de risque d'actions.

    La ligne directrice compare l'exigence obtenue en rejouant la couverture sur les vingt scénarios
    au seul volet « baisse de prix » de la section 7.2.2, c'est-à-dire à l'exigence d'un assureur
    qui ne se couvre pas. Le dénominateur est donc le choc d'actions pris seul, et non l'exigence
    conjointe du § 5.3 : une part de 84,8 % se lit « de l'exigence de risque d'actions ». La
    réduction est la différence, et elle ne peut pas être négative : une couverture qui ferait pire
    que rien ne donne aucun crédit, elle n'ajoute pas de capital.
    """
    from .capital import decomposer

    sans = decomposer(c).actions_seules
    avec = exigence_avec_couverture(c, pas, tolerance)
    reduction = max(sans - avec["exigence"], 0.0)
    return {"exigence_sans_couverture": sans, "exigence_avec_couverture": avec["exigence"],
            "credit": reduction,
            "part_reduite": reduction / sans if sans > 0 else float("nan"),
            "derive_du_chemin_plat": derive_du_chemin_plat(c, pas, tolerance),
            "scenarios_perdants": avec["scenarios_perdants"],
            "pire_scenario": avec["pire_scenario"], "pas": pas, "tolerance": tolerance}


# L'exemple travaillé de la section 7.3.2.3, recopié de la ligne directrice. Les colonnes sont la
# valeur du passif couvert, sa sensibilité, la valeur de l'actif de couverture et sa sensibilité.
EXEMPLE_DU_REGULATEUR = {
    "ouverture": {"passif": 1000.0, "sensibilite_passif": 100.0,
                  "actif": 0.0, "sensibilite_actif": 100.0},
    "apres_mouvement": {"passif": 1200.0, "actif": 180.0},
    "apres_reequilibrage": {"passif": 1200.0, "sensibilite_passif": 110.0,
                            "actif": 180.0, "sensibilite_actif": 110.0},
    "flux": {"passif": 5.0, "actif": -2.0},
    "variation_passif_publiee": 205.0,
    "variation_actif_publiee": 178.0,
    "perte_publiee": 27.0,
}


def refaire_l_exemple() -> dict:
    """L'exemple travaillé du régulateur, refait ligne par ligne.

    La variation d'une période est la position après rééquilibrage, moins la position d'ouverture,
    plus le flux encaissé ou payé. La perte de couverture est la différence entre les deux
    variations, et elle est ensuite actualisée d'un pas au taux de swap.
    """
    e = EXEMPLE_DU_REGULATEUR
    variation_passif = (e["apres_reequilibrage"]["passif"] - e["ouverture"]["passif"]
                        + e["flux"]["passif"])
    variation_actif = (e["apres_reequilibrage"]["actif"] - e["ouverture"]["actif"]
                       + e["flux"]["actif"])
    return {"variation_passif": variation_passif, "variation_actif": variation_actif,
            "perte": variation_passif - variation_actif,
            "coincide": (variation_passif == e["variation_passif_publiee"]
                         and variation_actif == e["variation_actif_publiee"]
                         and variation_passif - variation_actif == e["perte_publiee"])}
