"""
Comparaison à la littérature, harmonisée — figure du § 4.2.

Comparer des GWP par kWh publiés dans six pays revient à comparer des soleils
autant que des systèmes. Un FPV alpin à 1 388 kWh/kWc/an et un FPV néerlandais
à 795 n'ont pas la même chance : à structure IDENTIQUE, le premier afficherait
un GWP/kWh 1,7 fois plus bas. Le classement brut ne dit donc rien de la
conception.

────────────────────────────────────────────────────────────────────────────
MÉTHODE D'HARMONISATION

Chaque étude est ramenée à un productible COMMUN, arrondi à 1 000 kWh/kWc/an
sur 30 ans (29 190 kWh/kWc pour Raiatea : la référence ronde en est à 2,7 %,
et elle se cite mieux dans un axe de figure) :

    intensité structurelle (kg CO₂-eq/kWc)
        = GWP publié (g/kWh) × productible (kWh/kWc/an) × durée de vie ÷ 1000

    GWP harmonisé (g/kWh)
        = intensité ÷ (1 000 × 30) × 1000

Les deux opérations sont exactement inverses : aucune donnée n'est créée, on
change seulement de dénominateur. C'est une RENORMALISATION, pas une ré-ACV —
elle ne corrige ni le périmètre, ni la méthode d'impact, ni l'allocation de fin
de vie, qui restent ceux de chaque publication.

Sur la figure, le LOSANGE BLANC porte la valeur telle que publiée et la BARRE
la valeur harmonisée. L'écart entre les deux est l'effet du gisement solaire,
et rien d'autre.

────────────────────────────────────────────────────────────────────────────
POURQUOI UNE TYPOLOGIE ET PAS UN SIMPLE « FPV / SOL »

La couleur des barres ne dit pas seulement où flotte le système : elle dit
POURQUOI il est là où il est. C'est ce qui fait la lecture du § 4.2.

| Catégorie                  | Ce qu'elle explique                            |
|----------------------------|------------------------------------------------|
| FPV lagon corallien        | cette étude — structure aluminium marine       |
| FPV, site surdimensionné   | Frehner : barrage d'altitude, neige et glace   |
| FPV, modules peu efficaces | Cromratie : modules à 13 %, donc plus de m²/kWc|
| FPV eau intérieure, peu d'alu | IEA : flotteurs béton/acier + PEHD          |
| PV au sol                  | le plancher de référence                       |
| Concept jamais construit   | Hayibo : mousse, resté sur le papier           |

Autrement dit : Raiatea n'est pas haute « parce que c'est du flottant », elle
est haute parce que c'est de l'aluminium marin — d'où la colonne kg Al/kWc à
côté des barres, qui est le vrai facteur explicatif.

────────────────────────────────────────────────────────────────────────────
CE QUE L'HARMONISATION NE CORRIGE PAS — à écrire dans le texte

* Méthodes d'impact différentes : EF v3.1 (nous), UVEK/IPCC (IEA-PVPS),
  ReCiPe (Cromratie, Budi). Les écarts de facteurs de caractérisation GWP100
  sont faibles (le climat est la catégorie la plus stable d'un référentiel à
  l'autre), mais non nuls.
* Périmètres : Cromratie inclut le BoS et la maintenance dans son poste
  structure, Budi non. Hayibo ne compte pas de fin de vie.
* Un productible reste une HYPOTHÈSE quand l'article ne le publie pas. La
  colonne `fiabilite` le dit ligne par ligne et la figure hachure les barres
  concernées : l'intensité structurelle est proportionnelle au productible
  retenu, donc une erreur de 20 % sur le rendement fait 20 % sur l'intensité.
* Durées de vie : Budi retient 25 ans, tout le reste 30.

────────────────────────────────────────────────────────────────────────────
⚠ DEUX PRODUCTIBLES DU CLASSEUR ÉTAIENT FAUX (corrigés le 15/09/2026)

`Benchmark_litterature_ACV_FPV.xlsx` portait pour Cromratie et Budi des
rendements qui ne sont pas ceux des publications. Les deux sont maintenant
calculés à partir des chiffres que les articles donnent eux-mêmes.

CROMRATIE CLEMONS et al. 2021 — 1 550 → 1 167 kWh/kWc/an
    Table 1 : centrale de 150 MW (555 482 modules, soit 270 W l'unité — c'est
    bien du DC crête), 30 ans, « Average Yearly Energy Output 175 GWh ».
        175 000 000 kWh ÷ 150 000 kWc = 1 167 kWh/kWc/an
    Le 1 550 du classeur n'apparaît nulle part dans l'article. La figure de
    l'article, elle, utilisait DÉJÀ 1 167 (85,5 g harmonisés) : c'est le
    classeur qui était en retard, pas la figure.

BUDI et al. 2024 — 1 933 → 1 456 kWh/kWc/an
    7 005 878 243 kWh sur 25 ans. Le piège est la puissance : Cirata est
    décrite comme « a 145 MWac floating PV system », mais le texte précise
    « installed capacity of 192.5 MWp with a Power Purchase Agreement (PPA)
    limit of 145 MWac ». Le 1 933 divise par la limite AC du contrat ; notre
    unité, comme toutes les autres lignes, est le kWc DC crête.
        7 005 878 243 ÷ 25 ÷ 192 500 = 1 456 kWh/kWc/an
    Budi n'est pas dans la figure de l'article (`dans_article=False`), mais la
    ligne est disponible pour le texte.

────────────────────────────────────────────────────────────────────────────
SOURCE DES DONNÉES

`Benchmark_litterature_ACV_FPV.xlsx` (feuilles `Valeurs_publiees`,
`Harmonisation`, `Sources`, `Structures_seules`).

⚠ VÉRIFIÉ LE 17/09/2026 DANS LES ARTICLES EUX-MÊMES — la question « est-ce un
productible ou une irradiation ? » se pose pour chaque ligne, et elle a déjà
piégé le classeur une fois (voir NREL plus bas).

  IEA PVPS T12-29:2024, Tableau 6, ligne « Specific energy yield (AC, HV)
  [kWh/(kWp yr)] » : FPV_A 889, FPV_B 795, GPV_ew 795, GPV_op 962. Le rapport
  écrit la grandeur en toutes lettres et donne SÉPARÉMENT l'irradiation de
  Cologne (GHI 1 062 kWh/m²/an) : aucune ambiguïté. Ce sont des productibles
  MODÉLISÉS (PVsyst/BIGEYE, PR 0,80 supposé, dégradation 0,7 %/an incluse,
  30 ans) et non mesurés — et le rapport précise lui-même qu'ils sont
  « about 20% lower than the actual energy yield in year 1 » des deux FPV.
  Notre écart aux références IEA est donc, s'il bouge, surestimé.

  Cromratie Clemons 2021 : « Average Annual Output 175 014 000 kWh » pour
  150 MW crête -> 1 167 kWh/kWc/an. Productible. ✓
  Budi 2024 : 7 005 878 243 kWh sur 25 ans, 192,5 MWp -> 1 456. Productible. ✓
  Hsu/NREL 2012 : 1 700 est une IRRADIATION (voir la ligne NREL). ✗ corrigé.

  RESTENT À VÉRIFIER SUR L'ARTICLE : Frehner (1 388) et Hayibo (2 173), le
  second étant de toute façon reconstruit depuis une figure.

Les valeurs sont recopiées en dur pour que le package ne dépende pas d'un
classeur. Les quatre lignes « cette étude » sont, elles, RECALCULÉES depuis le
modèle dès qu'on passe `ctx` et `jeux` : elles ne peuvent pas rester sur un run
périmé (celles écrites ici sont celles du manuscrit, conservées comme témoin).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import electricite, modalites

# ── Références de normalisation ────────────────────────────────────────────
# ⚠ Le productible de NOS quatre entrées n'est plus écrit en dur : il se
# recalcule depuis `reference.PRODUCTIBLE_P0`. Le 973 de l'ancienne version
# correspondait à 1 025 kWh/kWc de 1ʳᵉ année ; depuis le 26/09/2026 la mesure
# corrigée vaut 1 096, donc 1 040,4 en moyenne sur 30 ans. Une constante en dur
# aurait fait diverger l'harmonisation du reste du modèle sans rien signaler.
# ⚠ Lu À L'APPEL et non au chargement : `from .parametres import CONST` fige
# la valeur au moment de l'import, et avec %autoreload une édition de
# `parametres.py` ne recharge PAS ce module-ci, qui garderait l'ancienne.
def _p_raiatea() -> float:
    from . import parametres as _p
    return round(_p.PRODUCTIBLE_P0 * (1 - _p.TAUX_DEGRADATION
                                      * (_p.DUREE_VIE_REFERENCE - 1) / 2), 1)

# Productible rond de la figure du § 4.2. Raiatea vaut 1 040 kWh/kWc/an en
# moyenne sur 30 ans : l'écart à 1 000 est de 2,7 %, il joue sur TOUTES les
# lignes de la même façon et ne change donc aucun classement.
PRODUCTIBLE_REFERENCE = 1000.0
DUREE_REFERENCE_AN = modalites.DUREE_VIE_ANS


CODES_CETTE_ETUDE = ("SH81", "SH51", "SH81-UV", "SH51-UV")


def productible_reference(duree_vie=None) -> float:
    """Productible MOYEN réel de Raiatea (kWh/kWc/an).

    N'est PAS le dénominateur de l'harmonisation (c'est `PRODUCTIBLE_REFERENCE`,
    arrondi à 1 000) — mais sert à le comparer, et à harmoniser « chez nous »
    si on préfère cette lecture : `harmoniser(productible_ref=...)`.
    """
    from .parametres import productible_moyen
    duree_vie = DUREE_REFERENCE_AN if duree_vie is None else duree_vie
    from . import parametres as _p
    return productible_moyen(_p.PRODUCTIBLE_P0,
                             _p.TAUX_DEGRADATION, duree_vie)


# ── Typologie : la couleur porte l'explication, pas seulement le milieu ────
CATEGORIES = {
    "marin": "This study, coral lagoon FPV",
    "site_surdimensionne": "FPV, structurally over-designed site",
    "modules_faible_rendement": "FPV, low-efficiency modules",
    "eau_douce_alu_bas": "FPV, inland water, low aluminium",
    "sol": "Ground-mounted PV",
    "concept": "Design concept, never built",
}

COULEURS_CATEGORIES = {
    "marin": "#B03A2E",
    "site_surdimensionne": "#E67E22",
    "modules_faible_rendement": "#8E44AD",
    "eau_douce_alu_bas": "#27AE60",
    "sol": "#2E86C1",
    "concept": "#95A5A6",
}

# ── Électricité de réseau déplacée, panneau de droite (g CO₂-eq/kWh) ───────
# Le repère qui donne son sens à toute la figure : même la pire configuration
# de Raiatea est un ordre de grandeur sous le kWh qu'elle remplace.
# Raiatea n'est pas recopié — il vient de `electricite.FE_ARCHIPELS`.
REFERENCES_RESEAU = {
    "EU grid mix, 2030 target": (176.0, "#7F8C8D"),
    "Raiatea fuel-oil generation": (electricite.FE_RAIATEA * 1000.0, "#34495E"),
}

# ── Les études ─────────────────────────────────────────────────────────────
# Une ligne = une valeur publiée. Champs :
#   cle              identifiant court, stable
#   libelle          étiquette de figure (anglais — l'article l'est)
#   categorie        clé de CATEGORIES : la typologie, pas le milieu seul
#   gwp_g_kwh        GWP PUBLIÉ, g CO₂-eq/kWh (le losange sur la figure)
#   productible      kWh/kWc/an du site de l'étude (ce qui est harmonisé)
#   duree_vie        ans
#   kg_al_kwc        aluminium par kWc : un nombre, 0.0 = « none » (le système
#                    n'en contient pas), None = « not reported ». DOCUMENTAIRE,
#                    n'entre dans aucun calcul.
#   fiabilite        "solide"   productible et durée relus dans une source
#                    "approche" productible reconstruit ou supposé
#   dans_article     figure du § 4.2 telle qu'elle est aujourd'hui
#   source           référence courte
#   note             ce qu'il reste à vérifier, affiché par `harmoniser`
ETUDES = [
    # ── Cette étude ────────────────────────────────────────────────────────
    # Valeurs du RUN DE RÉFÉRENCE (16/09/2026), écrasées par
    # `harmoniser(ctx, jeux)` dès qu'on lui passe un run. Le kg Al/kWc est lu
    # dans `modalites.DONNEES`, jamais recopié.
    #
    # ⚠ AUCUNE VALEUR EN DUR ICI, ET C'EST VOULU (01/10/2026).
    #
    # Ces quatre lignes ont porté un « repli » deux fois de suite, et il a été
    # faux les deux fois : 62,4 / 68,9 / 81,7 / 96,8 d'abord (run d'avant la
    # correction de l'aluminium), puis 66,4 / 73,6 / 88,4 / 103,7 (run du
    # 16/09/2026, d'avant la correction du productible du 26/09). Un repli dans
    # un benchmark est une valeur qui a l'air d'une source, que personne ne
    # revérifie, et qui périme en silence à chaque run.
    #
    # `gwp_g_kwh` et `productible` valent donc None. `harmoniser(ctx, jeux)` les
    # remplit depuis le modèle ; sans ctx/jeux elles restent NaN, la fonction le
    # dit, et les deux figures REFUSENT de se tracer. Pour tracer malgré tout
    # avec des valeurs choisies à la main (reproduire une figure publiée, par
    # exemple) : `harmoniser(repli={"SH51": 67.7, ...})`.
    dict(cle="SH81-UV", libelle="This study, SH81-UV, Raiatea",
         categorie="marin", gwp_g_kwh=None, productible=None, duree_vie=30,
         fiabilite="solide", dans_article=True, cette_etude=True,
         source="This study, live model"),
    dict(cle="SH81", libelle="This study, SH81, Raiatea",
         categorie="marin", gwp_g_kwh=None, productible=None, duree_vie=30,
         fiabilite="solide", dans_article=True, cette_etude=True,
         source="This study, live model"),
    dict(cle="SH51", libelle="This study, SH51, Raiatea",
         categorie="marin", gwp_g_kwh=None, productible=None, duree_vie=30,
         fiabilite="solide", dans_article=True, cette_etude=True,
         source="This study, live model"),
    dict(cle="SH51-UV", libelle="This study, SH51-UV, Raiatea",
         categorie="marin", gwp_g_kwh=None, productible=None, duree_vie=30,
         fiabilite="solide", dans_article=True, cette_etude=True,
         source="This study, live model"),

    # ── IEA-PVPS T12-29 (2024) ─────────────────────────────────────────────
    # Les quatre cas ont chacun LEUR productible : le « ~850 » du classeur
    # était une moyenne. Les valeurs ci-dessous sont celles qui reproduisent
    # exactement la figure du § 4.2 (publié × productible ÷ 1 000 = harmonisé)
    # et elles sont cohérentes entre elles — une orientation est-ouest perd
    # bien ~17 % sur un plein sud optimisé.
    dict(cle="IEA_GPV_op", libelle="IEA PVPS, GPV, optimum tilt, DE",
         categorie="sol", gwp_g_kwh=38.0, productible=962.0, duree_vie=30,
         kg_al_kwc=None, fiabilite="solide", dans_article=True,
         source="IEA-PVPS T12-29 (2024), Tab. A3 + B1/B2"),
    dict(cle="IEA_GPV_ew", libelle="IEA PVPS, GPV, east-west, DE",
         categorie="sol", gwp_g_kwh=46.0, productible=795.0, duree_vie=30,
         kg_al_kwc=None, fiabilite="solide", dans_article=True,
         source="IEA-PVPS T12-29 (2024), Tab. A3 + B1/B2"),
    dict(cle="IEA_FPV_A", libelle="IEA PVPS, FPV_A, HDPE floats, DE",
         categorie="eau_douce_alu_bas", gwp_g_kwh=49.0, productible=889.0,
         duree_vie=30, kg_al_kwc=2.2, fiabilite="solide", dans_article=True,
         source="IEA-PVPS T12-29 (2024), Tab. 2 + B1/B2"),
    dict(cle="IEA_FPV_B", libelle="IEA PVPS, FPV_B, steel/HDPE, NL",
         categorie="eau_douce_alu_bas", gwp_g_kwh=55.0, productible=795.0,
         duree_vie=30, kg_al_kwc=0.0, fiabilite="solide", dans_article=True,
         source="IEA-PVPS T12-29 (2024), Tab. 4 + B1/B2"),

    # ── Les autres références de la figure ─────────────────────────────────
    dict(cle="Cromratie",
         libelle="Cromratie Clemons et al., 13 % modules, TH",
         categorie="modules_faible_rendement", gwp_g_kwh=73.3,
         productible=1166.5, duree_vie=30, kg_al_kwc=None, fiabilite="solide",
         dans_article=True,
         source="Renew. Energy 168 (2021) 448-462, Tab. 1 : 175 GWh/an ÷ 150 MW"),
    dict(cle="Frehner", libelle="Frehner et al., alpine reservoir, CH",
         categorie="site_surdimensionne", gwp_g_kwh=94.0, productible=1388.0,
         duree_vie=30, kg_al_kwc=119.0, fiabilite="solide", dans_article=True,
         source="communiqué 15/09/2026 : 94 g/kWh publiés à 1 388 kWh/kWc/an, "
                "119 kg Al/kWc → 130,5 g harmonisés"),
    dict(cle="Hayibo", libelle="Hayibo et al., foam concept, USA",
         categorie="concept", gwp_g_kwh=11.0, productible=2173.0, duree_vie=30,
         kg_al_kwc=0.0, fiabilite="approche", dans_article=True,
         source="Sustain. Energy Fuels 6 (2022) 1398",
         note="productible 2 173 kWh/kWc/an reconstruit depuis la figure "
              "(11 g publiés → 23,9 g harmonisés). C'est très élevé, même pour "
              "le sud-ouest américain : à vérifier sur l'article"),

    # ── Hors figure, disponibles pour le texte ─────────────────────────────
    dict(cle="Budi", libelle="Budi et al., Cirata 192.5 MWp, ID",
         categorie="eau_douce_alu_bas", gwp_g_kwh=42.05, productible=1455.5,
         duree_vie=25, kg_al_kwc=None, fiabilite="solide", dans_article=True,
         source="Conf. LCA (2024) : 7 005 878 243 kWh ÷ 25 ans ÷ 192,5 MWp"),
    # TRANCHÉ le 17/09/2026 sur le résumé de l'article. Hsu et al. écrivent :
    # « harmonizing key performance characteristics (irradiation of 1,700
    # kilowatt-hours per square meter per year […]; system lifetime of 30 years;
    # module efficiency of 13.2% or 14.0% […]; and a performance ratio of 0.75
    # or 0.80 […]) ». Donc 1 700 est bien une IRRADIATION, et le productible
    # implicite vaut 1 700 × 0,75 = 1 275 kWh/kWc/an. L'harmonisé tombe de 76,5
    # à 57,4 g — ce qui replace enfin le PV au sol harmonisé SOUS notre étude,
    # au lieu de le laisser au-dessus des FPV d'eau douce, qui n'avait pas de
    # sens physique.
    dict(cle="NREL", libelle="Hsu / NREL, ground c-Si, harmonised",
         categorie="sol", gwp_g_kwh=45.0, productible=1275.0, duree_vie=30,
         kg_al_kwc=None, fiabilite="solide", dans_article=True,
         source="J. Ind. Ecol. 16(S1) S122, 1 700 kWh/m²/an × PR 0,75",
         note="productible DÉDUIT du protocole : irradiation 1 700 kWh/m²/an et "
              "PR 0,75 sont les deux paramètres d'harmonisation publiés."),
]


def aluminium_par_kwc() -> dict:
    """kg d'aluminium de structure par kWc, pour nos 4 configurations.

    Calculé depuis `modalites.DONNEES` — la masse d'aluminium et la puissance
    de CHAQUE plateforme. La figure du manuscrit divisait la même masse
    (606,4 kg) par les quatre puissances, ce qui donnait 46,4 / 54,8 / 76,7 /
    79,2 : une seule de ces valeurs était juste.
    """
    return {d["code"]: d["alu_structure"] / d["kwc"]
            for d in modalites.DONNEES.values()}


def harmoniser(ctx=None, jeux=None, productible_ref=None, duree_ref=None,
               incertitudes=None, repli=None, verbeux=True) -> pd.DataFrame:
    """Tableau harmonisé : intensité structurelle + GWP à productible commun.

    Si `ctx` et `jeux` sont fournis, les quatre lignes « cette étude » sont
    RECALCULÉES par le modèle : la figure ne peut pas rester sur un run
    périmé. Sans eux, ce sont les valeurs du manuscrit qui servent, et la
    fonction le dit.

    Parameters
    ----------
    incertitudes : DataFrame, optional
        Le tableau de `incertitude.incertitude(ctx, jeux)`. Fourni, il ajoute
        l'intervalle 5-95 % sur les quatre lignes « cette étude », harmonisé
        par le même facteur que la valeur centrale. Les autres lignes n'en ont
        pas : aucune des publications ne donne d'intervalle, et en inventer un
        serait pire que de laisser la colonne vide.
    repli : dict, optional
        {code: GWP publié g/kWh} pour remplir à la main les lignes « cette
        étude » quand on n'a pas de run sous la main — reproduire une figure
        déjà publiée, par exemple. À n'utiliser QUE délibérément : sans ctx,
        sans jeux et sans repli, ces lignes restent vides et les figures
        refusent de se tracer, ce qui est le comportement voulu.

    >>> tab = litterature.harmoniser(ctx, jeux)
    >>> litterature.figure_benchmark(tab)
    """
    duree_ref = DUREE_REFERENCE_AN if duree_ref is None else duree_ref
    productible_ref = (PRODUCTIBLE_REFERENCE if productible_ref is None
                       else productible_ref)
    energie_ref = productible_ref * duree_ref            # kWh/kWc sur la vie

    vivantes = _valeurs_du_modele(ctx, jeux, verbeux=verbeux)
    alu = aluminium_par_kwc()
    bornes = _bornes_incertitude(incertitudes)

    lignes = []
    manquantes = []
    for etude in ETUDES:
        etude = dict(etude)
        if etude.get("cette_etude"):
            etude["kg_al_kwc"] = alu.get(etude["cle"])
            if etude["cle"] in vivantes:
                etude.update(vivantes[etude["cle"]])
                etude["source"] = "This study, live model"
            elif repli and etude["cle"] in repli:
                # Valeur fournie à la main : le productible, lui, reste celui
                # du modèle, sinon on cumule deux sources de péremption.
                etude["gwp_g_kwh"] = float(repli[etude["cle"]])
                etude["productible"] = _p_raiatea()
                etude["source"] = "This study, value supplied by hand"
            else:
                manquantes.append(etude["cle"])
                etude["gwp_g_kwh"] = np.nan
                etude["productible"] = _p_raiatea()

        if etude["productible"] and etude["duree_vie"]:
            intensite = (etude["gwp_g_kwh"] * etude["productible"]
                         * etude["duree_vie"] / 1000.0)
            harmonise = intensite / energie_ref * 1000.0
        else:
            intensite = harmonise = np.nan

        # L'intervalle est appliqué EN RELATIF à la valeur harmonisée de la
        # ligne : il reste donc centré sur elle, quelle que soit sa provenance.
        rapport_bas, rapport_haut = bornes.get(etude["cle"], (np.nan, np.nan))
        bas, haut = harmonise * rapport_bas, harmonise * rapport_haut

        lignes.append({
            "cle": etude["cle"],
            "systeme": etude["libelle"],
            "categorie": etude["categorie"],
            "GWP publié g/kWh": etude["gwp_g_kwh"],
            "Productible kWh/kWc/an": etude["productible"],
            "Durée de vie an": etude["duree_vie"],
            "Intensité structurelle kg CO₂/kWc": intensite,
            "GWP harmonisé g/kWh": harmonise,
            "harmonisé p5 g/kWh": bas,
            "harmonisé p95 g/kWh": haut,
            "kg Al/kWc": etude.get("kg_al_kwc"),
            "fiabilite": etude["fiabilite"],
            "dans_article": etude["dans_article"],
            "cette_etude": bool(etude.get("cette_etude")),
            "source": etude["source"],
            "note": etude.get("note", ""),
        })

    tab = pd.DataFrame(lignes)
    # Les repères de normalisation voyagent AVEC le tableau : les figures les
    # relisent au lieu de réécrire « 1 000 kWh/kWc/an » dans un titre.
    tab.attrs["productible_ref"] = productible_ref
    tab.attrs["duree_ref"] = duree_ref

    if manquantes:
        # Imprimé que `verbeux` soit vrai ou faux : une ligne « cette étude »
        # vide est la panne qui produit une figure d'article fausse.
        print("⚠ benchmark SANS les lignes " + ", ".join(manquantes)
              + " : appelle harmoniser(ctx, jeux) pour les calculer, ou "
                "passe repli={...} si tu veux des valeurs choisies à la main. "
                "En l'état les figures du § 4.2 refuseront de se tracer.")

    if verbeux:
        print(f"Harmonisation à {productible_ref:.0f} kWh/kWc/an × "
              f"{duree_ref:.0f} ans = {energie_ref:,.0f} kWh/kWc"
              .replace(",", " ")
              + f" (Raiatea réel : {productible_reference():.0f})")
        for _, ligne in tab[tab["fiabilite"] != "solide"].iterrows():
            print(f"  ⚠ {ligne['cle']} [{ligne['fiabilite']}] "
                  f"{ligne['Productible kWh/kWc/an']:.0f} kWh/kWc/an → "
                  f"{ligne['GWP harmonisé g/kWh']:.0f} g"
                  + (f"\n      {ligne['note']}" if ligne["note"] else ""))
    return tab


def _bornes_incertitude(incertitudes) -> dict:
    """{code: (p5/nominal, p95/nominal)} — l'intervalle en RELATIF.

    On ne transporte pas les bornes en valeur absolue mais leur rapport à la
    valeur centrale du tirage. Ainsi l'intervalle reste centré sur la ligne
    quelle qu'elle soit, y compris si le tableau d'incertitude vient d'un run
    et la ligne des valeurs du manuscrit. Poser un p5 absolu sur une autre
    valeur centrale produirait une barre décalée, et personne ne le verrait.
    """
    if incertitudes is None or not len(incertitudes):
        return {}
    quantiles = incertitudes.attrs.get("quantiles", (5, 50, 95))
    bas, haut = f"p{min(quantiles)}", f"p{max(quantiles)}"
    return {ligne["code"]: (float(ligne[bas]) / float(ligne["nominal g/kWh"]),
                            float(ligne[haut]) / float(ligne["nominal g/kWh"]))
            for _, ligne in incertitudes.iterrows()}


def _valeurs_du_modele(ctx, jeux, verbeux=True) -> dict:
    """GWP vivants des 4 configurations, indexés par code (« SH51 »…)."""
    if ctx is None or jeux is None:
        if verbeux:
            print("(pas de ctx/jeux : les 4 lignes « cette étude » sont celles "
                  "du manuscrit, pas du modèle actuel)")
        return {}

    from . import systeme

    vivantes = {}
    for libelle, valeurs in jeux.items():
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        if verbeux:
            print("Benchmark :", libelle)
        vivantes[code] = {
            "gwp_g_kwh": systeme.gwp_g(ctx, **valeurs),
            "productible": float(valeurs["productible_kwh_kwc_an"]),
            "duree_vie": float(valeurs["duree_vie_an"]),
        }

    # Un code de `jeux` qui ne retombe pas sur une clé d'ETUDES laisserait la
    # ligne correspondante vide SANS erreur : c'est exactement comme ça qu'une
    # figure part avec un run périmé. On le dit ici, où la cause est visible.
    orphelines = sorted(set(CODES_CETTE_ETUDE) - set(vivantes))
    if orphelines:
        print(f"⚠ jeux ne fournit pas {orphelines} — codes vus : "
              f"{sorted(vivantes)}. Vérifie `modalites.DONNEES[...]['code']`.")
    return vivantes


# ══════════════════════════════════════════════════════════════════════════
# Figure du § 4.2
# ══════════════════════════════════════════════════════════════════════════
def _format_alu(valeur) -> str:
    """kg Al/kWc : un nombre, « none » (aucun) ou « not reported » (inconnu)."""
    if valeur is None or (isinstance(valeur, float) and np.isnan(valeur)):
        return "not reported"
    if valeur == 0:
        return "none"
    return f"{valeur:.0f}" if valeur >= 100 else f"{valeur:.1f}"


def _exiger_cette_etude(tab: pd.DataFrame, colonne: str) -> None:
    """Interdit de tracer un benchmark auquel il manque nos propres lignes.

    Les deux figures écartent les lignes sans valeur (`dropna`), ce qui est le
    bon comportement pour une publication dont le productible est inconnu —
    mais appliqué à NOS lignes il produit une figure d'apparence normale où
    l'étude a disparu. Une erreur franche vaut mieux qu'une figure muette.
    """
    vides = tab[tab["cette_etude"] & tab[colonne].isna()]
    if len(vides):
        raise ValueError(
            "benchmark incomplet : " + ", ".join(vides["cle"])
            + " sans valeur dans « %s ». Appelle " % colonne
            + "litterature.harmoniser(ctx, jeux) — ou, délibérément, "
              "harmoniser(repli={...}).")


def figure_benchmark(tab: pd.DataFrame, article_seulement=True, titre=None):
    """La figure du § 4.2 : barres harmonisées, losanges publiés, deux colonnes
    chiffrées, et le kWh de réseau déplacé sur son propre axe.

    Trois panneaux alignés sur les mêmes lignes :

    1. les barres, triées par GWP harmonisé croissant, colorées par TYPOLOGIE
       (cf. `CATEGORIES`) — le losange blanc marque la valeur publiée, donc
       l'écart losange-barre est l'effet du seul gisement solaire ;
    2. la colonne `GWP_harm`, pour citer un chiffre sans le lire sur l'axe ;
    3. la colonne `kg Al/kWc`, le vrai facteur explicatif de la hiérarchie.

    ⚠ LE PANNEAU « électricité déplacée » A ÉTÉ RETIRÉ (01/10/2026). Il portait
    deux barres sur une ÉCHELLE DIFFÉRENTE du panneau principal (0-1 000 contre
    0-150), c'est-à-dire deux axes x dans une même figure : le lecteur ne peut
    pas comparer visuellement une barre de gauche à une barre de droite, alors
    que la mise en page l'y invite. Deux valeurs ne justifiaient pas ce risque
    — elles se disent mieux en une phrase du texte, où le rapport peut être
    ÉNONCÉ (« onze à dix-sept fois ») plutôt que laissé à l'œil.

    `REFERENCES_RESEAU` et `_panneau_reseau` restent définis : ils servent à
    récupérer les valeurs pour le texte, et à refaire le panneau pour une
    présentation, où la contrainte n'est pas la même.

    Parameters
    ----------
    article_seulement : bool
        Restreint aux références montrées dans l'article. False ajoute Budi et
        NREL/Hsu.
    """
    _exiger_cette_etude(tab, "GWP harmonisé g/kWh")
    donnees = tab[tab["dans_article"]] if article_seulement else tab
    donnees = (donnees.dropna(subset=["GWP harmonisé g/kWh"])
               .sort_values("GWP harmonisé g/kWh", kind="stable")
               .reset_index(drop=True))
    n = len(donnees)

    productible_ref = tab.attrs.get("productible_ref", PRODUCTIBLE_REFERENCE)
    duree_ref = tab.attrs.get("duree_ref", DUREE_REFERENCE_AN)

    # La colonne alu doit loger « not reported », centré : son ratio tient
    # compte de la LARGEUR DU TEXTE, pas de celle du nombre. Et `right` laisse
    # une marge, sinon le texte centré déborde de la figure et se fait rogner.
    fig = plt.figure(figsize=(11.0, max(6.0, 0.40 * n + 3.1)))
    grille = fig.add_gridspec(
        1, 3, width_ratios=[1.0, 0.17, 0.30], wspace=0.0,
        left=0.325, right=0.95, top=0.935, bottom=0.20)
    ax = fig.add_subplot(grille[0, 0])
    ax_gwp = fig.add_subplot(grille[0, 1], sharey=ax)
    ax_alu = fig.add_subplot(grille[0, 2], sharey=ax)

    y = np.arange(n)
    couleurs = [COULEURS_CATEGORIES.get(c, "#808080")
                for c in donnees["categorie"]]
    hachures = ["///" if f != "solide" else "" for f in donnees["fiabilite"]]

    barres = ax.barh(y, donnees["GWP harmonisé g/kWh"], height=0.62,
                     color=couleurs, zorder=3)
    for barre, hachure in zip(barres, hachures):
        if hachure:
            barre.set_hatch(hachure)
            barre.set_edgecolor("white")

    # Intervalle Monte-Carlo, quand il existe — c'est-à-dire sur nos lignes.
    if "harmonisé p5 g/kWh" in donnees and donnees["harmonisé p5 g/kWh"].notna().any():
        avec = donnees["harmonisé p5 g/kWh"].notna()
        centre = donnees.loc[avec, "GWP harmonisé g/kWh"]
        ax.errorbar(centre, y[avec.to_numpy()],
                    xerr=np.vstack([
                        (centre - donnees.loc[avec, "harmonisé p5 g/kWh"]).clip(lower=0),
                        (donnees.loc[avec, "harmonisé p95 g/kWh"] - centre).clip(lower=0)]),
                    fmt="none", ecolor="#333333", elinewidth=1.3, capsize=4,
                    capthick=1.3, zorder=4)

    ax.scatter(donnees["GWP publié g/kWh"], y, marker="D", s=44,
               facecolor="white", edgecolor="black", linewidth=0.9, zorder=5)

    ax.set_yticks(y)
    ax.set_yticklabels(donnees["systeme"], fontsize=9)
    ax.set_ylim(n - 0.5, -0.5)                      # première ligne en haut
    ax.set_xlim(0, float(donnees["GWP harmonisé g/kWh"].max()) * 1.19)
    ref_lisible = f"{productible_ref:,.0f}".replace(",", " ")
    ax.set_xlabel(f"GWP100 harmonised to {ref_lisible} kWh kWp⁻¹ yr⁻¹, "
                  f"{duree_ref:.0f} yr (g CO₂-eq kWh⁻¹)", fontsize=9.5)
    ax.xaxis.set_major_locator(plt.MultipleLocator(25))
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="x", ls=":", color="#BBBBBB", alpha=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)

    # ── Colonnes chiffrées ────────────────────────────────────────────────
    _colonne(ax_gwp, y, [f"{v:.1f}" for v in donnees["GWP harmonisé g/kWh"]],
             "GWP$_{harm}$", gras=True)
    _colonne(ax_alu, y, [_format_alu(v) for v in donnees["kg Al/kWc"]],
             "kg Al kWp$^{-1}$", couleur="#555555")

    # ── Légende ───────────────────────────────────────────────────────────
    poignees = [plt.Rectangle((0, 0), 1, 1, color=COULEURS_CATEGORIES[cle])
                for cle in CATEGORIES]
    labels = list(CATEGORIES.values())
    poignees.append(plt.Line2D([], [], marker="D", ls="", markersize=7,
                               markerfacecolor="white",
                               markeredgecolor="black", markeredgewidth=0.9))
    labels.append("Value as published (before harmonisation)")
    if "harmonisé p5 g/kWh" in donnees and donnees["harmonisé p5 g/kWh"].notna().any():
        poignees.append(plt.Line2D([], [], color="#333333", lw=1.3,
                                   marker="|", markersize=8))
        labels.append("5th–95th percentile (Monte-Carlo)")
    fig.legend(poignees, labels, loc="lower center", ncol=3, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, 0.005),
               handlelength=1.5, columnspacing=2.0, labelspacing=0.45)

    if titre:
        fig.suptitle(titre, fontsize=12, weight="bold")
    return fig


def _colonne(ax, y, textes, entete, gras=False, couleur="black"):
    """Colonne de texte alignée sur les lignes du graphe.

    ⚠ On masque les décorations SANS toucher aux ticks de l'axe y : il est
    partagé avec le panneau principal (`sharey`), et un `set_yticks([])` ou un
    `axis("off")` ici effacerait les NOMS DES ÉTUDES à gauche de la figure.
    """
    ax.set_xlim(0, 1)
    ax.patch.set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    for cote in ("top", "right", "bottom", "left"):
        ax.spines[cote].set_visible(False)
    for yi, texte in zip(y, textes):
        ax.text(0.5, yi, texte, ha="center", va="center", fontsize=9.5,
                fontweight="bold" if gras else "normal", color=couleur)
    ax.text(0.5, -0.95, entete, ha="center", va="center", fontsize=9.5,
            fontweight="bold" if gras else "normal", color=couleur,
            clip_on=False)
    # Filet de séparation, à gauche de la colonne.
    ax.axvline(0.0, color="#CCCCCC", lw=0.9, ymin=-0.02, ymax=1.06,
               clip_on=False)


def _panneau_reseau(ax, n):
    """Les kWh de réseau déplacés — autre échelle, donc autre panneau.

    Les mettre sur l'axe principal écraserait les onze barres contre zéro :
    914 g contre 24 à 131. On garde donc deux échelles et on l'écrit.
    """
    ax.set_xlim(0, 1000)
    ax.set_ylim(n - 0.5, -0.5)
    # Même précaution que dans `_colonne` : l'axe y est partagé, on masque
    # sans effacer.
    ax.tick_params(left=False, labelleft=False)
    ax.set_xticks([0, 250, 500, 750, 1000])
    ax.tick_params(axis="x", labelsize=9)
    ax.set_xlabel("Displaced grid electricity\n(g CO₂-eq kWh⁻¹)", fontsize=9.5)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.grid(axis="x", ls=":", color="#BBBBBB", alpha=0.8)
    ax.set_axisbelow(True)
    ax.axvline(0.0, color="#CCCCCC", lw=0.9, ymin=-0.02, ymax=1.02,
               clip_on=False)

    for rang, (libelle, (valeur, couleur)) in enumerate(REFERENCES_RESEAU.items()):
        yi = 1.35 + rang * 3.0
        ax.barh([yi], [valeur], height=0.62, color=couleur, zorder=3)
        ax.text(0, yi - 0.72, libelle, fontsize=9, va="center", ha="left")
        ax.text(valeur - 8, yi, f"{valeur:.0f}", fontsize=9.5, weight="bold",
                color="white", va="center", ha="right", zorder=4)

    ax.text(0.015, n - 1.1, "different x-scale", fontsize=8.5, style="italic",
            color="#777777", transform=ax.get_yaxis_transform(),
            va="center", ha="left")


def figure_intensite(tab: pd.DataFrame, article_seulement=True, titre=None):
    """Intensité structurelle (kg CO₂-eq/kWc) — la grandeur réellement comparée.

    La figure du § 4.2 n'est que celle-ci divisée par l'énergie de référence.
    La tracer telle quelle évite de laisser croire que l'harmonisation produit
    un « vrai » GWP/kWh pour un site où le système n'est pas installé.
    """
    _exiger_cette_etude(tab, "Intensité structurelle kg CO₂/kWc")
    donnees = tab[tab["dans_article"]] if article_seulement else tab
    donnees = (donnees.dropna(subset=["Intensité structurelle kg CO₂/kWc"])
               .sort_values("Intensité structurelle kg CO₂/kWc")
               .reset_index(drop=True))

    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    y = np.arange(len(donnees))
    barres = ax.barh(y, donnees["Intensité structurelle kg CO₂/kWc"],
                     height=0.62, color=[COULEURS_CATEGORIES.get(c, "#808080")
                                         for c in donnees["categorie"]])
    for barre, fiabilite in zip(barres, donnees["fiabilite"]):
        if fiabilite != "solide":
            barre.set_hatch("///")
            barre.set_edgecolor("white")
    for barre, valeur in zip(barres, donnees["Intensité structurelle kg CO₂/kWc"]):
        ax.text(valeur, barre.get_y() + barre.get_height() / 2,
                f" {valeur:,.0f}".replace(",", " "), va="center", fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(donnees["systeme"], fontsize=9)
    for etiquette, est_nous in zip(ax.get_yticklabels(), donnees["cette_etude"]):
        if est_nous:
            etiquette.set_fontweight("bold")
    ax.set_ylim(len(donnees) - 0.5, -0.5)
    ax.set_xlim(0, float(donnees["Intensité structurelle kg CO₂/kWc"].max()) * 1.16)
    ax.set_xlabel("Embodied carbon (kg CO₂-eq per kWp installed)")
    ax.set_title(titre or "Embodied carbon per installed kWp, "
                          "independent of the solar resource")
    ax.grid(axis="x", ls=":", alpha=0.5)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)

    poignees = [plt.Rectangle((0, 0), 1, 1, color=COULEURS_CATEGORIES[cle])
                for cle in CATEGORIES if cle in set(donnees["categorie"])]
    labels = [libelle for cle, libelle in CATEGORIES.items()
              if cle in set(donnees["categorie"])]
    ax.legend(poignees, labels, fontsize=8.5, loc="lower right", frameon=False)
    plt.tight_layout()
    return fig


def figures(ctx=None, jeux=None, incertitudes=None, verbeux=True) -> dict:
    """Les figures du § 4.2, en un appel. {nom de fichier: Figure}."""
    tab = harmoniser(ctx, jeux, incertitudes=incertitudes, verbeux=verbeux)
    return {
        "F13_benchmark_litterature": figure_benchmark(tab),
        "F14_intensite_structurelle": figure_intensite(tab),
    }
