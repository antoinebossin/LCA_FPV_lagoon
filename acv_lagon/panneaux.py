"""
Poste « Panneaux PV ».

On reprend la brique parasol (`photovoltaic panel production … - adjusted`),
qui porte déjà toute la chaîne silicium → wafer → cellule → module avec ses
paramètres (épaisseur de verre, cadre alu, teneur en argent, mix électrique de
fabrication, recyclage des chutes de production).

Deux ajustements propres au projet :

1. **Packing des cellules.** L'entrée « photovoltaic cell » du module parasol
   est fixée à 0,90 m²/m². Nos modules semi-transparents (SH51-UV, SH81-UV)
   n'ont pas la même surface de cellules : on rebranche cette entrée sur le
   paramètre `packing_cellules`. C'est le seul endroit du package où l'on
   modifie une activité parasol — on ne peut pas la copier, `copyActivity`
   supprimant les formules paramétriques.

2. **Surface.** Le module parasol est exprimé au m². Notre système en
   consomme `puissance / rendement` m², c'est-à-dire la surface de modules
   réellement installée sur la plateforme.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import parasol_bridge

# Motifs d'exchanges à rebrancher (les noms varient un peu selon la version).
MOTIFS_CELLULE = ["photovoltaic cell*", "photovoltaic cell, multi-Si wafer*",
                  "photovoltaic cell, single-Si wafer*"]


def construire(ctx):
    """Renvoie l'activité panneau à utiliser dans le système, paramétrée."""
    panneau = parasol_bridge.panneau(ctx)
    _brancher_packing(ctx, panneau)
    # Tag d'axe : tout l'amont du module (silicium, wafer, cellule, verre,
    # cadre, énergie de fabrication) sera imputé au poste « Panneaux ».
    from . import config
    panneau.updateMeta(**{config.AXE: "Panneaux"})
    return panneau


def surface_modules(ctx):
    """Surface de modules installée sur une plateforme, en m².

    surface = puissance crête / rendement surfacique  (kWp ÷ kWp/m²)
    """
    return ctx.p.p_install_kwc / ctx.p.rendement_module


def _brancher_packing(ctx, panneau):
    """Remplace le montant fixe de l'entrée « cellule » par notre paramètre."""
    for motif in MOTIFS_CELLULE:
        try:
            panneau.updateExchanges({motif: ctx.p.packing_cellules})
            print(f"  packing cellules branché sur « {motif} » "
                  f"de {panneau['name']}")
            return
        except Exception:
            continue

    # Repli : on cherche à la main l'échange dont le produit contient 'cell'
    for exc in panneau.technosphere():
        if "photovoltaic cell" in exc.input["name"].lower():
            panneau.updateExchanges({exc.input["name"] + "*": ctx.p.packing_cellules})
            print(f"  packing cellules branché (repli) sur « {exc.input['name']} »")
            return

    raise LookupError(
        f"Aucune entrée « photovoltaic cell » trouvée dans {panneau['name']}. "
        "Inspecte l'activité avec agb.printAct(...) et complète MOTIFS_CELLULE.")


def masse_module_implicite(ctx, valeurs_params):
    """Masse d'un module, telle qu'elle découle de l'INVENTAIRE parasol.

    On somme les entrées du panneau dont le dataset cible est en kilogramme,
    évaluées pour un jeu de paramètres donné, puis on multiplie par la surface
    unitaire du module. Sert au garde-fou de cohérence fin de vie (cf.
    `checks.verifier_masse_panneaux`) : la masse envoyée au recyclage doit
    correspondre à la masse effectivement fabriquée.

    Returns
    -------
    kg par m² de module (float)
    """
    from lca_algebraic.params import _getAmountOrFormula

    panneau = parasol_bridge.panneau(ctx)
    total = 0.0
    detail = {}
    ignores = []

    for exc in panneau.technosphere():
        if "kilogram" not in str(exc.input.get("unit", "")).lower():
            continue
        nom_flux = exc.input["name"]
        if _hors_bilan_matiere(nom_flux):
            continue

        valeur = _evaluer(_getAmountOrFormula(exc), valeurs_params)
        if valeur is None:
            ignores.append(nom_flux)
            continue
        if valeur <= 0:
            continue
        total += valeur
        detail[nom_flux] = valeur

    if ignores:
        print(f"  ({len(ignores)} flux non évaluables ignorés : "
              f"{', '.join(n[:40] for n in ignores[:3])}…)")
    return total, detail


# Flux facturés au kilogramme mais qui ne sont PAS de la matière restant dans
# le module. Sans ce filtre, l'inventaire parasol donne 91 kg pour un module de
# 26 kg : 42 kg d'eau de procédé, 20 kg de « tempering, flat glass » (un SERVICE
# de trempe, facturé au kg de verre traité — le verre est déjà compté), et
# 2 kg d'emballage carton.
HORS_BILAN_MATIERE = (
    "water",              # eau de procédé, évacuée
    "tempering",          # service de trempe du verre (déjà compté en verre)
    "corrugated board",   # emballage
    "packaging",
    "pallet",
    "scrap",              # chutes recyclées = sorties
    "waste",
    "treatment of",
    "transport",
    "electricity",
    "heat",
)


def _hors_bilan_matiere(nom_flux: str) -> bool:
    nom = nom_flux.lower()
    return any(mot in nom for mot in HORS_BILAN_MATIERE)


def _evaluer(montant, valeurs_params):
    """Valeur numérique d'un montant d'échange (constante ou formule Sympy).

    `agb.compute_expr_value` attend le dict de paramètres en argument POSITIONNEL
    (pas en kwargs) et complète lui-même les paramètres manquants par leur valeur
    par défaut.
    """
    if montant is None:
        return None
    if isinstance(montant, (int, float)):
        return float(montant)
    try:
        return float(agb.compute_expr_value(montant, valeurs_params))
    except Exception:      # noqa: BLE001 — flux non évaluable, on le signale
        return None
