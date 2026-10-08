"""
Assemblage : NOTRE « Full PV system ».

Réponse au commentaire 3 du reviewer (« pourquoi ne pas construire ton propre
Full PV system plutôt que d'injecter des activités dans celui de parasol ? »).

Le système décrit UNE plateforme complète sur toute sa durée de vie :

    [fpv_lagon] Full PV system  (1 plateforme)
      ├── panneaux PV (brique parasol)      × surface de modules [m²]
      ├── onduleurs + câblage modules       × 1
      ├── structure (alu anodisé + inox)    × 1
      ├── flotteurs (EPS + peau MDPE)       × 1
      ├── lignes d'ancrage                  × 1
      ├── câble de liaison terre-mer        × P/P_parc (prorata de puissance)
      ├── maintenance                       × 1
      ├── répéteurs wifi                    × 1
      ├── transport (camion + mer + goélette) × 1
      ├── chantier (montage + démontage)    × 1
      └── fin de vie des panneaux (switch)  × 1

Le poste « Chantier » a été retiré en août 2026 puis REMIS le 05/10/2026. Ce
qui avait été retiré à juste titre était le prorata d'un chantier TERRESTRE de
570 kWc ; ce qui revient est le geste réel — quelques centaines de mètres de
bateau, sur le dataset de la maintenance. Le motif du retour est la complétude
de la frontière du système, pas un changement d'ordre de grandeur : le poste
pèse ~0,001 % du total au périmètre « transit seul ». Cf. `chantier.py`.

Il n'y a plus AUCUNE injection dans une activité parasol, plus aucune
neutralisation d'échange, plus aucun `freezeParams` suivi d'une restauration :
le graphe est construit une fois, dans l'ordre, et c'est tout.

L'unité fonctionnelle (1 kWh injecté) est passée à `compute_impacts` via
`functional_unit=`, la fonctionnalité native de lca_algebraic — au lieu
d'empiler deux activités « par kWc » puis « par kWh ».
"""

from __future__ import annotations

import lca_algebraic as agb

from . import (ancrage, cable, config, electricite, fin_de_vie, maintenance,
               onduleurs, panneaux, parametres, repeteurs, structure,
               transport)
from . import chantier

NOM = config.nom("Full PV system")

# Le câble terre-mer dessert les 4 plateformes du parc. Depuis le 06/10/2026
# chacune en porte une part proportionnelle à sa puissance crête, et non plus
# un quart : cf. `cable.part_cable`. La constante PART_CABLE a été retirée
# exprès — un `systeme.PART_CABLE` oublié quelque part doit lever une erreur,
# pas réintroduire silencieusement la clé ¼.


def construire(ctx):
    """Construit tous les postes puis le système, et le range dans le contexte."""
    print("\nConstruction des postes d'inventaire :")

    # Électricité locale : construite en premier, les postes s'y branchent.
    ctx.elec_locale = electricite.construire(ctx)

    ctx.postes["Panneaux"] = panneaux.construire(ctx)
    ctx.postes["Onduleurs"] = onduleurs.construire(ctx)
    ctx.postes["Structure"] = structure.construire(ctx)
    ctx.postes["Flotteurs"] = structure.construire_flotteurs(ctx)
    ctx.postes["Ancrage"] = ancrage.construire(ctx)
    ctx.postes["Cable"] = cable.construire(ctx)
    ctx.postes["Maintenance"] = maintenance.construire(ctx)
    ctx.postes["Repeteurs"] = repeteurs.construire(ctx)
    ctx.postes["Transport"] = transport.construire(ctx)
    ctx.postes["Chantier"] = chantier.construire(ctx)
    switch_eol, scenarios_eol = fin_de_vie.construire(ctx)
    ctx.postes["FinDeVie"] = switch_eol
    ctx.scenarios_eol = scenarios_eol

    systeme = agb.newActivity(
        ctx.db, NOM, unit="unit",
        exchanges={
            ctx.postes["Panneaux"]: panneaux.surface_modules(ctx),
            ctx.postes["Onduleurs"]: 1.0,
            ctx.postes["Structure"]: 1.0,
            ctx.postes["Flotteurs"]: 1.0,
            ctx.postes["Ancrage"]: 1.0,
            ctx.postes["Cable"]: cable.part_cable(ctx.p),
            ctx.postes["Maintenance"]: 1.0,
            ctx.postes["Repeteurs"]: 1.0,
            ctx.postes["Transport"]: 1.0,
            ctx.postes["Chantier"]: 1.0,
            ctx.postes["FinDeVie"]: 1.0,
        })

    ctx.systeme = systeme
    ctx.energie = energie_totale(ctx)
    print(f"\nSystème « {NOM} » assemblé : {len(ctx.postes)} postes.")
    return systeme


def energie_totale(ctx, nette=True):
    """kWh NETS livrés par la plateforme sur toute sa durée de vie.

        E_brute = puissance_crête × productible_annuel_moyen × durée_de_vie
        E_nette = E_brute − consommation des auxiliaires

    Le productible passé en paramètre est déjà le productible MOYEN, dégradation
    linéaire incluse (cf. `parametres.productible_moyen`) : parasol ne modélise
    pas la dégradation, on la porte dans la moyenne.

    ── Pourquoi « nette » (août 2026) ────────────────────────────────────────
    Les lignes directrices IEA-PVPS Task 12 définissent l'unité fonctionnelle
    comme le kWh **livré au réseau**. Les consommations auxiliaires de la
    centrale (aujourd'hui les répéteurs CPL, demain un éventuel monitoring) se
    déduisent donc du productible au dénominateur — elles ne s'achètent pas au
    réseau de l'île au numérateur. Compter les 1 577 kWh des répéteurs comme un
    achat au mix fioul polynésien (0,914 kg CO2-eq/kWh) leur donnait un poids
    de 6,25 g CO2-eq/kWh, soit 7 % du total pour deux boîtiers TP-Link : dix
    fois trop, parce que valorisés au FE du fioul au lieu de celui du kWh que
    la plateforme produit elle-même.

    `nette=False` restitue l'ancien dénominateur, utile pour chiffrer l'écart.
    """
    from . import repeteurs

    m = parametres.magnitude
    brute = (m(ctx.p.p_install_kwc) * m(ctx.p.productible_kwh_kwc_an)
             * m(ctx.p.duree_vie_an))
    if not nette:
        return brute
    return brute - m(repeteurs.consommation_kwh(ctx))


# ── Calcul ─────────────────────────────────────────────────────────────────
def impacts(ctx, methodes=None, axis=None, **valeurs):
    """Impacts du système, ramenés à 1 kWh injecté.

    C'est LA fonction de calcul du package. Elle passe par
    `agb.compute_impacts`, avec l'unité fonctionnelle en expression symbolique
    et, si demandé, la ventilation par poste (`axis="phase"`).

    >>> impacts(ctx, [config.GWP], **modalites.SH51)
    >>> impacts(ctx, config.METHODES_EF, axis=config.AXE, **modalites.SH51)
    """
    methodes = methodes or config.METHODES_EF
    return agb.compute_impacts(
        ctx.systeme, methodes,
        functional_unit=ctx.energie,
        axis=axis,
        **valeurs)


def gwp(ctx, **valeurs) -> float:
    """GWP100 en kg CO2-eq/kWh, valeur scalaire."""
    return float(impacts(ctx, [config.GWP], **valeurs).iloc[0, 0])


def gwp_g(ctx, **valeurs) -> float:
    """GWP100 en g CO2-eq/kWh."""
    return gwp(ctx, **valeurs) * 1000.0


def inventaire(ctx, **valeurs):
    """Inventaire (flux élémentaires) du système pour un jeu de paramètres."""
    return agb.compute_inventory(ctx.systeme, functional_unit=ctx.energie, **valeurs)


def afficher(ctx, **valeurs):
    """Affiche le détail des activités du modèle, formules évaluées.

    `agb.printAct` évalue les formules pour le jeu de paramètres fourni : c'est
    le moyen natif de vérifier les masses réellement injectées, sans écrire de
    fonction d'affichage maison.
    """
    agb.printAct(ctx.systeme, **valeurs)
    for nom_poste, act in ctx.postes.items():
        print(f"\n── {nom_poste} ──")
        agb.printAct(act, **valeurs)
