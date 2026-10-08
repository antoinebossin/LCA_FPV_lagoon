# ACV_propre — version figée du modèle

Analyse du cycle de vie d'une plateforme photovoltaïque flottante installée sur
le lagon de Ra'iātea, Polynésie française. Ce dossier reproduit les chiffres de
l'article et rien d'autre.

---

## Ce que ce dossier est, et ce qu'il n'est pas

`acv_lagon/` à la racine du projet reste le **dossier de travail**. Il garde ses
soixante-cinq sauvegardes `*.avant_*`, son historique et ses expérimentations,
et c'est lui qu'il faut modifier.

Ce dossier-ci est une **copie figée**. Les vingt-sept modules y sont identiques
à ceux du dossier de travail au 6 octobre 2026 ; seuls ont été écartés les
sauvegardes, le cache `__pycache__`, le dossier `_a_supprimer/` et
`brancher_chantier.py`, un correctif à usage unique déjà appliqué. **Rien n'a
été réécrit** : modifier le modèle ici ne servirait qu'à faire diverger les deux
copies.

Il existe pour deux raisons : disposer d'une version dont on sait qu'elle
produit les chiffres publiés, et pouvoir déposer quelque chose de lisible à côté
de l'article.

---

## Lancer

```
ACV_propre/
├── acv_lagon/        27 modules
├── ACV_main.ipynb    le carnet, dans l'ordre de l'article
└── README.md
```

Ouvrir `ACV_main.ipynb` et exécuter dans l'ordre. Le carnet localise `acv_lagon/`
tout seul en remontant l'arborescence, il n'y a pas de chemin à régler.

**Le noyau doit être celui du projet** (Python 3.11). Depuis un noyau plus
ancien, l'import de brightway2 échoue sur « unsupported pickle protocol: 5 »,
message dont la vraie cause est le choix du noyau. La première cellule le
vérifie et s'arrête proprement.

**Compter une trentaine de minutes** pour le carnet complet. Le Monte-Carlo à
500 000 tirages (§ 6) et les transpositions territoriales (§ 12) dominent ; les
cellules coûteuses portent un avertissement.

### Il faut aussi

- un projet Brightway contenant **ecoinvent 3.11 cut-off**, la méthode
  **EF v3.1** et **ReCiPe 2016 v1.03 endpoint (H)** ;
- `lca_algebraic`, `brightway2`, `pandas`, `matplotlib`, `numpy` ;
- `parasol_lca` pour l'inventaire de fabrication photovoltaïque.

La base ecoinvent est sous licence et ne peut pas être redistribuée. Les
identifiants d'activité utilisés sont listés dans le Supporting Information de
l'article, de sorte qu'un détenteur de licence puisse reconstruire le modèle.

---

## Le carnet, section par section

| § du carnet | Produit | Dans l'article |
|---|---|---|
| 1–3 | initialisation, modèle, quatre configurations | § 2 |
| 4 | résultat principal, dégradation, incertitude | § 3.1, tableaux 2 et 3, figure 4 |
| 5 | contribution par poste | § 3.2, figures 5 et 7, tableau 4 |
| 6 | Monte-Carlo, tornado, élasticités | § 2.6 et § 3.2, annexe S3 |
| 7 | fin de vie, sept modalités | § 2.5 et § 3.5, figure 11 |
| 8 | aluminium, origine et anodisation | § 3.2 |
| 9 | câble, par mètre posé | § 4.2 |
| 10 | lecture endpoint ReCiPe | § 3.3, figure 8 |
| 11 | CO₂ évité | § 3.4, tableau 6 |
| 12 | transposition aux 54 îles, contrôle NASA POWER | § 3.6, figures 9 et 10, annexe S2 |
| 13 | benchmark littérature harmonisé | § 2.9 et § 4.1, figure 6 |
| 14 | CAPEX et LCOE | § 3.3, tableau 5 |
| 15 | batterie de contrôles | — |
| 16 | export des figures | — |

---

## Conventions

| | |
|---|---|
| Base de fond | ecoinvent 3.11, system model **cut-off** |
| Méthode | EF v3.1, 16 catégories midpoint |
| Lecture secondaire | ReCiPe 2016 v1.03 endpoint (H), **non convertible** avec EF |
| Unité fonctionnelle | 1 kWh net livré au réseau, sur 30 ans |
| Référence | S2 (SH51, 51 % opaque) |
| Dégradation | 0,35 %/an, garantie fabricant (retour relecteur, 06/10/2026) ; 0,50, 0,70 et 1,00 en scénario |
| Disponibilité | 97 % en référence ; 100 % (productible reconstruit) en scénario |
| Productible moyen | 1 009 kWh kWp⁻¹ an⁻¹ sur 30 ans (1 096 × 0,97 = 1 063 en première année) |
| Câble d'export | alloué au prorata de la puissance crête (27,9 / 19,9 / 32,9 / 19,3 %) |

**Ce qui est tiré et ce qui ne l'est pas.** Cinquante paramètres sont tirés dans
le Monte-Carlo. Quatre ne le sont pas — fin de vie, origine de l'aluminium, mix
électrique de fabrication, gazole de manœuvre du chantier — parce que ce sont des
**choix**, et qu'un choix n'a pas de loi de probabilité. Les tirer reviendrait à
moyenner des options faites pour être comparées. Le détail est dans l'annexe S3
de l'article et dans `parametres.py`.

---

## Deux pièges, documentés parce qu'ils ont coûté du temps

**Ne jamais lire une constante par `from X import CONST`.** Dans un paquet
rechargé à chaud par `%autoreload`, cela fige la valeur au moment de l'import :
le fichier source change, la valeur servie non. Même piège pour une valeur par
défaut d'argument, évaluée une seule fois au `def`. On lit une constante **à
travers son module**, à l'appel.

**Ne jamais ajouter d'alias rétrocompatible après les définitions.** Un
`ancien_nom = autre_fonction` placé en fin de fichier écrase silencieusement la
fonction du même nom définie plus haut, sans la moindre erreur. Un avertissement
est posé à l'endroit où l'un d'eux avait été laissé, dans `resultats.py`.

---

## Vérifier

`tests.tout(ctx, jeux, REF)` est la batterie complète, à la fin du carnet. En
cours de route, `checks.Reference` fige le GWP de la configuration de référence
dès la première cellule de résultat : toute cellule qui le recalcule s'y compare
et lève une erreur en cas d'écart, plutôt que de laisser passer un chiffre faux.

Copie figée au 6 octobre 2026.
