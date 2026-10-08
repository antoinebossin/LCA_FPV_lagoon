"""
Garde-fous. À exécuter après chaque reconstruction du modèle.

Trois contrôles, chacun répondant à un risque identifié :

1. `verifier_parametres` — un nom de paramètre inconnu passé à
   `compute_impacts` est SILENCIEUSEMENT ignoré par lca_algebraic (simple
   `warn`). C'est le piège le plus dangereux du modèle : une faute de frappe
   sur `power_plant_installed_capacity` fait tourner tout le calcul sur la
   valeur par défaut de parasol sans le moindre message d'erreur visible.
   Ce contrôle lève une exception.

2. `verifier_masse_panneaux` — compare la masse de modules déclarée en fin de
   vie (`m_panneaux_kg`, fiches CS Wismar) à la masse implicite de l'inventaire
   de fabrication (verre + cadre + encapsulant + backsheet, évalués sur les
   mêmes paramètres). C'est le contrôle demandé par le reviewer : ce qui part
   au recyclage doit être ce qui a été fabriqué.

3. `verifier_nominal` — vérifie qu'une analyse en aval retrouve bien le
   résultat de référence. Remplace le `check_nominal` de l'ancien notebook,
   qui existait parce que `freezeParams` contaminait les analyses suivantes.
   Ici il ne sert plus que de filet de sécurité.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config, panneaux
from .modalites import DONNEES

TOLERANCE_MASSE = 0.15      # 15 % d'écart accepté entre inventaire et fiche
TOLERANCE_NOMINAL = 0.001   # 0,1 % de dérive acceptée


def verifier_parametres(valeurs: dict, strict=True):
    """Vérifie que chaque clé correspond à un paramètre réellement déclaré."""
    connus = set(agb.all_params())
    # les enums sont adressables par leur nom ; les booléens aussi
    inconnus = sorted(k for k in valeurs if k not in connus)
    if inconnus:
        message = (
            "Paramètres inconnus : " + ", ".join(inconnus) + ".\n"
            "lca_algebraic les ignorerait silencieusement (le calcul tournerait "
            "sur les valeurs par défaut). Paramètres disponibles :\n  "
            + "\n  ".join(sorted(connus)))
        if strict:
            raise KeyError(message)
        print("⚠ " + message)
        return False
    print(f"[check] {len(valeurs)} paramètres, tous reconnus ✓")
    return True


def verifier_masse_panneaux(ctx, valeurs: dict, libelle="", strict=False):
    """Compare la masse fiche fabricant à la masse implicite de l'inventaire."""
    kg_par_m2, detail = panneaux.masse_module_implicite(ctx, valeurs)
    if kg_par_m2 <= 0:
        print("⚠ [check] masse implicite du module non évaluable "
              "(formules non résolues) — contrôle ignoré.")
        return None

    surface_module = _surface_module(libelle)
    masse_inventaire = kg_par_m2 * surface_module
    n_modules = float(valeurs.get("n_modules", 1))
    masse_declaree = float(valeurs["m_panneaux_kg"]) / n_modules
    ecart = (masse_inventaire - masse_declaree) / masse_declaree

    print(f"[check] masse d'un module {libelle or ''} : "
          f"inventaire {masse_inventaire:.1f} kg vs fiche {masse_declaree:.1f} kg "
          f"({ecart*100:+.1f} %)")
    for nom_flux, valeur in sorted(detail.items(), key=lambda kv: -kv[1])[:6]:
        print(f"          {valeur*surface_module:7.2f} kg  {nom_flux[:60]}")

    if abs(ecart) > TOLERANCE_MASSE:
        message = (
            f"Incohérence fabrication / fin de vie : l'inventaire décrit un "
            f"module de {masse_inventaire:.1f} kg, la fin de vie en recycle "
            f"{masse_declaree:.1f} kg ({ecart*100:+.1f} %). Corrige soit "
            f"m_panneaux_kg, soit les paramètres du module (épaisseur de verre, "
            f"cadre alu, bifacialité).")
        if strict:
            raise AssertionError(message)
        print("⚠ " + message)
    return ecart


def _surface_module(libelle):
    if libelle in DONNEES:
        return DONNEES[libelle]["surface_module"]
    return 1.99


class Reference:
    """Mémorise un résultat de référence et détecte les dérives."""

    def __init__(self, valeur, libelle="référence"):
        self.valeur = float(valeur)
        self.libelle = libelle
        print(f">>> {libelle} = {self.valeur:.6f} kg CO2-eq/kWh "
              f"({self.valeur*1000:.1f} g)")

    def verifier(self, valeur, etape, strict=False):
        derive = (float(valeur) - self.valeur) / self.valeur
        etat = "OK" if abs(derive) <= TOLERANCE_NOMINAL else "*** DÉRIVE ***"
        print(f"[check] {etape:<40} {float(valeur):.6f} "
              f"({derive*100:+.3f} % vs {self.libelle})  {etat}")
        if strict and abs(derive) > TOLERANCE_NOMINAL:
            raise AssertionError(
                f"Dérive de {derive*100:+.3f} % à l'étape « {etape} » : "
                "le modèle n'est plus celui du résultat principal.")
        return derive


def verifier_couverture_axes(df_axe, tolerance=0.01):
    """Vérifie que la ventilation par poste couvre bien 100 % de l'impact.

    `compute_impacts(axis=...)` ajoute une ligne de total et une ligne de
    résidu, dont les noms varient selon la version de lca_algebraic
    (« *sum* »/« *all* » et « _other_ »/« *other* »). Un résidu non négligeable
    signale qu'une partie de l'arbre n'est rattachée à aucun poste — voir
    `resultats.contribution_directe()` pour la localiser.
    """
    from .resultats import totaux_axe

    _, total, reste = totaux_axe(df_axe)
    if total is None or reste is None:
        print("⚠ [check] pas de ligne de total ou de résidu dans le tableau "
              "par axe — vérifie les libellés de ta version de lca_algebraic.")
        return None

    part = (reste / total).abs().max()
    if part > tolerance:
        print(f"⚠ [check] {part*100:.1f} % de l'impact n'est rattaché à aucun "
              f"poste. Deux causes possibles :\n"
              f"    1. une activité de 1er niveau n'a pas d'attribut "
              f"« {config.AXE} » ;\n"
              f"    2. une activité de premier plan est partagée entre deux "
              f"postes tagués — l'algorithme d'axe ne sait alors pas à qui "
              f"l'attribuer.\n"
              f"    Lance resultats.contribution_directe(ctx, valeurs) pour "
              f"localiser le poste concerné.")
    else:
        print(f"[check] ventilation par poste complète "
              f"(reste non attribué : {part*100:.2f} %) ✓")
    return part
