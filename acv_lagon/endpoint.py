"""
Lecture ENDPOINT (ReCiPe 2016, perspective H) — EN PARALLÈLE du midpoint.

════════════════════════════════════════════════════════════════════════════
CE QUE CE MODULE EST, ET CE QU'IL N'EST PAS

Le résultat principal de l'étude reste le MIDPOINT EF v3.1, seize catégories.
Ce module en donne une seconde lecture, agrégée en trois aires de protection.
Trois précautions, toutes à écrire dans l'article :

1. L'ENDPOINT VIENT EN PLUS, JAMAIS À LA PLACE. C'est la position de Bare,
   Hofstetter, Pennington et Udo de Haes (Int J LCA 5(6) 319-326, 2000), qui
   reste la référence sur la question : « endpoint models may be more relevant,
   but less certain (i.e., higher model and parameter uncertainty). Midpoint
   modeling may be more certain […] but less relevant to what the decision
   makers really want to know », d'où leur conclusion que « both midpoint and
   endpoint methodologies provide useful information to the decision maker ».

2. CE N'EST PAS UNE CONVERSION DE NOS RÉSULTATS EF. EF v3.1 n'a pas de niveau
   endpoint — le rapport JRC de référence s'arrête explicitement aux seize
   catégories midpoint. ReCiPe est une autre méthode, avec sa propre
   modélisation de bout en bout. Même inventaire, caractérisation différente :
   les trois scores ci-dessous ne sont pas la somme pondérée de nos seize.

3. LES TROIS SCORES NE S'ADDITIONNENT PAS. DALY, species·yr et USD2013 n'ont
   pas de commune mesure. On publie trois indicateurs côte à côte.

════════════════════════════════════════════════════════════════════════════
⚠ CE QUE « ECOSYSTEM QUALITY » NE CONTIENT PAS

Les douze voies agrégées dans cette aire de protection — acidification
terrestre, changement climatique sur les écosystèmes, écotoxicités,
eutrophisations, usage des SOLS, oxydants photochimiques, usage de l'eau — sont
toutes pilotées par des ÉMISSIONS, à l'échelle globale ou régionale.

Il y a `land use`. Il n'y a PAS `sea use`. Aucune voie ne représente
l'occupation d'un habitat marin, l'ombrage d'une communauté corallienne ni
l'effet récif artificiel. Le score en species·yr de cette plateforme sera
dominé par le cuivre du câble, exactement comme nos catégories de toxicité
midpoint, et il ne dira rien du lagon.

Cette asymétrie est vérifiable par n'importe quel relecteur dans la liste des
méthodes de la base : c'est elle qu'il faut citer, et non un score endpoint,
pour justifier que l'effet local sur le récif relève de l'étude écologique
compagnon et non de l'ACV. Woods et al. (Environment International, 2016) le
formulent ainsi : « impact indicators for major drivers of marine biodiversity
loss are currently lacking ».
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, modalites, resultats, systeme

ORDRE = ("human health", "ecosystem quality", "natural resources")

LIBELLES = {
    "human health": "Human health",
    "ecosystem quality": "Ecosystem quality",
    "natural resources": "Natural resources",
}


# ══════════════════════════════════════════════════════════════════════════
# 1. Disponibilité et unités
# ══════════════════════════════════════════════════════════════════════════
def verifier_disponibilite(verbeux=True) -> bool:
    """Les trois méthodes existent-elles dans le projet Brightway ouvert ?

    On le contrôle AVANT tout calcul : `compute_impacts` sur une méthode
    absente lève une erreur peu lisible, et la cause réelle (une base sans
    ReCiPe endpoint) mérite d'être nommée.
    """
    import brightway2 as bw

    presentes = set(bw.methods)
    manquantes = [m for m in config.METHODES_RECIPE_H if m not in presentes]
    if manquantes:
        print("⚠ méthode(s) absente(s) du projet :")
        for m in manquantes:
            print("   ", m)
        print("   `[m for m in bw.methods if m[0].startswith(\"ReCiPe 2016\")]` "
              "liste ce que porte TA base.")
        return False
    if verbeux:
        print(f"  {len(config.METHODES_RECIPE_H)} méthodes endpoint trouvées "
              f"({config.RECIPE_H})")
    return True


def unites() -> dict:
    """{aire de protection: unité}, lue dans la base plutôt que codée en dur."""
    import brightway2 as bw

    u = {}
    for methode in config.METHODES_RECIPE_H:
        aire = methode[2]
        try:
            u[aire] = bw.Method(methode).metadata.get(
                "unit", config.UNITES_RECIPE[aire])
        except Exception:      # noqa: BLE001
            u[aire] = config.UNITES_RECIPE[aire]
    return u


# ══════════════════════════════════════════════════════════════════════════
# 2. Les trois scores
# ══════════════════════════════════════════════════════════════════════════
def scores(ctx, jeux, verbeux=True) -> pd.DataFrame:
    """Les trois aires de protection, pour les quatre configurations.

    Une ligne par configuration, une colonne par aire, PAR kWh net livré —
    même unité fonctionnelle que tout le reste de l'étude.

    >>> endpoint.scores(ctx, jeux)
    """
    u = unites()
    lignes = []
    for libelle, valeurs in jeux.items():
        if verbeux:
            print("Endpoint :", libelle)
        df = systeme.impacts(ctx, config.METHODES_RECIPE_H, **valeurs)
        serie = df.iloc[0]
        ligne = {"modalite": libelle,
                 "code": modalites.DONNEES.get(libelle, {}).get("code", libelle)}
        for methode, valeur in zip(config.METHODES_RECIPE_H, serie):
            aire = methode[2]
            ligne[f"{LIBELLES[aire]} ({u[aire]}/kWh)"] = float(valeur)
        lignes.append(ligne)

    tab = pd.DataFrame(lignes).set_index("code")
    tab.attrs["unites"] = u
    tab.attrs["methode"] = config.RECIPE_H
    if verbeux:
        print(f"\n  {config.RECIPE_H} — par kWh net livré")
        for aire in ORDRE:
            col = f"{LIBELLES[aire]} ({u[aire]}/kWh)"
            print(f"    {LIBELLES[aire]:<18} "
                  + " | ".join(f"{c} {v:.3e}"
                               for c, v in tab[col].items()))
        print("  ⚠ les trois colonnes ne s'additionnent pas (unités distinctes)")
    return tab


# ══════════════════════════════════════════════════════════════════════════
# 3. Qui porte quoi — le résultat intéressant
# ══════════════════════════════════════════════════════════════════════════
def contributions(ctx, valeurs, verbeux=False) -> pd.DataFrame:
    """Ventilation par poste des trois aires, pour UNE configuration.

    `exacte=True` est imposé : la ventilation par axe de lca_algebraic laisse
    ~10 % non attribués sur le GWP et bien davantage sur les catégories
    dominées par l'électricité. Sur un résultat agrégé, un résidu de cet ordre
    serait indéfendable.
    """
    return resultats.contribution(ctx, valeurs,
                                  methodes=config.METHODES_RECIPE_H,
                                  exacte=True)


def parts(ctx, jeux, verbeux=True) -> dict:
    """{libellé de configuration: tableau de contribution}, prêt pour la figure.

    C'est ce dict qu'attend `resultats.figure_barres_100(contributions=…)`.
    """
    tableaux = {}
    for libelle, valeurs in jeux.items():
        if verbeux:
            print("Contribution endpoint :", libelle)
        tableaux[libelle] = contributions(ctx, valeurs)
    return tableaux


# ══════════════════════════════════════════════════════════════════════════
# 3 bis. Quelle VOIE porte chaque aire — ce que les trois agrégats cachent
# ══════════════════════════════════════════════════════════════════════════
def voies(ctx, valeurs, verbeux=True) -> pd.DataFrame:
    """Les vingt-deux voies derrière les trois scores, pour UNE configuration.

    Ces voies ne sont PAS à publier comme des résultats : les publier
    reviendrait à refaire du midpoint avec une seconde méthode, ce qui
    doublerait la section 3 sans rien ajouter. Elles servent à répondre à une
    seule question, et c'est la seule qui justifie un paragraphe endpoint dans
    l'article :

        le classement des configurations ne change pas d'une aire à l'autre —
        est-ce que la CAUSE de l'impact, elle, change ?

    Un agrégat en DALY ne le dit pas. Si le score de santé humaine est porté
    par `climate change: human health`, l'endpoint ne fait que redire le
    midpoint carbone dans une autre unité et ne mérite qu'une phrase. S'il est
    porté par les toxicités et les particules, alors il dit quelque chose que
    le midpoint ne disait pas, et il faut l'écrire.

    Un garde-fou : si `human toxicity: non-carcinogenic` ou
    `ecotoxicity: freshwater` domine, le résultat repose sur la partie la moins
    robuste de ReCiPe (facteurs USEtox pour les métaux, largement pilotés par
    les émissions à long terme des stériles miniers). Lancer alors
    `sans_long_terme` AVANT d'écrire quoi que ce soit.
    """
    lignes = []
    for aire in ORDRE:
        sous = config.METHODES_RECIPE_H_DETAIL[aire]
        serie = systeme.impacts(ctx, sous, **valeurs).iloc[0]
        total = float(serie.sum())
        for methode, valeur in zip(sous, serie):
            valeur = float(valeur)
            lignes.append({
                "aire": LIBELLES[aire],
                "voie": methode[2],
                "score": valeur,
                "part_aire_%": 100.0 * valeur / total if total else np.nan,
            })

    tab = pd.DataFrame(lignes)
    if verbeux:
        for aire in ORDRE:
            bloc = (tab[tab["aire"] == LIBELLES[aire]]
                    .sort_values("part_aire_%", ascending=False))
            print(f"\n  {LIBELLES[aire]} — {len(bloc)} voies")
            cumul = 0.0
            for _, r in bloc.iterrows():
                avant, cumul = cumul, cumul + r["part_aire_%"]
                # ← marque les voies nécessaires pour atteindre 90 % de l'aire.
                cle = "  ←" if avant < 90.0 else ""
                print(f"    {r['part_aire_%']:5.1f} %  (cumul {cumul:5.1f} %)  "
                      f"{r['voie']}{cle}")
    return tab


# ══════════════════════════════════════════════════════════════════════════
# 3 ter. Sensibilité aux émissions à long terme
# ══════════════════════════════════════════════════════════════════════════
def methodes_no_lt(verbeux=True):
    """Les trois tuples « (H) no LT », DÉCOUVERTS dans la base, non codés en dur.

    L'orthographe de ces variantes a changé d'une version d'ecoinvent à
    l'autre ; on les cherche donc au lieu de les écrire, et on le dit quand
    elles manquent plutôt que de laisser `compute_impacts` échouer.
    """
    import brightway2 as bw

    trouvees = {}
    for m in bw.methods:
        if not (str(m[0]).startswith("ReCiPe 2016") and "(H)" in str(m[0])
                and "no LT" in str(m[0])):
            continue
        if not str(m[1]).startswith("total:"):
            continue
        for aire in ORDRE:
            if aire in str(m[1]):
                trouvees[aire] = tuple(m)

    manquantes = [a for a in ORDRE if a not in trouvees]
    if manquantes:
        print("⚠ variante « no LT » introuvable pour :", ", ".join(manquantes))
        print("   `[m for m in bw.methods if \"no LT\" in m[0]]` liste ce que "
              "porte TA base ;")
        print("   si elle n'en porte aucune, la sensibilité long terme n'est "
              "pas faisable et il faut l'écrire comme une limite.")
        return None
    if verbeux:
        print("  variantes « no LT » trouvées :", trouvees[ORDRE[0]][0])
    return [trouvees[a] for a in ORDRE]


def sans_long_terme(ctx, jeux, verbeux=True):
    """Compare (H) et (H) no LT : quelle part du score vient de l'après-100 ans ?

    POURQUOI CE CONTRÔLE N'EST PAS OPTIONNEL ICI. Les facteurs de toxicité de
    ReCiPe pour les métaux intègrent les émissions des stériles miniers et des
    mâchefers sur un horizon quasi infini. ecoinvent livre pour cette raison
    une variante tronquée à cent ans — l'existence même de cette variante est
    l'aveu que le choix d'horizon est discutable. Sur un système dont
    l'inventaire est fait d'aluminium, de cuivre et d'inox, ce choix peut
    déplacer le score de santé humaine d'un facteur, pas de quelques pourcents.

    Un relecteur de SETA le demandera. Autant publier les deux.
    """
    methodes = methodes_no_lt(verbeux=verbeux)
    if methodes is None:
        return None

    lignes = []
    for libelle, valeurs in jeux.items():
        if verbeux:
            print("Long terme :", libelle)
        avec = systeme.impacts(ctx, config.METHODES_RECIPE_H, **valeurs).iloc[0]
        sans = systeme.impacts(ctx, methodes, **valeurs).iloc[0]
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        for aire, a, s in zip(ORDRE, avec, sans):
            a, s = float(a), float(s)
            lignes.append({
                "code": code,
                "aire": LIBELLES[aire],
                "avec LT": a,
                "sans LT": s,
                "part long terme %": 100.0 * (a - s) / a if a else np.nan,
            })

    tab = pd.DataFrame(lignes)
    if verbeux:
        print("\n  Part du score due aux émissions au-delà de 100 ans")
        for aire in ORDRE:
            bloc = tab[tab["aire"] == LIBELLES[aire]]
            print(f"    {LIBELLES[aire]:<18} "
                  + " | ".join(f"{r['code']} {r['part long terme %']:5.1f} %"
                               for _, r in bloc.iterrows()))
        print("  > 50 % quelque part : le score endpoint se discute d'abord "
              "comme un choix d'horizon,")
        print("    et les deux variantes doivent figurer dans l'article.")
    return tab


# ══════════════════════════════════════════════════════════════════════════
# 4. Contrôle : le total vaut-il la somme de ses voies ?
# ══════════════════════════════════════════════════════════════════════════
def verifier(ctx, valeurs, tolerance=1e-6, verbeux=True) -> bool:
    """`total: X` == somme des sous-catégories de X ?

    Ce contrôle vaut surtout pour ce qu'il exclut : si les tuples « total: »
    retenus étaient en réalité autre chose qu'une somme (une pondération, un
    doublon), l'écart le dirait immédiatement. Il confirme aussi que la base
    porte bien les douze voies d'ecosystem quality et non onze, comme c'est le
    cas de la perspective (I).
    """
    ok = True
    for aire in ORDRE:
        sous = config.METHODES_RECIPE_H_DETAIL[aire]
        total = float(systeme.impacts(
            ctx, [(config.RECIPE_H, f"total: {aire}", aire)], **valeurs).iloc[0, 0])
        detail = systeme.impacts(ctx, sous, **valeurs).iloc[0]
        somme = float(detail.sum())
        ecart = abs(somme - total) / abs(total) if total else float("nan")
        bon = ecart <= tolerance
        ok &= bon
        if verbeux:
            print(f"  {'✓' if bon else '✗'} {LIBELLES[aire]:<18} "
                  f"total {total:.4e} | somme de {len(sous)} voies {somme:.4e} "
                  f"| écart {ecart:.2e}")
    return ok


# ══════════════════════════════════════════════════════════════════════════
# 5. Figure de travail
# ══════════════════════════════════════════════════════════════════════════
def figure(ctx, jeux, titre=None, verbeux=True):
    """Barres empilées à 100 %, une barre par aire de protection.

    Délègue à `resultats.figure_barres_100`, donc mêmes couleurs et mêmes
    libellés de poste que toutes les autres figures de l'étude — c'est ce qui
    permet de lire celle-ci à côté de la figure midpoint sans retraduire.

    Ce n'est PAS le graphical abstract : c'est la figure qui sert à voir si le
    classement des postes change d'une aire à l'autre.
    """
    return resultats.figure_barres_100(
        contributions=parts(ctx, jeux, verbeux=verbeux),
        titre=titre or ("ReCiPe 2016 endpoint (H) — three areas of protection\n"
                        "secondary reading, in parallel with the EF v3.1 "
                        "midpoint results"),
        verbeux=verbeux)
