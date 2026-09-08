#set document(title: "Que coûte à un assureur la promesse de protéger un placement ?", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [fonds-distincts], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Que coûte à un assureur la promesse de protéger un placement ?]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/31-fonds-distincts")[Guilou001/31-fonds-distincts]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Supposons qu'un assureur garantisse 100 dollars à l'échéance d'un placement. Si le fonds ne vaut plus que 80 dollars ce jour-là, il doit payer les 20 dollars manquants.

Cette promesse devient plus coûteuse quand les actions baissent. Elle peut aussi coûter davantage quand leurs mouvements futurs deviennent plus incertains, même sans baisse immédiate.

Ce projet refait les calculs réglementaires canadiens de cette garantie simple. Il sépare le choc sur les actions du choc sur leur volatilité, c'est-à-dire l'ampleur attendue de leurs variations.

*Les deux chocs comptent. Celui qui domine dépend de la grille réglementaire utilisée.*

== Comparer les chocs sur le même contrat

L'exemple suivant porte sur un fonds de 100 dollars, une garantie de 100 dollars et une échéance de dix ans. La volatilité de départ est fixée à 18 % par an.

#figure(image("../results/figures/presentation.png", width: 100%), caption: [Capital des deux chocs séparés et du scénario conjoint selon les deux grilles publiées])

Chaque groupe applique une des deux grilles publiées par le BSIF, le régulateur financier fédéral canadien. La barre du scénario conjoint montre pourquoi additionner les deux chocs isolés ne donne pas le bon total.

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Grille de volatilité*],
    [*Actions seules*],
    [*Volatilité seule*],
    [*Deux chocs ensemble*],
    [À terme, appendice 7-A],
    [7,90 \$],
    [7,97 \$],
    [13,85 \$],
    [Au comptant, appendice 7-B],
    [7,90 \$],
    [5,17 \$],
    [11,69 \$],
)

Les montants sont par tranche de 100 dollars de fonds. Les deux grilles décrivent différemment la volatilité selon l'échéance. Leur choix change le classement des chocs. #link("results/tables/decomposition.csv")[Décomposition complète].

== Contrôler la lecture du règlement

Le programme utilise les tableaux figés du régime 2025, relevés le 30 août 2026. Il retrouve les neuf chocs des exemples officiels.

Un total imprimé ne correspond pas à ses propres entrées. Le document donne 51,4 alors que 54,0 moins 3,6 fait 50,4. Le dépôt présente les deux nombres et le calcul intermédiaire.

D'autres exercices font varier la durée de la garantie et rejouent une couverture sur les vingt trajectoires imposées par le régulateur.

== Ce qui reste hors du modèle

La garantie étudiée est payable à une échéance fixe. Les retraits garantis à vie, les revalorisations de garantie et la réassurance ne sont pas modélisés.

Les chiffres représentent une composante du capital de risque de marché. Ils ne donnent ni le prix commercial du contrat ni le capital total d'un assureur.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pytest\nuv run fdg tout", block: true, lang: "bash")

Aucun téléchargement n'est nécessaire. Les grilles réglementaires utilisées sont conservées dans le paquet. Le graphique de présentation se régénère hors réseau avec #raw("uv run python scripts/figure_presentation.py"), depuis les tableaux publiés.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

A simple segregated fund maturity guarantee is valued under Canada's published equity and volatility stresses. The ranking of the two shocks changes between the forward and spot grids. The calculation covers a market risk component, not an insurer's full capital requirement.
