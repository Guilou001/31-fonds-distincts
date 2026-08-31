"""Les trois appendices du chapitre 7 du TSAV, recopiés de la page du BSIF.

**Ce qu'ils contiennent.** L'appendice 7-A donne, pour chaque niveau de volatilité implicite et pour
treize échéances, le nombre de points de volatilité qu'il faut ajouter pour obtenir le scénario de
choc. L'appendice 7-B fait la même chose sur une base au comptant plutôt qu'à terme. L'appendice 7-C
donne vingt trajectoires de prix d'actions sur un an, à pas hebdomadaire et à pas mensuel, qui
servent à mesurer la qualité d'une couverture dynamique.

**Pourquoi ils sont figés dans un fichier plutôt que téléchargés.** La page du BSIF les publie en
HTML, dans des tableaux dont la mise en forme change d'une version à l'autre de la ligne directrice.
Un chargeur qui les extrairait à chaque exécution casserait au premier changement de gabarit, et
sans le dire. Le fichier `tables/appendices_licat_7.json` porte donc les 3 270 nombres relevés le
30 août 2026, avec la référence de leur source, et le dépôt les traite comme une donnée de
référence. Ce qui change avec la ligne directrice se change à la main, une fois, en connaissance de
cause.

**Comment on sait qu'ils sont bien lus.** Deux vérifications, dans `tests/test_appendices.py`. Les
vingt cellules que la ligne directrice cite nommément dans ses exemples se retrouvent dans la table
recopiée. Et les tables mensuelle et hebdomadaire de l'appendice 7-C finissent au même point. Les
neuf exemples travaillés eux-mêmes sont vérifiés ailleurs, dans `tests/test_chocs.py`.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

FICHIER = Path(__file__).parent / "tables" / "appendices_licat_7.json"


@cache
def charger() -> dict:
    """Les trois appendices, lus une fois et gardés en mémoire."""
    return json.loads(FICHIER.read_text(encoding="utf-8"))


def volatilites() -> list[int]:
    """Les niveaux de volatilité de la colonne de gauche, en points de pourcentage, de 1 à 75."""
    return charger()["volatilites"]


def mois() -> list[int]:
    """Les échéances de l'en-tête, en mois : 1, 6, 12, 24, 36, 48, 60, 84, 120, 144, 180, 360,
    1200. Elles ne sont pas régulièrement espacées, ce qui compte pour l'interpolation."""
    return charger()["mois"]


def table_des_chocs(base: str = "terme") -> list[list[float]]:
    """La grille de chocs, 75 lignes de volatilité par 13 colonnes d'échéance.

    La base « terme » est celle de l'appendice 7-A, qui s'applique aux volatilités à terme employées
    pour évaluer les passifs reformulés. La base « comptant » est celle de l'appendice 7-B.
    """
    cle = {"terme": "chocs_a_terme", "comptant": "chocs_au_comptant"}[base]
    return charger()[cle]


def scenarios(pas: str = "hebdomadaire") -> list[list[float]]:
    """Les vingt trajectoires de prix d'actions de l'appendice 7-C.

    Chaque trajectoire part de 100 et court sur un an. Le pas hebdomadaire donne 53 points, du
    dimanche zéro à la semaine 52 ; le pas mensuel en donne 13. Les deux échantillonnages sont les
    mêmes trajectoires, ce que prouve leur dernier point commun.
    """
    cle = {"hebdomadaire": "scenarios_hebdomadaires", "mensuel": "scenarios_mensuels"}[pas]
    return charger()[cle]


def source() -> str:
    return charger()["source"]
