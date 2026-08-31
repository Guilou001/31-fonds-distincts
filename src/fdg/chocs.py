"""Le choc de volatilité du chapitre 7, et la structure qu'il cache.

**Ce que le régulateur demande.** Pour mesurer le capital de risque de marché d'une garantie de
fonds distincts, il ne suffit pas de faire baisser les actions. Il faut aussi faire monter la
volatilité implicite, parce qu'une garantie est une option vendue : sa valeur monte quand le marché
s'agite, même si le niveau ne bouge pas. La ligne directrice publie une grille de chocs et demande
de l'**interpoler linéairement** entre ses points.

**L'interpolation, en mots simples.** La grille donne un choc pour une volatilité de départ entière
et pour treize échéances. Un assureur dont la volatilité vaut 18,7 % à 115 mois ne tombe sur aucune
case. Il faut donc interpoler deux fois : d'abord entre les lignes 18 et 19, puis entre les colonnes
84 et 120 mois. C'est une interpolation bilinéaire, et la ligne directrice la déroule sur neuf
exemples travaillés que ce module reproduit tous.

**Ce que la grille cache.** À un mois, le choc amène la volatilité à **41 %** quelle que soit la
volatilité de départ : un assureur à 5 % reçoit +36, un assureur à 54 % reçoit −13, et les deux
finissent au même endroit. À 360 et 1200 mois, la cible est **25 %**, également pour tous. Entre les
deux, la cible dépend de la volatilité de départ. Autrement dit, aux deux bouts de la courbe le
régulateur impose un niveau, et au milieu il impose un déplacement. La ligne directrice ne l'écrit
nulle part, et `etudes.py` le mesure colonne par colonne.
"""

from __future__ import annotations

from . import appendices

CIBLE_COURT_TERME = 41.0
CIBLE_LONG_TERME = 25.0


def _encadrer(valeurs: list[float], x: float) -> tuple[int, int, float]:
    """Les deux indices qui encadrent x et le poids du second.

    En dehors de la grille, on ne prolonge pas : on retient la valeur du bord. Extrapoler un choc de
    volatilité au-delà de 75 % de volatilité de départ ou de 1200 mois inventerait un chiffre que le
    régulateur n'a pas publié.
    """
    if x <= valeurs[0]:
        return 0, 0, 0.0
    if x >= valeurs[-1]:
        n = len(valeurs) - 1
        return n, n, 0.0
    haut = next(i for i, v in enumerate(valeurs) if v >= x)
    bas = haut - 1
    poids = (x - valeurs[bas]) / (valeurs[haut] - valeurs[bas])
    return bas, haut, poids


def choc(volatilite: float, mois: float, base: str = "terme") -> float:
    """Le choc en points de volatilité, interpolé linéairement dans les deux dimensions.

    `volatilite` est la volatilité implicite annualisée courante, en points de pourcentage, et non
    en fraction : 18,7 et non 0,187. C'est l'unité de la grille du régulateur, et la respecter évite
    une conversion silencieuse.
    """
    grille = appendices.table_des_chocs(base)
    vols, mm = appendices.volatilites(), appendices.mois()
    iv, jv, pv = _encadrer([float(v) for v in vols], volatilite)
    im, jm, pm = _encadrer([float(m) for m in mm], mois)
    bas = (1 - pv) * grille[iv][im] + pv * grille[jv][im]
    haut = (1 - pv) * grille[iv][jm] + pv * grille[jv][jm]
    return (1 - pm) * bas + pm * haut


def volatilite_choquee(volatilite: float, mois: float, base: str = "terme") -> float:
    """La volatilité une fois le choc appliqué, c'est-à-dire ce qui entre dans la réévaluation."""
    return volatilite + choc(volatilite, mois, base)


def cible_par_echeance(base: str = "terme") -> list[dict]:
    """Ce que devient une volatilité de départ, échéance par échéance, sur toute la grille.

    Rend pour chaque colonne la volatilité choquée la plus basse et la plus haute obtenues en
    parcourant les 75 niveaux de départ. Quand les deux coïncident, la colonne impose un niveau ;
    quand elles s'écartent, elle impose un déplacement.
    """
    grille = appendices.table_des_chocs(base)
    vols, mm = appendices.volatilites(), appendices.mois()
    sortie = []
    for j, m in enumerate(mm):
        cibles = [vols[i] + grille[i][j] for i in range(len(vols))]
        sortie.append({"mois": m, "cible_minimale": min(cibles), "cible_maximale": max(cibles),
                       "etendue": max(cibles) - min(cibles),
                       # la pente de la cible contre la volatilité de départ : zéro quand le
                       # régulateur impose un niveau, un quand il laisse l'assureur où il est
                       "pente": (cibles[-1] - cibles[0]) / (vols[-1] - vols[0])})
    return sortie


def volatilite_pivot(base: str = "terme") -> list[dict]:
    """La volatilité de départ à laquelle le choc change de signe, échéance par échéance.

    En dessous de ce niveau le régulateur fait monter la volatilité, au-dessus il la fait baisser.
    C'est la conséquence directe de la structure : le choc pousse tout le monde vers une bande
    commune, si bien qu'un assureur déjà agité voit sa volatilité **réduite** par le scénario de
    tension. Le pivot se lit comme le niveau de volatilité que le régulateur juge normal à cette
    échéance.
    """
    grille = appendices.table_des_chocs(base)
    vols, mm = appendices.volatilites(), appendices.mois()
    sortie = []
    for j, m in enumerate(mm):
        colonne = [grille[i][j] for i in range(len(vols))]
        pivot = None
        for i in range(len(vols) - 1):
            if colonne[i] > 0 >= colonne[i + 1]:
                # interpolation linéaire du zéro entre deux lignes entières
                poids = colonne[i] / (colonne[i] - colonne[i + 1])
                pivot = vols[i] + poids
                break
        sortie.append({"mois": m, "pivot": pivot,
                       "choc_au_plus_bas": colonne[0], "choc_au_plus_haut": colonne[-1]})
    return sortie
