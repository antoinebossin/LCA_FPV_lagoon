"""
Poste « Chantier » : montage sur le lagon et démontage en fin de vie.

════════════════════════════════════════════════════════════════════════════
POURQUOI CE POSTE REVIENT (05/10/2026)

Il avait existé, puis été retiré en août 2026 — la note en fin de
`transport.py` en garde la trace. Le motif du retrait était bon : l'ancien
poste valorisait 7 673 MJ de gazole d'ENGIN DE CHANTIER TERRESTRE pour une
centrale parasol de 570 kWc, mis au prorata de la puissance installée. Or les
plateformes de Raiatea ont été REMORQUÉES à la petite embarcation. Le prorata
importait dans le modèle un chantier qui n'a jamais eu lieu.

Ce qui revient n'est pas cet ancien poste. C'est le geste réel, et sur le même
dataset que la maintenance (`diesel, burned in fishing vessel`) — exactement ce
que la note de retrait recommandait de faire si l'on voulait le recompter un
jour.

LE MOTIF EST MÉTHODOLOGIQUE, PAS NUMÉRIQUE, ET IL FAUT L'ASSUMER
L'ordre de grandeur est écrasé : 500 m de bateau à l'aller comme au retour, à
la consommation déduite de la maintenance, font ~0,08 L de gazole et de
l'ordre de 0,001 g CO₂-eq/kWh — mille fois sous l'arrondi des tableaux. Ce
poste n'est donc pas là pour changer un résultat. Il est là pour que la
frontière du système soit COMPLÈTE et VÉRIFIABLE : une ACV annoncée
cradle-to-grave dont l'installation et le démontage sont absents se fait
reprendre en revue, et « c'est négligeable » affirmé sans chiffre n'est pas
une réponse. Avec ce poste, la phrase devient « installation et démontage
pèsent 0,001 % du total », ce qui est une mesure et non une excuse.

LE PÉRIMÈTRE RETENU : TRANSIT + MANŒUVRE (arbitré le 05/10/2026)

La distance n'est pas le chantier. Mettre une plateforme en place, c'est la
remorquer — quelques minutes — PUIS la positionner, mouiller quatre ancres de
plusieurs dizaines de kilos, tendre les élastiques, vérifier en plongée. Des
minutes de moteur en charge pendant lesquelles le bateau ne parcourt presque
aucune distance. Compter le seul transit donnait 0,075 L et 0,0009 g CO₂-eq/kWh,
soit 0,001 % du total : un nombre qui invite la question plutôt qu'il ne la
clôt, et qui fait soupçonner un inventaire bâclé.

Le périmètre retenu ajoute donc **30 minutes de manœuvre par opération, soit
~10 L de gazole** (`DIESEL_MANOEUVRE_L`), montage et démontage comptés
séparément. Le poste pèse alors ~20,1 L, 0,24 g CO₂-eq/kWh, 0,35 % du total.
Toujours marginal — mais marginal et DÉFENDABLE : la phrase de l'article
devient « installation and decommissioning account for 0.35 % of the total »,
ce qui est une mesure, pas une excuse.

UNE PLATEFORME À LA FOIS, ET C'EST CE QUI REND LE POSTE ADDITIF
Les plateformes sont remorquées une par une. Le geste décrit ici est donc bien
celui d'UNE plateforme, à la même échelle que tout le reste du modèle : il n'y
a pas de mutualisation du chantier entre les quatre, contrairement au câble
d'export (`cable.part_cable`, au prorata de la puissance crête).
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import PCI_DIESEL_MJ_PAR_L, U

NOM = config.nom("chantier (montage + demontage)")

# ── Consommation du bateau de travail, L/km ────────────────────────────────
#
# DÉDUITE DE LA MAINTENANCE, pour que les deux postes décrivent le même bateau.
# `maintenance.py` pose 0,3 L par visite pour « 4 A/R × 1 km », lu ici comme
# quatre allers-retours d'un kilomètre chacun, soit 4 km : 0,075 L/km.
#
# ⚠ CETTE VALEUR EST BASSE POUR UN BATEAU, ET C'EST ASSUMÉ. 7,5 L/100 km
# correspond à une voiture, pas à un hors-bord de 30 ch, qui consomme plutôt
# 10 L/h et donc de l'ordre de 50 L/100 km en navigation. Le 0,3 L/visite de
# `maintenance.py` est donc probablement bas d'un facteur dix.
#
# DÉCISION DU 05/10/2026 : on NE touche PAS à `maintenance.diesel_par_visite_l`.
# Le poste maintenance pèse 2,3 % du résultat ; le multiplier par dix le
# porterait à ~20 %, ce qui serait un changement majeur sur la foi d'une
# estimation de consommation, pas d'une mesure. Tant que le relevé réel n'est
# pas au dossier, la valeur du dossier reste la valeur du dossier.
#
# Conséquence pour CE poste : le transit y est marginal de toute façon, et
# l'essentiel vient de `DIESEL_MANOEUVRE_L`, qui est une estimation directe en
# litres et ne dépend donc pas de ce taux. Une erreur d'un facteur dix sur
# `L_PAR_KM_BATEAU` déplacerait le poste de 0,075 L à 0,75 L sur un total de
# 20,1 L : 3 %. L'incohérence est réelle mais SANS EFFET ici.
L_PAR_KM_BATEAU = 0.075

# ── Gazole brûlé EN STATION, par opération (L) ─────────────────────────────
# 30 minutes de manœuvre à ~20 L/h de consommation en charge. C'est le poste
# qui porte réellement le chantier : le transit, lui, est mille fois plus
# petit. Valeur arbitrée le 05/10/2026 ; `p.diesel_manoeuvre_l` la rend
# ajustable sans toucher au code.
DIESEL_MANOEUVRE_L = 10.0

# Deux opérations dans la vie du système : la pose et la dépose. Elles sont
# comptées au même forfait de manœuvre — un démontage n'est pas plus simple
# qu'une pose, il faut remonter les ancres.
N_OPERATIONS = 2


def construire(ctx):
    """Montage + démontage d'une plateforme, sur toute la durée de vie."""
    p = ctx.p

    # Distance parcourue par le bateau à chaque opération, telle que spécifiée :
    # 500 m au montage, 500 m au démontage. Les deux paramètres sont distincts
    # pour que la sensibilité puisse les bouger séparément — un démontage se
    # fait rarement dans les mêmes conditions qu'une pose.
    km = (p.dist_montage_m + p.dist_demontage_m) * (0.001 * U("km/m"))

    # Transit + manœuvre. La seconde domine d'un facteur ~270.
    litres = (km * (L_PAR_KM_BATEAU * U("L/km"))
              + N_OPERATIONS * p.diesel_manoeuvre_l)
    diesel_mj = litres * (PCI_DIESEL_MJ_PAR_L * U("MJ/L"))

    act = agb.newActivity(
        ctx.db, NOM, unit="unit",
        exchanges={ctx.ei.diesel_bateau: diesel_mj})
    act.updateMeta(**{config.AXE: "Chantier"})
    return act


def expliquer(ctx=None, valeurs=None):
    """Chiffre le poste et le met en regard des deux périmètres possibles.

    Sert à répondre, avec des nombres, à « pourquoi si peu ? » — et à montrer
    ce que donnerait le périmètre large, sans avoir à relancer le modèle.

    >>> from acv_lagon import chantier
    >>> chantier.expliquer()
    """
    # GWP du gazole brûlé en bateau, kg CO2-eq/MJ. Ordre de grandeur ecoinvent
    # pour `diesel, burned in fishing vessel` — sert à l'illustration, jamais
    # au calcul : le modèle, lui, interroge la base.
    GWP_PAR_MJ = 0.088
    E_VIE_KWH = 231821.0            # SH51, kWh nets sur la durée de vie

    print("Poste « Chantier » — montage et démontage d'une plateforme\n")
    print(f"  consommation retenue : {L_PAR_KM_BATEAU} L/km "
          f"(déduite de maintenance.py)")
    print(f"  PCI du gazole        : {PCI_DIESEL_MJ_PAR_L} MJ/L\n")

    for intitule, km, operations_l in [
            ("transit seul (500 + 500 m)", 1.0, 0.0),
            ("+ 30 min de manoeuvre par operation  <- RETENU",
             1.0, N_OPERATIONS * DIESEL_MANOEUVRE_L),
            ("+ une demi-journee de vedette par operation", 1.0, 80.0)]:
        litres = km * L_PAR_KM_BATEAU + operations_l
        mj = litres * PCI_DIESEL_MJ_PAR_L
        kg = mj * GWP_PAR_MJ
        g_par_kwh = kg / E_VIE_KWH * 1000
        print(f"  {intitule}")
        print(f"      {litres:7.3f} L -> {mj:8.2f} MJ -> {kg:7.3f} kg CO2-eq "
              f"-> {g_par_kwh:.4f} g/kWh  ({g_par_kwh / 68.0 * 100:.3f} % "
              f"d'un total de 68 g)")
    print("\n  Le transit n'est pas le chantier : positionner la plateforme "
          "et mouiller\n  quatre ancres prend des minutes de moteur en charge "
          "sans parcourir de\n  distance. C'est `diesel_manoeuvre_l` qui "
          "porte le poste, pas la distance.")
