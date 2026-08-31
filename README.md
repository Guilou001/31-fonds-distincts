# Le choc de volatilité pèse plus lourd que le choc d'actions, et personne ne l'a écrit

Depuis 2025, le BSIF exige des assureurs vie qu'ils calculent le capital de leurs garanties de fonds
distincts en faisant baisser les actions **et** monter la volatilité en même temps. La partie
volatilité est la nouveauté, et elle est publiée sous forme d'une grille de mille nombres sans un mot
sur ce qu'elle fait. Ce dépôt la refait, mesure ce qu'elle coûte, et trouve une erreur dans les
exemples du régulateur.

[![ci](https://github.com/Guilou001/31-fonds-distincts/actions/workflows/ci.yml/badge.svg)](https://github.com/Guilou001/31-fonds-distincts/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12-blue)
![licence](https://img.shields.io/badge/code-MIT-green)

**Résultat en une phrase.** Sur une garantie de dix ans à cent pour cent, le choc de volatilité exige
à lui seul **7,97 dollars** de capital par cent dollars de fonds contre **7,90** pour le choc
d'actions, soit **57,6 %** de l'exigence conjointe ; les neuf exemples travaillés de la ligne
directrice se reproduisent tous, sauf une addition, qui imprime **51,4 là où 54,0 moins 3,6 fait
50,4**.

*Summary in English. OSFI's 2025 segregated fund guarantee regime requires insurers to shock equity
levels and implied volatilities simultaneously. This repository rebuilds the volatility shock grid of
Appendix 7-A (75 × 13 published values), reproduces all nine of the guideline's worked interpolation
examples and finds that one of the nine printed totals does not add up (51.4 where 54.0 − 3.6 = 50.4).
It then measures what nobody publishes: the volatility shock alone accounts for 22.7 % to 57.6 % of
the joint market risk requirement depending on term, peaking at 64.4 % around twelve years, and the
two shocks interfere rather than add. The grid turns out to pin one-month volatility at 41 % and
thirty-year volatility at 25 % whatever the insurer's starting level, so an insurer above roughly
45 % sees its volatility reduced by the stress. Replaying a delta hedge over the twenty prescribed
scenarios of Appendix 7-C removes 84.8 % of the requirement, and all twenty scenarios lose money.*

## 1. La question posée

**Le produit, en mots simples.** Un fonds distinct est un fonds commun de placement vendu par un
assureur, avec une promesse en plus : quelle que soit la valeur du fonds à l'échéance, le détenteur
récupère au moins un montant garanti. L'assureur prélève des frais annuels et, en échange, comble la
différence si le fonds a baissé.

**Ce que l'assureur a vendu.** Exactement une option de vente. Si le fonds finit au-dessus de la
garantie, l'assureur ne paie rien ; sinon, il paie la différence. C'est pourquoi une hausse de
volatilité lui coûte cher alors même que le niveau du marché n'a pas bougé.

**Ce que le régulateur a changé.** L'ancien régime chargeait le capital par des facteurs tabulés. Le
nouveau demande de réévaluer le passif sous un scénario de tension, et ce scénario comporte deux
chocs simultanés : les actions baissent de 35 %, et la volatilité implicite bouge selon une grille
publiée en appendice. La question est de savoir lequel des deux fait le capital.

## 2. D'où vient le projet, et ce qu'il apporte

La ligne directrice publie tout ce qu'il faut : la grille des chocs, neuf exemples travaillés de son
interpolation, vingt trajectoires de prix imposées pour juger une couverture, et un exemple chiffré
de la mécanique de couverture. Aucun dépôt public ne la calcule.

Trois apports.

- **Les neuf exemples travaillés refaits**, dont huit se referment et un non.
- **La structure cachée de la grille**, qui n'est pas une table de chocs mais une table qui épingle
  les deux bouts de la courbe de volatilité et laisse le milieu suivre l'assureur.
- **Le partage de l'exigence** entre le choc d'actions et le choc de volatilité, mesuré selon la
  monnaie et l'échéance, et le crédit qu'une couverture dynamique fait gagner sur les vingt
  scénarios du régulateur.

## 3. Les données

Aucun téléchargement récurrent : tout vient de la ligne directrice elle-même.

| Source | Ce qu'elle donne | Volume |
|---|---|---:|
| Appendice 7-A | le choc de volatilité sur une base à terme | 75 × 13 valeurs |
| Appendice 7-B | le même sur une base au comptant | 75 × 13 valeurs |
| Appendice 7-C | vingt trajectoires de prix d'actions sur un an | 53 semaines et 13 mois |
| Section 7.2.2 | neuf exemples travaillés d'interpolation | 9 lignes |
| Section 7.3.2.3 | un exemple chiffré de la mécanique de couverture | 9 lignes |
| Section 5.2.1 | le facteur de choc des actions, 35 % | 1 valeur |

Les 3 270 nombres sont relevés le 30 août 2026 et figés dans `src/fdg/tables/`. Ils ne sont pas
retéléchargés à chaque exécution : la page du BSIF les publie en HTML, dans des tableaux dont la mise
en forme change d'une version à l'autre, et un chargeur automatique casserait au premier changement
de gabarit **sans le dire**. Ce qui change avec la ligne directrice se change à la main, une fois.

## 4. La méthode, pas à pas

1. **Recopier les trois appendices**, puis vérifier qu'ils ont été lus dans le bon sens : les vingt
   cellules que les exemples citent nommément doivent se retrouver, et les tables hebdomadaire et
   mensuelle de l'appendice 7-C doivent finir au même point.
2. **Écrire l'interpolation bilinéaire** que la ligne directrice décrit, puis la confronter aux neuf
   exemples travaillés.
3. **Évaluer la garantie** sous la mesure neutre au risque que le chapitre impose, par la formule
   fermée de Black et Scholes et par simulation, et exiger qu'elles se rejoignent.
4. **Appliquer les chocs**, séparément puis ensemble, et mesurer ce que chacun apporte.
5. **Rejouer la couverture** sur les vingt trajectoires imposées, semaine après semaine.

## 5. Les résultats

### 5.1 Neuf chocs sur neuf, huit totaux sur neuf

La ligne directrice déroule neuf calculs, trois volatilités de départ par trois échéances, avec
l'arithmétique écrite en toutes lettres.

| Volatilité de départ | Mois | Choc publié | Choc recalculé | Total publié | Total recalculé |
|---:|---:|---:|---:|---:|---:|
| 5,0 % | 1 | +36,0 | +36,000 | 41,0 | 41,0 |
| 5,0 % | 115 | +29,1 | +29,136 | 34,1 | 34,1 |
| 5,0 % | 550 | +20,0 | +20,000 | 25,0 | 25,0 |
| 18,7 % | 1 | +22,3 | +22,300 | 41,0 | 41,0 |
| 18,7 % | 115 | +16,2 | +16,246 | 34,9 | 34,9 |
| 18,7 % | 550 | +6,3 | +6,300 | 25,0 | 25,0 |
| 54,0 % | 1 | −13,0 | −13,000 | 41,0 | 41,0 |
| **54,0 %** | **115** | **−3,6** | **−3,581** | **51,4** | **50,4** |
| 54,0 % | 550 | −29,0 | −29,000 | 25,0 | 25,0 |

Comment lire ce tableau, en trois constats. Le premier est que les neuf chocs se retrouvent, à la
décimale que la ligne directrice imprime : l'interpolation est comprise et la grille est lue dans le
bon sens, ce que confirment aussi les vingt cellules citées nommément dans les exemples. Le deuxième
est que la huitième ligne ne se referme pas : le choc est juste, mais l'addition ne l'est pas, car
54,0 moins 3,6 fait 50,4 et non 51,4. Le troisième est que ce n'est pas une convention d'arrondi :
les deux lignes qui l'encadrent dans le même tableau, 54,0 moins 13,0 égale 41,0 et 54,0 moins 29,0
égale 25,0, tombent toutes les deux juste.

Constat mesuré le 30 août 2026 sur la version 2025 de la ligne directrice.

### 5.2 La grille n'est pas une table de chocs, c'est une table de cibles aux deux bouts

| Échéance | Volatilité choquée la plus basse | La plus haute | Étendue |
|---:|---:|---:|---:|
| 1 mois | 41,0 % | 41,1 % | **0,1** |
| 24 mois | 21,5 % | 67,5 % | 46,0 |
| 120 mois | 35,7 % | 64,3 % | 28,6 |
| 360 mois | 25,0 % | 25,0 % | **0,0** |
| 1200 mois | 25,0 % | 25,0 % | **0,0** |

Comment lire ce tableau, en trois constats. Le premier est qu'à un mois, les soixante-quinze niveaux
de volatilité de départ arrivent tous à **41 %** : un assureur à 5 % reçoit +36, un assureur à 54 %
reçoit −13, et les deux finissent au même endroit. Le deuxième est qu'à trente et à cent ans, ils
arrivent tous à **25 %**, cette fois exactement. Le troisième est qu'entre les deux, l'étendue
s'ouvre jusqu'à quarante-six points : au milieu de la courbe, le régulateur impose un déplacement et
non un niveau. La ligne directrice ne l'écrit nulle part.

La conséquence pratique se lit sur le pivot, le niveau de volatilité au-delà duquel le choc devient
une **baisse** : il vaut 25,0 % aux très longues échéances, 51,4 % à quinze ans, et 44,7 % en
médiane. Autrement dit, un assureur dont la volatilité implicite dépasse la mi-quarantaine voit sa
volatilité **réduite** par le scénario de tension.

![Où arrive une volatilité de départ, selon l'échéance](results/figures/grille_des_chocs.png)

Comment lire cette figure : l'abscisse est la volatilité de départ, l'ordonnée celle qui sort du
choc, et la diagonale marque l'absence de choc. Une courbe horizontale signifie que le régulateur
impose un niveau. Les courbes coupent la diagonale entre 40 et 50 % : à gauche du croisement le choc
monte, à droite il descend.

### 5.3 Le choc de volatilité est la plus grosse moitié, entre neuf et dix-sept ans

Exigence de capital, en dollars pour cent dollars de fonds, sur une volatilité de départ de 18 %.

| Contrat | Choc d'actions seul | Choc de volatilité seul | Les deux ensemble | Somme des deux | Part de la volatilité |
|---|---:|---:|---:|---:|---:|
| garantie à 75 %, 3 ans | 8,84 | 3,56 | 12,62 | 12,40 | 28,2 % |
| garantie à 75 %, 10 ans | 5,29 | 6,20 | 10,89 | 11,48 | 56,9 % |
| garantie à 100 %, 3 ans | 17,66 | 5,63 | 20,42 | 23,29 | 27,6 % |
| **garantie à 100 %, 10 ans** | **7,90** | **7,97** | **13,85** | **15,87** | **57,6 %** |
| garantie à 100 %, 20 ans | 3,95 | 2,80 | 6,19 | 6,75 | 45,2 % |
| garantie à 125 %, 3 ans | 23,19 | 5,61 | 24,75 | 28,80 | 22,7 % |
| garantie à 125 %, 10 ans | 10,05 | 8,88 | 15,78 | 18,93 | 56,3 % |

Comment lire ce tableau, en trois constats. Le premier est qu'à dix ans, le choc de volatilité exige
**plus** que le choc d'actions, et cela pour les trois niveaux de garantie : c'est le résultat de
tête du dépôt. Le deuxième est que les deux chocs **ne s'additionnent pas** : l'exigence conjointe
est plus petite que leur somme, de 2,0 dollars sur le contrat type et jusqu'à 4,1 sur la garantie à
125 % à trois ans. Le mécanisme est simple : la baisse des actions pousse la garantie dans la
monnaie, et une option très dans la monnaie perd sa sensibilité à la volatilité. Le troisième est
qu'il existe une exception, la garantie à 75 % à trois ans, où les deux chocs se **renforcent** de
0,23 : cette garantie est si loin de la monnaie que la baisse des actions l'en rapproche au lieu de
l'y enfoncer, et l'amène là où la volatilité compte le plus.

![Ce que chaque choc exige, contrat par contrat](results/figures/decomposition.png)

Comment lire cette figure : deux barres par contrat pour les chocs pris seuls, un losange pour les
deux ensemble, un trait vertical pour leur somme. Le losange est presque toujours à gauche du trait,
et l'écart entre les deux est ce que la rencontre des deux chocs retire.

![La part de l'exigence que le choc de volatilité explique](results/figures/part_de_la_volatilite.png)

Comment lire cette figure : la part passe la moitié vers neuf ans, culmine à **64,4 % autour de douze
ans**, et redescend ensuite. Les deux coudes, vers sept et douze ans, ne sont pas dans les données de
l'assureur : ce sont les colonnes 84 et 144 mois de la grille du régulateur, entre lesquelles
l'interpolation est linéaire. La grille imprime donc sa propre géométrie dans le capital exigé.

### 5.4 Une couverture dynamique fait tomber 85 % de l'exigence, et perd dans les vingt scénarios

| Rééquilibrage | Bande de non-intervention | Exigence avec couverture | Crédit | Part de l'exigence effacée |
|---|---:|---:|---:|---:|
| hebdomadaire | aucune | 1,20 | 6,69 | **84,8 %** |
| hebdomadaire | 1 % | 1,28 | 6,62 | 83,8 % |
| hebdomadaire | 5 % | 1,86 | 6,03 | 76,4 % |
| mensuel | aucune | 1,39 | 6,50 | 82,4 % |
| mensuel | 5 % | 2,06 | 5,84 | 73,9 % |

Comment lire ce tableau, en trois constats. Le premier est que la couverture ne fait jamais tomber
l'exigence à zéro : le rééquilibrage discret laisse toujours passer quelque chose, et c'est
exactement ce que le test du régulateur mesure. Le deuxième est que la fréquence compte moins que la
discipline : passer de l'hebdomadaire au mensuel coûte 2,4 points de crédit, alors que laisser filer
une bande de cinq pour cent en coûte 8,4. Le troisième est que **les vingt scénarios sont perdants**,
sans exception : un vendeur d'options qui se couvre en delta perd sur les grands mouvements, quel
qu'en soit le sens.

![Les vingt trajectoires imposées, et ce que la couverture laisse passer](results/figures/scenarios.png)

Comment lire cette figure : à gauche les vingt trajectoires, dix qui montent et dix qui baissent,
partage exact et voulu par le régulateur. À droite l'erreur de suivi de chacune, rangée par prix
d'arrivée. Les trajectoires baissières coûtent **2,26 fois** les haussières, parce qu'elles poussent
la garantie vers la monnaie, là où sa sensibilité bouge le plus vite.

## 6. Reproduire

```bash
uv sync --locked --all-extras
uv run pytest                 # 43 tests fermés, sans réseau
uv run fdg tout               # les quatre études et les cinq figures
```

Aucun téléchargement n'est nécessaire : les trois appendices sont dans le paquet. Tous les chiffres
de ce README viennent des fichiers de `results/`.

## 7. Limites, avec leur statut

| Limite | Statut |
|---|---|
| Le contrat modélisé est une garantie à l'échéance simple | déclaré ; ni cliquet, ni retrait garanti à vie, ni réassurance, qui sont l'essentiel d'un vrai portefeuille |
| Les rachats sont supposés indépendants du niveau du marché | reconnu ; on rachète moins quand la garantie vaut cher, ce qui augmenterait l'exigence de rachat que ce dépôt ne calcule pas |
| Seul le risque de marché est calculé | déclaré ; les volets crédit, mortalité, longévité, déchéance, frais et opérationnel demandent des données propres à l'assureur |
| Le passif reformulé est évalué en Black et Scholes à volatilité constante | déclaré ; la grille du régulateur est une surface, et une vraie évaluation emploierait un modèle à volatilité stochastique |
| L'assiette d'actions est supposée entièrement en actions cotées de marchés développés | déclaré ; c'est le facteur de 35 % de la section 5.2.1, et un fonds mixte en aurait un plus bas |
| Le crédit de couverture suppose une couverture en delta seul | déclaré ; un programme réel couvre aussi la sensibilité au second ordre, ce qui réduirait encore l'erreur de suivi |
| Les appendices sont figés au 30 août 2026 | déclaré ; la version 2026 de la ligne directrice n'était pas publiée à cette date, et la note d'ajustement du 22 mai 2025 est intégrée à la version employée |
| L'exigence est calculée par contrat, pas par portefeuille | reconnu ; un portefeuille réel agrège des cohortes dont les monnaies diffèrent, et la section 5.3 montre que la part de la volatilité en dépend fortement |

## 8. Crédits, licence, citation

Test de suffisance du capital des sociétés d'assurance-vie (2025), chapitre 7 sur le risque lié aux
garanties de fonds distincts, appendices 7-A, 7-B et 7-C, et chapitre 5 section 5.2.1 pour le facteur
d'actions. Bureau du surintendant des institutions financières, relevé le 30 août 2026. La note
réglementaire d'ajustement du 22 mai 2025 est intégrée à la version employée.

Code sous licence MIT, rapport sous licence CC BY 4.0. Figures produites par
[gv-fintools](https://github.com/Guilou001/gv-fintools).

Voisinage dans le portefeuille :
[17-alm-assurance-vie](https://github.com/Guilou001/17-alm-assurance-vie) calcule le module de risque
de taux du même test de suffisance, chapitre 5, sur un bloc de rentes ; celui-ci calcule le module de
risque de marché du chapitre 7, sur des garanties de fonds distincts. Les deux se lisent ensemble
comme les deux moitiés du capital d'un assureur vie.
[15-valorisation-options](https://github.com/Guilou001/15-valorisation-options) porte la machinerie
d'évaluation d'options que ce dépôt applique à un produit d'assurance. Le rapport
`rapport/rapport.pdf` est engendré depuis ce README.
