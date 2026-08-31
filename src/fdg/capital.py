"""L'exigence de capital de risque de marché, et ce que chaque choc y apporte.

**Ce que la ligne directrice demande.** L'exigence est la hausse du passif reformulé quand on fait
baisser les actions et monter la volatilité **en même temps**. Les deux chocs ne sont pas deux
exigences qu'on additionne : c'est une seule réévaluation sous deux chocs simultanés.

**Pourquoi la distinction compte.** Une garantie est une option de vente. Faire baisser le
sous-jacent la rapproche de la monnaie, ce qui augmente sa valeur. Faire monter la volatilité
l'augmente aussi. Mais une option très dans la monnaie perd sa sensibilité à la volatilité : une
fois qu'elle est certaine d'être exercée, l'agitation ne change plus grand-chose. Les deux chocs se
gênent donc, et leur effet conjoint est plus petit que la somme des deux. Ce module mesure de
combien.

**Le facteur d'actions.** Le chapitre 7 renvoie aux sections 5.2 et 5.4 du même document, qui posent
35 % pour une action cotée d'un marché développé. C'est ce facteur qui sert par défaut ici, et il
est déclaré en paramètre pour qu'on puisse en essayer un autre.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import chocs
from .garantie import Contrat, passif_reformule

# Section 5.2.1 du TSAV 2025 : 35 % pour les actions cotées des marchés développés.
FACTEUR_ACTIONS = 0.35


def contrat_choque(c: Contrat, actions: bool, volatilite: bool,
                   facteur: float = FACTEUR_ACTIONS, base: str = "terme") -> Contrat:
    """Le contrat une fois les chocs demandés appliqués.

    Le choc d'actions ne touche que le fonds, pas la garantie : c'est le principe même du produit,
    la promesse ne bouge pas quand le marché baisse. Le choc de volatilité se lit dans la grille du
    régulateur, qui travaille en points de pourcentage alors que le contrat travaille en fraction :
    la conversion se fait ici, une fois.
    """
    fonds = c.fonds * (1 - facteur) if actions else c.fonds
    vol = c.volatilite
    if volatilite:
        vol = chocs.volatilite_choquee(100 * c.volatilite, 12 * c.annees, base) / 100
    return replace(c, fonds=fonds, volatilite=vol)


@dataclass(frozen=True)
class Decomposition:
    """L'exigence conjointe, et ce que chaque choc y apporte pris seul."""

    passif: float
    actions_seules: float
    volatilite_seule: float
    conjointe: float

    @property
    def somme_des_parts(self) -> float:
        return self.actions_seules + self.volatilite_seule

    @property
    def interaction(self) -> float:
        """Ce que l'exigence conjointe retire à la somme des deux chocs pris séparément.

        Négatif quand les deux chocs se gênent, ce qui est le cas usuel : une garantie poussée dans
        la monnaie par la baisse des actions devient moins sensible à la volatilité.
        """
        return self.conjointe - self.somme_des_parts

    @property
    def part_de_la_volatilite(self) -> float:
        """La part de l'exigence conjointe que le choc de volatilité explique à lui seul."""
        if self.conjointe == 0:
            return float("nan")
        return self.volatilite_seule / self.conjointe


def decomposer(c: Contrat, facteur: float = FACTEUR_ACTIONS,
               base: str = "terme") -> Decomposition:
    """L'exigence sous chaque choc et sous les deux, à partir du même passif de départ."""
    depart = passif_reformule(c)

    def exigence(actions: bool, vol: bool) -> float:
        return passif_reformule(contrat_choque(c, actions, vol, facteur, base)) - depart

    return Decomposition(passif=depart, actions_seules=exigence(True, False),
                         volatilite_seule=exigence(False, True),
                         conjointe=exigence(True, True))


def exigence(c: Contrat, facteur: float = FACTEUR_ACTIONS, base: str = "terme") -> float:
    """L'exigence de risque de marché telle que la ligne directrice la définit : les deux chocs
    ensemble, et jamais leur somme."""
    return decomposer(c, facteur, base).conjointe
