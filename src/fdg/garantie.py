"""Ce que vaut une garantie de fonds distincts, et pourquoi c'est une option vendue.

**Le produit, en mots simples.** Un fonds distinct est un fonds commun de placement vendu par un
assureur, avec une promesse en plus. Quelle que soit la valeur du fonds à l'échéance, le détenteur
récupère au moins un montant garanti, souvent 75 ou 100 % de ce qu'il a versé. L'assureur prélève
des frais annuels sur le fonds et, en échange, comble la différence si le fonds a baissé.

**Ce que l'assureur a vendu.** Exactement une option de vente. Si le fonds finit au-dessus de la
garantie, l'assureur ne paie rien ; s'il finit en dessous, il paie la différence. Le passif de
l'assureur vaut donc la valeur d'un put, dont le sous-jacent est le fonds et le prix d'exercice la
garantie. C'est la raison pour laquelle une hausse de volatilité coûte cher à l'assureur alors même
que le niveau du marché n'a pas bougé, et c'est ce que le choc de volatilité du chapitre 7 vise.

**Ce que la ligne directrice demande.** Les passifs reformulés se calculent en actualisant au taux
de swap et en supposant que tous les actifs rapportent ce même taux. Autrement dit : une évaluation
neutre au risque. Ce module la fait de deux façons, par la formule fermée de Black et Scholes et par
simulation, et le test exige qu'elles se rejoignent.

**Ce que ce module ne fait pas.** Il ne modélise ni les garanties à cliquet, ni les retraits
garantis à vie, ni la réassurance. Un vrai passif d'assureur en contient, et le dépôt le déclare
plutôt que de faire semblant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class Contrat:
    """Une garantie à l'échéance sur un fonds distinct.

    Les taux et volatilités sont en fraction, pas en pourcentage : 0,187 et non 18,7. La grille du
    régulateur, elle, travaille en points, et `capital.py` fait la conversion à un seul endroit.
    """

    fonds: float = 100.0            # la valeur du fonds aujourd'hui
    garantie: float = 100.0         # le montant promis à l'échéance
    annees: float = 10.0            # ce qui reste à courir
    taux: float = 0.035             # le taux de swap, qui sert d'actualisation et de rendement
    volatilite: float = 0.18        # la volatilité implicite du fonds
    frais: float = 0.025            # les frais annuels prélevés sur le fonds
    part_frais_garantie: float = 0.006   # la part des frais qui rémunère la garantie
    deces: float = 0.005            # le taux de décès annuel, constant
    decheance: float = 0.06         # le taux de rachat annuel, constant

    @property
    def sortie_annuelle(self) -> float:
        """Le taux auquel les contrats quittent le portefeuille, décès et rachats confondus.

        Les deux sont traités comme des forces constantes qui s'additionnent, ce qui suppose
        qu'aucun rachat ne dépend du niveau du marché. C'est faux dans la vraie vie, où l'on rachète
        moins quand la garantie vaut cher, et le dépôt le déclare en limite.
        """
        return self.deces + self.decheance

    @property
    def survie(self) -> float:
        """La part des contrats encore en vigueur à l'échéance."""
        return math.exp(-self.sortie_annuelle * self.annees)


def valeur_de_la_garantie(c: Contrat) -> float:
    """La valeur actuelle de ce que l'assureur devra payer, par la formule fermée.

    Le fonds dérive au taux de swap diminué des frais, puisque les frais sortent du fonds. La
    garantie est donc un put dont le sous-jacent porte un « dividende » égal aux frais. La formule
    est celle de Black et Scholes avec rendement continu, multipliée par la part des contrats encore
    en vigueur à l'échéance.
    """
    if c.garantie <= 0:
        # sans promesse, il n'y a rien à payer ; le logarithme ci-dessous n'est pas défini
        return 0.0
    if c.annees <= 0:
        return max(c.garantie - c.fonds, 0.0) * c.survie
    if c.volatilite <= 0:
        # sans incertitude, le fonds n'a plus qu'une trajectoire : il dérive au taux de swap
        # diminué des frais. Le paiement est connu d'avance, et il reste à l'actualiser. La
        # formule ci-dessous n'est pas définie à volatilité nulle, sa limite l'est.
        a_l_echeance = c.fonds * math.exp((c.taux - c.frais) * c.annees)
        paiement = max(c.garantie - a_l_echeance, 0.0)
        return paiement * math.exp(-c.taux * c.annees) * c.survie
    racine = c.volatilite * math.sqrt(c.annees)
    d1 = (math.log(c.fonds / c.garantie)
          + (c.taux - c.frais + 0.5 * c.volatilite ** 2) * c.annees) / racine
    d2 = d1 - racine
    put = (c.garantie * math.exp(-c.taux * c.annees) * norm.cdf(-d2)
           - c.fonds * math.exp(-c.frais * c.annees) * norm.cdf(-d1))
    return put * c.survie


def valeur_des_frais(c: Contrat) -> float:
    """La valeur actuelle des frais que l'assureur encaissera pour porter la garantie.

    Les frais sont prélevés sur le fonds, donc leur montant suit le fonds. Sous la mesure neutre au
    risque, l'espérance actualisée du fonds à la date t vaut le fonds d'aujourd'hui diminué des
    frais déjà prélevés, ce qui rend l'intégrale calculable en forme fermée.
    """
    taux = c.frais + c.sortie_annuelle
    if taux <= 0:
        return c.part_frais_garantie * c.fonds * c.annees
    return c.part_frais_garantie * c.fonds * (1 - math.exp(-taux * c.annees)) / taux


def passif_reformule(c: Contrat) -> float:
    """Le passif reformulé : ce qu'on devra payer, moins ce qu'on encaissera pour le porter.

    C'est la grandeur que le chapitre 7 appelle Restated Liabilities. Elle peut être négative quand
    les frais valent plus que la garantie, ce qui est le cas normal d'une garantie très en dehors de
    la monnaie, et le dépôt ne l'écrête pas.
    """
    return valeur_de_la_garantie(c) - valeur_des_frais(c)


def valeur_par_simulation(c: Contrat, tirages: int = 200_000, graine: int = 20260830) -> dict:
    """La même valeur, par simulation, pour contrôler la formule fermée.

    La simulation n'apporte rien de plus ici, puisque le contrat a une forme fermée. Elle sert de
    garde-fou : une formule fermée mal transcrite passe tous les tests d'unité et se trompe quand
    même. Deux chemins indépendants qui tombent sur le même nombre, c'est autre chose.
    """
    rng = np.random.default_rng(graine)
    z = rng.standard_normal(tirages)
    fonds = c.fonds * np.exp((c.taux - c.frais - 0.5 * c.volatilite ** 2) * c.annees
                             + c.volatilite * math.sqrt(c.annees) * z)
    paiement = np.maximum(c.garantie - fonds, 0.0) * math.exp(-c.taux * c.annees) * c.survie
    return {"valeur": float(paiement.mean()),
            "erreur_type": float(paiement.std(ddof=1) / math.sqrt(tirages))}


def delta(c: Contrat, ecart: float = 1e-4) -> float:
    """La sensibilité du passif à un mouvement du fonds, par différence centrée.

    C'est la quantité d'actions qu'un assureur doit vendre pour neutraliser sa garantie, et donc ce
    dont la couverture dynamique du chapitre 7 a besoin. La différence centrée plutôt que la forme
    fermée : elle reste juste si l'on change le contrat, ce qu'une formule recopiée ne fait pas.
    """
    from dataclasses import replace

    haut = passif_reformule(replace(c, fonds=c.fonds * (1 + ecart)))
    bas = passif_reformule(replace(c, fonds=c.fonds * (1 - ecart)))
    return (haut - bas) / (2 * ecart * c.fonds)
