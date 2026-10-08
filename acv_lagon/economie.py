# -*- coding: utf-8 -*-
"""
CAPEX et LCOE du démonstrateur, et positionnement dans le corpus FPV.

────────────────────────────────────────────────────────────────────────────
D'OÙ VIENNENT LES CHIFFRES

Le CAPEX est celui de l'onglet « Calcul CAPEX » de `Scenarios_financiers_V2.xlsx`
(dépenses réelles arrêtées au 20/02/2025), qu'Antoine tient à jour et qui fait
foi. Le modèle de LCOE ci-dessous ré-implémente l'onglet « Calcul LCOE » du
même classeur : il est vérifié en rejouant ses valeurs (`verifier_lcoe()`), et
non recopié. Si le classeur bouge, c'est le test qui le dira.

⚠ DEUX JEUX DE CAPEX COEXISTENT, ET IL FAUT TRANCHER

  · `CAPEX_REFERENCE` — août 2026, 292 586 € pour le parc. La fibre optique
    (2 020 €) et la liaison satellite Sofar (5 596 €) en ont été retirées
    comme hors projet, et l'estimation « mise en place du câble, 6 400 € » a
    été remplacée par le coût réel Sunzil de 35 000 € (pose des onduleurs et
    des câbles, 8 750 € par plateforme).

  · `CAPEX_MANUSCRIT` — le tableau 4 de l'article, 298 986 €, soit exactement
    6 400 € de plus, répartis à 1 600 € par plateforme. Sa légende dit encore
    « laying of the submarine cable, carried out in-house and valued at
    €6 400 ».

    Autrement dit le manuscrit ajoute une estimation que la référence a déjà
    remplacée par un coût réel. Si les deux décrivent bien la même dépense,
    le manuscrit la compte DEUX FOIS. À confirmer avant soumission : c'est
    1 600 € par plateforme, soit 2 % du CAPEX unitaire et autant sur le LCOE.

Par défaut on calcule sur `CAPEX_ARTICLE`, c'est-à-dire sur le tableau 4 tel
qu'il est écrit dans le manuscrit : le but est que le texte, les tableaux et
les figures de l'article disent tous la même chose. Passer
`capex=CAPEX_REFERENCE` donne l'autre lecture ; l'écart sur le LCOE est de
2 %, il ne change aucun classement ni aucune conclusion.

────────────────────────────────────────────────────────────────────────────
CE QUE LE LCOE N'EST PAS

Un LCOE de démonstrateur n'est pas un LCOE de technologie. Quatre plateformes
de 40 kWc posées sur un lagon à 17 000 km de l'usine portent des coûts fixes
— ingénierie, fret, mission d'installation — qu'une centrale amortit sur mille
fois plus de puissance. Le chiffre sert à SITUER, pas à conclure, et c'est
ainsi qu'il faut l'écrire dans l'article.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ══════════════════════════════════════════════════════════════════════════
# 1. Données d'entrée
# ══════════════════════════════════════════════════════════════════════════
ORDRE = ["SH81", "SH51", "SH81-UV", "SH51-UV"]
PUISSANCE_KWC = {"SH81": 11.06, "SH51": 7.90, "SH81-UV": 13.05, "SH51-UV": 7.65}

CAPEX_REFERENCE = {"SH81": 71401.77, "SH51": 67130.78,
                   "SH81-UV": 80791.36, "SH51-UV": 73261.77}
CAPEX_MANUSCRIT = {"SH81": 73002.0, "SH51": 68731.0,
                   "SH81-UV": 82391.0, "SH51-UV": 74862.0}
# Ce que l'article publie. À rebasculer sur CAPEX_REFERENCE si Antoine
# confirme le double comptage des 6 400 € de pose de câble.
CAPEX_ARTICLE = CAPEX_MANUSCRIT

# Remplacement des onduleurs à l'année 15, par plateforme.
RECAPEX_ONDULEURS_AN15 = {"SH81": 8784.52, "SH51": 6274.66,
                          "SH81-UV": 14431.71, "SH51-UV": 6902.12}
# Remplacement des flotteurs à l'année 20 : seuls les 9 flotteurs montés sont
# changés (9 × 280 €) plus 2 500 € de pose.
RECAPEX_FLOTTEURS_AN20 = 9 * 280.0 + 2500.0

OPEX_ANNUEL = 691.52          # € par plateforme et par an
DUREE_VIE_AN = 30
# Source unique : le productible est déclaré dans `parametres.py`. Le classeur
# `Scenarios_financiers_V2.xlsx` (onglet « Calcul LCOE », cellule B5) porte la
# MÊME valeur, mise à jour le 26/09/2026 en même temps que celle-ci. Les deux
# doivent bouger ensemble, sans quoi `verifier_lcoe` le dira.
# Lu À L'APPEL, à travers le module : voir la note de `litterature`.
from . import parametres as _par                # noqa: E402  (source unique)
# ⚠ PAS DE SECONDE CONSTANTE. Le taux de dégradation est déclaré une seule
# fois, dans `parametres.py`, et lu ICI À L'APPEL. Un
# `DEGRADATION = 0.0070` recopié dans ce module serait la façon la plus sûre
# de publier un jour une intensité carbone calculée à 0,70 %/an et un coût
# actualisé calculé à 0,35 %/an, sans que rien ne le signale.
#
# Une exception, et une seule : `verifier_lcoe` compare le modèle au
# CLASSEUR, qui a été bâti sur la garantie fabricant. Ce test doit donc figer
# sa propre valeur — il teste la FORMULE, pas le scénario du jour.
DEGRADATION_CLASSEUR = 0.0035   # ce que porte Scenarios_financiers_V2.xlsx
# Idem pour le productible : la cellule B5 du classeur porte 1 096 kWh/kWc, le
# productible reconstruit à PLEINE disponibilité. Depuis le 06/10/2026 le
# modèle applique 97 % de disponibilité (`parametres.TAUX_DISPONIBILITE`) ; le
# test, lui, doit rester sur la valeur du classeur, sans quoi il échoue de
# 3 % sans que la formule soit en cause (constaté au run v6_10).
PRODUCTIBLE_CLASSEUR = 1096.0
TAUX = (0.06, 0.08, 0.10)
TAUX_REFERENCE = 0.08

# Valeurs de contrôle, telles que le classeur les sort (€/kWh).
# ⚠ Relevées dans le classeur APRÈS passage de B5 à 1 096 kWh/kWc (26/09/2026).
# Si le productible change encore, il faut changer les deux : la cellule B5 du
# classeur et ce tableau. C'est le prix d'un test qui compare deux choses.
LCOE_ATTENDU = {
    0.06: {"SH81": 0.536, "SH51": 0.704, "SH81-UV": 0.516, "SH51-UV": 0.784},
    0.08: {"SH81": 0.629, "SH51": 0.826, "SH81-UV": 0.604, "SH51-UV": 0.923},
    0.10: {"SH81": 0.728, "SH51": 0.957, "SH81-UV": 0.699, "SH51-UV": 1.070},
}

# ══════════════════════════════════════════════════════════════════════════
# 2. Le modèle
# ══════════════════════════════════════════════════════════════════════════
def energie_annuelle(code, p0=None, degradation=None,
                     duree=DUREE_VIE_AN):
    """kWh produits chaque année, dégradation linéaire depuis la 1re année."""
    p0 = _par.PRODUCTIBLE_P0 if p0 is None else p0
    degradation = (_par.TAUX_DEGRADATION if degradation is None
                   else degradation)
    annees = np.arange(1, duree + 1)
    return PUISSANCE_KWC[code] * p0 * (1.0 - degradation * (annees - 1))


def lcoe(code, taux=TAUX_REFERENCE, capex=None, duree=DUREE_VIE_AN,
         opex=OPEX_ANNUEL, p0=None, degradation=None):
    """LCOE en €/kWh : coûts actualisés sur énergie actualisée.

    Les deux termes sont actualisés au MÊME taux — c'est la définition, et
    c'est aussi l'erreur la plus fréquente que d'actualiser les coûts sans
    actualiser l'énergie, ce qui donne un LCOE flatteur d'un facteur 2.
    """
    capex = (capex or CAPEX_ARTICLE)[code]
    annees = np.arange(1, duree + 1)
    actualisation = (1.0 + taux) ** annees

    couts = capex + float(np.sum(opex / actualisation))
    if duree >= 15:
        couts += RECAPEX_ONDULEURS_AN15[code] / (1.0 + taux) ** 15
    if duree >= 20:
        couts += RECAPEX_FLOTTEURS_AN20 / (1.0 + taux) ** 20

    energie = float(np.sum(
        energie_annuelle(code, p0=p0, duree=duree, degradation=degradation)
        / actualisation))
    return couts / energie


def capex_unitaire(code, capex=None):
    """€ par Wc installé."""
    return (capex or CAPEX_ARTICLE)[code] / (PUISSANCE_KWC[code] * 1000.0)


def table(capex=None, taux=TAUX, verbeux=True) -> pd.DataFrame:
    """Le tableau économique des quatre plateformes, plus le parc."""
    capex = capex or CAPEX_ARTICLE
    lignes = []
    for code in ORDRE:
        ligne = {"configuration": code, "kWc": PUISSANCE_KWC[code],
                 "CAPEX €": capex[code], "CAPEX €/Wc": capex_unitaire(code, capex)}
        for t in taux:
            ligne[f"LCOE €/kWh @{t:.0%}"] = lcoe(code, t, capex)
        lignes.append(ligne)

    tab = pd.DataFrame(lignes).set_index("configuration")

    # Le parc : un LCOE de parc est le rapport des SOMMES, pas la moyenne des
    # rapports. Une moyenne arithmétique des quatre LCOE donnerait un chiffre
    # qui ne correspond à aucun flux réel.
    total_kwc = sum(PUISSANCE_KWC.values())
    parc = {"kWc": total_kwc, "CAPEX €": sum(capex.values()),
            "CAPEX €/Wc": sum(capex.values()) / (total_kwc * 1000.0)}
    for t in taux:
        annees = np.arange(1, DUREE_VIE_AN + 1)
        act = (1.0 + t) ** annees
        couts = sum(capex[c] + float(np.sum(OPEX_ANNUEL / act))
                    + RECAPEX_ONDULEURS_AN15[c] / (1 + t) ** 15
                    + RECAPEX_FLOTTEURS_AN20 / (1 + t) ** 20 for c in ORDRE)
        energie = sum(float(np.sum(energie_annuelle(c) / act)) for c in ORDRE)
        parc[f"LCOE €/kWh @{t:.0%}"] = couts / energie
    tab.loc["Array"] = parc

    if verbeux:
        print(tab.round(3).to_string())
    return tab


def verifier_lcoe(tolerance=0.01, verbeux=True) -> bool:
    """Le modèle rejoue-t-il les valeurs du classeur ?

    Sans ce test, rien ne dit que la ré-implémentation décrit le même calcul
    que l'onglet Excel — et un LCOE faux passe inaperçu, puisqu'il n'a pas
    d'ordre de grandeur évident.
    """
    ok = True
    for taux, attendus in LCOE_ATTENDU.items():
        for code, attendu in attendus.items():
            calcule = lcoe(code, taux, capex=CAPEX_REFERENCE,
                           p0=PRODUCTIBLE_CLASSEUR,
                           degradation=DEGRADATION_CLASSEUR)
            ecart = abs(calcule - attendu) / attendu
            bon = ecart <= tolerance
            ok &= bon
            if verbeux:
                print(f"  {'✓' if bon else '✗'} LCOE {code:<8} @{taux:.0%} "
                      f"calculé {calcule:.3f} vs classeur {attendu:.3f} "
                      f"({ecart*100:+.1f} %)")
    if verbeux:
        print("  →", "le modèle reproduit le classeur" if ok
              else "ÉCART : le modèle ne décrit pas le même calcul")
    return ok


# ══════════════════════════════════════════════════════════════════════════
# 3. Positionnement dans le corpus FPV commercial
# ══════════════════════════════════════════════════════════════════════════
# ⚠ PROVISOIRE. Statistiques relevées À L'ŒIL sur les figures 11 et 12 de
# Rodríguez-Gallegos et al., qui publient la base SERIS. Antoine a demandé les
# données sources aux auteurs : dès qu'elles arrivent, on remplace ce bloc et
# rien d'autre. Les valeurs ci-dessous ne doivent PAS être citées dans le
# texte de l'article tant que ce remplacement n'est pas fait.
TAUX_EUR_USD = 1.08           # à figer sur le taux moyen de l'année citée

# année : (moustache basse, Q1, médiane, Q3, moustache haute) en USD/Wc
CAPEX_SERIS_USD_WC = {
    2015: (2.35, 3.35, 3.40, 4.05, 4.05),
    2016: (1.20, 1.85, 2.15, 2.75, 4.40),
    2017: (1.15, 1.60, 2.20, 2.50, 3.45),
    2018: (0.85, 1.20, 1.80, 2.45, 3.25),
    2019: (0.95, 1.15, 1.50, 2.40, 2.95),
    2020: (0.55, 0.85, 1.25, 1.85, 3.00),
    2021: (0.40, 0.75, 0.95, 1.60, 2.20),
    2022: (0.45, 0.80, 1.10, 1.50, 2.60),
}
# Prix de l'électricité annoncé (USD/kWh) : la droite de régression publiée
# (R² = 0,55) et l'étendue du nuage des dernières années.
PRIX_SERIS_USD_KWH = {"pente": -0.0246, "origine_annee": 2010, "origine": 0.41,
                      "nuage_2022": (0.045, 0.16)}


def _ecarter(valeurs, mini):
    """Écarte verticalement des étiquettes trop proches, sans changer l'ordre.

    Deux plateformes séparées par 0,02 €/Wc voient leurs libellés se
    chevaucher. On décale les TEXTES, jamais les points : le lecteur doit
    pouvoir lire la valeur, et la position du marqueur reste exacte.
    """
    ordre = sorted(range(len(valeurs)), key=lambda i: valeurs[i])
    posees = list(valeurs)
    for rang in range(1, len(ordre)):
        i, precedent = ordre[rang], ordre[rang - 1]
        if posees[i] - posees[precedent] < mini:
            posees[i] = posees[precedent] + mini
    return posees


def figure_positionnement(capex=None, taux=TAUX_REFERENCE, titre=None,
                          verbeux=True):
    """Où tombent les quatre plateformes dans le corpus FPV commercial.

    Deux panneaux et NON deux axes sur une même figure : le CAPEX est en €/Wc
    et le coût de l'électricité en €/kWh, deux grandeurs sans rapport
    d'échelle. Les superposer sur un double axe laisserait croire à une
    corrélation que la figure ne montre pas.
    """
    tab = table(capex=capex, taux=(taux,), verbeux=False)
    cle = f"LCOE €/kWh @{taux:.0%}"
    couleurs = {"SH81": "#F2C14E", "SH51": "#4FB3BF",
                "SH81-UV": "#4E9F6B", "SH51-UV": "#F26D9B", "Array": "#333333"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.6))

    # ── panneau A : CAPEX ────────────────────────────────────────────────
    annees = sorted(CAPEX_SERIS_USD_WC)
    stats = [dict(label=str(a), whislo=CAPEX_SERIS_USD_WC[a][0] / TAUX_EUR_USD,
                  q1=CAPEX_SERIS_USD_WC[a][1] / TAUX_EUR_USD,
                  med=CAPEX_SERIS_USD_WC[a][2] / TAUX_EUR_USD,
                  q3=CAPEX_SERIS_USD_WC[a][3] / TAUX_EUR_USD,
                  whishi=CAPEX_SERIS_USD_WC[a][4] / TAUX_EUR_USD, fliers=[])
             for a in annees]
    ax1.bxp(stats, showfliers=False, widths=0.55,
            boxprops=dict(facecolor="#D9D9D9", edgecolor="#808080"),
            medianprops=dict(color="#333333", lw=1.6),
            whiskerprops=dict(color="#808080"),
            capprops=dict(color="#808080"), patch_artist=True)
    codes = ORDRE + ["Array"]
    vals1 = [tab.loc[c, "CAPEX €/Wc"] for c in codes]
    textes1 = _ecarter(vals1, 0.42)
    for code, v, yt in zip(codes, vals1, textes1):
        ax1.scatter(len(annees) + 0.9, v, s=95, zorder=5,
                    color=couleurs[code], edgecolor="white", linewidth=1.2)
        ax1.plot([len(annees) + 0.98, len(annees) + 1.12], [v, yt],
                 color="#999999", lw=0.7, zorder=4)
        ax1.annotate(f"{code}  {v:.2f}", (len(annees) + 1.15, yt), fontsize=8,
                     va="center", ha="left", color="#222222")
    ax1.axvline(len(annees) + 0.45, color="#BBBBBB", ls=":", lw=1)
    ax1.set_xlim(0.4, len(annees) + 2.9)
    ax1.set_ylabel("CAPEX (€/Wc)")
    ax1.set_title("A. Capital cost", fontsize=11, weight="bold", loc="left")
    ax1.grid(axis="y", ls=":", alpha=0.45)
    ax1.set_axisbelow(True)

    # ── panneau B : coût de l'électricité ────────────────────────────────
    p = PRIX_SERIS_USD_KWH
    xs = np.array([2010, 2023])
    ax2.plot(xs, (p["origine"] + p["pente"] * (xs - p["origine_annee"]))
             / TAUX_EUR_USD, color="#808080", lw=1.6,
             label="SERIS announced price, published trend")
    bas, haut = (v / TAUX_EUR_USD for v in p["nuage_2022"])
    ax2.fill_between([2020, 2023], bas, haut, color="#D9D9D9", alpha=0.75,
                     label="recent announced prices")
    vals2 = [tab.loc[c, cle] for c in codes]
    textes2 = _ecarter(vals2, max(vals2) * 0.075)
    for code, v, yt in zip(codes, vals2, textes2):
        ax2.scatter(2025.2, v, s=95, zorder=5, color=couleurs[code],
                    edgecolor="white", linewidth=1.2)
        ax2.plot([2025.35, 2025.55], [v, yt], color="#999999", lw=0.7, zorder=4)
        ax2.annotate(f"{code}  {v:.2f}", (2025.6, yt), fontsize=8,
                     va="center", ha="left", color="#222222")
    ax2.axvline(2024.4, color="#BBBBBB", ls=":", lw=1)
    ax2.set_xlim(2009, 2029.5)
    ax2.set_xticks(list(range(2010, 2027, 3)))    # des années entières
    ax2.set_ylim(0, max(tab[cle]) * 1.18)
    ax2.set_ylabel(f"Levelised cost of electricity (€/kWh, {taux:.0%} discount rate)")
    ax2.set_xlabel("Completion year")
    ax2.set_title("B. Cost of electricity", fontsize=11, weight="bold", loc="left")
    ax2.grid(ls=":", alpha=0.45)
    ax2.set_axisbelow(True)
    ax2.legend(fontsize=7.5, loc="upper right", frameon=False)

    fig.suptitle(titre or "The Raiatea demonstrator against commercial "
                 "floating PV (SERIS database)", fontsize=12, weight="bold")
    fig.text(0.5, 0.015,
             "Grey: commercial FPV projects, read from the published figures of "
             "Rodríguez-Gallegos et al. Provisional values, to be replaced by the "
             f"source data. Converted at {TAUX_EUR_USD:.2f} USD/€.",
             ha="center", fontsize=7.5, color="#555555")
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    if verbeux:
        print(f"  positionnement : CAPEX {tab.loc['Array','CAPEX €/Wc']:.2f} €/Wc, "
              f"LCOE {tab.loc['Array', cle]:.3f} €/kWh pour le parc")
    return fig
