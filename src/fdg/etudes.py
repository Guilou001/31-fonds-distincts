"""Les quatre études du dépôt, chacune rendant le tableau qu'elle produit."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from . import appendices, capital, chocs, couverture, reference
from .garantie import Contrat, passif_reformule, valeur_par_simulation


def exemples_du_regulateur() -> pd.DataFrame:
    """Les neuf exemples travaillés, refaits par l'interpolation du dépôt."""
    lignes = []
    for e in reference.EXEMPLES:
        calcule = chocs.choc(e.volatilite, e.mois)
        total = e.volatilite + round(calcule, 1)
        lignes.append({
            "volatilite": e.volatilite, "mois": e.mois,
            "choc_publie": e.choc_publie, "choc_recalcule": calcule,
            "choc_coincide": abs(round(calcule, 1) - e.choc_publie) < 1e-9,
            "total_publie": e.volatilite_choquee_publiee, "total_recalcule": total,
            "total_coincide": abs(total - e.volatilite_choquee_publiee) < 1e-9,
        })
    return pd.DataFrame(lignes)


def cellules_citees() -> pd.DataFrame:
    """Les vingt cellules de la grille que les exemples nomment, contre la table recopiée."""
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    lignes = []
    for (v, m), citee in sorted(reference.CELLULES_CITEES.items()):
        lue = grille[vols.index(v)][mois.index(m)]
        lignes.append({"volatilite": v, "mois": m, "valeur_citee": citee, "valeur_lue": lue,
                       "coincide": abs(lue - citee) < 1e-9})
    return pd.DataFrame(lignes)


def structure_de_la_grille() -> pd.DataFrame:
    """Ce que la grille impose, colonne par colonne : un niveau ou un déplacement.

    Pour chaque échéance, on applique le choc à chacun des soixante-quinze niveaux de volatilité de
    départ et on regarde où ils arrivent. Une étendue nulle signifie que le régulateur impose un
    niveau, le même pour tous. Une corde de un signifierait qu'il laisse chacun où il est.
    """
    lignes = []
    for base in ("terme", "comptant"):
        for c in chocs.cible_par_echeance(base):
            lignes.append({"base": base, **c})
    return pd.DataFrame(lignes)


def pivots() -> pd.DataFrame:
    """Le niveau de volatilité au-delà duquel le choc du régulateur devient une baisse."""
    lignes = []
    for base in ("terme", "comptant"):
        for p in chocs.volatilite_pivot(base):
            lignes.append({"base": base, **p})
    return pd.DataFrame(lignes)


def decomposition_par_contrat(contrats: dict[str, Contrat],
                              bases: tuple[str, ...] = ("terme", "comptant")) -> pd.DataFrame:
    """L'exigence de risque de marché et ce que chaque choc y apporte, contrat par contrat.

    Le calcul est refait sous les deux grilles publiées, l'appendice 7-A à terme et l'appendice 7-B
    au comptant. Le choix n'est pas neutre : il décide lequel des deux chocs pèse le plus lourd. Et
    la ligne directrice ne dit pas lequel employer pour un passif évalué à volatilité plate.
    """
    lignes = []
    for base in bases:
        for nom, c in contrats.items():
            d = capital.decomposer(c, base=base)
            lignes.append({
                "base": base,
                "contrat": nom, "fonds": c.fonds, "garantie": c.garantie, "annees": c.annees,
                "volatilite": c.volatilite,
                "volatilite_choquee": chocs.volatilite_choquee(
                    100 * c.volatilite, 12 * c.annees, base) / 100,
                "passif_reformule": d.passif, "actions_seules": d.actions_seules,
                "volatilite_seule": d.volatilite_seule, "conjointe": d.conjointe,
                "somme_des_parts": d.somme_des_parts, "interaction": d.interaction,
                "part_de_la_volatilite": d.part_de_la_volatilite,
            })
    return pd.DataFrame(lignes)


def part_par_echeance(depart: Contrat | None = None) -> pd.DataFrame:
    """La part de l'exigence que le choc de volatilité explique, échéance par échéance.

    C'est le tableau que la figure du même nom dessine : trois rapports de garantie au fonds, sur
    quarante-neuf échéances d'un an à vingt-cinq ans, par demi-année.
    """
    depart = depart or Contrat()
    lignes = []
    for rapport in (0.75, 1.00, 1.25):
        for k in range(49):
            annees = 1.0 + 0.5 * k
            d = capital.decomposer(replace(depart, garantie=depart.fonds * rapport, annees=annees))
            lignes.append({"rapport_garantie_fonds": rapport, "annees": annees,
                           "actions_seules": d.actions_seules,
                           "volatilite_seule": d.volatilite_seule, "conjointe": d.conjointe,
                           "part_de_la_volatilite": d.part_de_la_volatilite})
    return pd.DataFrame(lignes)


def contrats_types(base: Contrat | None = None) -> dict[str, Contrat]:
    """Une famille de contrats qui balaie la monnaie et l'échéance.

    La monnaie est le rapport de la garantie au fonds. Une garantie « dans la monnaie » vaut plus
    que le fonds, donc l'assureur devra probablement payer ; une garantie « en dehors » vaut moins,
    et l'assureur ne paiera probablement rien.
    """
    base = base or Contrat()
    familles = {}
    for etiquette, rapport in (("garantie à 75 %", 0.75), ("garantie à 100 %", 1.00),
                               ("garantie à 125 %", 1.25)):
        for annees in (3.0, 10.0, 20.0):
            nom = f"{etiquette}, {annees:.0f} ans"
            familles[nom] = replace(base, garantie=base.fonds * rapport, annees=annees)
    return familles


def credit_par_frequence(c: Contrat) -> pd.DataFrame:
    """Le crédit de couverture selon le pas de rééquilibrage et la bande de non-intervention."""
    lignes = []
    for pas in ("hebdomadaire", "mensuel"):
        for tolerance in (0.0, 0.01, 0.05):
            r = couverture.credit_de_couverture(c, pas, tolerance)
            lignes.append({"pas": pas, "tolerance": tolerance, **{
                k: v for k, v in r.items() if k not in ("pas", "tolerance")}})
    return pd.DataFrame(lignes)


def scenarios_de_couverture(c: Contrat, pas: str = "hebdomadaire") -> pd.DataFrame:
    """L'erreur de suivi de chacun des vingt scénarios, et où le scénario finit."""
    table = appendices.scenarios(pas)
    resultat = couverture.exigence_avec_couverture(c, pas)
    lignes = []
    for j, valeur in enumerate(resultat["valeurs"]):
        lignes.append({"scenario": j + 1, "valeur_actuelle": valeur,
                       "prix_final": table[-1][j],
                       "prix_minimal": min(ligne[j] for ligne in table)})
    return pd.DataFrame(lignes)


def controle_de_la_formule(c: Contrat, tirages: int = 400_000) -> dict:
    """La formule fermée du passif, contrôlée par simulation.

    Une formule fermée mal transcrite passe tous les tests d'unité et se trompe quand même. Deux
    chemins indépendants qui tombent sur le même nombre, c'est autre chose.
    """
    from .garantie import valeur_de_la_garantie

    ferme = valeur_de_la_garantie(c)
    simule = valeur_par_simulation(c, tirages)
    ecart = ferme - simule["valeur"]
    return {"forme_fermee": ferme, "simulation": simule["valeur"],
            "erreur_type": simule["erreur_type"], "ecart": ecart,
            "ecarts_types": abs(ecart) / simule["erreur_type"] if simule["erreur_type"] else 0.0,
            "passif_reformule": passif_reformule(c)}
