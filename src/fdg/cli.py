"""La ligne de commande : vérifier la grille, décomposer l'exigence, rejouer la couverture."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from . import etudes, figures, reference
from .garantie import Contrat

app = typer.Typer(add_completion=False, help=__doc__)

TABLES = Path("results/tables")


def _ecrire(table, nom: str) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    chemin = TABLES / f"{nom}.csv"
    table.to_csv(chemin, index=False)
    typer.echo(f"  {chemin}  {len(table)} lignes")
    return chemin


@app.command()
def exemples() -> None:
    """Les neuf exemples travaillés de la ligne directrice, refaits un par un."""
    cellules = etudes.cellules_citees()
    typer.echo(f"  cellules citées retrouvées : {int(cellules['coincide'].sum())}"
               f" sur {len(cellules)}")
    _ecrire(cellules, "cellules_citees")
    table = etudes.exemples_du_regulateur()
    typer.echo(table.to_string(index=False))
    _ecrire(table, "exemples_du_regulateur")
    if not bool(table["total_coincide"].all()):
        typer.echo("\n" + reference.NOTE_SUR_LA_HUITIEME_LIGNE)


@app.command()
def structure() -> None:
    """Ce que la grille impose colonne par colonne : un niveau ou un déplacement."""
    table = etudes.structure_de_la_grille()
    typer.echo(table[table["base"] == "terme"].to_string(index=False))
    _ecrire(table, "structure_de_la_grille")
    pivots = etudes.pivots()
    typer.echo(pivots[pivots["base"] == "terme"].to_string(index=False))
    _ecrire(pivots, "pivots")
    figures.grille_des_chocs()


@app.command()
def exigence() -> None:
    """L'exigence de risque de marché, et ce que chaque choc y apporte."""
    table = etudes.decomposition_par_contrat(etudes.contrats_types())
    typer.echo(table[["base", "contrat", "actions_seules", "volatilite_seule", "conjointe",
                      "interaction", "part_de_la_volatilite"]].to_string(index=False))
    _ecrire(table, "decomposition")
    part = etudes.part_par_echeance()
    _ecrire(part, "part_par_echeance")
    controle = etudes.controle_de_la_formule(Contrat())
    typer.echo("\n  contrôle de la formule fermée par simulation : "
               f"{controle['ecarts_types']:.2f} erreur type")
    Path("results").mkdir(exist_ok=True)
    Path("results/controle.json").write_text(
        json.dumps({k: float(v) for k, v in controle.items()}, indent=2), encoding="utf-8")
    figures.decomposition(table[table["base"] == "terme"])
    figures.part_de_la_volatilite(part)


@app.command()
def couverture() -> None:
    """Le crédit de capital qu'une couverture dynamique fait gagner sur les vingt scénarios."""
    c = Contrat()
    table = etudes.credit_par_frequence(c)
    typer.echo(table[["pas", "tolerance", "exigence_sans_couverture",
                      "exigence_avec_couverture", "credit", "part_reduite",
                      "derive_du_chemin_plat"]].to_string(index=False))
    _ecrire(table, "credit_de_couverture")
    detail = etudes.scenarios_de_couverture(c)
    _ecrire(detail, "scenarios_de_couverture")
    figures.credit(table)
    figures.scenarios(detail)


@app.command()
def tout() -> None:
    """Tout, dans l'ordre de la démonstration."""
    exemples()
    structure()
    exigence()
    couverture()


if __name__ == "__main__":      # pragma: no cover
    app()
