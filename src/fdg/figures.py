"""Les quatre figures du dépôt. Chacune reçoit un tableau déjà calculé et n'invente aucun nombre."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from gvf.style import GRIS, OKABE_ITO, appliquer, enregistrer, formateur, fr

from . import appendices

DOSSIER = Path("results/figures")


def _fin(fig, nom: str, dossier: Path = DOSSIER) -> list[Path]:
    # pas de `tight_layout` : la feuille de style partagée active la mise en page sous contrainte
    chemins = enregistrer(fig, dossier, nom)
    plt.close(fig)
    return chemins


def grille_des_chocs(dossier: Path = DOSSIER) -> list[Path]:
    """Où arrive une volatilité de départ, selon l'échéance.

    L'axe des abscisses est la volatilité de départ, l'axe des ordonnées la volatilité une fois le
    choc appliqué. La diagonale marque l'absence de choc. Une courbe horizontale signifie que le
    régulateur impose un niveau ; une courbe parallèle à la diagonale, qu'il impose un déplacement.
    """
    appliquer()
    grille = appendices.table_des_chocs("terme")
    vols, mois = appendices.volatilites(), appendices.mois()
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    a_tracer = [1, 12, 60, 120, 360]
    for i, m in enumerate(a_tracer):
        j = mois.index(m)
        cibles = [vols[k] + grille[k][j] for k in range(len(vols))]
        ax.plot(vols, cibles, lw=1.9, color=OKABE_ITO[i % len(OKABE_ITO)],
                label=f"{m} mois" if m > 1 else "1 mois")
    ax.plot(vols, vols, ls="--", lw=1.1, color=GRIS, label="aucun choc")
    ax.annotate("le très court terme est\népinglé à 41 %", (60, 41), textcoords="offset points",
                xytext=(-8, 16), ha="right", fontsize=8, color=GRIS)
    ax.annotate("le très long terme\nest épinglé à 25 %", (60, 25), textcoords="offset points",
                xytext=(-8, -30), ha="right", fontsize=8, color=GRIS)
    ax.set_xlabel("volatilité implicite de départ")
    ax.set_ylabel("volatilité une fois le choc appliqué")
    for axe in (ax.xaxis, ax.yaxis):
        axe.set_major_formatter(formateur(decimales=0, suffixe=" %"))
    ax.legend(fontsize=8, ncols=6, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "grille_des_chocs", dossier)


def decomposition(table, dossier: Path = DOSSIER) -> list[Path]:
    """Ce que chaque choc exige, contrat par contrat, et ce que leur rencontre retire."""
    appliquer()
    t = table.sort_values("conjointe")
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    y = np.arange(len(t))
    hauteur = 0.34
    ax.barh(y + hauteur / 2, t["actions_seules"], height=hauteur, color=OKABE_ITO[0],
            label="Choc d'actions seul")
    ax.barh(y - hauteur / 2, t["volatilite_seule"], height=hauteur, color=OKABE_ITO[1],
            label="Choc de volatilité seul")
    ax.plot(t["conjointe"], y, "D", ms=7, color=OKABE_ITO[3], label="Les deux ensemble")
    ax.plot(t["somme_des_parts"], y, "|", ms=13, mew=2, color=GRIS, label="Somme des deux")
    ax.set_yticks(y, [n for n in t["contrat"]], fontsize=8.4)
    ax.set_xlabel("exigence de capital, en dollars pour cent dollars de fonds")
    ax.xaxis.set_major_formatter(formateur(decimales=0))
    ax.legend(fontsize=8, ncols=4, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "decomposition", dossier)


def scenarios(table, dossier: Path = DOSSIER) -> list[Path]:
    """Les vingt trajectoires du régulateur, et l'erreur de suivi que chacune laisse."""
    appliquer()
    prix = appendices.scenarios("hebdomadaire")
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    semaines = np.arange(len(prix))
    for j in range(len(prix[0])):
        trajectoire = [ligne[j] for ligne in prix]
        baisse = trajectoire[-1] < 100
        axes[0].plot(semaines, trajectoire, lw=1.2, alpha=0.85,
                     color=OKABE_ITO[3] if baisse else OKABE_ITO[2])
    axes[0].axhline(100, color=GRIS, lw=1.0, ls="--")
    axes[0].set_xlabel("semaine")
    axes[0].set_ylabel("prix de l'action, départ à 100")
    axes[0].set_title("Les vingt trajectoires imposées", fontsize=10)
    axes[0].annotate("dix baissent", (52, 60), fontsize=8.5, color=OKABE_ITO[3], ha="right")
    axes[0].annotate("dix montent", (52, 155), fontsize=8.5, color=OKABE_ITO[2], ha="right")

    t = table.sort_values("prix_final")
    couleurs = [OKABE_ITO[3] if p < 100 else OKABE_ITO[2] for p in t["prix_final"]]
    axes[1].bar(np.arange(len(t)), t["valeur_actuelle"], color=couleurs, width=0.72)
    axes[1].set_xticks(np.arange(len(t)), [str(int(s)) for s in t["scenario"]], fontsize=7.4)
    axes[1].set_xlabel("scénario, rangé par prix d'arrivée")
    axes[1].set_ylabel("erreur de suivi actualisée")
    axes[1].set_title("Ce que la couverture laisse passer", fontsize=10)
    axes[1].yaxis.set_major_formatter(formateur(decimales=1))
    return _fin(fig, "scenarios", dossier)


def credit(table, dossier: Path = DOSSIER) -> list[Path]:
    """Le crédit de couverture, selon le pas de rééquilibrage et la bande de non-intervention."""
    appliquer()
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    largeur = 0.36
    pas_distincts = list(dict.fromkeys(table["pas"]))
    tolerances = sorted(set(table["tolerance"]))
    x = np.arange(len(tolerances))
    for i, pas in enumerate(pas_distincts):
        sous = table[table["pas"] == pas].set_index("tolerance").reindex(tolerances)
        ax.bar(x + (i - 0.5) * largeur, sous["part_reduite"], width=largeur,
               color=OKABE_ITO[i], label=f"rééquilibrage {pas}")
        for k, v in enumerate(sous["part_reduite"]):
            ax.text(x[k] + (i - 0.5) * largeur, v, fr(100 * v, 1) + " %", ha="center",
                    va="bottom", fontsize=8, color=GRIS)
    ax.set_xticks(x, [f"bande de {fr(100 * t, 0)} %" if t else "aucune bande" for t in tolerances])
    ax.set_ylabel("part de l'exigence que\nla couverture fait tomber")
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(formateur(decimales=0, suffixe=" %", facteur=100))
    ax.legend(fontsize=8, ncols=2, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "credit_de_couverture", dossier)


def part_de_la_volatilite(dossier: Path = DOSSIER) -> list[Path]:
    """La part de l'exigence que le choc de volatilité explique, selon l'échéance."""
    from dataclasses import replace

    from .capital import decomposer
    from .garantie import Contrat

    appliquer()
    base = Contrat()
    annees = np.arange(1.0, 25.5, 0.5)
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for i, rapport in enumerate((0.75, 1.00, 1.25)):
        parts = []
        for a in annees:
            d = decomposer(replace(base, garantie=base.fonds * rapport, annees=float(a)))
            parts.append(d.part_de_la_volatilite)
        ax.plot(annees, parts, lw=1.9, color=OKABE_ITO[i],
                label=f"garantie à {fr(100 * rapport, 0)} %")
    ax.axhline(0.5, color=GRIS, lw=1.0, ls="--")
    ax.text(1.2, 0.505, "la moitié de l'exigence", fontsize=8, color=GRIS, va="bottom")
    ax.set_xlabel("années restant à courir")
    ax.set_ylabel("part de l'exigence conjointe que le choc\nde volatilité explique à lui seul")
    ax.yaxis.set_major_formatter(formateur(decimales=0, suffixe=" %", facteur=100))
    ax.legend(fontsize=8, ncols=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "part_de_la_volatilite", dossier)
