"""
Incertitude et sensibilité, pour les QUATRE configurations.

Jusqu'ici le Monte-Carlo et les analyses de sensibilité ne tournaient que sur
la configuration de référence, et — plus gênant — ils tiraient TOUS les
paramètres depuis les valeurs par défaut du registre, qui sont celles de S2.
Lancé sur S1, le tirage aurait échantillonné `n_modules` dans [19 ; 21] alors
que S1 en porte 28, et `m_alu_structure_kg` autour de 606 kg alors que S1 en
porte 718. Ce module corrige les deux choses : il tire par configuration, et
il tire ce qu'il faut.

────────────────────────────────────────────────────────────────────────────
CE QUE LA BANDE D'INCERTITUDE REPRÉSENTE (décidé le 16/09/2026)

**Une incertitude de DONNÉES, pas un éventail de conceptions.** La question à
laquelle la bande répond est « à quel point connaît-on CETTE plateforme ? ».
Quatre familles de paramètres, quatre traitements :

0. DONNÉES DE LA CONFIGURATION — tout ce que `modalites.py` renseigne et qui
   n'est pas explicitement classé ailleurs reste À SA VALEUR. C'est la règle
   par défaut, et elle est volontairement fail-safe : un paramètre injecté par
   une brique tierce (parasol renseigne l'épaisseur de verre, le cadre alu
   surfacique, la bifacialité) est une MESURE sur nos modules, pas une
   inconnue. Sans cette règle il était tiré sur la loi générique de parasol, et
   nos relevés étaient jetés — c'est le défaut corrigé le 16/09/2026, repéré
   parce que la batterie affichait « 52 paramètres tirés » pour 41 paramètres
   au modèle.

   L'unique exception est `productible_kwh_kwc_an` (`PARAMS_ECHANTILLONNES`) :
   il est renseigné par modalité mais son incertitude est réelle, mesurée et
   commune aux quatre.

1. FIGÉS — ce qui est compté ou relevé, donc connu :

       n_modules, n_onduleurs, n_ancres, n_repeteurs      (dénombrés)
       p_install_kwc, rendement_module, packing_cellules  (plaque, géométrie)
       duree_vie_an                                       (convention d'UF)
       maint_par_an                                       (protocole retenu)

   Les tirer serait inventer de l'incertitude là où il n'y en a pas — et,
   pour les dénombrements, produire des « 19,4 modules ».

   `duree_vie_an` mérite un mot : son défaut (30 ans) est SUR son maximum
   ([20 ; 30]). Tout tirage ne pouvait donc que raccourcir la vie et
   augmenter le GWP — un biais systématique à la hausse, invisible dans un
   intervalle. Et le productible moyen dépend de la durée par la
   dégradation, sans être recalculé au tirage. La durée de vie est une
   convention d'unité fonctionnelle : elle est figée ici, et traitée comme un
   SCÉNARIO par `resultats.plage_duree_de_vie`, qui recalcule P̄ correctement.

   `maint_par_an` a rejoint cette famille le 16/09/2026, pour la même raison :
   15 visites par an est le protocole retenu, pas une inconnue. Son mode à 15
   dans [12 ; 26] donnait une moyenne de tirage de 17,7 visites — la variante
   de protocole était comptée deux fois, dans la bande ET dans le scénario, et
   poussait la médiane au-dessus du nominal. Elle est désormais chiffrée par
   `resultats.variante_maintenance` et par elle seule.

2. RELATIFS — les masses propres à chaque configuration. Elles ont une vraie
   tolérance, mais leur valeur nominale change d'une plateforme à l'autre. On
   conserve donc la FORME et la LARGEUR RELATIVE de la loi déclarée, recentrée
   sur la valeur de la configuration :

       tirage = loi_déclarée(u) × (valeur de la configuration ÷ défaut)

   C'est ce qui permet d'appliquer « ±5 % sur l'aluminium » aux 718 kg de S1
   comme aux 606 kg de S2.

3. ABSOLUS — tout le reste : longueurs, densités, distances, durées de vie des
   sous-ensembles, productible. Ces grandeurs sont communes aux quatre
   plateformes ; on les tire selon leur loi déclarée dans `parametres.py`.

Les axes de scénario (`fin_de_vie`, `origine_aluminium`, mix de fabrication)
restent hors du tirage : comparer trois conventions comptables n'est pas une
incertitude (cf. `parametres.SCENARIOS`).

⚠ LIMITE ASSUMÉE — les corrélations ne sont pas modélisées. `m_systeme_t` est
recomposée à partir de l'ancrage, du câble, des modules et de la structure ;
elle est pourtant tirée indépendamment d'eux. Un tirage peut donc associer une
ossature lourde à un système léger. L'effet est du second ordre (le transport
pèse ~3 % du total), mais c'est à écrire dans les limites plutôt qu'à taire.

────────────────────────────────────────────────────────────────────────────
POURQUOI PAS SOBOL ICI

`agb.incer_stochastic_matrix` reste disponible (`resultats.monte_carlo`) et
donne de vrais indices de Sobol. Mais son plan de Saltelli coûte
n × (2·D + 2) évaluations — pour 4 configurations et ~30 paramètres variables,
c'est deux ordres de grandeur de plus que ce qu'on fait ici.

Ce module utilise à la place les COEFFICIENTS DE RÉGRESSION STANDARDISÉS (SRC),
calculés sur l'échantillon déjà tiré : coût nul, et interprétation directe —
le SRC est la variation de sortie, en écarts-types, produite par une variation
d'un écart-type de l'entrée. Le carré du SRC est la part de variance expliquée
par ce paramètre.

Leur validité tient à une hypothèse : que le modèle soit à peu près linéaire
sur la plage tirée. On ne la suppose pas, on la MESURE — `contributions_variance`
renvoie le R² de la régression. Au-delà de ~0,9, les SRC se lisent comme des
parts de variance. En dessous, il faut passer à Sobol, et la fonction le dit.
"""

from __future__ import annotations

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
import pandas as pd
import lca_algebraic as agb

from . import config, modalites, parametres, systeme

# ── Politique de tirage ────────────────────────────────────────────────────
# Compté, relevé ou conventionnel : figé au tirage. Voir le docstring.
PARAMS_FIGES = (
    "n_modules", "n_onduleurs", "n_ancres", "n_repeteurs",
    "p_install_kwc", "rendement_module", "packing_cellules",
    "duree_vie_an", "maint_par_an",
    # Longueur RELEVÉE au décamètre (60 m enterrés), comme les dénombrements
    # ci-dessus : connue, donc figée. Cf. parametres.py.
    "dist_cable_terre_m",
)

# Masses propres à chaque configuration : loi déclarée, recentrée sur la
# valeur de la configuration. `parametres.PARAMS_PAR_MODALITE` est la source —
# on en retire ce qui est déjà figé ci-dessus.
PARAMS_RELATIFS = tuple(nom for nom in parametres.PARAMS_PAR_MODALITE
                        if nom not in PARAMS_FIGES)

# Paramètres que `modalites.py` renseigne ET dont l'incertitude reste réelle et
# commune aux quatre plateformes : ils sont tirés sur leur propre loi, en
# absolu. C'est la SEULE exception à la règle « ce que la configuration
# renseigne est une donnée » (cf. `echantillon`).
PARAMS_ECHANTILLONNES = ("productible_kwh_kwc_an",)

QUANTILES = (5, 50, 95)

# ── Marqueur du résultat déterministe sur la figure des violons ──────────
# (calibré le 02/10/2026 : la première version tranchait le violon en deux)
# Il portait un losange blanc à fin liéré noir — c'est-à-dire la MÊME masse
# visuelle et la MÊME couleur que le point blanc de la médiane, à quelques
# pixels de distance. Deux marqueurs clairs de taille voisine sur le même axe :
# le lecteur doit comparer les formes pour savoir lequel est lequel.
#
# On change donc de CLASSE de forme, pas de glyphe : une règle HORIZONTALE se
# distingue au premier coup d'œil d'un point rond et d'une barre verticale, et
# elle se lit encore en vignette. Elle déborde légèrement le violon (0,43 contre
# 0,375 de demi-largeur) pour qu'on ne la confonde pas avec un fragment de
# grille, et porte un halo blanc qui la détache de n'importe quelle teinte de
# violon.
#
# Encre quasi noire, et pas une couleur : les quatre violons sont pastels et
# une teinte vive en reprendrait une au hasard. Le noir ne jure avec aucune,
# reste lisible en niveaux de gris et ne pose aucun problème de déficience
# chromatique. C'est l'ORIENTATION qui porte la distinction, pas la couleur.
LARGEUR_VIOLON = 0.75
COULEUR_NOMINAL = "#111111"
# Le trait tient DANS le violon (0,22 contre 0,375 de demi-largeur) et reste
# fin : c'est son ORIENTATION qui le distingue du point rond de la médiane et
# de la barre verticale des percentiles, pas sa masse. Une règle débordante et
# épaisse — la première tentative — coupait la distribution en deux et prenait
# le pas sur la donnée qu'elle annote.
DEMI_REGLE = 0.20
EPAISSEUR_REGLE = 1.6
HALO_REGLE = 2.8           # liseré blanc : lisible sur n'importe quelle teinte


# ══════════════════════════════════════════════════════════════════════════
# 1. Tirage
# ══════════════════════════════════════════════════════════════════════════
def echantillon(ctx, valeurs, n=500, seed=0, methodes=None, verbeux=True):
    """Tire `n` jeux de paramètres POUR UNE CONFIGURATION et calcule les impacts.

    Returns
    -------
    (X, Y) : deux DataFrames de `n` lignes — les paramètres tirés et les
    impacts correspondants. `X` ne contient que les colonnes réellement
    tirées : un paramètre figé n'a pas de variance et n'a rien à faire dans
    une analyse de sensibilité.

    >>> X, Y = incertitude.echantillon(ctx, jeux[REF], n=500, seed=0)
    """
    from lca_algebraic.params import DistributionType

    methodes = methodes or [config.GWP]
    rng = np.random.default_rng(seed)
    _verifier_lois_a_jour(valeurs)

    tirages, colonnes = {}, {}
    figes, donnees, relatifs, absolus = [], [], [], []

    for nom, param in agb.all_params().items():
        fixe = (nom in parametres.SCENARIOS
                or nom in PARAMS_FIGES
                or getattr(param, "distrib", None) == DistributionType.FIXED)
        if fixe:
            tirages[nom] = valeurs.get(nom, param.default)
            figes.append(nom)
            continue

        # ⚠ RÈGLE DE SÉCURITÉ (16/09/2026). Tout paramètre que la configuration
        # RENSEIGNE est une donnée de cette plateforme, et reste à sa valeur —
        # sauf s'il est explicitement déclaré relatif ou échantillonné.
        #
        # Sans cette règle, les paramètres parasol injectés par `modalites.py`
        # (épaisseur de verre, cadre alu surfacique, bifacialité…) tombaient
        # dans la catégorie « absolus » : le tirage les remplaçait par la loi
        # générique de parasol et JETAIT nos mesures. La batterie de tests
        # affichait « 52 paramètres tirés » pour 41 paramètres au modèle —
        # c'est ce qui a mis la puce à l'oreille.
        if (nom in valeurs
                and nom not in PARAMS_RELATIFS
                and nom not in PARAMS_ECHANTILLONNES):
            tirages[nom] = valeurs[nom]
            donnees.append(nom)
            continue

        brut = np.asarray(param.rand(rng.random(n)), dtype=float)
        if nom in PARAMS_RELATIFS and nom in valeurs:
            defaut = float(param.default)
            if defaut == 0:
                raise ValueError(
                    f"« {nom} » est déclaré relatif mais son défaut vaut 0 : "
                    f"impossible de recentrer la loi sur la configuration.")
            brut = brut * (float(valeurs[nom]) / defaut)
            relatifs.append(nom)
        else:
            absolus.append(nom)
        tirages[nom] = brut.tolist()
        colonnes[nom] = brut

    # Les valeurs de la configuration qui ne correspondent à aucun paramètre du
    # registre passent telles quelles : mieux vaut les transmettre que les
    # perdre en silence.
    for nom, valeur in valeurs.items():
        tirages.setdefault(nom, valeur)

    if verbeux:
        print(f"  {n} tirages | {len(colonnes)} paramètres variables "
              f"({len(relatifs)} recentrés, {len(absolus)} absolus) | "
              f"{len(figes)} figés, {len(donnees)} tenus pour données de la "
              f"configuration")

    Y = agb.compute_impacts(ctx.systeme, methodes,
                            functional_unit=ctx.energie, **tirages)
    X = pd.DataFrame(colonnes)
    if len(Y) != n:
        raise RuntimeError(
            f"{len(Y)} résultats pour {n} tirages : `compute_impacts` n'a pas "
            f"vectorisé le tirage comme attendu. Vérifie la version de "
            f"lca_algebraic avant d'utiliser cette distribution.")
    return X, Y.reset_index(drop=True)


def echantillons(ctx, jeux, n=500, seed=0, methodes=None, verbeux=True) -> dict:
    """Le tirage des QUATRE configurations. {libellé: (X, Y)}.

    Chaque configuration reçoit sa propre graine, dérivée de `seed` : les
    tirages restent reproductibles ET indépendants d'une configuration à
    l'autre — utiliser la même graine partout ferait bouger les quatre
    ensemble, ce qui donnerait des écarts trompeusement stables.
    """
    resultat = {}
    for rang, (libelle, valeurs) in enumerate(jeux.items()):
        if verbeux:
            print(f"Monte-Carlo : {libelle}")
        resultat[libelle] = echantillon(ctx, valeurs, n=n, seed=seed + rang,
                                        methodes=methodes, verbeux=verbeux)
    return resultat


# ══════════════════════════════════════════════════════════════════════════
# 2. La bande d'incertitude
# ══════════════════════════════════════════════════════════════════════════
def incertitude(ctx, jeux, n=500, seed=0, methode=None, echs=None,
                quantiles=QUANTILES, verbeux=True) -> pd.DataFrame:
    """Intervalle d'incertitude des 4 configurations, en g CO₂-eq/kWh.

    Une ligne par configuration : le nominal (calcul déterministe), la moyenne
    et les quantiles du tirage, et la demi-largeur relative — le « ± x % » que
    l'on écrit dans l'article.

    La colonne « écart nominal % » mérite un œil : si le nominal n'est pas au
    milieu de la bande, c'est que les lois sont asymétriques (elles le sont) ou
    qu'une plage est mal centrée. Un écart de plus de quelques pour cent est un
    signal, pas un détail.

    >>> tab = incertitude.incertitude(ctx, jeux, n=500, seed=0)
    >>> resultats.figure_gwp(df, incertitudes=tab)
    """
    methode = methode or config.GWP
    echs = echs or echantillons(ctx, jeux, n=n, seed=seed, methodes=[methode],
                                verbeux=verbeux)

    lignes = []
    for libelle, valeurs in jeux.items():
        _, Y = echs[libelle]
        serie = np.asarray(Y.iloc[:, 0], dtype=float) * 1000.0     # g/kWh
        nominal = systeme.gwp_g(ctx, **valeurs)
        q = {f"p{p}": float(np.percentile(serie, p)) for p in quantiles}
        bas, haut = q[f"p{min(quantiles)}"], q[f"p{max(quantiles)}"]

        lignes.append({
            "modalite": libelle,
            "code": modalites.DONNEES.get(libelle, {}).get("code", libelle),
            "nominal g/kWh": nominal,
            "moyenne g/kWh": float(serie.mean()),
            **q,
            "écart-type g/kWh": float(serie.std(ddof=1)),
            "CV %": float(serie.std(ddof=1) / serie.mean() * 100.0),
            "demi-largeur %": (haut - bas) / 2.0 / nominal * 100.0,
            "écart nominal %": (float(np.median(serie)) / nominal - 1.0) * 100.0,
            "n": len(serie),
        })

    tab = pd.DataFrame(lignes)
    tab.attrs["methode"] = methode
    tab.attrs["quantiles"] = tuple(quantiles)
    if verbeux:
        for _, l in tab.iterrows():
            print(f"  {l['code']:8s} {l['nominal g/kWh']:6.1f} g "
                  f"[{l[f'p{min(quantiles)}']:.1f} ; {l[f'p{max(quantiles)}']:.1f}] "
                  f"soit ±{l['demi-largeur %']:.0f} % "
                  f"(CV {l['CV %']:.1f} %, médiane {l['écart nominal %']:+.1f} %)")
    return tab


def figure_incertitude(echs, tab=None, titre=None):
    """Violons des quatre distributions, avec nominal et intervalle.

    Le violon montre la FORME de la distribution — ce qu'une barre d'erreur ne
    dit pas. Les lois triangulaires asymétriques du modèle produisent des
    distributions visiblement penchées, et c'est une information.
    """
    libelles = list(echs)
    series = [np.asarray(echs[l][1].iloc[:, 0], dtype=float) * 1000.0
              for l in libelles]
    codes = [modalites.DONNEES.get(l, {}).get("code", l) for l in libelles]

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    violons = ax.violinplot(series, showextrema=False, widths=LARGEUR_VIOLON)
    for corps, code in zip(violons["bodies"], codes):
        corps.set_facecolor(config.COULEURS.get(code, "#808080"))
        corps.set_alpha(0.75)
        corps.set_edgecolor("white")

    for rang, serie in enumerate(series, start=1):
        bas, median, haut = np.percentile(serie, [5, 50, 95])
        ax.vlines(rang, bas, haut, color="#333333", lw=2.4, zorder=3)
        ax.plot(rang, median, "o", color="white", markersize=6,
                markeredgecolor="#333333", zorder=4)

    if tab is not None:
        for rang, nominal in enumerate(tab["nominal g/kWh"], start=1):
            ax.hlines(nominal, rang - DEMI_REGLE, rang + DEMI_REGLE,
                      color=COULEUR_NOMINAL, lw=EPAISSEUR_REGLE, zorder=6,
                      capstyle="butt",
                      path_effects=[pe.withStroke(linewidth=HALO_REGLE,
                                                  foreground="white")])
        # `hlines` ne produit pas de poignée de légende lisible : on en fabrique
        # une qui ressemble exactement à ce qui est tracé.
        ax.legend(handles=[Line2D([0], [0], color=COULEUR_NOMINAL,
                                  lw=EPAISSEUR_REGLE,
                                  label="Deterministic result")],
                  fontsize=8.5, loc="upper left", framealpha=0.95)

    ax.set_xticks(range(1, len(series) + 1))
    ax.set_xticklabels(codes, fontsize=9.5)
    ax.set_ylabel("GWP100 (g CO₂-eq / kWh)")
    ax.set_title(titre or
                 f"Parameter uncertainty — {len(series[0])} Monte-Carlo runs "
                 f"per configuration\n"
                 "bar = 5th–95th percentile, dot = median, "
                 "horizontal rule = deterministic result")
    ax.grid(axis="y", ls=":", alpha=0.5)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 3. D'où vient la variance — SRC sur le même échantillon
# ══════════════════════════════════════════════════════════════════════════
def contributions_variance(X: pd.DataFrame, Y: pd.DataFrame,
                           colonne=0, seuil_r2=0.90) -> pd.DataFrame:
    """Coefficients de régression standardisés, et le R² qui les valide.

    SRC = coefficient de la régression linéaire sur variables CENTRÉES RÉDUITES.
    Son signe dit le sens de l'effet, son carré la part de variance expliquée.
    La somme des SRC² vaut le R² de la régression : c'est ce qui permet de lire
    la colonne « part de variance % » comme une décomposition — à condition que
    le R² soit élevé.

    `tab.attrs["r2"]` porte ce R², et la fonction prévient si le modèle n'est
    pas assez linéaire pour que la lecture tienne.
    """
    y = np.asarray(Y.iloc[:, colonne], dtype=float)
    noms = [c for c in X.columns if X[c].std(ddof=1) > 0]
    A = X[noms].to_numpy(dtype=float)

    A_std = (A - A.mean(axis=0)) / A.std(axis=0, ddof=1)
    y_std = (y - y.mean()) / y.std(ddof=1)
    beta, *_ = np.linalg.lstsq(A_std, y_std, rcond=None)

    residus = y_std - A_std @ beta
    r2 = float(1.0 - residus.var(ddof=1) / y_std.var(ddof=1))

    # ⚠ « part de variance » = SRC², BRUT, sans renormalisation à 100 %.
    # Avec des régresseurs indépendants la somme vaut le R² ; la forcer à 100
    # masquerait justement ce que la régression n'explique pas, et ferait
    # passer un R² de 0,7 pour une décomposition complète.
    tab = pd.DataFrame({
        "parametre": noms,
        "SRC": beta,
        "|SRC|": np.abs(beta),
        "part de variance %": beta ** 2 * 100.0,
    }).sort_values("|SRC|", ascending=False).reset_index(drop=True)
    tab.attrs["r2"] = r2
    tab.attrs["somme_src2"] = float((beta ** 2).sum())

    if r2 < seuil_r2:
        print(f"  ⚠ R² = {r2:.3f} < {seuil_r2:.2f} : le modèle n'est pas assez "
              f"linéaire sur la plage tirée pour que les SRC se lisent comme "
              f"des parts de variance. Utilise resultats.monte_carlo() "
              f"(indices de Sobol) pour cette configuration.")
    return tab


def variance_modalites(ctx, jeux, n=500, seed=0, methode=None, echs=None,
                       n_parametres=12, verbeux=True) -> pd.DataFrame:
    """Part de variance par paramètre, pour les QUATRE configurations.

    Tableau large : une ligne par paramètre, une colonne par configuration.
    C'est la lecture utile — un paramètre peut dominer sur une plateforme et
    disparaître sur une autre (le câble est partagé par quatre plateformes,
    donc son poids relatif dépend de la puissance installée).
    """
    methode = methode or config.GWP
    echs = echs or echantillons(ctx, jeux, n=n, seed=seed, methodes=[methode],
                                verbeux=verbeux)

    colonnes, r2 = {}, {}
    for libelle, (X, Y) in echs.items():
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        src = contributions_variance(X, Y)
        colonnes[code] = src.set_index("parametre")["part de variance %"]
        r2[code] = src.attrs["r2"]

    tab = pd.DataFrame(colonnes).fillna(0.0)
    tab["moyenne %"] = tab.mean(axis=1)
    tab = tab.sort_values("moyenne %", ascending=False)
    tab.attrs["r2"] = r2
    if n_parametres:
        tab = tab.head(int(n_parametres))
    if verbeux:
        print("  R² de la régression : "
              + " | ".join(f"{c} {v:.3f}" for c, v in r2.items()))
    return tab


def figure_variance_modalites(tab: pd.DataFrame, titre=None):
    """Barres groupées : part de variance par paramètre et par configuration."""
    codes = [c for c in tab.columns if c != "moyenne %"]
    parametres_tries = list(tab.index)[::-1]
    y = np.arange(len(parametres_tries))
    hauteur = 0.8 / len(codes)

    fig, ax = plt.subplots(figsize=(10.5, 0.42 * len(parametres_tries) + 2.4))
    for rang, code in enumerate(codes):
        ax.barh(y + (rang - (len(codes) - 1) / 2) * hauteur,
                tab.loc[parametres_tries, code], height=hauteur,
                color=config.COULEURS.get(code, "#808080"), label=code)

    ax.set_yticks(y)
    ax.set_yticklabels(parametres_tries, fontsize=8.5)
    ax.set_xlabel("Share of output variance (%)")
    r2 = tab.attrs.get("r2", {})
    ax.set_title(titre or
                 "Where the uncertainty comes from — standardised regression "
                 "coefficients\n"
                 + ("linear model R² : "
                    + ", ".join(f"{c} {v:.2f}" for c, v in r2.items())
                    if r2 else ""))
    ax.legend(fontsize=8.5, title="Configuration", title_fontsize=8.5)
    ax.grid(axis="x", ls=":", alpha=0.5)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 4. Sensibilité OAT des quatre configurations
# ══════════════════════════════════════════════════════════════════════════
def tornado_modalites(ctx, jeux, n_parametres=10, verbeux=True) -> pd.DataFrame:
    """Tornado OAT des quatre configurations, dans un seul tableau long.

    Même politique que le tirage : les paramètres figés (dénombrements, plaque,
    durée de vie) ne sont pas balayés, et les paramètres relatifs le sont
    autour de la valeur de LEUR configuration — sinon on balaierait l'écart
    entre plateformes, qui est un scénario et non une incertitude.
    """
    registre = agb.all_params()
    lignes = []
    for libelle, valeurs in jeux.items():
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        if verbeux:
            print("Tornado :", libelle)
        nominal = systeme.gwp(ctx, **valeurs)

        for nom, param in registre.items():
            if nom in PARAMS_FIGES or nom in parametres.SCENARIOS:
                continue
            # Même règle de sécurité que le tirage : ce que la configuration
            # renseigne est une donnée, on ne la balaie pas (sinon on balaierait
            # les paramètres parasol injectés par `modalites.py` autour de leurs
            # valeurs génériques, pas des nôtres).
            if (nom in valeurs and nom not in PARAMS_RELATIFS
                    and nom not in PARAMS_ECHANTILLONNES):
                continue
            mini, maxi = getattr(param, "min", None), getattr(param, "max", None)
            if mini is None or maxi is None:
                continue
            echelle = 1.0
            if nom in PARAMS_RELATIFS and nom in valeurs:
                echelle = float(valeurs[nom]) / float(param.default)
            bas = systeme.gwp(ctx, **{**valeurs, nom: mini * echelle})
            haut = systeme.gwp(ctx, **{**valeurs, nom: maxi * echelle})
            lignes.append({
                "modalite": libelle, "code": code, "parametre": nom,
                "min": min(bas, haut) * 1000.0,
                "max": max(bas, haut) * 1000.0,
                "nominal": nominal * 1000.0,
                "amplitude %": abs(haut - bas) / nominal * 100.0,
            })

    tab = pd.DataFrame(lignes)
    if n_parametres:
        garde = (tab.groupby("parametre")["amplitude %"].max()
                 .nlargest(int(n_parametres)).index)
        tab = tab[tab["parametre"].isin(garde)]
    return tab.sort_values(["code", "amplitude %"])


def figure_tornado_modalites(tab: pd.DataFrame, ncols=2, titre=None):
    """Les quatre tornados en petits multiples, échelle x commune.

    L'échelle commune est le point : sans elle on compare des largeurs de
    barres tracées à des zooms différents, ce qui ne veut rien dire.
    """
    codes = list(dict.fromkeys(tab["code"]))
    nrows = int(np.ceil(len(codes) / ncols))
    ordre = (tab.groupby("parametre")["amplitude %"].max()
             .sort_values().index.tolist())

    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(7.2 * ncols, 0.34 * len(ordre) * nrows + 2.2),
                             sharex=True)
    axes = np.atleast_1d(axes).ravel()
    xmin = float(tab["min"].min()) * 0.98
    xmax = float(tab["max"].max()) * 1.02

    for ax, code in zip(axes, codes):
        part = tab[tab["code"] == code].set_index("parametre").reindex(ordre)
        y = np.arange(len(ordre))
        nominal = float(part["nominal"].dropna().iloc[0])
        ax.barh(y, part["max"] - part["min"], left=part["min"], height=0.68,
                color=config.COULEURS.get(code, "#808080"), alpha=0.9)
        ax.axvline(nominal, color="k", ls="--", lw=1)
        ax.set_yticks(y)
        ax.set_yticklabels(ordre, fontsize=8)
        ax.set_title(f"{code} — {nominal:.1f} g CO₂-eq/kWh", fontsize=10,
                     weight="bold")
        ax.set_xlim(xmin, xmax)
        ax.grid(axis="x", ls=":", alpha=0.5)
        ax.set_axisbelow(True)
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)

    for ax in axes[len(codes):]:
        ax.axis("off")
    for ax in axes[max(0, len(axes) - ncols):]:
        ax.set_xlabel("GWP100 (g CO₂-eq / kWh)")
    fig.suptitle(titre or "One-at-a-time sensitivity — four configurations, "
                          "common scale", fontsize=12, weight="bold")
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 5. Tout d'un coup
# ══════════════════════════════════════════════════════════════════════════
def figures(ctx, jeux, n=500, seed=0, verbeux=True) -> dict:
    """Les figures d'incertitude et de sensibilité. {nom de fichier: Figure}.

    Un seul tirage sert aux trois figures : la bande, la décomposition de
    variance et le tableau. Le tornado, lui, est déterministe.
    """
    echs = echantillons(ctx, jeux, n=n, seed=seed, verbeux=verbeux)
    tab = incertitude(ctx, jeux, echs=echs, verbeux=verbeux)
    variance = variance_modalites(ctx, jeux, echs=echs, verbeux=verbeux)
    tornade = tornado_modalites(ctx, jeux, verbeux=verbeux)
    return {
        "F16_incertitude_4modalites": figure_incertitude(echs, tab),
        "F17_variance_parametres": figure_variance_modalites(variance),
        "F18_tornado_4modalites": figure_tornado_modalites(tornade),
    }


def _verifier_lois_a_jour(valeurs, tolerance=0.01):
    """Les lois ENREGISTRÉES suivent-elles encore les constantes du modèle ?

    ⚠ LE BUG QUE CETTE FONCTION REND IMPOSSIBLE (26/09/2026).

    Les paramètres de `PARAMS_ECHANTILLONNES` sont tirés de la loi DÉCLARÉE,
    pas de la valeur de la configuration : c'est voulu, leur incertitude est
    absolue. Mais cette loi est enregistrée dans le projet Brightway, et une
    ré-exécution de `parametres.declarer()` ne l'écrase pas toujours. Le
    résultat déterministe suivait alors `parametres.PRODUCTIBLE_P0` pendant que
    le Monte-Carlo continuait de tirer autour de l'ancienne valeur : nominal
    56,3 g et médiane des tirages 59,2 g, soit un nominal SOUS son propre
    intervalle. Rien ne le signalait.

    C'est la troisième fois que ce paquet se fait prendre par un nominal hors
    de sa propre loi. Cette fois, ça s'arrête ici.
    """
    from . import parametres as _p
    registre = agb.all_params()
    for nom in PARAMS_ECHANTILLONNES:
        param = registre.get(nom)
        if param is None or nom not in valeurs:
            continue
        declare, attendu = float(param.default), float(valeurs[nom])
        if abs(declare - attendu) > tolerance * max(abs(attendu), 1e-9):
            raise RuntimeError(
                f"« {nom} » : la loi enregistrée est centrée sur {declare:.1f} "
                f"alors que la configuration vaut {attendu:.1f}. Le tirage "
                f"porterait sur une valeur périmée et le nominal tomberait "
                f"hors de son propre intervalle.\n"
                f"   Cause : le paramètre est persisté dans le projet "
                f"Brightway et n'a pas été réécrit.\n"
                f"   Remède : noyau neuf, puis agb.resetParams() avant "
                f"projet.initialiser() pour forcer la redéclaration.")
