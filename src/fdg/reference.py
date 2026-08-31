"""Les exemples travaillés de la ligne directrice, recopiés tels qu'imprimés.

Le chapitre 7 déroule neuf calculs de choc de volatilité, trois volatilités de départ par trois
échéances, avec l'arithmétique écrite en toutes lettres. Ce sont les vérités connues du dépôt, et
elles viennent du régulateur lui-même plutôt que d'un article.

Relevé le 30 août 2026 sur la version 2025 du Test de suffisance du capital des sociétés
d'assurance-vie, chapitre 7, section 7.2.2, sous le titre « Examples: Calculation of Equity Implied
Volatility Shocks ».
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExempleDeChoc:
    """Une ligne du tableau d'exemples : la volatilité de départ, l'échéance, le choc et le total."""

    volatilite: float
    mois: int
    choc_publie: float
    volatilite_choquee_publiee: float


# Les neuf lignes, dans l'ordre où la ligne directrice les imprime.
EXEMPLES = [
    ExempleDeChoc(5.0, 1, 36.0, 41.0),
    ExempleDeChoc(5.0, 115, 29.1, 34.1),
    ExempleDeChoc(5.0, 550, 20.0, 25.0),
    ExempleDeChoc(18.7, 1, 22.3, 41.0),
    ExempleDeChoc(18.7, 115, 16.2, 34.9),
    ExempleDeChoc(18.7, 550, 6.3, 25.0),
    ExempleDeChoc(54.0, 1, -13.0, 41.0),
    ExempleDeChoc(54.0, 115, -3.6, 51.4),
    ExempleDeChoc(54.0, 550, -29.0, 25.0),
]

# Les cellules de la grille que les exemples citent nommément, avec la valeur citée. Les retrouver
# prouve que la table a été lue dans le bon sens, ce qui est la première chose à établir quand on
# recopie une grille de soixante-quinze lignes sur treize colonnes.
CELLULES_CITEES = {
    (5, 1): 36.0, (5, 84): 18.2, (5, 120): 30.9, (5, 360): 20.0, (5, 1200): 20.0,
    (18, 1): 23.0, (18, 84): 9.3, (18, 120): 18.1, (18, 360): 7.0, (18, 1200): 7.0,
    (19, 1): 22.0, (19, 84): 9.0, (19, 120): 17.1, (19, 360): 6.0, (19, 1200): 6.0,
    (54, 1): -13.0, (54, 84): -4.7, (54, 120): -3.4, (54, 360): -29.0, (54, 1200): -29.0,
}

NOTE_SUR_LA_HUITIEME_LIGNE = """\
Huit des neuf lignes se referment. La huitième non.

La ligne directrice écrit, pour une volatilité de départ de 54,0 % à 115 mois, un choc de −3,6 puis
une volatilité choquée de 51,4. Or 54,0 moins 3,6 fait 50,4. Le choc lui-même est juste : la grille
donne −4,7 à 84 mois et −3,4 à 120 mois, et l'interpolation que la ligne directrice écrit
elle-même, (5 × −4,7 + 31 × −3,4) ÷ 36, vaut −3,58, arrondi à −3,6. C'est l'addition de la dernière
colonne qui est fausse, d'un point exactement.

Les huit autres additions tombent juste, y compris les deux qui encadrent celle-ci dans le même
tableau : 54,0 moins 13,0 fait bien 41,0, et 54,0 moins 29,0 fait bien 25,0.
"""
