"""
Calculs de résultats et figures.

Tout ce qui n'est pas de l'inventaire vit ici : comparaison des modalités,
analyse de contribution, sensibilité, Monte-Carlo, fin de vie.

Principe : on appelle les fonctions NATIVES de lca_algebraic dès qu'elles
existent (`compute_impacts(axis=...)`, `oat_matrix`, `oat_dashboard`,
`incer_stochastic_matrix`, `distrib`) et on n'écrit du code maison que pour les
figures spécifiques au rapport. Les bornes de sensibilité ne sont plus dans un
dictionnaire séparé : elles viennent des `min`/`max` déclarés avec chaque
paramètre (`parametres.py`), donc une figure ne peut plus diverger du modèle.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import lca_algebraic as agb

from . import checks, config, modalites, parametres, systeme


# ══════════════════════════════════════════════════════════════════════════
# 1. Comparaison des 4 modalités
# ══════════════════════════════════════════════════════════════════════════
def comparer_modalites(ctx, jeux, methodes=None) -> pd.DataFrame:
    """Une colonne par modalité, une ligne par catégorie d'impact."""
    methodes = methodes or config.METHODES_EF
    colonnes = {}
    for libelle, valeurs in jeux.items():
        print("Calcul :", libelle)
        res = systeme.impacts(ctx, methodes, **valeurs)
        colonnes[libelle] = res.iloc[0]
    return pd.DataFrame(colonnes)


def _barres_erreur(valeurs_g, incertitudes):
    """Convertit le tableau d'incertitude en `yerr` matplotlib (2 × n).

    Renvoie None si le tableau est absent, ou s'il ne couvre pas exactement les
    colonnes tracées : mieux vaut une figure sans barres d'erreur qu'une figure
    où l'intervalle d'une configuration est posé sur une autre.
    """
    if incertitudes is None or not len(incertitudes):
        return None
    quantiles = incertitudes.attrs.get("quantiles", (5, 50, 95))
    bas_nom, haut_nom = f"p{min(quantiles)}", f"p{max(quantiles)}"
    par_modalite = incertitudes.set_index("modalite")
    if not set(valeurs_g.index).issubset(par_modalite.index):
        manquantes = sorted(set(valeurs_g.index) - set(par_modalite.index))
        print(f"⚠ pas de barres d'erreur : l'incertitude ne couvre pas "
              f"{manquantes}. Relance incertitude.incertitude(ctx, jeux) sur "
              f"le même `jeux` que cette figure.")
        return None
    bas, haut = [], []
    for libelle, nominal in valeurs_g.items():
        ligne = par_modalite.loc[libelle]
        bas.append(max(nominal - float(ligne[bas_nom]), 0.0))
        haut.append(max(float(ligne[haut_nom]) - nominal, 0.0))
    return np.vstack([bas, haut])


def figure_gwp(df: pd.DataFrame, refs=None, titre=None, incertitudes=None):
    """Barres GWP des 4 modalités + repères littérature.

    Parameters
    ----------
    incertitudes : DataFrame, optional
        Le tableau rendu par `incertitude.incertitude(ctx, jeux)`. Passé ici,
        il ajoute sur chaque barre l'intervalle 5-95 % du Monte-Carlo : c'est
        LA figure du § 3 qui porte l'incertitude, plutôt qu'un violon relégué
        en annexe. Les barres d'erreur sont asymétriques — les lois
        triangulaires du modèle le sont — et sont donc tracées telles quelles,
        sans les symétriser en « ± quelque chose ».
    """
    refs = config.REFS_LITTERATURE if refs is None else refs
    ligne = _ligne_gwp(df)
    valeurs_g = df.loc[ligne] * 1000.0

    libelles = [modalites.code(c) if c in modalites.DONNEES else str(c)
                for c in valeurs_g.index]
    couleurs = [config.COULEURS.get(l, "#808080") for l in libelles]

    barres_erreur = _barres_erreur(valeurs_g, incertitudes)

    fig, ax = plt.subplots(figsize=(11, 5))
    barres = ax.bar(range(len(valeurs_g)), valeurs_g.values, color=couleurs)
    if barres_erreur is not None:
        ax.errorbar(range(len(valeurs_g)), valeurs_g.values,
                    yerr=barres_erreur, fmt="none", ecolor="#333333",
                    elinewidth=1.4, capsize=5, capthick=1.4, zorder=5)

    x0 = len(valeurs_g)
    items = list(refs.items())
    barres_ref = ax.bar(range(x0, x0 + len(items)), [v for _, v in items],
                        color="#9b59b6", hatch="//", alpha=0.85, edgecolor="white")
    if items:
        ax.axvline(x0 - 0.5, ls=":", color="grey", lw=1)

    ax.set_xticks(range(x0 + len(items)))
    ax.set_xticklabels(libelles + [l for l, _ in items], fontsize=8)
    ax.set_ylabel("g CO₂-eq / kWh")
    sous_titre = ("FU: 1 kWh delivered | solid = this study (EF v3.1) | "
                  "hatched = literature (indicative)")
    if barres_erreur is not None:
        n_tirages = int(incertitudes["n"].iloc[0])
        sous_titre += (f"\nerror bars: 5th–95th percentile, "
                       f"{n_tirages} Monte-Carlo runs per configuration")
    ax.set_title(titre or "Carbon footprint (GWP100) — four configurations vs "
                          f"literature\n{sous_titre}")
    for b, v in zip(list(barres) + list(barres_ref),
                    list(valeurs_g.values) + [v for _, v in items]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}",
                ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    return fig


def figure_toutes_categories(df: pd.DataFrame):
    """Grille 4×4 : les 16 catégories EF v3.1 pour les 4 modalités."""
    fig, axes = plt.subplots(4, 4, figsize=(20, 18))
    for i, (categorie, valeurs) in enumerate(df.iterrows()):
        ax = axes.flatten()[i]
        libelles = [modalites.code(c) if c in modalites.DONNEES else str(c)
                    for c in valeurs.index]
        ax.bar(range(len(valeurs)), valeurs.values,
               color=[config.COULEURS.get(l, "#808080") for l in libelles])
        ax.set_title(str(categorie).split("[")[0][:44], fontsize=10, weight="bold")
        ax.set_xticks(range(len(valeurs)))
        ax.set_xticklabels(libelles if i >= 12 else [], fontsize=8)
        for x, v in enumerate(valeurs.values):
            ax.text(x, v, f"{v:.2e}", ha="center", va="bottom", fontsize=7)
    for ax in axes.flatten()[len(df):]:
        ax.axis("off")
    fig.suptitle("Environmental footprint — 16 EF v3.1 categories\n"
                 "FU: 1 kWh delivered", fontsize=15, weight="bold")
    plt.tight_layout()
    return fig


def plage_duree_de_vie(ctx, jeux, durees=(20, 30)):
    """GWP de chaque modalité pour plusieurs durées de vie.

    Le productible moyen est réajusté à chaque durée (même formule de
    dégradation), sinon on comparerait deux modèles différents.
    """
    from .parametres import productible_moyen

    lignes = {}
    for duree in durees:
        p_moyen = productible_moyen(parametres.PRODUCTIBLE_P0,
                                    parametres.TAUX_DEGRADATION, duree)
        surcharge = {"duree_vie_an": duree,
                     "productible_kwh_kwc_an": round(p_moyen, 1)}
        colonne = {}
        for libelle, valeurs in jeux.items():
            colonne[libelle] = systeme.gwp_g(ctx, **{**valeurs, **surcharge})
        lignes[f"{duree} ans"] = colonne
    return pd.DataFrame(lignes)


def sensibilite_degradation(ctx, taux=None, duree_vie=None, verbeux=True):
    """GWP des quatre modalités pour chacun des taux de dégradation publiés.

    La dégradation n'est PAS un paramètre incertain au sens du Monte-Carlo, et
    on ne la tire donc pas dans une loi : c'est un choix de SCÉNARIO, et c'est
    ainsi que la guideline Task 12 la traite — une valeur par défaut
    (0,7 %/an) et une variante de sensibilité (0,5 %/an). On y ajoute la
    garantie du fabricant (0,35 %/an), qui est la valeur documentée mais pas
    la valeur opposable.

    Le productible étant au DÉNOMINATEUR de l'unité fonctionnelle, et la
    dégradation n'entrant nulle part ailleurs dans l'inventaire, toutes les
    catégories d'impact se déplacent du même facteur. Ce tableau n'est donc
    pas seulement vrai pour le GWP : son dernier ratio vaut pour les seize.

    >>> resultats.sensibilite_degradation(ctx)
    """
    taux = parametres.TAUX_DEGRADATION_VARIANTES if taux is None else taux
    duree_vie = (parametres.DUREE_VIE_REFERENCE if duree_vie is None
                 else duree_vie)

    lignes, rendements = {}, {}
    for nom, d in taux.items():
        colonne = f"{nom} ({d * 100:.2f} %/yr)"
        p_moyen = parametres.productible_moyen(
            parametres.PRODUCTIBLE_P0, d, duree_vie)
        rendements[colonne] = round(p_moyen, 1)
        if verbeux:
            print(f"Dégradation {d * 100:.2f} %/an -> productible moyen "
                  f"{p_moyen:.1f} kWh/kWc/an")
        jeux = modalites.jeux_de_parametres(ctx, duree_vie=duree_vie,
                                            degradation=d, verbeux=False)
        lignes[colonne] = {libelle: systeme.gwp_g(ctx, **valeurs)
                           for libelle, valeurs in jeux.items()}

    tab = pd.DataFrame(lignes)
    tab.loc["Mean yield (kWh kWp-1 yr-1)"] = pd.Series(rendements)
    _ecarts_a_la_reference(tab)

    if verbeux:
        print("\n  Toutes les catégories d'impact se déplacent du même facteur :")
        print("  la dégradation n'agit que sur le dénominateur.")
    return tab


def _ecarts_a_la_reference(tab):
    """Ajoute une colonne « Δ … » par variante, écart en % à la 1re colonne.

    L'ancienne version ne comparait que la DERNIÈRE colonne à la première :
    juste à trois scénarios, muette dès qu'on en ajoute un quatrième.
    """
    colonnes = list(tab.columns)
    ref = colonnes[0]
    for col in colonnes[1:]:
        tab[f"Δ {col}"] = [
            f"{100 * (tab.loc[i, col] / tab.loc[i, ref] - 1):+.1f} %"
            if tab.loc[i, ref] else "" for i in tab.index]
    return tab


def sensibilite_disponibilite(ctx, taux=None, duree_vie=None, verbeux=True):
    """GWP des quatre modalités pour chaque taux de disponibilité publié.

    Ajouté le 06/10/2026 sur demande du relecteur : 97 % en référence, 100 %
    (le productible reconstruit à pleine disponibilité, § 2.4) en sensibilité.
    Comme la dégradation, la disponibilité n'agit que sur le dénominateur de
    l'unité fonctionnelle : toutes les catégories se déplacent du même facteur.
    La dégradation reste celle de référence (`parametres.TAUX_DEGRADATION`).

    >>> resultats.sensibilite_disponibilite(ctx)
    """
    taux = parametres.TAUX_DISPONIBILITE_VARIANTES if taux is None else taux
    duree_vie = (parametres.DUREE_VIE_REFERENCE if duree_vie is None
                 else duree_vie)

    lignes, rendements = {}, {}
    for nom, a in taux.items():
        colonne = f"{nom} ({a * 100:.0f} %)"
        p0 = parametres.PRODUCTIBLE_P0_PLEINE_DISPO * a
        p_moyen = parametres.productible_moyen(
            p0, parametres.TAUX_DEGRADATION, duree_vie)
        rendements[colonne] = round(p_moyen, 1)
        if verbeux:
            print(f"Disponibilité {a * 100:.0f} % -> 1re année {p0:.1f}, "
                  f"moyen {p_moyen:.1f} kWh/kWc/an")
        jeux = modalites.jeux_de_parametres(ctx, duree_vie=duree_vie, p0=p0,
                                            verbeux=False)
        lignes[colonne] = {libelle: systeme.gwp_g(ctx, **valeurs)
                           for libelle, valeurs in jeux.items()}

    tab = pd.DataFrame(lignes)
    tab.loc["Mean yield (kWh kWp-1 yr-1)"] = pd.Series(rendements)
    _ecarts_a_la_reference(tab)
    return tab


# ══════════════════════════════════════════════════════════════════════════
# 2. Contribution par poste (fonctionnalité native : axis)
# ══════════════════════════════════════════════════════════════════════════
def contribution(ctx, valeurs, methodes=None, verifier=True, exacte=False):
    """Ventilation de l'impact par poste.

    Deux algorithmes, entre lesquels `exacte` arbitre.

    `exacte=False` (défaut) — `compute_impacts(axis="phase")`, la
    fonctionnalité native de lca_algebraic : une seule LCA, très rapide. MAIS
    elle échoue à ventiler les activités de premier plan PARTAGÉES entre deux
    postes tagués : le mix électrique de fabrication de parasol est consommé à
    la fois par la branche panneau et par la branche onduleur, et l'algorithme,
    ne sachant à qui l'imputer, le verse dans `_other_`. D'où les ~11 % non
    attribués sur le GWP — et jusqu'à 53 % sur les catégories dominées par
    l'électricité, comme le rayonnement ionisant.

    `exacte=True` — une LCA par poste de premier niveau, chacune incluant tout
    son amont, multipliée par la quantité consommée. La somme vaut le total PAR
    CONSTRUCTION, puisque le système est une combinaison linéaire de ses
    postes : il n'y a pas de résidu possible. C'est ~9 fois plus lent (9 LCA au
    lieu d'une), donc quelques secondes — négligeable ici.

    ➜ Pour le rapport, utilise `exacte=True`. La version par axe reste utile
    pour un aperçu rapide et pour le contrôle croisé (`comparer_contributions`).
    """
    methodes = methodes or config.METHODES_EF
    if exacte:
        return contribution_directe(ctx, valeurs, methodes)
    df = systeme.impacts(ctx, methodes, axis=config.AXE, **valeurs)
    if verifier:
        checks.verifier_couverture_axes(df)
    return df


# Lignes de TOTAL ajoutées par compute_impacts(axis=...) : à ne jamais tracer
# comme une part du camembert (le nom exact varie selon la version de
# lca_algebraic : « *sum* », « *all* », « _all_ »).
LIGNES_TOTAL = ("*sum*", "*all*", "_all_", "*total*")
# Lignes de RÉSIDU : impact non rattaché à un poste. À garder VISIBLE, mais
# jamais confondu avec un poste.
#   « _other_ » / « *other* » — résidu de `compute_impacts(axis=...)` ;
#   « *ecart* »               — résidu de `contribution_directe`, qui vaut
#                               total − somme des postes (≈ 0 par construction).
# Sans « *ecart* » dans cette liste, la ventilation directe faisait apparaître
# une onzième « catégorie » dans les légendes et les camemberts.
LIGNES_RESTE = ("_other_", "*other*", "*ecart*")


def totaux_axe(df_axe: pd.DataFrame):
    """Sépare (postes, total, résidu non attribué) d'un tableau par axe."""
    total = next((df_axe.loc[i] for i in LIGNES_TOTAL if i in df_axe.index), None)
    reste = next((df_axe.loc[i] for i in LIGNES_RESTE if i in df_axe.index), None)
    postes = df_axe.drop(index=[i for i in LIGNES_TOTAL + LIGNES_RESTE
                                if i in df_axe.index])
    return postes, total, reste


def figure_donut(df_axe: pd.DataFrame, methode=None, titre=None):
    """Camembert de contribution pour une catégorie d'impact.

    La ligne de total (« *sum* ») est retirée — sinon elle occupe la moitié du
    camembert. Le résidu non attribué (« _other_ ») est au contraire CONSERVÉ,
    sous le libellé « Non attribué » : le masquer donnerait une figure qui
    semble complète alors qu'elle ne l'est pas.
    """
    colonne = methode if methode is not None else df_axe.columns[0]
    postes, _, reste = totaux_axe(df_axe)

    serie = postes[colonne]
    if reste is not None and abs(float(reste[colonne])) > 0:
        serie = pd.concat([serie, pd.Series({"Unallocated": float(reste[colonne])})])
    serie = serie[serie.abs() > 0].sort_values(ascending=False)
    total = serie.sum()

    fig = plt.figure(figsize=(12, 6.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.55], wspace=0.02)
    ax_leg = fig.add_subplot(gs[0]); ax_leg.axis("off")
    ax = fig.add_subplot(gs[1]); ax.set_aspect("equal")

    parts, _ = ax.pie(serie.abs().values, labels=None, startangle=90,
                      colors=plt.cm.tab10.colors[:len(serie)],
                      wedgeprops=dict(width=0.42))
    for part, (nom, valeur) in zip(parts, serie.items()):
        pct = valeur / total * 100
        if abs(pct) < 5:
            continue
        angle = np.radians((part.theta1 + part.theta2) / 2)
        ax.annotate(f"{nom}\n{pct:.1f}%",
                    xy=(1.05 * np.cos(angle), 1.05 * np.sin(angle)),
                    xytext=(1.32 * np.cos(angle), 1.32 * np.sin(angle)),
                    fontsize=11, fontweight="bold", ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", color="gray", lw=0.9),
                    annotation_clip=False)
    ax_leg.legend(parts, [f"{n}  —  {v/total*100:.1f}%" for n, v in serie.items()],
                  loc="center", fontsize=11, frameon=True, borderpad=1.0,
                  labelspacing=0.9)
    ax.set_title(titre or f"Contribution by item — {str(colonne).split('[')[0]}",
                 fontsize=13, pad=26)
    plt.subplots_adjust(left=0.01, right=0.93, top=0.86, bottom=0.05)
    return fig


def exporter_figures(ctx, jeux, ref=None, dossier="figures", dpi=300,
                     n_monte_carlo=500, graine=0):
    """Exporte toutes les figures du rapport en PNG haute résolution.

    Les figures du document de référence ont été produites à partir des
    chiffres d'un run donné. Cette fonction les REGÉNÈRE depuis le modèle
    vivant : après toute correction d'inventaire, relancer cet export garantit
    que les figures du rapport correspondent au code, sans retouche manuelle.

    >>> resultats.exporter_figures(ctx, jeux, REF)
    """
    import os

    if ref is not None:
        print("(l'argument « ref » n'a plus d'effet : toutes les modalités "
              "sont exportées)")
    os.makedirs(dossier, exist_ok=True)
    faites = []

    def _sauver(fig, nom):
        chemin = os.path.join(dossier, nom)
        fig.savefig(chemin, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        faites.append(chemin)
        print(f"  {chemin}")

    print(f"Export des figures dans « {dossier}/ » ({dpi} dpi) :")

    # ── Figures qui portent déjà les 4 modalités ──────────────────────────
    df = comparer_modalites(ctx, jeux, [config.GWP])
    _sauver(figure_gwp(df), "F1_gwp_modalites.png")
    _sauver(figure_contribution_postes(ctx, jeux, verbeux=False),
            "F2_contribution_postes_4modalites.png")
    _sauver(figure_barres_100(ctx=ctx, jeux=jeux, verbeux=False),
            "F2b_barres_100_categories_4modalites.png")
    _sauver(figure_fin_de_vie_diptyque(ctx, jeux, verbeux=False),
            "F2c_fin_de_vie_diptyque.png")

    # ── Figures propres à une configuration : produites POUR LES QUATRE ───
    # Il n'y a plus de plateforme de référence : chaque configuration a sa
    # série complète, et les fichiers sont suffixés par son code (SH51…).
    for libelle, valeurs_mod in jeux.items():
        code = modalites.code(libelle) if libelle in modalites.DONNEES \
            else str(libelle)
        slug = code.replace(" ", "_").replace("/", "-")
        print(f"  — configuration {code}")

        # La répartition par catégorie est désormais produite pour les quatre
        # modalités en une seule figure (F2b) : plus besoin d'un fichier par
        # configuration ici.
        _sauver(figure_schema_systeme(ctx, valeurs_mod),
                f"F3_schema_systeme_{slug}.png")

        tornado(ctx, valeurs_mod, figure=True)
        _sauver(plt.gcf(), f"F5_tornado_{slug}.png")

        matrice_elasticite(ctx, valeurs_mod, variation=0.20, figure=True)
        _sauver(plt.gcf(), f"F6_elasticite_{slug}.png")

        eol = comparer_fin_de_vie(ctx, valeurs_mod)
        _sauver(figure_fin_de_vie(eol), f"F7_fin_de_vie_{slug}.png")

    # ── Discussion : CO₂ évité, territoire, littérature ───────────────────
    # Importés ICI et pas en tête de fichier : ces deux modules n'ont rien à
    # faire dans la chaîne de calcul, ils ne servent qu'à l'export. L'import
    # local garde aussi `resultats` utilisable si l'un d'eux est retiré.
    from . import incertitude, litterature, territoire

    # L'incertitude est calculée UNE fois : elle sert aux barres d'erreur de la
    # figure principale (F1, retracée ici) et aux figures F16-F18.
    bande = incertitude.incertitude(ctx, jeux, n=n_monte_carlo, seed=graine,
                                    verbeux=False)
    _sauver(figure_gwp(df, incertitudes=bande), "F1_gwp_modalites.png")

    for nom_fichier, figure in territoire.figures(ctx, jeux,
                                                  verbeux=False).items():
        _sauver(figure, f"{nom_fichier}.png")
    for nom_fichier, figure in litterature.figures(
            ctx, jeux, incertitudes=bande, verbeux=False).items():
        _sauver(figure, f"{nom_fichier}.png")
    for nom_fichier, figure in incertitude.figures(
            ctx, jeux, n=n_monte_carlo, seed=graine, verbeux=False).items():
        _sauver(figure, f"{nom_fichier}.png")

    print(f"{len(faites)} figures exportées.")
    return faites


def figure_schema_systeme(ctx, valeurs, methode=None, titre=None):
    """Schéma en boîtes du système, avec le poids réel de chaque poste.

    Le diagramme classique d'un rapport d'ACV — mais généré À PARTIR DU MODÈLE
    plutôt que dessiné à la main : il ne peut donc pas diverger du code. Chaque
    boîte porte son poste, son unité de couplage et sa contribution au GWP,
    l'intensité de la couleur suivant le poids.

    Préférable au « Graph Explorer » d'Activity Browser pour une figure de
    rapport : AB déplie tout l'arbre ecoinvent (des milliers de nœuds) alors
    qu'ici on montre les 9 postes de premier niveau, qui sont le vrai objet du
    discours.
    """
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    methode = methode or config.GWP
    contrib = contribution_directe(ctx, valeurs, [methode])
    colonne = contrib.columns[0]
    postes = contrib.drop(index=[i for i in ("*total*", "*ecart*")
                                 if i in contrib.index])[colonne].astype(float)
    total = float(postes.sum())
    part = (postes / total * 100).sort_values(ascending=False)

    unites = {"Panneaux": "m² of module", "Onduleurs": "kg",
              "Structure": "kg Al + stainless", "Flotteurs": "kg EPS + MDPE",
              "Ancrage": "kg", "Cable": "kg (share ∝ kWp)", "Maintenance": "visits",
              "Repeteurs": "kg + kWh", "Transport": "t·km",
              # La grandeur qui pilote le poste est un volume de gazole, pas
              # une distance : la manœuvre domine le transit d'un facteur ~270.
              "Chantier": "L of fuel", "FinDeVie": "kg"}

    n = len(part)
    cols = 5
    rows = int(np.ceil(n / cols))
    fig, ax = plt.subplots(figsize=(2.55 * cols, 2.05 * rows + 2.4))
    ax.set_xlim(0, cols); ax.set_ylim(-1.5, rows + 0.4); ax.axis("off")

    cmap = plt.get_cmap("YlOrRd")
    vmax = float(part.max()) or 1.0
    for i, (poste, pct) in enumerate(part.items()):
        c, r = i % cols, rows - 1 - i // cols
        couleur = cmap(0.12 + 0.68 * pct / vmax)
        ax.add_patch(FancyBboxPatch((c + 0.08, r + 0.12), 0.84, 0.72,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.4, edgecolor="#333333",
                                    facecolor=couleur))
        ax.text(c + 0.5, r + 0.63,
                LIBELLES_POSTES.get(str(poste), str(poste)),
                ha="center", va="center",
                fontsize=10.5, weight="bold")
        ax.text(c + 0.5, r + 0.44, f"[{unites.get(str(poste), '')}]",
                ha="center", va="center", fontsize=7.5, style="italic",
                color="#444444")
        ax.text(c + 0.5, r + 0.25, f"{postes[poste]*1000:.2f} g  ({pct:.0f} %)",
                ha="center", va="center", fontsize=9)
        ax.add_patch(FancyArrowPatch((c + 0.5, r + 0.10), (c + 0.5, -0.30),
                                     arrowstyle="-|>", mutation_scale=9,
                                     linewidth=0.8, color="#777777",
                                     shrinkA=0, shrinkB=0, alpha=0.55))

    ax.add_patch(FancyBboxPatch((0.35, -1.15), cols - 0.7, 0.72,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=2.0, edgecolor="#1f4e79",
                                facecolor="#dce9f5"))
    energie = float(agb.compute_expr_value(
        getattr(ctx.energie, "magnitude", ctx.energie), valeurs))
    ax.text(cols / 2, -0.62,
            f"[fpv_lagon] Full PV system  —  {total*1000:.1f} g CO₂-eq / kWh",
            ha="center", va="center", fontsize=11.5, weight="bold")
    ax.text(cols / 2, -0.93,
            f"FU: 1 kWh NET delivered   |   {energie:,.0f} kWh over the lifetime"
            .replace(",", " "),
            ha="center", va="center", fontsize=9, color="#1f4e79")

    ax.set_title(titre or "System architecture and contribution by item (GWP100)",
                 fontsize=13, weight="bold", pad=14)
    plt.tight_layout()
    return fig


def _tableaux_contribution(df_contrib, ctx, jeux, contributions, verbeux):
    """Normalise les trois façons d'alimenter une figure de contribution."""
    if contributions is not None:
        return dict(contributions)
    if ctx is not None and jeux is not None:
        tableaux = {}
        for libelle, valeurs in jeux.items():
            if verbeux:
                print("Contribution :", libelle)
            tableaux[libelle] = contribution(ctx, valeurs, exacte=True)
        return tableaux
    if df_contrib is None:
        raise TypeError(
            "Fournis soit un tableau de contribution en premier argument, "
            "soit ctx= et jeux= pour calculer les quatre modalités, "
            "soit contributions={libellé: tableau}.")
    return {None: df_contrib}


def _parts_100(df_contrib):
    """Passe un tableau de contribution en % par catégorie d'impact."""
    postes, _, reste = totaux_axe(df_contrib)
    if reste is not None and float(abs(reste).max()) > 0:
        postes = pd.concat([postes, reste.to_frame("Unallocated").T])
    return postes.div(postes.sum(axis=0), axis=1) * 100.0


# Titres de catégorie d'impact : la chaîne ecoinvent est en minuscules et
# traîne sa définition après un tiret. On coupe à la définition et on met la
# capitale, sinon une figure de revue affiche « climate change » en bas de
# casse au milieu de titres capitalisés (commentaire du relecteur sur la v4).
_ACRONYMES = ("PM", "EF", "GWP", "ODP", "CTU", "UV")


def _titre_categorie(nom, longueur=34):
    texte = str(nom).split(" - ")[0].split("[")[0].strip()
    if not texte:
        return texte
    mots = []
    for mot in texte.split(" "):
        mots.append(mot if mot.upper() in _ACRONYMES else mot)
    texte = " ".join(mots)
    texte = texte[0].upper() + texte[1:]
    # « human toxicity: non-carcinogenic » -> capitale aussi après les deux-points
    if ": " in texte:
        tete, queue = texte.split(": ", 1)
        texte = tete + ": " + queue[0].upper() + queue[1:]
    return texte[:longueur]


def _palette_postes(postes):
    """Couleur par poste, COMMUNE à toutes les figures du rapport.

    Une couleur attachée au poste et non au rang : c'est la condition pour que
    l'œil puisse comparer quatre panneaux entre eux.
    """
    secours = plt.get_cmap("tab20")(np.linspace(0, 1, 20))
    couleurs, i = {}, 0
    for poste in postes:
        couleur = COULEURS_POSTES.get(str(poste))
        if couleur is None:
            couleur = secours[i % 20]
            i += 1
        couleurs[str(poste)] = couleur
    return couleurs


def figure_barres_100(df_contrib=None, titre=None, ordre=None, *,
                      ctx=None, jeux=None, contributions=None, ncols=2,
                      verbeux=True):
    """Barres empilées à 100 %, une barre par catégorie d'impact.

    Remplace avantageusement le camembert : le camembert ne montre qu'UNE
    catégorie à la fois, alors qu'ici les 16 se lisent d'un coup et se
    comparent entre elles. C'est là que se voient les inversions de hiérarchie
    — la Structure domine le carbone, mais pas forcément l'écotoxicité ou les
    ressources métalliques, et c'est tout l'intérêt d'une ACV multicritère.

    Trois façons de l'appeler :

    >>> resultats.figure_barres_100(ctx=ctx, jeux=jeux)      # les 4 modalités
    >>> resultats.figure_barres_100(                         # une seule
    ...     resultats.contribution(ctx, jeux[REF], exacte=True))
    >>> resultats.figure_barres_100(contributions={"S2": df_s2, "S4": df_s4})

    Avec plusieurs modalités, l'ORDRE des postes, leur COULEUR et l'échelle
    sont communs aux panneaux — sans quoi la comparaison visuelle est
    trompeuse — et la légende est tracée une seule fois pour la figure.
    """
    tableaux = _tableaux_contribution(df_contrib, ctx, jeux, contributions,
                                      verbeux)
    parts = {libelle: _parts_100(df) for libelle, df in tableaux.items()}

    # Ordre des postes commun : moyenne sur toutes les catégories ET toutes
    # les modalités.
    if ordre is None:
        moyennes = pd.DataFrame({lib: p.mean(axis=1) for lib, p in parts.items()})
        ordre = list(moyennes.mean(axis=1).sort_values(ascending=False).index)
    ordre = [p for p in ordre if any(p in part.index for part in parts.values())]

    premier = next(iter(parts.values()))
    categories = [_titre_categorie(c) for c in premier.columns]
    couleurs = _palette_postes(ordre)

    n = len(parts)
    if n == 1:
        nrows, ncols = 1, 1
        figsize = (13, 7)
    else:
        nrows = int(np.ceil(n / ncols))
        figsize = (7.6 * ncols, 0.34 * len(categories) * nrows + 2.6)

    fig, axes = plt.subplots(nrows, ncols, sharex=True, sharey=True,
                             figsize=figsize)
    axes = np.atleast_1d(axes).ravel()
    y = np.arange(len(categories))

    for ax, (libelle, part) in zip(axes, parts.items()):
        bas = np.zeros(len(part.columns))
        for poste in ordre:
            if poste not in part.index:
                continue
            v = part.loc[poste].values.astype(float)
            ax.barh(y, v, left=bas, color=couleurs[str(poste)],
                    label=LIBELLES_POSTES.get(str(poste), str(poste)),
                    edgecolor="white", linewidth=0.5)
            # étiquette seulement si la part est lisible
            for i, (largeur, gauche) in enumerate(zip(v, bas)):
                if largeur >= 6:
                    ax.text(gauche + largeur / 2, i, f"{largeur:.0f}",
                            ha="center", va="center", fontsize=7,
                            color="white", weight="bold")
            bas += v

        ax.set_xlim(0, 100)
        ax.set_yticks(y)
        ax.set_yticklabels(categories, fontsize=8)
        ax.grid(axis="x", ls=":", alpha=0.4)
        ax.set_axisbelow(True)
        if libelle is not None:
            ax.set_title(_libelle_modalite(libelle), fontsize=10.5,
                         weight="bold")

    axes[0].invert_yaxis()
    for ax in axes[n:]:
        ax.axis("off")
    for ax in axes[max(0, n - ncols):n]:
        ax.set_xlabel("share of impact (%)")

    poignees, etiquettes = axes[0].get_legend_handles_labels()
    fig.legend(poignees, etiquettes, loc="center left",
               bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
    fig.suptitle(titre or "Contribution by item — 16 EF v3.1 categories\n"
                          "(100 % stacked bars, FU: 1 kWh delivered)",
                 fontsize=12.5, weight="bold")
    plt.tight_layout(rect=(0, 0, 1, 0.96 if n > 1 else 0.93))
    return fig


# ══════════════════════════════════════════════════════════════════════════
# Contribution par poste, avec le premier contributeur EN ENCART DANS LA BARRE
# ══════════════════════════════════════════════════════════════════════════
#
# L'idée est celle du camembert à deux couronnes (anneau intérieur = poste,
# anneau extérieur = ce qui le compose), transposée en barres : chaque barre
# de poste porte à l'intérieur une barre plus fine pour son ou ses premiers
# contributeurs. On lit d'un coup « les panneaux pèsent 15,8 g, dont 9,1 g de
# cellule silicium », sans avoir besoin d'une seconde figure.
#
# Les quatre modalités sont tracées côte à côte : plus de plateforme de
# référence. L'ordre des postes et l'échelle des x sont communs aux quatre
# panneaux, sinon la comparaison visuelle est trompeuse.

# ── Libellés d'affichage en ANGLAIS ────────────────────────────────────────
#
# Ces tables ne servent QU'À l'affichage des figures. Les CLÉS restent celles du
# modèle (config.PHASES, fin_de_vie.MODALITES, libellés de modalites.DONNEES) :
# rien de ce qui indexe un DataFrame ou un dict n'est renommé, donc le reste du
# package et le notebook continuent de fonctionner à l'identique.

# Scénarios de fin de vie — équivalents anglais de fin_de_vie.LIBELLES, utilisés
# pour les LÉGENDES uniquement. Les colonnes des tableaux gardent leurs noms
# français, pour ne pas casser comparer_fin_de_vie() ni les cellules du notebook.
LIBELLES_SCENARIOS_EN = {
    "enfouissement": "Local landfill (French Polynesia)",
    "recyclage_cutoff": "NZ recycling — cut-off",
    "recyclage_closed_loop": "NZ recycling — closed-loop (credits)",
}

# Les libellés de modalités sont des CLÉS de `jeux` : on ne les renomme pas, on
# se contente de les angliciser au moment de les écrire sur une figure.
_MOTS_MODALITE = {
    "semi-transp.": "semi-transparent",
    "opaque": "opaque",
}


def _libelle_modalite(libelle):
    """Libellé de modalité anglicisé, pour un titre de figure seulement."""
    texte = str(libelle)
    for fr, en in _MOTS_MODALITE.items():
        texte = texte.replace(fr, en)
    return texte


LIBELLES_POSTES = {
    "Panneaux": "PV modules",
    "Onduleurs": "Inverters + wiring",
    "Structure": "Structure (Al + stainless)",
    "Flotteurs": "Floats (EPS + MDPE)",
    "Ancrage": "Mooring",
    "Cable": "Export cable",
    "Maintenance": "Maintenance",
    "Repeteurs": "Wi-Fi repeaters",
    "Transport": "Transport",
    # Les DEUX opérations sous un seul libellé : c'est la formule attendue
    # dans une déclaration de frontière cradle-to-grave, et elle dit au
    # relecteur que ni la pose ni la dépose ne manquent.
    "Chantier": "Installation & decommissioning",
    "FinDeVie": "End of life",
}

# Couleur FIXE par poste : la même dans TOUTES les figures du rapport, sinon
# l'œil compare des couleurs qui ne veulent plus rien dire d'un panneau à
# l'autre.
#
# ⚠ La palette précédente était un dégradé de rouge → jaune trié par poids.
# Deux défauts, rédhibitoires dès qu'on empile (barres à 100 %) :
#   * les six postes secondaires étaient tous dans des ocres voisins,
#     illisibles une fois côte à côte ;
#   * deux paires étaient LITTÉRALEMENT identiques — Maintenance = Transport
#     (#F7DC9B) et Ancrage = FinDeVie (#F9E7B8). Dans une barre empilée, deux
#     segments adjacents de même couleur se lisent comme un seul.
#
# Palette qualitative de Paul Tol (schémas « bright » et « vibrant ») : dix
# teintes distinctes, sûres pour les daltonismes courants (deutéranopie,
# protanopie) et de luminances assez écartées pour rester lisibles en niveaux
# de gris. L'association reste mnémonique quand elle le peut — bleu pour les
# polymères des flotteurs, cuivre pour le câble, gris pour la fin de vie.
COULEURS_POSTES = {
    "Structure": "#CC3311",     # rouge vif — aluminium, poste dominant
    "Panneaux": "#4477AA",      # bleu — silicium et verre
    "Cable": "#EE7733",         # orange cuivré
    "Flotteurs": "#66CCEE",     # cyan — polymères
    "Onduleurs": "#AA3377",     # magenta — électronique
    "Transport": "#228833",     # vert
    "Maintenance": "#CCBB44",   # olive
    "Ancrage": "#009988",       # turquoise
    "FinDeVie": "#666666",      # gris foncé
    "Repeteurs": "#EE99AA",     # rose
    "Chantier": "#997700",      # brun — opération nautique, voisine du gazole
                                # de la maintenance sans se confondre avec
    "Unallocated": "#BBBBBB",  # gris clair — jamais un poste
}

# Noms courts des flux, par mot-clé — du plus spécifique au plus général.
LIBELLES_FLUX = {
    "photovoltaic cell": "Si cell",
    "single-si wafer": "single-Si wafer",
    "multi-si wafer": "multi-Si wafer",
    "solar glass": "solar glass",
    "flat glass": "flat glass",
    "tempering": "glass tempering",
    "aluminium alloy": "Al frame",
    "aluminium, primary": "primary Al",
    "aluminium": "aluminium",
    "chromium steel": "A4 stainless",
    "steel": "galv. steel",
    "copper": "copper",
    "silver": "silver",
    "silicon": "silicon",
    "polystyrene": "EPS foam",
    "polyethylene terephthalate": "PET rope",
    "polyethylene": "MDPE / HDPE",
    "ethylvinylacetate": "EVA",
    "nylon 6": "PA6 pulley",
    "synthetic rubber": "SBR hawser",
    "corrugated board": "packaging",
    "electricity": "electricity",
    "tap water": "fresh water",
    "diesel": "diesel",
    "container ship": "container ship",
    "ferry": "schooner",
    "lorry": "lorry",
    "electronics": "electronics",
    "inverter": "inverter",
    "landfill": "landfill",
    "incineration": "incineration",
}

_CACHE_LCA_FOND = {}       # méthode -> objet bw.LCA réutilisé
_CACHE_SCORES = {}         # (méthode, clé d'activité) -> score unitaire


def _libelle_court(nom, longueur=24):
    """Nom lisible d'un dataset ecoinvent ou parasol."""
    texte = str(nom)
    bas = texte.lower()
    for motif, court in LIBELLES_FLUX.items():
        if motif in bas:
            return court
    for prefixe in (config.PREFIXE, config.PREFIXE_PARASOL,
                    "market group for ", "market for ", "treatment of "):
        texte = texte.replace(prefixe, "")
    return texte[:longueur]


def _score_unitaire_fond(act, methode):
    """Impact d'une unité d'une activité de FOND (non paramétrique).

    `compute_impacts` ne sait travailler que sur des activités de premier plan
    (il refuse explicitement les bases de fond). Pour les datasets ecoinvent on
    passe donc par une LCA Brightway classique, réutilisée d'un appel à l'autre
    — ces scores ne dépendent d'aucun paramètre, ils sont donc valables pour
    les quatre modalités.
    """
    import brightway2 as bw

    cle_methode = tuple(methode)
    cle = (cle_methode, act.key)
    if cle in _CACHE_SCORES:
        return _CACHE_SCORES[cle]

    lca = _CACHE_LCA_FOND.get(cle_methode)
    if lca is not None:
        try:
            lca.redo_lcia({act: 1})
        except Exception:      # noqa: BLE001 — matrice incompatible
            lca = None
    if lca is None:
        lca = bw.LCA({act: 1}, methode)
        lca.lci()
        lca.lcia()
        _CACHE_LCA_FOND[cle_methode] = lca

    _CACHE_SCORES[cle] = float(lca.score)
    return _CACHE_SCORES[cle]


def sous_contributions(ctx, valeurs, methode=None, tolerance=0.02) -> dict:
    """Décompose chaque poste en ses entrées de PREMIER NIVEAU.

    Renvoie `{poste: Series(flux -> impact par kWh)}`, déjà multiplié par la
    quantité de poste consommée par le système : la somme d'une série vaut donc
    la valeur du poste dans `contribution_directe`.

    Les sous-activités de premier plan (cellule PV de parasol, branches de fin
    de vie, électricité locale) passent par `compute_impacts`, donc restent
    paramétriques ; les datasets ecoinvent passent par une LCA statique mise en
    cache.
    """
    from lca_algebraic.params import _getAmountOrFormula
    from .panneaux import _evaluer

    methode = methode or config.GWP
    energie = float(agb.compute_expr_value(
        getattr(ctx.energie, "magnitude", ctx.energie), valeurs))

    detail = {}
    for exc in ctx.systeme.technosphere():
        quantite_poste = _evaluer(_getAmountOrFormula(exc), valeurs)
        if not quantite_poste:
            continue
        poste = exc.input.get(config.AXE) or exc.input["name"]

        flux = {}
        for sous_exc in exc.input.technosphere():
            quantite = _evaluer(_getAmountOrFormula(sous_exc), valeurs)
            if not quantite:
                continue
            cible = sous_exc.input
            if cible["database"] == ctx.db:
                unitaire = float(agb.compute_impacts(
                    cible, [methode], **valeurs).iloc[0, 0])
            else:
                unitaire = _score_unitaire_fond(cible, methode)
            nom = _libelle_court(cible["name"])
            flux[nom] = flux.get(nom, 0.0) + unitaire * quantite * quantite_poste / energie

        serie = pd.Series(flux, dtype=float)
        if poste in detail:
            serie = detail[poste].add(serie, fill_value=0.0)
        detail[poste] = serie.sort_values(ascending=False)

    return detail


def _assombrir(couleur, facteur=0.60):
    import matplotlib.colors as mcolors
    r, v, b = mcolors.to_rgb(couleur)
    return (r * facteur, v * facteur, b * facteur)


def figure_contribution_postes(ctx, jeux, methode=None, n_sous=1, ncols=2,
                               titre=None, unite="g", n_postes_sous=4,
                               verbeux=True):
    """Contribution par poste des QUATRE modalités, contributeur imbriqué.

    Chaque barre de poste porte, en plus foncé et plus fin, la barre de son (ou
    ses `n_sous`) premiers contributeurs : « Panneaux 15,8 g, dont cellule Si
    9,1 g ». C'est l'information qu'apporte la seconde couronne d'un camembert,
    mais lisible sur les quatre configurations à la fois.

    Parameters
    ----------
    jeux :
        Le dict complet des modalités (`modalites.jeux_de_parametres`). Toutes
        sont tracées : il n'y a plus de plateforme de référence.
    n_sous :
        Nombre de contributeurs imbriqués par poste (1 par défaut, 2 lisible).
    """
    methode = methode or config.GWP
    facteur = 1000.0 if unite == "g" else 1.0

    # ── 1. Calculs, modalité par modalité ─────────────────────────────────
    postes_par_modalite, sous_par_modalite, totaux = {}, {}, {}
    for libelle, valeurs in jeux.items():
        if verbeux:
            print("Contribution :", libelle)
        contrib = contribution_directe(ctx, valeurs, [methode])
        colonne = contrib.columns[0]
        serie = contrib.drop(index=[i for i in ("*total*", "*ecart*")
                                    if i in contrib.index])[colonne].astype(float)
        postes_par_modalite[libelle] = serie
        totaux[libelle] = float(serie.sum())
        sous_par_modalite[libelle] = sous_contributions(ctx, valeurs, methode)

    # ── 2. Ordre et échelle COMMUNS aux quatre panneaux ───────────────────
    moyennes = pd.DataFrame(postes_par_modalite).mean(axis=1)
    ordre = list(moyennes.sort_values(ascending=False).index)
    xmax = max(float(s.max()) for s in postes_par_modalite.values()) * facteur

    # Le libellé d'un contributeur va-t-il DANS sa barre foncée ? La décision
    # est prise une fois pour les quatre panneaux (sur la modalité où la barre
    # est la plus étroite), sinon le même poste s'afficherait tantôt dedans,
    # tantôt dehors, et la figure deviendrait pénible à lire en comparaison.
    dedans = {}
    for poste in ordre:
        for rang in range(n_sous):
            largeurs, noms = [], []
            for serie_sous in sous_par_modalite.values():
                s = serie_sous.get(poste)
                if s is None or len(s) <= rang:
                    continue
                largeurs.append(float(s.iloc[rang]) * facteur)
                noms.append(str(s.index[rang]))
            if not largeurs:
                continue
            besoin = xmax * 0.017 * (max(len(n) for n in noms) + 6)
            dedans[(poste, rang)] = min(largeurs) >= besoin

    # ── 3. Tracé ──────────────────────────────────────────────────────────
    n = len(jeux)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, sharex=True,
                             figsize=(7.6 * ncols, 0.46 * len(ordre) * nrows + 2.2))
    axes = np.atleast_1d(axes).ravel()

    for ax, (libelle, serie) in zip(axes, postes_par_modalite.items()):
        total = totaux[libelle]
        detail = sous_par_modalite[libelle]
        y = np.arange(len(ordre))

        for i, poste in enumerate(ordre):
            valeur = float(serie.get(poste, 0.0)) * facteur
            couleur = COULEURS_POSTES.get(poste, "#95A5A6")
            ax.barh(i, valeur, height=0.64, color=couleur,
                    edgecolor="white", linewidth=0.6, zorder=2)

            # ── barres imbriquées : les premiers contributeurs du poste ────
            # Au-delà des `n_postes_sous` premiers postes, la barre mesure moins
            # de 3 % du total : la barre imbriquée y est invisible et son
            # étiquette « of which … » ne fait qu'encombrer la marge. On ne la
            # trace donc que sur les postes qui la portent (commentaire du
            # relecteur sur la v4).
            reportes = []
            sous = detail.get(poste) if i < n_postes_sous else None
            if sous is not None and len(sous):
                gauche = 0.0
                for rang, (nom_flux, part) in enumerate(sous.head(n_sous).items()):
                    largeur = float(part) * facteur
                    if largeur <= 0:
                        continue
                    ax.barh(i, largeur, left=gauche, height=0.28,
                            color=_assombrir(couleur, 0.58 + 0.12 * rang),
                            edgecolor="white", linewidth=0.5, zorder=3)
                    texte = f"{nom_flux} {largeur:.2f}"
                    if dedans.get((poste, rang), False):
                        ax.text(gauche + largeur / 2, i, texte, va="center",
                                ha="center", fontsize=7, color="white",
                                weight="bold", zorder=5)
                    else:
                        reportes.append(texte)
                    gauche += largeur

            # ── une SEULE étiquette à droite : poste + contributeurs reportés
            # (les écrire séparément faisait se chevaucher les textes dès que
            #  le poste était petit)
            etiquette = (f"{valeur:.2f} {unite}   "
                         f"({valeur / (total * facteur) * 100:.1f} %)")
            if reportes:
                etiquette += "   of which " + " · ".join(reportes)
            ax.text(valeur + xmax * 0.012, i, etiquette,
                    va="center", ha="left", fontsize=7.5, zorder=4)

        ax.set_yticks(y)
        ax.set_yticklabels([LIBELLES_POSTES.get(p, str(p)) for p in ordre],
                           fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, xmax * 1.52)      # place pour les étiquettes reportées
        ax.set_title(f"{_libelle_modalite(libelle)}  —  "
                     f"{total * facteur:.2f} {unite} CO₂-eq/kWh",
                     fontsize=10.5, weight="bold")
        ax.grid(axis="x", ls=":", alpha=0.35)
        ax.set_axisbelow(True)
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)

    for ax in axes[n:]:
        ax.axis("off")
    for ax in axes[max(0, n - ncols):n]:
        ax.set_xlabel(f"{unite} CO₂-eq / kWh")

    fig.suptitle(titre or
                 "Contribution by item — the four configurations\n"
                 "light bar = item · nested dark bar = leading contributor · "
                 "FU: 1 kWh delivered",
                 fontsize=12.5, weight="bold")
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def table_contribution_detaillee(ctx, jeux, methode=None, n_sous=3,
                                 unite="g") -> pd.DataFrame:
    """Le même contenu que la figure, en tableau — pour le texte du rapport.

    Une ligne par (modalité, poste), avec la valeur du poste et ses `n_sous`
    premiers contributeurs. Sert aussi de contrôle : `écart` doit être ~0, sinon
    le poste porte des flux qui ne sont pas des entrées technosphère de premier
    niveau (biosphère directe, par exemple).
    """
    methode = methode or config.GWP
    facteur = 1000.0 if unite == "g" else 1.0
    lignes = []

    for libelle, valeurs in jeux.items():
        contrib = contribution_directe(ctx, valeurs, [methode])
        colonne = contrib.columns[0]
        postes = contrib.drop(index=[i for i in ("*total*", "*ecart*")
                                     if i in contrib.index])[colonne].astype(float)
        detail = sous_contributions(ctx, valeurs, methode)
        total = float(postes.sum())

        for poste, valeur in postes.sort_values(ascending=False).items():
            sous = detail.get(poste, pd.Series(dtype=float))
            ligne = {
                "modalite": libelle,
                "poste": LIBELLES_POSTES.get(poste, str(poste)),
                f"poste ({unite}/kWh)": valeur * facteur,
                "part (%)": valeur / total * 100 if total else np.nan,
            }
            for rang, (nom_flux, part) in enumerate(sous.head(n_sous).items(), 1):
                ligne[f"#{rang}"] = nom_flux
                ligne[f"#{rang} ({unite}/kWh)"] = float(part) * facteur
            ligne["ecart"] = (valeur - float(sous.sum())) * facteur
            lignes.append(ligne)

    return pd.DataFrame(lignes).round(3)


# ══════════════════════════════════════════════════════════════════════════
# Élasticité : sensibilité à une variation RELATIVE identique pour tous
# ══════════════════════════════════════════════════════════════════════════
def matrice_elasticite(ctx, valeurs, variation=0.20, methodes=None,
                       parametres_testes=None, figure=True):
    """Élasticité de chaque impact à une variation de ±`variation` de chaque
    paramètre.

    Élasticité = (ΔI/I) / (Δp/p) : « si ce paramètre augmente de 20 %, l'impact
    augmente de X × 20 % ». Une élasticité de 1 signifie proportionnalité
    directe, 0 aucune influence, négative une influence inverse.

    Différence avec `tornado` et `oat_natif`, qui balaient les bornes min/max :
    ici tous les paramètres subissent la MÊME variation relative. On mesure
    donc la sensibilité STRUCTURELLE du modèle, indépendamment de ce qu'on
    croit savoir de l'incertitude de chaque grandeur. Les deux lectures sont
    complémentaires — un paramètre peut être très élastique et pourtant sans
    enjeu parce qu'on le connaît très bien, et inversement.

    Les axes de scénario (enums) sont exclus : ±20 % n'a pas de sens sur eux.
    """
    from . import parametres as P

    methodes = methodes or config.METHODES_EF
    registre = agb.all_params()
    if parametres_testes is None:
        parametres_testes = [nom for nom, param in registre.items()
                             if nom in valeurs
                             and isinstance(valeurs[nom], (int, float))
                             and nom not in P.SCENARIOS
                             and getattr(param, "type", "float") != "enum"]

    base = systeme.impacts(ctx, methodes, **valeurs).iloc[0].astype(float)
    lignes = {}
    for nom in parametres_testes:
        v0 = float(valeurs[nom])
        if v0 == 0:
            continue
        haut = systeme.impacts(ctx, methodes,
                               **{**valeurs, nom: v0 * (1 + variation)}).iloc[0]
        bas = systeme.impacts(ctx, methodes,
                              **{**valeurs, nom: v0 * (1 - variation)}).iloc[0]
        # pente centrée, normalisée : (ΔI/I) / (Δp/p)
        lignes[nom] = ((haut.astype(float) - bas.astype(float))
                       / (2 * variation * base)).replace([np.inf, -np.inf], 0)

    df = pd.DataFrame(lignes).T.fillna(0.0)
    df.columns = [str(c).split(" - ")[0][:34] for c in df.columns]
    df = df.loc[df.abs().max(axis=1).sort_values(ascending=False).index]

    if figure and not df.empty:
        _heatmap_elasticite(df, variation)
    return df


def _heatmap_elasticite(df, variation):
    fig, ax = plt.subplots(figsize=(12, 0.42 * len(df) + 3))
    vmax = float(df.abs().max().max()) or 1.0
    im = ax.imshow(df.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                   aspect="auto")
    ax.set_xticks(range(len(df.columns)))
    ax.set_xticklabels(df.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(df.index)))
    ax.set_yticklabels(df.index, fontsize=8)
    for i in range(len(df.index)):
        for j in range(len(df.columns)):
            v = df.values[i, j]
            if abs(v) >= 0.01:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(v) > 0.55 * vmax else "black")
    ax.set_title(f"Impact elasticity (±{variation:.0%} on each "
                 f"parameter)\n1.00 = direct proportionality", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.6, label="elasticity")
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# Revue des plages et des lois de probabilité
# ══════════════════════════════════════════════════════════════════════════
def apercu_distributions(n=20000, seed=0) -> pd.DataFrame:
    """Tableau de revue de TOUS les paramètres : plage, loi, quantiles tirés.

    Sert à l'exercice « travailler les min/max » : une plage large n'est pas
    neutre, elle décide de la place du paramètre dans le tornado et dans les
    indices de Sobol. Ce tableau met côte à côte ce qu'on a DÉCLARÉ (min, max,
    loi) et ce que ça PRODUIT réellement au tirage (p5, médiane, p95).

    Colonne « demi-plage % » = (max − min) / (2 × défaut) : l'incertitude
    relative implicite. Au-delà de ~20 %, il faut pouvoir la justifier.
    """
    from lca_algebraic.params import DistributionType

    rng = np.random.default_rng(seed)
    lignes = []
    for nom, param in sorted(agb.all_params().items()):
        distrib = getattr(param, "distrib", None)
        mini, maxi = getattr(param, "min", None), getattr(param, "max", None)
        defaut = getattr(param, "default", None)
        ligne = {"paramètre": nom,
                 "groupe": getattr(param, "group", "") or "",
                 "loi": distrib,
                 "min": mini, "défaut": defaut, "max": maxi,
                 "std": getattr(param, "std", None)}
        if isinstance(defaut, (int, float)) and mini is not None and defaut:
            ligne["demi-plage %"] = round((maxi - mini) / (2 * defaut) * 100, 1)
        if distrib and distrib != DistributionType.FIXED:
            try:
                tirages = np.asarray(param.rand(rng.random(n)), dtype=float)
                ligne["p5"] = round(float(np.percentile(tirages, 5)), 3)
                ligne["médiane"] = round(float(np.percentile(tirages, 50)), 3)
                ligne["p95"] = round(float(np.percentile(tirages, 95)), 3)
                ligne["hors bornes %"] = round(
                    float(((tirages < mini) | (tirages > maxi)).mean() * 100), 2
                ) if mini is not None else None
            except Exception:      # noqa: BLE001
                pass
        lignes.append(ligne)
    return pd.DataFrame(lignes).set_index("paramètre")


def contribution_directe(ctx, valeurs, methodes=None) -> pd.DataFrame:
    """Contribution par poste calculée poste par poste — contrôle croisé.

    Pour chaque entrée de 1er niveau du système, on calcule son impact complet
    (amont inclus) et on le multiplie par la quantité consommée. La somme vaut
    le total par construction, puisque le système est une combinaison linéaire
    de ses postes.

    C'est plus lent que `contribution()` (une LCA par poste au lieu d'une), mais
    ça ne dépend pas de l'algorithme d'axe de lca_algebraic. Utile quand la
    ligne « non attribué » de `contribution()` n'est pas négligeable : la
    comparaison des deux tableaux dit exactement quel poste est mal ventilé.
    """
    from lca_algebraic.params import _getAmountOrFormula
    from .panneaux import _evaluer

    methodes = methodes or config.METHODES_EF
    total = systeme.impacts(ctx, methodes, **valeurs).iloc[0]

    lignes = {}
    for exc in ctx.systeme.technosphere():
        quantite = _evaluer(_getAmountOrFormula(exc), valeurs)
        if not quantite:
            continue
        poste = exc.input.get(config.AXE) or exc.input["name"]
        impact = agb.compute_impacts(exc.input, methodes,
                                     functional_unit=ctx.energie,
                                     **valeurs).iloc[0] * quantite
        lignes[poste] = lignes.get(poste, 0) + impact

    df = pd.DataFrame(lignes).T
    df.loc["*total*"] = total
    df.loc["*ecart*"] = total - df.drop(index=["*total*"]).sum()
    return df


def comparer_contributions(ctx, valeurs, methode=None) -> pd.DataFrame:
    """Met côte à côte la ventilation par axe et la ventilation directe.

    Un écart sur une ligne localise le poste dont l'arbre est partagé avec un
    autre poste (l'algorithme d'axe ne sait alors pas à qui l'attribuer).
    """
    methode = methode or config.GWP
    par_axe = contribution(ctx, valeurs, [methode], verifier=False)
    directe = contribution_directe(ctx, valeurs, [methode])

    postes_axe, total_axe, reste_axe = totaux_axe(par_axe)
    colonne = par_axe.columns[0]

    df = pd.DataFrame({
        "par axe (g/kWh)": postes_axe[colonne] * 1000,
        "directe (g/kWh)": directe[colonne] * 1000,
    })
    if reste_axe is not None:
        df.loc["Non attribué (axe)"] = [float(reste_axe[colonne]) * 1000, 0.0]
    df["écart"] = df["par axe (g/kWh)"] - df["directe (g/kWh)"]
    return df.round(3).sort_values("écart", key=abs, ascending=False)


# ══════════════════════════════════════════════════════════════════════════
# 3. Coûts carbone marginaux (kg CO2e par mètre, par kg, par visite…)
# ══════════════════════════════════════════════════════════════════════════
def cout_marginal(ctx, valeurs, parametre, activite=None, methode=None,
                  pas_relatif=0.02, absolu=True):
    """Dérivée de l'impact par rapport à un paramètre : d(impact)/d(paramètre).

    C'est LA bonne façon de répondre à « combien coûte un mètre de câble en
    plus ? ». Deux erreurs classiques qu'elle évite :

    * **reconstruire depuis un pourcentage de contribution.** La part du câble
      inclut le câble sous-marin ET le câble terrestre, dont les masses
      linéiques diffèrent d'un facteur ~15 (4,6 vs 0,29 kg de cuivre/m). Une
      moyenne sur les deux ne veut rien dire ;
    * **lire l'amplitude min↔max du tornado.** Elle mélange l'effet du
      paramètre et la largeur de la borne choisie ; si la relation n'est pas
      linéaire, la pente moyenne n'est pas la pente locale.

    Ici on prend une différence centrée autour du point nominal : c'est la
    pente locale, exacte pour une relation linéaire (ce qui est le cas de tous
    nos flux matière).

    Parameters
    ----------
    activite :
        Activité sur laquelle mesurer. Par défaut le système complet (une
        plateforme). Passer `ctx.postes["Cable"]` pour raisonner sur l'objet
        physique entier, indépendamment de la clé de répartition.
    absolu :
        True  -> résultat en kg CO2-eq par unité de paramètre (impact total) ;
        False -> résultat en kg CO2-eq/kWh par unité de paramètre.
    """
    methode = methode or config.GWP
    cible = ctx.systeme if activite is None else activite
    unite_fonctionnelle = 1 if absolu else ctx.energie

    registre = agb.all_params()
    x = float(valeurs[parametre]) if parametre in valeurs \
        else float(registre[parametre].default)
    pas = abs(x) * pas_relatif or 1e-6

    def impact(valeur):
        return float(agb.compute_impacts(
            cible, [methode], functional_unit=unite_fonctionnelle,
            **{**valeurs, parametre: valeur}).iloc[0, 0])

    return (impact(x + pas) - impact(x - pas)) / (2 * pas)


def _marginal_vectoriel(ctx, valeurs, parametre, methodes, activite=None,
                        absolu=True, pas_relatif=0.02):
    """Dérivée de TOUTES les catégories d'un coup, par différence centrée.

    `cout_marginal` ne prend qu'une méthode : l'appeler seize fois ferait
    trente-deux LCA pour une information que deux suffisent à produire, puisque
    `compute_impacts` évalue toutes les méthodes en une passe. Même différence
    centrée, même pas relatif — seul le nombre d'appels change.
    """
    cible = ctx.systeme if activite is None else activite
    uf = 1 if absolu else ctx.energie

    registre = agb.all_params()
    x = (float(valeurs[parametre]) if parametre in valeurs
         else float(registre[parametre].default))
    pas = abs(x) * pas_relatif or 1e-6

    def impacts(v):
        return agb.compute_impacts(
            cible, methodes, functional_unit=uf,
            **{**valeurs, parametre: v}).iloc[0].values.astype(float)

    return (impacts(x + pas) - impacts(x - pas)) / (2 * pas)


def intensites_cable(ctx, valeurs, methodes=None, verbeux=True) -> pd.DataFrame:
    """Coût marginal d'UN MÈTRE de câble posé, dans les SEIZE catégories.

    `intensites_carbone` ne donne que le carbone. Or le câble porte 72,6 % de
    l'écotoxicité eau douce et 56 % du dommage sanitaire endpoint : la
    discussion a besoin du prix d'un mètre dans ces catégories-là, pas
    seulement en CO2. C'est le chiffre qui permet d'écrire « rapprocher le
    point de raccordement de cent mètres vaut tant » autrement qu'en carbone.

    >>> resultats.intensites_cable(ctx, jeux[REF])

    TROIS COLONNES, TROIS QUESTIONS — et il faut savoir laquelle on cite :

    * **par m (unité de la catégorie)** — impact de L'OBJET PHYSIQUE, mesuré
      sur l'activité `Cable`, dont la quantité de référence est le câble
      ENTIER. La clé de répartition entre plateformes n'y est pas. Répond à
      « combien pèse un mètre de câble ? » ;
    * **par m, effet sur le résultat** — mesuré sur le SYSTÈME complet et
      rapporté à l'unité fonctionnelle, donc clé (prorata P) et productible inclus.
      Répond à « de combien mon résultat publié bouge-t-il ? » ;
    * **% du total par m** — la colonne précédente en pourcent du résultat de
      la plateforme. C'est LA colonne citable : elle dit dans quelles
      catégories la longueur du câble est structurante, et dans lesquelles
      elle ne l'est pas.

    ⚠ UN MÈTRE HORIZONTAL N'EST PAS UN MÈTRE DE CÂBLE. Le câble descend : un
    mètre de distance au rivage en fait un peu plus d'un de câble posé. On
    divise donc par l'allongement, exactement comme `intensites_carbone`, pour
    que la colonne soit bien « par mètre POSÉ ».

    Coût : cinq LCA (système ±pas, câble ±pas, total), pas trente-deux.
    """
    from . import cable

    methodes = methodes or config.METHODES_EF
    categories = [m[1] for m in methodes]
    act_cable = ctx.postes["Cable"]

    def defaut(nom):
        return float(valeurs.get(nom, agb.all_params()[nom].default))

    d, prof = defaut("dist_cable_eau_m"), defaut("profondeur_eau_m")
    allongement = ((cable.longueur_cable_eau_num(d + 1, prof)
                    - cable.longueur_cable_eau_num(d - 1, prof)) / 2.0)

    total = systeme.impacts(ctx, methodes, **valeurs).iloc[0].values.astype(float)
    par_m_objet = _marginal_vectoriel(ctx, valeurs, "dist_cable_eau_m",
                                      methodes, activite=act_cable,
                                      absolu=True) / allongement
    par_m_resultat = _marginal_vectoriel(ctx, valeurs, "dist_cable_eau_m",
                                         methodes, activite=None,
                                         absolu=False) / allongement

    tab = pd.DataFrame({
        "par m (objet)": par_m_objet,
        "par m (resultat/kWh)": par_m_resultat,
        "% du total par m": par_m_resultat / total * 100.0,
    }, index=categories)
    # ⚠ f-string, PAS l'opérateur % : "% pour les %.1f m" % valeur fait lire
    # le « % p » initial comme un spécificateur de format et lève
    # ValueError: unsupported format character 'p'. Corrigé le 05/10/2026.
    longueur_3d = cable.longueur_cable_eau_num(d, prof)
    tab[f"% pour les {longueur_3d:.1f} m"] = tab["% du total par m"] * longueur_3d
    tab = tab.sort_values("% du total par m", ascending=False)

    if verbeux:
        longueur = longueur_3d
        print(f"Coût marginal d'un mètre de câble POSÉ "
              f"({cable.CU_PAR_M:.3f} kg Cu/m, TOP HORN 4G95)")
        print(f"  longueur 3D nominale {longueur:.1f} m | "
              f"allongement {allongement:.3f} m de câble par m horizontal\n")
        apercu = tab[["% du total par m",
                      tab.columns[-1]]].copy()
        apercu.columns = ["% du total / m", f"% du total, les {longueur:.0f} m"]
        print(apercu.round(3).to_string())
        tete = tab.index[0]
        print(f"\n  ➜ Catégorie la plus sensible à la longueur : {tete} "
              f"({tab.loc[tete, '% du total par m']:.3f} % par mètre).")
        print("  ➜ La colonne « par m (objet) » est l'impact du mètre de câble "
              "lui-même,\n    sans la clé de répartition : c'est elle qu'on cite pour parler "
              "du câble, pas du kWh.")
        print("  ⚠ La dernière colonne extrapole la pente locale sur toute la "
              "longueur. Elle\n    doit retomber PRÈS de la part du câble dans "
              "la contribution (72,6 % en\n    écotoxicité eau douce) — c'est "
              "un contrôle de linéarité, pas un résultat\n    à citer tel "
              "quel : le câble porte aussi des termes fixes (connectique,\n"
              "    tronçon enterré) qui ne dépendent pas de la distance au "
              "rivage.")
    return tab


def intensites_carbone(ctx, valeurs, methode=None) -> pd.DataFrame:
    """Coût carbone marginal d'un mètre de câble et d'un mètre de profondeur.

    Deux colonnes, deux questions différentes — et il faut savoir laquelle on
    cite :

    * **kg CO2-eq / m** — impact de l'OBJET PHYSIQUE, mesuré sur l'activité qui
      porte le flux (le câble entier, un ancrage). Répond à « combien pèse un
      mètre de câble ? », indépendamment de la clé de répartition entre
      plateformes et de l'énergie produite.
    * **g CO2-eq/kWh / m** — effet sur le RÉSULTAT PUBLIÉ d'une plateforme,
      mesuré sur le système complet et rapporté à l'unité fonctionnelle. La
      clé de répartition du câble (prorata P) et le productible y sont donc inclus.
      C'est ce chiffre qui répond à « de combien mon résultat bouge-t-il si le
      câble fait un mètre de plus ? ».

    Le rapport entre les deux colonnes n'est pas une simple constante : le
    câble est réparti entre les plateformes au prorata de leur puissance,
    l'ancrage ne l'est pas.

    Chaque ligne est mesurée sur l'activité qui porte réellement le flux, donc
    **ancrage et câble ne sont jamais mélangés** :

    * le câble est mesuré sur l'activité `Cable` (dont la quantité de référence
      est le câble ENTIER — la clé de répartition entre plateformes
      n'intervient pas). Depuis le 15/09/2026 il n'y en a plus qu'UN, le même
      TOP HORN 4G95 en mer puis enterré : les deux lignes « par m posé » et
      « par m enterré » doivent donc donner le MÊME coût marginal, ce qui sert
      de contrôle interne ;
    * l'ancrage est mesuré sur l'activité `Ancrage` (une plateforme, ses
      `n_ancres` lignes) ;
    * la profondeur agit sur les deux, séparément puis cumulé.

    Depuis le découplage de la bathymétrie, `profondeur_eau_m` ne décrit plus
    que la profondeur SOUS LA PLATEFORME : le fond du chenal ne bouge plus.
    Un mètre de fond en plus vaut donc ~1 m de câble (la descente verticale) et
    tan(63°) ≈ 1,96 m de corde par ligne d'ancrage.
    """
    from . import cable, transport

    methode = methode or config.GWP
    act_cable = ctx.postes["Cable"]
    act_ancrage = ctx.postes["Ancrage"]
    n_plateformes = transport.N_PLATEFORMES

    def defaut(nom):
        return float(valeurs.get(nom, agb.all_params()[nom].default))

    def par_kwh(param):
        """d(g CO2-eq/kWh)/d(param), sur le SYSTÈME complet (clé du câble incluse)."""
        return 1000.0 * cout_marginal(ctx, valeurs, param, activite=None,
                                      methode=methode, absolu=False)

    d = defaut("dist_cable_eau_m")
    prof = defaut("profondeur_eau_m")
    n_ancres = defaut("n_ancres")

    # ── Câbles, par mètre ─────────────────────────────────────────────────
    par_m_horizontal = cout_marginal(ctx, valeurs, "dist_cable_eau_m",
                                     activite=act_cable, methode=methode)
    par_m_terre = cout_marginal(ctx, valeurs, "dist_cable_terre_m",
                                activite=act_cable, methode=methode)
    # Un mètre horizontal de plus fait un peu plus d'un mètre de câble posé.
    allongement = ((cable.longueur_cable_eau_num(d + 1, prof)
                    - cable.longueur_cable_eau_num(d - 1, prof)) / 2.0)
    par_m_pose = par_m_horizontal / allongement

    # ── Profondeur, poste par poste ───────────────────────────────────────
    prof_cable = cout_marginal(ctx, valeurs, "profondeur_eau_m",
                               activite=act_cable, methode=methode)
    prof_ancrage = cout_marginal(ctx, valeurs, "profondeur_eau_m",
                                 activite=act_ancrage, methode=methode)

    longueur_3d = cable.longueur_cable_eau_num(d, prof)
    dl_dprof = (cable.longueur_cable_eau_num(d, prof + 0.1)
                - cable.longueur_cable_eau_num(d, prof - 0.1)) / 0.2

    # Contrôle interne : un mètre de câble enterré et un mètre de câble posé,
    # c'est le même câble depuis le 15/09/2026. Les deux dérivées doivent donc
    # coïncider ; un écart non nul signale que les deux tronçons ont divergé.
    ecart_pose_enterre = (par_m_terre / par_m_pose - 1.0) if par_m_pose else float("nan")

    # Effets sur le résultat publié (g CO2-eq/kWh d'UNE plateforme)
    kwh_m_horizontal = par_kwh("dist_cable_eau_m")
    kwh_m_terre = par_kwh("dist_cable_terre_m")
    kwh_profondeur = par_kwh("profondeur_eau_m")   # câble ET ancrage à la fois

    lignes = [
        ("Câble sous-marin — par m posé", par_m_pose,
         kwh_m_horizontal / allongement,
         f"{cable.CU_PAR_M:.3f} kg Cu/m (TOP HORN 4G95, 4 × 95 mm²) ; "
         f"longueur 3D nominale {longueur_3d:.1f} m"),
        ("Câble sous-marin — par m horizontal", par_m_horizontal,
         kwh_m_horizontal,
         f"{allongement:.3f} m de câble posé par m horizontal"),
        ("Câble enterré — par m", par_m_terre, kwh_m_terre,
         f"même TOP HORN que la partie immergée : {cable.CU_PAR_M:.3f} kg Cu/m "
         f"+ {cable.ENV_PAR_M:.3f} kg/m d'enveloppe. Contrôle : doit valoir la "
         f"ligne « par m posé » ({ecart_pose_enterre:+.2%} d'écart)"),
        ("Profondeur — ancrage seul, 1 plateforme", prof_ancrage, None,
         f"{n_ancres:.0f} lignes × tan(63°) = "
         f"{n_ancres * 1.9626:.2f} m de corde par m de profondeur"),
        ("Profondeur — ancrage, par ligne", prof_ancrage / n_ancres, None,
         "une seule ligne d'ancrage"),
        ("Profondeur — câble seul (câble entier)", prof_cable, None,
         f"descente verticale : {dl_dprof:.2f} m de câble par m de profondeur"),
        ("Profondeur — effet total sur une plateforme",
         prof_ancrage + prof_cable * cable.part_cable_num(defaut("p_install_kwc")),
         kwh_profondeur,
         f"ancrage de la plateforme + sa part de câble "
         f"({cable.part_cable_num(defaut('p_install_kwc')):.1%}, prorata P)"),
        ("Profondeur — parc complet",
         prof_ancrage * n_plateformes + prof_cable, None,
         f"{n_plateformes:.0f} ancrages + 1 câble partagé"),
    ]
    return pd.DataFrame(
        [{"grandeur": g, "kg CO2-eq / m": v,
          "g CO2-eq/kWh / m": w, "note": n} for g, v, w, n in lignes]
    ).set_index("grandeur")


# ⚠ NE PAS REMETTRE D'ALIAS ICI. Il y en avait un — `intensites_cable =
# intensites_carbone`, hérité d'un renommage — et comme il était placé APRÈS
# les deux définitions, il écrasait au chargement du module la vraie
# `intensites_cable` définie ligne 1309. Le symptôme : un appel qui renvoie
# un tableau indexé par « grandeur » au lieu des seize catégories, sans la
# moindre erreur. Retiré le 05/10/2026.


# ══════════════════════════════════════════════════════════════════════════
# 4. Sensibilité
# ══════════════════════════════════════════════════════════════════════════
def tornado(ctx, valeurs, parametres_testes=None, methode=None, figure=True):
    """Tornado OAT : chaque paramètre varie de son min à son max déclaré.

    Les bornes proviennent des `min`/`max` de `parametres.py` : il n'y a plus
    de dictionnaire de bornes parallèle à tenir à jour.
    """
    methode = methode or config.GWP
    registre = agb.all_params()
    if parametres_testes is None:
        parametres_testes = [nom for nom in valeurs
                             if nom in registre
                             and getattr(registre[nom], "min", None) is not None]

    nominal = systeme.gwp(ctx, **valeurs)
    lignes = []
    for nom in parametres_testes:
        param = registre[nom]
        bas = systeme.gwp(ctx, **{**valeurs, nom: param.min})
        haut = systeme.gwp(ctx, **{**valeurs, nom: param.max})
        lignes.append({
            "parametre": f"{nom} [{param.min:g} ↔ {param.max:g}]",
            "min": min(bas, haut), "max": max(bas, haut),
            "amplitude_%": abs(haut - bas) / nominal * 100})
    tor = pd.DataFrame(lignes).sort_values("amplitude_%")

    if figure and len(tor):
        fig, ax = plt.subplots(figsize=(10, 0.42 * len(tor) + 2))
        y = range(len(tor))
        ax.barh(y, tor["max"] - tor["min"], left=tor["min"], color="#2196F3", alpha=0.85)
        ax.axvline(nominal, color="k", ls="--", lw=1, label=f"baseline {nominal*1000:.1f} g")
        ax.set_yticks(list(y)); ax.set_yticklabels(tor["parametre"], fontsize=8)
        ax.set_xlabel("GWP100 (kg CO₂-eq/kWh)")
        ax.set_title("One-at-a-time sensitivity — parameter min/max bounds")
        ax.legend(); plt.tight_layout()
    return tor


def oat_natif(ctx, valeurs=None, methodes=None, n=10):
    """Matrice OAT native de lca_algebraic (toutes catégories × paramètres).

    Les axes de scénario en sont exclus : `fin_de_vie` y pesait 55 %, écrasant
    tous les vrais paramètres — comparer trois conventions comptables n'est pas
    une analyse de sensibilité.
    """
    from . import parametres

    if valeurs:
        _figer_hors_analyse(valeurs)
    with parametres.scenarios_figes():
        return agb.oat_matrix(ctx.systeme, methodes or config.METHODES_EF,
                              functional_unit=ctx.energie, n=n)


def oat_dashboard(ctx, methodes=None):
    """Tableau de bord OAT interactif (widget Jupyter natif lca_algebraic)."""
    return agb.oat_dashboard(ctx.systeme, methodes or config.METHODES_EF,
                             functional_unit=ctx.energie)


def monte_carlo(ctx, methodes=None, n=1024):
    """Sobol + Monte-Carlo natifs : les distributions déclarées avec chaque
    paramètre (triangulaire par défaut, bornes min/max) sont utilisées telles
    quelles.

    `n` est le nombre de BASE du plan de Saltelli : le nombre réel
    d'évaluations vaut n × (2·D + 2), où D est le nombre de paramètres non
    fixés (~41 ici) — soit 84 fois plus. Défaut 1024 et non 1000 : SALib
    exige une puissance de 2 pour que les propriétés d'équirépartition de la
    séquence de Sobol soient respectées (c'est l'objet du UserWarning).
    """
    from . import parametres

    with parametres.scenarios_figes() as figes:
        print(f"[MC] axes de scénario figés hors tirage : {', '.join(figes)}")
        return agb.incer_stochastic_matrix(
            ctx.systeme, methodes or config.METHODES_EF,
            functional_unit=ctx.energie, n=n)


# ── Distribution des impacts ───────────────────────────────────────────────
#
# ⚠ POURQUOI ON N'APPELLE PAS `agb.distrib(..., n=...)`
#
# Dans lca_algebraic 1.4.1, `distrib()` N'A PAS de paramètre `n`. Sa signature
# est (model, methods, functional_unit, func_unit_name, Y, nb_cols, axes,
# title, invert, scales, unit_overrides, height, width, **kwargs) : un `n=`
# passé par l'appelant tombe dans `**kwargs`, est ignoré pour
# l'échantillonnage, puis transmis en fin de fonction à `_graph()` — qui ne
# l'accepte pas non plus.
#
# Et à la ligne 1186 du module, quand `Y` n'est pas fourni :
#
#     _, _, Y = _stochastics(model, methods, n=DEFAULT_N * 16, ...)
#
# soit n = 1024 × 16 = 16 384, EN DUR. Avec le plan de Saltelli et nos ~41
# paramètres, cela fait 16 384 × (2×41 + 2) = 1 376 256 évaluations. Pire,
# `_generate_random_params` matérialise les tirages en LISTES PYTHON
# (`param.rand(X[:, i]).tolist()`) : 41 listes de 1,38 million de flottants,
# ~1,8 Go rien que pour les paramètres, avant le moindre calcul d'ACV. D'où le
# noyau tué par l'OOM killer — quelle que soit la valeur de `n` demandée.
#
# La parade : calculer nous-mêmes `Y` avec un `n` maîtrisé, et le PASSER à
# `distrib` via son argument `Y=`, qui court-circuite l'échantillonnage.
#
# Au passage on gagne en justesse : le plan de Saltelli est conçu pour estimer
# des indices de Sobol, pas pour représenter une loi. Sa structure en blocs
# déforme légèrement les marginales. Pour un violon et des quantiles, un
# tirage aléatoire simple est le bon outil — ce n'est pas un pis-aller.


def echantillonner(ctx, n=500, methodes=None, seed=None, verbeux=True):
    """Tire `n` jeux de paramètres et renvoie les impacts correspondants (Y).

    Chaque paramètre est tiré selon SA loi déclarée dans `parametres.py`
    (triangulaire par défaut, bornes min/max), via `ParamDef.rand` — exactement
    la mécanique de lca_algebraic, mais en tirage aléatoire simple et avec un
    `n` qui veut dire quelque chose : n = nombre d'évaluations du modèle.

    `seed` rend le tirage reproductible, ce qui est indispensable dès qu'un
    chiffre issu de cette distribution entre dans le rapport.
    """
    from lca_algebraic.params import DistributionType

    from . import parametres

    methodes = methodes or [config.GWP]
    rng = np.random.default_rng(seed)

    valeurs, variables = {}, []
    for nom, param in agb.all_params().items():
        # Les axes de scénario gardent leur valeur par défaut : ce sont des
        # choix, pas des incertitudes (cf. `parametres.SCENARIOS`).
        if (nom in parametres.SCENARIOS
                or getattr(param, "distrib", None) == DistributionType.FIXED):
            valeurs[nom] = param.default
            continue
        valeurs[nom] = np.asarray(param.rand(rng.random(n))).tolist()
        variables.append(nom)

    if verbeux:
        print(f"[MC] {n} tirages × {len(variables)} paramètres variables "
              f"({len(agb.all_params()) - len(variables)} fixés) — "
              f"{n} évaluations du modèle")
    return agb.compute_impacts(ctx.systeme, methodes,
                               functional_unit=ctx.energie, **valeurs)


def distribution(ctx, methodes=None, n=500, seed=None, **kwargs):
    """Distribution des impacts (violon + statistiques), à `n` maîtrisé.

    >>> resultats.distribution(ctx, [config.GWP], n=500, seed=0)
    """
    methodes = methodes or [config.GWP]
    Y = echantillonner(ctx, n=n, methodes=methodes, seed=seed)
    # Y= court-circuite l'échantillonnage interne de lca_algebraic
    return agb.distrib(ctx.systeme, methodes, functional_unit=ctx.energie,
                       Y=Y, **kwargs)


def _figer_hors_analyse(valeurs):
    """Positionne les valeurs par défaut des paramètres sur la modalité étudiée.

    ⚠ Effet de bord assumé : `oat_matrix` et le Monte-Carlo natifs partent des
    valeurs PAR DÉFAUT des paramètres, pas d'un dict passé en argument. On les
    recale donc sur la modalité étudiée. Relancer `projet.initialiser()` remet
    les défauts d'origine.
    """
    registre = agb.all_params()
    modifies, ignores = 0, []
    for nom, valeur in valeurs.items():
        if nom not in registre:
            continue
        # Les enums et booléens portent des CHAÎNES : il faut les recaler eux
        # aussi. L'ancienne version filtrait sur isinstance(valeur, (int,
        # float)), si bien que le mix électrique de fabrication restait à son
        # défaut parasol (« CN ») pendant toute l'analyse de sensibilité alors
        # que le résultat principal tournait sur le mix européen.
        try:
            registre[nom].default = valeur
            modifies += 1
        except Exception:      # noqa: BLE001 — valeur refusée par le paramètre
            ignores.append(nom)
    print(f"[oat] {modifies} valeurs par défaut recalées sur la modalité étudiée."
          + (f" ({len(ignores)} refusées : {', '.join(ignores)})" if ignores else ""))


# ══════════════════════════════════════════════════════════════════════════
# 4. Fin de vie
# ══════════════════════════════════════════════════════════════════════════
def comparer_fin_de_vie(ctx, valeurs, methodes=None) -> pd.DataFrame:
    """Les trois modalités de fin de vie, toutes catégories d'impact.

    Colonnes 1 et 2 = les deux SCÉNARIOS à présenter (enfouissement, recyclage
    en cut-off). Colonne 3 = le MÊME scénario de recyclage sous la règle
    d'allocation closed-loop, c'est-à-dire la borne basse de l'incertitude
    méthodologique — pas un troisième scénario physique.

    La colonne « fourchette méthodo % » chiffre directement l'écart cut-off ↔
    closed-loop : c'est le nombre à citer dans le rapport pour montrer le poids
    du choix de modélisation du recyclage (Wang 2025 : 31 % sur son cas).
    """
    from .fin_de_vie import LIBELLES

    methodes = methodes or config.METHODES_EF
    colonnes = {}
    for cle in ("enfouissement", "recyclage_cutoff", "recyclage_closed_loop"):
        colonnes[LIBELLES[cle]] = systeme.impacts(
            ctx, methodes, **{**valeurs, "fin_de_vie": cle}).iloc[0]

    df = pd.DataFrame(colonnes)
    enf, cut, cl = (df[LIBELLES[c]] for c in
                    ("enfouissement", "recyclage_cutoff", "recyclage_closed_loop"))
    df["recyclage vs enfouissement %"] = (cut / enf - 1.0) * 100
    df["fourchette methodo %"] = (cl / cut - 1.0) * 100
    return df


def sensibilite_incineration(ctx, jeux=None, methodes=None,
                             verbeux=True) -> pd.DataFrame:
    """Et si les flotteurs étaient incinérés plutôt qu'enfouis ? LES 4 MODALITÉS.

    Sans argument, balaie les quatre configurations et les cinq scénarios de
    fin de vie concernés (référence + les quatre lots d'incinération) :

    >>> tab = resultats.sensibilite_incineration(ctx)

    ⚠ 20 LCA, compter ~3 min. Le tableau renvoyé a la MÊME FORME que celui de
    `donnees_fin_de_vie`, donc les deux se concatènent.

    LES CINQ SCÉNARIOS
      * enfouissement                      — la RÉFÉRENCE, flotteurs en décharge
      * incineration_flotteurs             — EPS + MDPE au feu, CUT-OFF
      * incineration_flotteurs_valorisee   — idem, électricité créditée
      * incineration_polymeres             — + l'élastique SBR (lot Seitz 2026)
      * incineration_polymeres_valorisee   — idem, électricité créditée

    LAQUELLE PUBLIER : « incineration_flotteurs ». Dans le system model
    cut-off, l'électricité et la chaleur d'un incinérateur sont des co-produits
    COUPÉS : elles quittent le système sans charge, à la disposition de qui les
    consomme. Le détenteur du déchet porte toute la combustion et ne reçoit
    rien. Créditer cette électricité est de l'avoided burden, avec la même
    objection qu'au closed-loop — borne basse, pas un résultat.

    POURQUOI L'INCINÉRATION PERD SUR LE CLIMAT, ET C'EST LE RÉSULTAT
    Un polyéthylène enfoui ne se minéralise pas sur l'horizon du GWP100 : son
    carbone fossile reste dans le sol et la décharge se comporte comme un
    stockage. Le brûler le libère intégralement — 3,14 kg CO2 par kg de PE,
    3,38 par kg de PS, c'est de la stœchiométrie. La valorisation ne rattrape
    qu'environ la moitié de l'écart, parce qu'un petit four insulaire ne
    convertit qu'environ 13 % du pouvoir calorifique en électricité nette.

    ⚠ SCÉNARIO PROSPECTIF. La Polynésie française n'a pas d'incinérateur en
    service ; le projet de Nive'e était encore à l'étude en 2025. Cette
    comparaison dit « que se passerait-il si », pas « que fait-on ».
    """
    from . import fin_de_vie as _fdv
    from .fin_de_vie import INCINERATION_SCENARIOS

    if _fdv.INCINERATION_DISPONIBLE is False:
        raise RuntimeError(
            "Les datasets d'incinération n'ont pas été résolus : les quatre "
            "modalités pointent sur la référence et ce tableau ne dirait "
            "rien. Lance ecoinvent.diagnostic_incineration(), corrige "
            "ecoinvent.INCINERATION, puis reconstruis le modèle.")

    # `jeux` accepte le dict des quatre modalités (DÉFAUT), un code ou un
    # libellé pour n'en balayer qu'une, ou un dict de paramètres isolé.
    #
    # Le défaut est volontairement LES QUATRE : une sensibilité qui ne porte
    # que sur S2 ne dit pas si l'effet dépend de la configuration — et ici il
    # en dépend, puisque la masse de flotteurs est la même pour des puissances
    # installées qui vont de 7,9 à 13,05 kWc. L'écart en g/kWh varie donc en
    # 1/kWc, et c'est un contrôle de cohérence gratuit.
    if jeux is None:
        jeux = modalites.jeux_de_parametres(ctx, verbeux=False)
    elif isinstance(jeux, str):
        tous = modalites.jeux_de_parametres(ctx, verbeux=False)
        libelle = _resoudre_modalite(tous, jeux)
        jeux = {libelle: tous[libelle]}
    elif not isinstance(next(iter(jeux.values())), dict):
        jeux = {"(jeu fourni)": jeux}          # un dict de paramètres isolé

    methodes = methodes or config.METHODES_EF
    # ⚠ On zippe POSITIONNELLEMENT les noms de catégorie avec les valeurs, comme
    # `donnees_fin_de_vie` : l'index que renvoie `systeme.impacts` n'a pas le
    # même format selon la version de lca_algebraic, et s'y fier casse.
    categories = [m[1] for m in methodes]
    # Les scénarios suivent `INCINERATION_SCENARIOS` : ajouter une variante
    # là-bas l'ajoute ici, sans retoucher cette fonction.
    cles = ("enfouissement",) + tuple(INCINERATION_SCENARIOS)

    lignes = []
    for libelle_mod, valeurs in jeux.items():
        if verbeux:
            print(f"Fin de vie : {libelle_mod}")
        par_scenario = {}
        for cle in cles:
            res = systeme.impacts(ctx, methodes,
                                  **{**valeurs, "fin_de_vie": cle}).iloc[0]
            par_scenario[cle] = res.values.astype(float)

        reference = par_scenario["enfouissement"]
        for cle in cles:
            for i, categorie in enumerate(categories):
                base = reference[i]
                lignes.append({
                    "modalite": libelle_mod,
                    "code": modalites.DONNEES.get(libelle_mod, {}).get(
                        "code", libelle_mod),
                    "scenario": cle,
                    "categorie": categorie,
                    "valeur": par_scenario[cle][i],
                    "% enfouissement": (par_scenario[cle][i] / base * 100
                                        if base else float("nan")),
                })
    tab = pd.DataFrame(lignes)

    if verbeux:
        _afficher_sensibilite_incineration(ctx, jeux, tab, cles)
    return tab


def _masse_kg(expr, valeurs):
    """Valeur numérique d'une masse symbolique, en kg. Renvoie (valeur, raison).

    ⚠ `panneaux._evaluer` ne suffit PAS ici, et c'est le piège qui a fait
    sortir « non évalué » au premier essai. Il est écrit pour des MONTANTS
    D'ÉCHANGE, qui sont du Sympy nu. Les masses de `structure.masses()`, elles,
    sont des grandeurs PINT (`units_enabled=True`) enveloppant une expression
    Sympy — et `compute_expr_value` ne sait pas lire une Quantity.

    `parametres.magnitude()` existe exactement pour ça : il retire l'unité et
    rend le Sympy nu. On passe donc par lui d'abord, puis par `_evaluer`, puis
    par `float` pour le cas d'une constante. L'échec renvoie SA RAISON plutôt
    qu'un None muet : un `assert` transformait ici une erreur de type en
    AssertionError, ce qui ne disait rien de ce qui n'allait pas.
    """
    from . import parametres as _par
    from .panneaux import _evaluer

    noyau = _par.magnitude(expr)
    valeur = _evaluer(noyau, valeurs)
    if valeur is not None:
        return valeur, None
    try:
        return float(noyau), None
    except Exception as err:                                    # noqa: BLE001
        return None, f"{type(err).__name__}: {str(err)[:60]}"


def _afficher_sensibilite_incineration(ctx, jeux, tab, cles):
    """Lecture à l'écran : le GWP d'abord, puis ce qui sort du lot.

    Seize catégories x cinq scénarios x quatre modalités font 320 nombres :
    les imprimer tous n'informe personne. On affiche donc le GWP en entier —
    c'est le résultat — puis UNIQUEMENT les catégories où l'incinération
    déplace le résultat de plus de 2 %, parce que ce sont les seules qui
    pourraient raconter autre chose que le carbone.
    """
    from .fin_de_vie import (INCINERATION_SCENARIOS, KWH_ELEC_PAR_KG,
                             PCI_MJ_PAR_KG, RENDEMENT_ELEC_INCINERATION,
                             _masses_a_incinerer)

    valeurs_ref = next(iter(jeux.values()))

    # ── Ce qui brûle ──────────────────────────────────────────────────────
    print("\nMasse incinérée par plateforme, sur toute la durée de vie :")
    for lot in dict.fromkeys(f for f, _ in INCINERATION_SCENARIOS.values()):
        brules, echecs = {}, []
        for fraction, expr in _masses_a_incinerer(ctx, lot).items():
            valeur, raison = _masse_kg(expr, valeurs_ref)
            if valeur is None:
                echecs.append(f"{fraction} ({raison})")
            else:
                brules[fraction] = valeur
        if echecs:
            print(f"  {'+'.join(lot):22s} NON ÉVALUÉ : {', '.join(echecs)}")
            continue
        detail = ", ".join(f"{k.upper()} {v:.1f}"
                           for k, v in sorted(brules.items()))
        mj = sum(brules[k] * PCI_MJ_PAR_KG[k] for k in brules)
        kwh = sum(brules[k] * KWH_ELEC_PAR_KG[k] for k in brules)
        print(f"  {'+'.join(lot):22s} {sum(brules.values()):6.1f} kg "
              f"({detail})  ->  {mj / 1000:5.1f} GJ  ->  {kwh:4.0f} kWh "
              f"nets a {RENDEMENT_ELEC_INCINERATION * 100:.1f} %")

    # ── Le GWP, en g/kWh, modalités en colonnes ───────────────────────────
    gwp = (tab[tab.categorie == "climate change"]
           .pivot(index="scenario", columns="code", values="valeur") * 1000)
    gwp = gwp.reindex([c for c in cles if c in gwp.index])
    # `pivot` trie les colonnes alphabétiquement, ce qui donne SH51 avant SH81
    # et casse l'ordre S1..S4 de toutes les autres tables du rapport. On le
    # rétablit depuis l'ordre de `jeux`.
    ordre = [modalites.DONNEES.get(lib, {}).get("code", lib) for lib in jeux]
    gwp = gwp.reindex(columns=[c for c in ordre if c in gwp.columns])
    print("\nChangement climatique, g CO2-eq par kWh net :")
    print(gwp.round(1).to_string())

    if "enfouissement" in gwp.index:
        ref = gwp.loc["enfouissement"]
        print("\n  ecart a l'enfouissement, g CO2-eq/kWh :")
        print((gwp - ref).drop(index="enfouissement").round(2).to_string())
        print("\n  soit en pourcent :")
        print(((gwp / ref - 1.0) * 100).drop(index="enfouissement")
              .round(1).to_string())

    # ── Les autres catégories : seulement celles qui bougent ──────────────
    autres = tab[(tab.categorie != "climate change")
                 & (tab.scenario != "enfouissement")].copy()
    autres["ecart"] = (autres["% enfouissement"] - 100).abs()
    bougent = sorted(autres[autres.ecart > 2.0].categorie.unique())
    print(f"\nAutres categories deplacees de plus de 2 % : "
          f"{len(bougent)} sur {tab.categorie.nunique() - 1}")
    if bougent:
        detail = (autres[autres.categorie.isin(bougent)]
                  .pivot_table(index="categorie", columns="scenario",
                               values="% enfouissement", aggfunc="mean"))
        print((detail - 100).round(1).to_string())
        print("  (% d'ecart a l'enfouissement, moyenne des modalites balayees)")
    else:
        print("  aucune — l'incineration ne deplace QUE le carbone, et c'est "
              "en soi\n  un resultat : le gain de toxicite qu'on pourrait "
              "attendre du feu\n  n'existe pas dans ces methodes.")

    print("\n⚠ Scenario PROSPECTIF : pas d'incinerateur en service en "
          "Polynesie francaise.")
    print("⚠ Publier « incineration_flotteurs ». Les variantes « valorisee » "
          "sont des\n  BORNES (avoided burden sur une base cut-off), pas des "
          "resultats.")
    print("⚠ Aucune de ces categories ne caracterise le microplastique : le "
          "seul effet\n  qui jouerait POUR le feu est hors methode.")


def recette(nom, loc=None, methode=None) -> pd.DataFrame:
    """Ouvre un dataset de fond et renvoie sa RECETTE (flux technosphère).

    L'équivalent en tableau de ce qu'affiche Activity Browser, sans quitter le
    notebook — et avec en prime le GWP au kg de chaque ingrédient, ce qui rend
    la lecture immédiate.

    C'est l'outil pour répondre à « de quoi est fait ce marché ? », par exemple
    pour connaître la part de primaire et de secondaire d'un marché
    d'aluminium au lieu de la déduire d'un facteur d'émission agrégé.

    >>> resultats.recette("market for aluminium, wrought alloy", "GLO")
    """
    import lca_algebraic as agb

    from . import config, ecoinvent, structure

    methode = methode or config.GWP

    # Résolution tolérante : une localisation qui n'existe pas ne doit pas
    # lever une exception qui tue les cellules suivantes, elle doit DIRE
    # quelles localisations existent. (« IAI Area, World » n'existe pas en
    # 3.11 — le monde s'y appelle autrement.)
    candidats = [a for a in ecoinvent._base() if a["name"] == nom]
    if not candidats:
        candidats = [a for a in ecoinvent._base()
                     if nom.lower() in a["name"].lower()]
    if not candidats:
        print(f"Aucun dataset nommé « {nom} ». Essaie "
              f"resultats.datasets_aluminium(motif=...) ou "
              f"ecoinvent.chercher('...').")
        return pd.DataFrame()

    exact = [a for a in candidats if a.get("location") == loc] if loc else []
    if loc and not exact:
        print(f"⚠ « {nom} » n'existe pas en « {loc} ». Localisations "
              f"disponibles :")
        return (pd.DataFrame([{"nom": a["name"], "loc": a.get("location", ""),
                               "unité": a.get("unit", ""),
                               "GWP / unité": structure._gwp_par_kg(a)}
                              for a in candidats])
                .sort_values(["nom", "loc"]).reset_index(drop=True))
    act = exact[0] if exact else candidats[0]
    if len(candidats) > 1 and not loc:
        print(f"({len(candidats)} localisations pour ce nom — "
              f"« {act.get('location','')} » retenue ; précise `loc=` pour "
              f"une autre)")

    print(f"{act['name']} | {act.get('location','')} | {act.get('unit','')} "
          f"| GWP {structure._gwp_par_kg(act)} par unité")

    lignes = []
    for exc in act.technosphere():
        cible = exc.input
        lignes.append({
            "montant": exc.get("amount"),
            "unité": cible.get("unit", ""),
            "activité": cible["name"],
            "loc": cible.get("location", ""),
            "GWP / unité": structure._gwp_par_kg(cible),
        })
    df = pd.DataFrame(lignes)
    if df.empty:
        print("  (aucun flux technosphère — dataset élémentaire ?)")
        return df
    df["contribution"] = (df["montant"] * df["GWP / unité"]).round(4)
    return df.sort_values("contribution", ascending=False,
                          key=abs).reset_index(drop=True)


def datasets_aluminium(ctx=None, motif=None) -> pd.DataFrame:
    """Inventaire des datasets d'aluminium et d'anodisation de la base.

    Version tableau de `ecoinvent.diagnostic_aluminium()` — un DataFrame
    s'affiche correctement dans une cellule, et `resultats` est déjà importé
    dans le notebook (pas besoin d'importer `ecoinvent`).

    >>> resultats.datasets_aluminium()
    >>> resultats.datasets_aluminium(motif="anodising")
    """
    from . import ecoinvent

    familles = [("marché alu", ("market for aluminium",)),
                ("production alu", ("aluminium production",)),
                ("scrap alu", ("aluminium scrap",)),
                ("extrusion / mise en forme", ("extrusion, aluminium",)),
                ("anodisation", ("anodising",))]
    if motif:
        familles = [(motif, (motif.lower(),))]

    lignes = []
    for famille, motifs in familles:
        for act in ecoinvent._base():
            nom = act["name"].lower()
            if not all(m in nom for m in motifs):
                continue
            lignes.append({
                "famille": famille,
                "nom": act["name"],
                "localisation": act.get("location", ""),
                "unité": act.get("unit", ""),
                "signe": ecoinvent.signe_dechet(act),
            })
    df = pd.DataFrame(lignes)
    if df.empty:
        print("Aucun dataset trouvé — vérifie que la base est bien chargée.")
        return df
    return (df.drop_duplicates(subset=["nom", "localisation"])
              .sort_values(["famille", "nom", "localisation"])
              .reset_index(drop=True))


def variante_maintenance(ctx, jeux, rythmes=(15, 26), methode=None,
                         verbeux=True) -> pd.DataFrame:
    """Effet du RYTHME de maintenance, en scénario — pas en incertitude.

    15 nettoyages par an est le choix de conception du protocole ; 26 (un tous
    les quinze jours) est la variante haute qu'on veut pouvoir chiffrer. Ce
    n'est pas la même chose qu'une incertitude : on ne se demande pas combien
    de visites on fera sans le savoir, on compare deux protocoles. D'où une
    section à part, comme pour la durée de vie ou la fin de vie.

    Chaque visite porte l'eau douce de lavage et le gazole de l'embarcation ;
    l'effet est donc linéaire en nombre de visites, et le tableau le montre en
    g CO₂-eq/kWh et en % du total.

    >>> resultats.variante_maintenance(ctx, jeux)
    >>> resultats.variante_maintenance(ctx, jeux, rythmes=(5, 15, 26))
    """
    methode = methode or config.GWP
    reference = rythmes[0]

    lignes = []
    for libelle, valeurs in jeux.items():
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        if verbeux:
            print("Maintenance :", libelle)
        base = None
        for rythme in rythmes:
            gwp = systeme.gwp_g(ctx, **{**valeurs, "maint_par_an": rythme})
            if rythme == reference:
                base = gwp
            lignes.append({
                "modalite": libelle, "code": code,
                "visites/an": rythme,
                "GWP g/kWh": gwp,
                "écart vs référence g/kWh": gwp - base if base is not None else np.nan,
                "écart vs référence %": ((gwp / base - 1) * 100
                                         if base else np.nan),
            })

    tab = pd.DataFrame(lignes)
    tab.attrs["reference"] = reference

    if verbeux:
        for rythme in rythmes[1:]:
            part = tab[tab["visites/an"] == rythme]
            print(f"  {reference} → {rythme} visites/an : "
                  f"{part['écart vs référence g/kWh'].min():+.2f} à "
                  f"{part['écart vs référence g/kWh'].max():+.2f} g/kWh "
                  f"({part['écart vs référence %'].min():+.2f} à "
                  f"{part['écart vs référence %'].max():+.2f} %)")
        # Garde-fou de méthode : une variante de protocole ne doit pas être
        # comptée deux fois, dans ce tableau ET dans la bande d'incertitude.
        # Elle ne l'est que si `maint_par_an` est encore TIRÉ — ce qui n'est
        # plus le cas depuis le 16/09/2026 (il est dans
        # `incertitude.PARAMS_FIGES`). On vérifie donc la politique, pas les
        # bornes : les bornes, elles, décrivent désormais l'étendue du scénario.
        from . import incertitude

        if "maint_par_an" not in incertitude.PARAMS_FIGES:
            param = agb.all_params().get("maint_par_an")
            bornes = (f"[{param.min:g} ; {param.max:g}]"
                      if param is not None else "(inconnues)")
            print(f"  ⚠ maint_par_an est TIRÉ au Monte-Carlo, plage {bornes} : "
                  f"la variante de protocole est donc comptée deux fois, ici "
                  f"et dans la bande d'incertitude. Ajoute-le à "
                  f"incertitude.PARAMS_FIGES.")
    return tab


def figure_variante_maintenance(tab: pd.DataFrame, titre=None):
    """Barres groupées : GWP de chaque configuration, par rythme de nettoyage."""
    rythmes = sorted(tab["visites/an"].unique())
    codes = list(dict.fromkeys(tab["code"]))
    x = np.arange(len(codes))
    largeur = 0.8 / len(rythmes)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for rang, rythme in enumerate(rythmes):
        part = tab[tab["visites/an"] == rythme].set_index("code").reindex(codes)
        barres = ax.bar(x + (rang - (len(rythmes) - 1) / 2) * largeur,
                        part["GWP g/kWh"], width=largeur,
                        color=[config.COULEURS.get(c, "#808080") for c in codes],
                        alpha=0.45 + 0.55 * rang / max(len(rythmes) - 1, 1),
                        edgecolor="white",
                        label=f"{rythme} cleanings / year")
        for barre, ecart in zip(barres, part["écart vs référence %"]):
            if ecart and not np.isnan(ecart) and abs(ecart) > 0.01:
                ax.text(barre.get_x() + barre.get_width() / 2,
                        barre.get_height(), f"{ecart:+.1f} %",
                        ha="center", va="bottom", fontsize=7.5)

    ax.set_xticks(x)
    ax.set_xticklabels(codes, fontsize=9.5)
    ax.set_ylabel("GWP100 (g CO₂-eq / kWh)")
    ax.set_title(titre or "Cleaning schedule — a design scenario, not an "
                          "uncertainty\nlabels: deviation from the "
                          f"{tab.attrs.get('reference', rythmes[0])}-cleanings "
                          "baseline")
    ax.legend(fontsize=8.5)
    ax.grid(axis="y", ls=":", alpha=0.5)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    plt.tight_layout()
    return fig


def variante_aluminium(ctx, valeurs, methodes=None) -> pd.DataFrame:
    """Chiffre les corrections sur l'aluminium de structure.

    Deux colonnes par modalité d'`origine_aluminium` — avec et sans
    anodisation. C'est le tableau à mettre dans le rapport : l'aluminium
    pèse ~45 % du résultat, aucun autre choix de dataset n'a autant d'effet.

    ⚠ RER_SUP suppose le recyclé DÉCLARÉ par le producteur sur la TOTALITÉ
    de l'aluminium : c'est une borne basse, pas une moyenne pondérée.

    ⚠ Le basculement de l'anodisation passe par `structure.ANODISATION`, une
    constante de module : il faut donc RECONSTRUIRE le système entre les deux.
    On ne le fait pas ici (trop lourd) ; la colonne « sans anodisation » est
    obtenue en mettant `surface_anodisee_m2_par_kg` à 0, ce qui revient
    exactement au même.
    """
    methodes = methodes or [config.GWP]
    colonnes = {}
    # Les modalités sont LUES dans le paramètre : ajouter une valeur à
    # l'enum suffit désormais à la faire apparaître dans le tableau.
    origines = getattr(ctx.p.origine_aluminium, "values", None) \
        or ("GLO", "RER", "RER_SUP")
    for origine in origines:
        for libelle, surface in (("avec anodisation", None), ("sans", 0.0)):
            v = {**valeurs, "origine_aluminium": origine}
            if surface is not None:
                v["surface_anodisee_m2_par_kg"] = surface
            try:
                colonnes[f"{origine} — {libelle}"] = systeme.impacts(
                    ctx, methodes, **v).iloc[0]
            except Exception as err:      # noqa: BLE001
                print(f"  ⚠ variante {origine}/{libelle} indisponible : {err}")

    df = pd.DataFrame(colonnes)
    reference = "GLO — sans"          # l'inventaire d'avant ce chantier
    if reference in df.columns:
        for col in list(colonnes):
            if col != reference:
                df[f"Δ% vs {reference}"] = (df[col] / df[reference] - 1) * 100
    return df


def resume_aluminium(ctx, valeurs) -> pd.DataFrame:
    """Le même tableau, en g CO2-eq/kWh — une ligne par variante."""
    df = variante_aluminium(ctx, valeurs, [config.GWP])
    variantes = [c for c in df.columns if not c.startswith("Δ")]
    serie = (df.loc[df.index[0], variantes] * 1000).astype(float)
    out = pd.DataFrame({"g CO2-eq/kWh": serie.round(2)})
    base = float(serie.get("GLO — sans", serie.iloc[0]))
    out["Δ g"] = (serie - base).round(2)
    out["Δ %"] = ((serie / base - 1) * 100).round(1)
    return out


def figure_fin_de_vie(df_eol, reference_litterature=73.3):
    """Deux scénarios en barres + la fourchette méthodologique en moustache.

    Le choix graphique porte le message : la closed-loop n'est pas une
    troisième barre (ce serait la présenter comme un scénario physique
    alternatif), c'est une barre d'erreur sous le recyclage en cut-off.
    """
    from .fin_de_vie import LIBELLES

    ligne = _ligne_gwp(df_eol)
    enf = df_eol.loc[ligne, LIBELLES["enfouissement"]] * 1000
    cut = df_eol.loc[ligne, LIBELLES["recyclage_cutoff"]] * 1000
    cl = df_eol.loc[ligne, LIBELLES["recyclage_closed_loop"]] * 1000

    fig, ax = plt.subplots(figsize=(8, 5))
    barres = ax.bar([0, 1], [enf, cut], color=["#c0392b", "#27ae60"], zorder=2)

    # borne closed-loop = incertitude de choix méthodologique sur le recyclage
    ax.errorbar([1], [cut], yerr=[[max(cut - cl, 0)], [max(cl - cut, 0)]],
                fmt="none", ecolor="#2c3e50", capsize=8, lw=1.6, zorder=3,
                label=f"allocation rule: cut-off ↔ closed-loop "
                      f"({min(cut, cl):.1f} – {max(cut, cl):.1f} g)")
    ax.axhline(reference_litterature, ls=":", color="#8e44ad", lw=1.4, zorder=1,
               label=f"Cromratie Clemons 2021 "
                     f"({reference_litterature:.0f} g, FPV Thailand)")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Landfill\n(French Polynesia, status quo)",
                        "NZ recycling\n(cut-off — reference)"])
    ax.set_ylabel("g CO₂-eq / kWh")
    ax.set_title("Module end of life — cradle to grave")
    for b, v in zip(barres, [enf, cut]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}",
                ha="center", va="bottom")
    ax.legend(fontsize=8, loc="best"); plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# Diptyque fin de vie : le carbone ne discrimine pas, la toxicité si
# ══════════════════════════════════════════════════════════════════════════
#
# Panneau A — GWP, quatre configurations, trois règles. L'écart cut-off ↔
#   closed-loop y est annoté comme une CONVENTION D'ALLOCATION, pas comme un
#   écart physique : c'est le même scénario industriel des deux côtés.
# Panneau B — SH51 seule, sur les quatre catégories où la fin de vie change
#   réellement quelque chose, normalisées à l'enfouissement = 100 %.
#
# Le diptyque porte à lui seul l'argument de la section : sur le climat, le
# choix de filière ne départage rien ; sur la toxicité et les ressources, il
# départage massivement. C'est le prolongement direct du message multicritère.

SCENARIOS_EOL = ("enfouissement", "recyclage_cutoff", "recyclage_closed_loop")

# Le closed-loop est HACHURÉ : signaler visuellement qu'il ne s'agit pas d'un
# troisième scénario physique mais d'une autre façon de compter le même.
STYLES_EOL = {
    "enfouissement": dict(color="#CC3311"),
    "recyclage_cutoff": dict(color="#228833"),
    "recyclage_closed_loop": dict(color="#9CCFA8", hatch="///",
                                  edgecolor="#228833", linewidth=0.9),
}

# Catégories où la fin de vie pèse réellement (panneau B).
CATEGORIES_FIN_DE_VIE = (
    "ecotoxicity: freshwater",
    "human toxicity: non-carcinogenic",
    "human toxicity: carcinogenic",
    "material resources: metals/minerals",
)

LIBELLES_CATEGORIES = {
    "ecotoxicity: freshwater": "Freshwater\necotoxicity",
    "human toxicity: non-carcinogenic": "Human toxicity\nnon-carcinogenic",
    "human toxicity: carcinogenic": "Human toxicity\ncarcinogenic",
    "material resources: metals/minerals": "Metal / mineral\nresources",
    "climate change": "Climate\nchange",
}


def _methode_de_categorie(categorie):
    """Tuple de méthode EF v3.1 correspondant à un nom de catégorie."""
    methode = next((m for m in config.METHODES_EF if m[1] == categorie), None)
    if methode is None:
        raise KeyError(
            f"Catégorie « {categorie} » absente de config.METHODES_EF. "
            f"Disponibles : {sorted({m[1] for m in config.METHODES_EF})}")
    return methode


def _resoudre_modalite(jeux, demandee):
    """Accepte le libellé complet (« S2 (SH51…) ») ou le code (« SH51 »)."""
    if demandee is None:
        return next(iter(jeux))
    if demandee in jeux:
        return demandee
    for libelle in jeux:
        if libelle in modalites.DONNEES and \
                modalites.DONNEES[libelle]["code"] == demandee:
            return libelle
    raise KeyError(f"Modalité « {demandee} » introuvable. "
                   f"Attendu un libellé parmi {list(jeux)} ou un code "
                   f"parmi {[d['code'] for d in modalites.DONNEES.values()]}.")


def donnees_fin_de_vie(ctx, jeux, categories=None, verbeux=True) -> pd.DataFrame:
    """Tableau long : modalité × scénario × catégorie.

    Une ligne par combinaison, avec la valeur absolue et le pourcentage de
    l'enfouissement. C'est CE tableau qu'il faut citer dans le texte : la
    figure n'est qu'une mise en forme.

    >>> tab = resultats.donnees_fin_de_vie(ctx, jeux)
    >>> tab[tab.modalite.str.contains("SH51,")].round(1)
    """
    categories = list(categories or CATEGORIES_FIN_DE_VIE)
    if "climate change" not in categories:
        categories = ["climate change"] + categories
    methodes = [_methode_de_categorie(c) for c in categories]

    from .fin_de_vie import LIBELLES

    lignes = []
    for libelle_mod, valeurs in jeux.items():
        if verbeux:
            print("Fin de vie :", libelle_mod)
        par_scenario = {}
        for cle in SCENARIOS_EOL:
            res = systeme.impacts(ctx, methodes,
                                  **{**valeurs, "fin_de_vie": cle}).iloc[0]
            par_scenario[cle] = res.values.astype(float)

        reference = par_scenario["enfouissement"]
        for cle in SCENARIOS_EOL:
            for i, categorie in enumerate(categories):
                base = reference[i]
                lignes.append({
                    "modalite": libelle_mod,
                    "code": modalites.DONNEES.get(libelle_mod, {}).get(
                        "code", libelle_mod),
                    "scenario": cle,
                    "scenario_libelle": LIBELLES[cle],
                    "categorie": categorie,
                    "valeur": par_scenario[cle][i],
                    "% enfouissement": (par_scenario[cle][i] / base * 100
                                        if base else np.nan),
                })
    return pd.DataFrame(lignes)


def figure_fin_de_vie_diptyque(ctx, jeux, modalite_detail="SH51",
                               categories=None, tableau=None, verbeux=True):
    """Diptyque fin de vie — panneau A (climat, 4 config.) + panneau B (toxicité).

    Parameters
    ----------
    modalite_detail :
        Configuration détaillée au panneau B : code (« SH51 ») ou libellé
        complet.
    tableau :
        Sortie de `donnees_fin_de_vie` déjà calculée, pour ne pas relancer
        douze LCA si tu ajustes seulement la mise en forme.
    """
    from .fin_de_vie import LIBELLES

    categories = list(categories or CATEGORIES_FIN_DE_VIE)
    tab = tableau if tableau is not None else donnees_fin_de_vie(
        ctx, jeux, categories, verbeux=verbeux)
    ref_mod = _resoudre_modalite(jeux, modalite_detail)

    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(14.5, 6.0), gridspec_kw={"width_ratios": [1.05, 1.0]})

    # ── Panneau A : climat, quatre configurations ─────────────────────────
    clim = tab[tab["categorie"] == "climate change"]
    ordre_mod = [m for m in jeux if m in set(clim["modalite"])]
    codes = [modalites.DONNEES.get(m, {}).get("code", str(m)) for m in ordre_mod]

    def _serie(cle):
        s = clim[clim["scenario"] == cle].set_index("modalite")["valeur"]
        return np.array([float(s[m]) * 1000 for m in ordre_mod])

    valeurs_a = {cle: _serie(cle) for cle in SCENARIOS_EOL}
    x = np.arange(len(ordre_mod))
    largeur = 0.26

    for i, cle in enumerate(SCENARIOS_EOL):
        ax_a.bar(x + (i - 1) * largeur, valeurs_a[cle], largeur,
                 label=LIBELLES_SCENARIOS_EN.get(cle, LIBELLES[cle]),
                 zorder=2, **STYLES_EOL[cle])

    cut, closed = valeurs_a["recyclage_cutoff"], valeurs_a["recyclage_closed_loop"]
    for j, xi in enumerate(x):
        x_cut, x_cl = xi, xi + largeur
        # La flèche est tracée au BORD DROIT de la barre closed-loop, pas en
        # son milieu : au milieu elle barrait l'étiquette de valeur.
        x_fleche = x_cl + largeur / 2
        ax_a.plot([x_cut, x_fleche], [cut[j], cut[j]], ls=":", lw=0.9,
                  color="#444444", zorder=4)
        ax_a.annotate("", xy=(x_fleche, cut[j]), xytext=(x_fleche, closed[j]),
                      arrowprops=dict(arrowstyle="<->", color="#444444",
                                      lw=1.1, shrinkA=0, shrinkB=0), zorder=5)
        if cut[j]:
            # Un cartouche blanc derrière le pourcentage : sans lui
            # l'étiquette se perd dans les barres et la grille (commentaire
            # du relecteur sur la v4).
            ax_a.text(x_fleche + 0.045, (cut[j] + closed[j]) / 2,
                      f"−{(1 - closed[j] / cut[j]) * 100:.0f} %", fontsize=7.5,
                      color="#222222", va="center", ha="left", zorder=6,
                      weight="bold",
                      bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                                edgecolor="#BBBBBB", linewidth=0.6,
                                alpha=0.92))

    haut = float(max(valeurs_a["enfouissement"].max(), cut.max()))
    ax_a.annotate("allocation convention\n(same physical scenario)",
                  xy=(x[0] + 1.5 * largeur + 0.05, (cut[0] + closed[0]) / 2),
                  xytext=(x[0] - 0.10, haut * 1.14),
                  fontsize=8.5, style="italic", color="#333333", ha="left",
                  va="center", zorder=6,
                  arrowprops=dict(arrowstyle="-", color="#444444", lw=0.8,
                                  connectionstyle="arc3,rad=-0.2"))

    ax_a.set_xticks(x)
    ax_a.set_xticklabels(codes, fontsize=9.5)
    ax_a.set_ylabel("g CO₂-eq / kWh")
    ax_a.set_ylim(0, haut * 1.28)
    ax_a.set_title("A — Climate change (GWP100)", fontsize=11,
                   weight="bold", loc="left")
    for i, cle in enumerate(SCENARIOS_EOL):
        for xi, v in zip(x + (i - 1) * largeur, valeurs_a[cle]):
            ax_a.text(xi, v, f"{v:.0f}", ha="center", va="bottom", fontsize=7.5,
                      zorder=5)

    # ── Panneau B : toxicité et ressources, normalisées ───────────────────
    detail = tab[(tab["modalite"] == ref_mod) & (tab["categorie"] != "climate change")]
    ordre_cat = [c for c in categories if c != "climate change"]
    xb = np.arange(len(ordre_cat))

    for i, cle in enumerate(SCENARIOS_EOL):
        s = detail[detail["scenario"] == cle].set_index("categorie")["% enfouissement"]
        v = np.array([float(s[c]) for c in ordre_cat])
        ax_b.bar(xb + (i - 1) * largeur, v, largeur, zorder=2, **STYLES_EOL[cle])
        for xi, vi in zip(xb + (i - 1) * largeur, v):
            ax_b.text(xi, vi, f"{vi:.0f}", ha="center", va="bottom",
                      fontsize=7.5, zorder=5)

    ax_b.axhline(100, ls="--", lw=1.0, color="#444444", zorder=3)
    ax_b.set_xticks(xb)
    ax_b.set_xticklabels([LIBELLES_CATEGORIES.get(c, c) for c in ordre_cat],
                         fontsize=8.5)
    ax_b.set_ylabel("% of landfill baseline (= 100)")
    code_ref = modalites.DONNEES.get(ref_mod, {}).get("code", str(ref_mod))
    ax_b.set_title(f"B — {code_ref}, impacts normalised to landfill",
                   fontsize=11, weight="bold", loc="left")

    for ax in (ax_a, ax_b):
        ax.grid(axis="y", ls=":", alpha=0.4)
        ax.set_axisbelow(True)
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)

    poignees, etiquettes = ax_a.get_legend_handles_labels()
    fig.legend(poignees, etiquettes, loc="lower center", ncol=3, fontsize=9.5,
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    plt.tight_layout(rect=(0, 0.06, 1, 1))
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 5. Inspection
# ══════════════════════════════════════════════════════════════════════════
def lister_activites(ctx) -> pd.DataFrame:
    """Toutes les activités de la base de premier plan, avec leur poste."""
    import brightway2 as bw
    lignes = []
    for act in bw.Database(ctx.db):
        lignes.append({
            "nom": act["name"],
            "origine": "parasol" if act["name"].startswith(config.PREFIXE_PARASOL)
                       else ("projet" if act["name"].startswith(config.PREFIXE) else "?"),
            "poste": act.get(config.AXE, ""),
            "unité": act.get("unit", ""),
            "n_flux": len(list(act.technosphere())),
        })
    return pd.DataFrame(lignes).sort_values(["origine", "nom"]).reset_index(drop=True)


def lister_parametres():
    """Tableau de tous les paramètres (natif lca_algebraic)."""
    return agb.list_parameters()


def _ligne_gwp(df):
    for idx in df.index:
        texte = str(idx).lower()
        if "climate change" in texte or "global warming" in texte:
            return idx
    return df.index[0]


# ══════════════════════════════════════════════════════════════════════════
# Camembert à deux couronnes (« sunburst ») — figure demandée sur la v4
# ══════════════════════════════════════════════════════════════════════════
def _eclaircir(couleur, facteur):
    """Mélange la couleur avec du blanc. facteur=0 -> couleur, 1 -> blanc."""
    import matplotlib.colors as mcolors
    r, v, b = mcolors.to_rgb(couleur)
    return (r + (1 - r) * facteur, v + (1 - v) * facteur, b + (1 - b) * facteur)


def _texte_radial(ax, angle_deg, rayon, texte, taille, couleur):
    """Écrit un libellé le long du rayon, tête en haut des deux côtés."""
    rotation = angle_deg
    ha = "center"
    if 90 < angle_deg % 360 < 270:
        rotation = angle_deg + 180
    return ax.text(np.deg2rad(angle_deg), rayon, texte, rotation=rotation,
                   rotation_mode="anchor", ha=ha, va="center", fontsize=taille,
                   color=couleur)


def _sans_parenthese(libelle):
    """« Floats (EPS + MDPE) » -> « Floats ».

    Dans le camembert, la parenthèse du libellé de poste répète ce que la
    couronne extérieure écrit déjà, matière par matière. Elle allonge
    l'étiquette jusqu'à la faire déborder de son anneau, où elle passe sous
    la couronne suivante et devient illisible."""
    texte = str(libelle)
    return texte.split(" (")[0].strip() if " (" in texte else texte


def _retirer_trop_etroites(fig, ax, etiquettes, rayons, angles):
    """Efface les libellés des parts plus étroites que la hauteur du texte.

    Un libellé radial est contraint deux fois : par l'épaisseur de l'anneau
    (sa longueur, traitée par `_ajuster_aux_anneaux`) et par l'ouverture
    angulaire de sa part (sa hauteur). Sur une part de 2 %, un texte de
    8,5 pt mord sur ses deux voisines, et le lecteur ne sait plus à laquelle
    il se rapporte. Mieux vaut pas de libellé qu'un libellé mal attribué :
    le texte de l'article porte ces valeurs.
    """
    fig.canvas.draw()
    rendu = fig.canvas.get_renderer()
    centre = ax.transData.transform((0.0, 0.0))
    bord = ax.transData.transform((0.0, 1.0))
    pixels_par_rayon = float(np.hypot(*(bord - centre)))
    retires = 0
    for texte, rayon, etendue in zip(etiquettes, rayons, angles):
        if texte is None or not texte.get_text():
            continue
        haut = texte.get_window_extent(renderer=rendu).height
        large_angulaire = etendue * rayon * pixels_par_rayon
        if large_angulaire < haut * 1.05:
            texte.set_text("")
            retires += 1
    return retires


def _ajuster_aux_anneaux(fig, ax, etiquettes, epaisseurs, taille_mini=5.5):
    """Réduit les étiquettes qui débordent de leur anneau.

    Un libellé radial s'écrit le long du rayon : rien ne l'empêche de sortir
    de son anneau et de passer sous la couronne voisine. Plutôt que de
    deviner un budget de caractères — qui dépend de la police, de la taille
    de la figure et du texte lui-même — on dessine une fois et on mesure.
    """
    fig.canvas.draw()
    rendu = fig.canvas.get_renderer()
    centre = ax.transData.transform((0.0, 0.0))
    bord = ax.transData.transform((0.0, 1.0))
    pixels_par_rayon = float(np.hypot(*(bord - centre)))

    def longueur(texte):
        """Longueur du texte LE LONG DE SON PROPRE AXE, en pixels.

        `get_window_extent` rend la boîte englobante à l'écran : pour un
        libellé tourné de 45°, cette boîte est bien plus étroite que le
        texte n'est long, et la mesure passe alors qu'il déborde. On le
        remet donc droit le temps de le mesurer.
        """
        angle = texte.get_rotation()
        texte.set_rotation(0)
        large = texte.get_window_extent(renderer=rendu).width
        texte.set_rotation(angle)
        return large

    rognees = 0
    for texte, epaisseur in zip(etiquettes, epaisseurs):
        if texte is None:
            continue
        large = epaisseur * pixels_par_rayon
        for _ in range(8):
            if longueur(texte) <= large:
                break
            taille = texte.get_fontsize() * 0.92
            if taille < taille_mini:
                # on a atteint le plancher lisible : on coupe le texte
                contenu = texte.get_text()
                if len(contenu) <= 6:
                    break
                texte.set_text(contenu[:-2].rstrip(" .") + "…")
                continue
            texte.set_fontsize(taille)
            rognees += 1
    return rognees


def figure_camembert(ctx, valeurs, methode=None, titre=None, unite="g",
                     seuil_interne=3.0, seuil_externe=1.5, verbeux=True):
    """Contribution en deux couronnes : les postes, puis leurs matières.

    ─────────────────────────────────────────────────────────────────────
    POURQUOI CETTE FIGURE EN PLUS DES BARRES

    `figure_contribution_postes` compare QUATRE configurations et répond à
    « laquelle est la meilleure ». Ce camembert n'en montre qu'UNE et répond
    à une autre question : « de quoi est faite cette empreinte, matière par
    matière ». La couronne intérieure porte les postes, l'extérieure les flux
    qui les composent, et la somme des deux est la même — d'où le total au
    centre, qui sert de contrôle visuel.

    C'est la forme retenue par Frehner et al. pour l'installation alpine ;
    la reprendre rend les deux études directement comparables à l'œil.

    ⚠ Un camembert ne se lit bien QUE parce que chaque part porte son
    étiquette et sa valeur. Les parts sous `seuil_*` (en % du total) ne sont
    donc pas étiquetées : elles restent tracées, mais leur nom encombrerait
    plus qu'il n'informerait. Le texte de l'article doit citer les valeurs.

    Le seuil intérieur est à 3 % et non à 2 % : à 2 %, la maintenance et le
    transport reçoivent un libellé aussi long que l'anneau est épais, posé
    sur une part de huit degrés, et le lecteur ne sait plus lequel des deux
    il lit. Les parts de la couronne extérieure sous `seuil_externe` sont
    réunies en un « Rest » plutôt que laissées en copeaux non nommés.

    Les couleurs sont celles de TOUTES les autres figures (`COULEURS_POSTES`),
    et la couronne extérieure décline la teinte de son poste du foncé au
    clair : l'identité d'un poste reste lisible d'une figure à l'autre.
    """
    methode = methode or config.GWP
    facteur = 1000.0 if unite == "g" else 1.0

    directe = contribution_directe(ctx, valeurs, [methode])
    colonne = directe.columns[0]
    postes = (directe[colonne].drop(index=["*total*", "*ecart*"], errors="ignore")
              .sort_values(ascending=False))
    postes = postes[postes > 0] * facteur
    total = float(postes.sum())

    detail = sous_contributions(ctx, valeurs, methode)

    fig, ax = plt.subplots(figsize=(9.5, 8.4),
                           subplot_kw=dict(projection="polar"))
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.axis("off")

    R_INT, R_EXT = (0.42, 0.72), (0.72, 1.00)
    ECART = np.deg2rad(0.6)           # le filet blanc entre deux parts

    angle = 0.0
    etiquettes, epaisseurs, rayons, ouvertures = [], [], [], []
    for poste, valeur in postes.items():
        etendue = 2 * np.pi * valeur / total
        couleur = COULEURS_POSTES.get(str(poste), "#95A5A6")
        part = valeur / total * 100

        ax.bar(x=angle + etendue / 2, height=R_INT[1] - R_INT[0],
               width=max(etendue - ECART, etendue * 0.5), bottom=R_INT[0],
               color=couleur, edgecolor="white", linewidth=1.4, zorder=2)
        if part >= seuil_interne:
            nom = _sans_parenthese(LIBELLES_POSTES.get(str(poste), poste))
            etiquettes.append(_texte_radial(
                ax, np.rad2deg(angle + etendue / 2),
                (R_INT[0] + R_INT[1]) / 2,
                f"{nom}  {valeur:.1f} {unite}", 8.5, "white"))
            epaisseurs.append(R_INT[1] - R_INT[0])
            rayons.append((R_INT[0] + R_INT[1]) / 2)
            ouvertures.append(etendue)

        # ── couronne extérieure : les flux de ce poste ────────────────────
        sous = detail.get(poste)
        if sous is None or not len(sous):
            angle += etendue
            continue
        sous = sous[sous > 0].sort_values(ascending=False) * facteur
        if sous.sum() > 0:
            sous = sous * (valeur / float(sous.sum()))     # boucler sur le poste
        # Les flux sous le seuil d'étiquetage sont dessinés mais jamais
        # nommés : une dizaine de copeaux d'un millimètre qui se lisent comme
        # du bruit. On les réunit en un « Rest », comme le fait Frehner et al.
        # Rien n'est perdu : la somme du poste est la même.
        menus = sous[sous / total * 100 < seuil_externe]
        if len(menus) > 1:
            sous = sous[sous / total * 100 >= seuil_externe]
            sous = pd.concat([sous, pd.Series({"Rest": float(menus.sum())})])
            sous = sous.sort_values(ascending=False)
        a2 = angle
        for rang, (flux, v) in enumerate(sous.items()):
            e2 = 2 * np.pi * float(v) / total
            ax.bar(x=a2 + e2 / 2, height=R_EXT[1] - R_EXT[0],
                   width=max(e2 - ECART * 0.7, e2 * 0.5), bottom=R_EXT[0],
                   color=_eclaircir(couleur, min(0.12 + 0.16 * rang, 0.78)),
                   edgecolor="white", linewidth=1.0, zorder=2)
            if float(v) / total * 100 >= seuil_externe:
                etiquettes.append(_texte_radial(
                    ax, np.rad2deg(a2 + e2 / 2),
                    (R_EXT[0] + R_EXT[1]) / 2,
                    f"{flux} {float(v):.1f}", 7.5, "#222222"))
                epaisseurs.append(R_EXT[1] - R_EXT[0])
                rayons.append((R_EXT[0] + R_EXT[1]) / 2)
                ouvertures.append(e2)
            a2 += e2
        angle += etendue

    ax.set_ylim(0, R_EXT[1])
    ax.text(0, 0, f"{total:.0f} {unite} CO₂-eq\nper kWh", ha="center",
            va="center", fontsize=13, weight="bold", zorder=5)
    fig.suptitle(titre or "Contribution by item and by material\n"
                 "inner ring: life cycle item · outer ring: its material flows",
                 fontsize=12, weight="bold", y=0.97)
    fig.text(0.5, 0.025,
             f"Outer-ring flows below {seuil_externe:.1f} % of the total are "
             f"pooled as \u00ab Rest \u00bb. Slices too narrow to carry a "
             f"legible label are drawn unlabelled; their values are given in "
             f"the text.",
             ha="center", fontsize=7.5, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    rognees = _ajuster_aux_anneaux(fig, ax, etiquettes, epaisseurs)
    retires = _retirer_trop_etroites(fig, ax, etiquettes, rayons, ouvertures)
    if verbeux:
        print(f"  camembert : {len(postes)} postes, total {total:.1f} {unite}/kWh"
              + (f", {rognees} étiquette(s) réduite(s)" if rognees else "")
              + (f", {retires} retirée(s) faute de place" if retires else ""))
    return fig
