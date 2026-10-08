"""
Poste « Câble » : liaison terre-mer, partagée par les 4 plateformes.

Remplace `[parasol] photovoltaics, electric installation per kg`, qui a été
écarté (commentaire 4 du reviewer) : ce dataset ecoinvent forfaitaire
« installation électrique d'un 3 kWc en bâtiment » n'a rien à voir avec un
câble sous-marin de 380 m, et faisait doublon avec ce poste.

UN SEUL CÂBLE (correction du 15/09/2026). Le TOP HORN 4G95 part des plateformes,
traverse le lagon, puis continue ENTERRÉ jusqu'au point de raccordement. Le
modèle décrivait auparavant deux câbles différents : un FESTOONFLEX en mer et un
FESTOONFLEX 5 G 6 mm² à terre, ce dernier codé en dur sans aucune source. Les
constantes `CU_TERRE` et `PE_TERRE` ont donc été supprimées, et la longueur
enterrée s'ajoute simplement à la longueur en mer.

Longueur 3D du câble sous-marin : ce n'est pas la distance horizontale. On
ajoute
  1. la descente verticale plateforme flottante → fond (`profondeur_eau_m`) ;
  2. la bathymétrie du trajet : le câble suit le fond, sa longueur est la somme
     des segments 3D le long du profil `BATHY_ABS_M`.

    L_eau = Σ_i √((Δxᵢ · d_eau)² + (Δzᵢ · profondeur)²) + profondeur
    L_totale = L_eau + `dist_cable_terre_m`  (60 m enterrés, même câble 4G95)

L'expression est SYMBOLIQUE : `dist_cable_eau_m` et `profondeur_eau_m`
pilotent réellement la masse de cuivre, et les analyses de sensibilité natives
de lca_algebraic les voient.

Le câble étant unique pour les 4 plateformes, il est injecté à 0,25 dans le
système d'UNE plateforme (cf. `systeme.py`).
"""

from __future__ import annotations

import math

import lca_algebraic as agb

from . import config
from .parametres import U

NOM = config.nom("cable de liaison terre-mer (partage 4 plateformes)")

# Profil bathymétrique plage → plateforme, en profondeurs ABSOLUES relevées (m).
#   x = fraction de la distance horizontale (0 = plage, 1 = plateforme)
#   z = profondeur en mètres à cette abscisse
#
# ⚠ Le fond ne bouge pas. Ces profondeurs sont FIXES : ce sont des relevés.
# Seul le point d'arrivée (x = 1) suit `profondeur_eau_m`, puisque c'est la
# profondeur sous la plateforme — la seule grandeur qui dépend de l'endroit
# où on la mouille.
#
# Version précédente : le profil entier était normalisé par la profondeur de
# la plateforme, si bien que passer de 3 à 10 m faisait aussi passer le chenal
# de 12 à 40 m. La sensibilité à la profondeur était alors deux fois trop
# grande (dL/dprofondeur = 2,0 m/m au lieu de 1,0), et elle mélangeait deux
# choses sans rapport : la position de la plateforme et la forme du lagon.
BATHY_ABS_M = [
    (0.000, 1.0),    # plage : 1 m
    (0.500, 1.0),    # fin du plateau à 1 m
    (0.675, 12.0),   # pointe du chenal
    (0.850, 3.0),    # sortie du chenal
    (1.000, 3.0),    # plateforme — remplacé par `profondeur_eau_m`
]

# Profondeur relevée sous la plateforme (valeur par défaut du paramètre).
PROFONDEUR_REFERENCE_M = BATHY_ABS_M[-1][1]

# ── Masses linéiques (kg/m) — FICHE TOP HORN 4G95 (correction 15/09/2026) ──
#
# Câble retenu : TOP HORN 4G95, 4 conducteurs de 95 mm², âme cuivre nu souple
# classe 5, isolation et gaine élastomère. C'est LE câble du démonstrateur, en
# mer comme sous terre — le FESTOONFLEX ne sert qu'entre les modules et les
# micro-onduleurs (cf. `onduleurs.py`).
#
# Le cuivre ne change pas : 4 × 912 kg/km, le Copper Index fabricant pour un
# conducteur de 95 mm². Contrôle de plausibilité : 95 mm² de cuivre PLEIN
# pèsent 851 kg/km, donc 912 kg/km incorpore un facteur de câblage de 1,072 —
# cohérent pour un conducteur souple classe 5.
#
# L'ENVELOPPE EST OBTENUE PAR DIFFÉRENCE : 4 995 − 3 648 = 1 347 kg/km, soit
# 27 % de la masse du câble. On n'a PAS transposé le ratio non-cuivre du
# FESTOONFLEX (232/4 995 ≈ 6 %) : il aurait donné 4 695 kg/km de cuivre pour
# 4 × 95 mm², au-dessus de la masse du cuivre plein — physiquement impossible.
# Ce ratio venait d'une ligne « 1 × » de la fiche CIC que ce module signalait
# déjà comme géométriquement douteuse.
#
# Contrôle inverse : 1 347 kg/km ≈ 1 036 mm² de section hors cuivre à densité
# 1,3, soit ~42 mm de diamètre hors tout pour un 4G95 élastomère. Cohérent.
# ── MÉTHODE COMMUNE À TOUS LES CÂBLES DU MODÈLE (16/09/2026) ──────────────
#
# Un fabricant donne toujours la masse TOTALE au km. Il ne donne pas toujours
# la part de cuivre, et jamais celle de l'enveloppe. On applique donc partout
# la même règle, en trois temps :
#
#   1. CUIVRE = section × densité × nombre de conducteurs × facteur de câblage.
#      C'est de la physique, pas une estimation.
#   2. TOTAL  = la fiche fabricant. C'est la seule donnée mesurée.
#   3. ENVELOPPE = TOTAL − CUIVRE. Par différence, donc porteuse de toute
#      l'incertitude des deux autres.
#
# Le facteur de câblage tient au fait qu'un conducteur souple est un toron
# hélicoïdal : sa longueur de fil dépasse la longueur de câble. Il est CALÉ sur
# le seul cas où le fabricant donne les deux nombres — le TOP HORN 4G95, dont
# le Copper Index de 912 kg/km par conducteur de 95 mm² se compare aux
# 851,2 kg/km du cuivre plein : 912 / 851,2 = 1,0714. Valeur usuelle pour une
# classe 5, et c'est elle qu'on transpose au 3G1,5 des onduleurs, faute d'un
# Copper Index publié pour ce câble-là.
RHO_CUIVRE_KG_M3 = 8960.0
FACTEUR_CABLAGE = 1.0714            # calé sur le TOP HORN (912 / 851,2)
FACTEUR_CABLAGE_MIN = 1.00          # conducteur massif, borne physique basse
FACTEUR_CABLAGE_MAX = 1.10          # toron très pas-court, borne haute usuelle


def cuivre_par_m(section_mm2, n_conducteurs, facteur=FACTEUR_CABLAGE) -> float:
    """Masse de cuivre par mètre de câble, en kg/m — depuis la géométrie.

    >>> cuivre_par_m(95, 4)        # TOP HORN 4G95
    3.6476...                      # à comparer aux 3,648 du Copper Index
    >>> cuivre_par_m(1.5, 3)       # câble module → onduleur
    0.0432...
    """
    return n_conducteurs * section_mm2 * 1e-6 * RHO_CUIVRE_KG_M3 * facteur


def enveloppe_par_m(total_par_m, section_mm2, n_conducteurs,
                    facteur=FACTEUR_CABLAGE) -> float:
    """Isolation + gaine, par différence. kg/m."""
    return total_par_m - cuivre_par_m(section_mm2, n_conducteurs, facteur)


def bornes_enveloppe(total_par_m, section_mm2, n_conducteurs,
                     tolerance_totale=0.02) -> tuple:
    """Plage plausible de l'enveloppe, par propagation des deux incertitudes.

    L'enveloppe est un RESTE : elle hérite de l'incertitude du total (tolérance
    de fabrication, `tolerance_totale`) ET de celle du facteur de câblage, qui
    n'est pas publié. Les deux se composent dans le mauvais sens — un total bas
    avec un cuivre haut donne l'enveloppe la plus basse.

    >>> bornes_enveloppe(4.995, 95, 4)      # TOP HORN
    (1.1501..., 1.6902...)
    """
    bas = (total_par_m * (1 - tolerance_totale)
           - cuivre_par_m(section_mm2, n_conducteurs, FACTEUR_CABLAGE_MAX))
    haut = (total_par_m * (1 + tolerance_totale)
            - cuivre_par_m(section_mm2, n_conducteurs, FACTEUR_CABLAGE_MIN))
    return bas, haut


# ── TOP HORN 4G95 : les trois masses linéiques ─────────────────────────────
SECTION_MM2 = 95.0
N_CONDUCTEURS = 4
CU_PAR_M = 3.648            # 4 × 912 kg/km — Copper Index FABRICANT
TOTAL_PAR_M = 4.995         # fiche TOP HORN 4G95, masse totale
ENV_PAR_M = TOTAL_PAR_M - CU_PAR_M      # 1,347 kg/m — isolation + gaine

# Contrôle de plausibilité inverse : 1 347 kg/km ≈ 1 036 mm² de section hors
# cuivre à densité 1,3, soit ~42 mm de diamètre hors tout pour un 4G95
# élastomère. Cohérent. Et la part de cuivre, 73 %, est celle attendue d'un
# gros câble — les petites sections sont majoritairement de l'isolant
# (le 3G1,5 des onduleurs n'est qu'à 35 % de cuivre).
#
# ⚠ On n'a PAS transposé le ratio non-cuivre du FESTOONFLEX (232/4 995 ≈ 6 %) :
# il aurait donné 4 695 kg/km de cuivre pour 4 × 95 mm², au-dessus de la masse
# du cuivre plein — physiquement impossible.

# Rétrocompatibilité : d'anciennes cellules importaient ces noms.
CU_EAU = CU_PAR_M
PE_EAU = ENV_PAR_M

# ⚠ LIMITE À GARDER EN TÊTE SUR L'ENVELOPPE.
# L'isolation et la gaine sont en ÉLASTOMÈRE ; le modèle les impute au dataset
# PEHD, plus léger en impact. Le poste pesait ~0,5 g CO2-eq/kWh quand
# l'enveloppe valait 232 kg/km ; avec 1 347 kg/km il devient six fois plus
# lourd, donc le proxy mérite désormais d'être justifié explicitement — ou
# remplacé par un mélange PVC/caoutchouc si la fiche détaille la construction.


def _profil(profondeur_plateforme):
    """Profil bathymétrique en mètres absolus, arrivée à la profondeur donnée.

    `profondeur_plateforme` peut être un nombre, un symbole Sympy ou une
    grandeur Pint : les profondeurs relevées sont donc portées à la même unité.
    """
    metre = U("m")
    points = [(x, z * metre) for x, z in BATHY_ABS_M[:-1]]
    points.append((1.0, profondeur_plateforme))
    return points


def longueur_cable_eau(dist_horizontale, profondeur):
    """Longueur 3D du câble sous-marin (expression symbolique ou numérique).

    = somme des segments 3D le long du fond + descente verticale depuis la
    plateforme flottante. Seul le dernier segment et la descente dépendent de
    `profondeur` : au nominal, un mètre de fond en plus coûte donc exactement
    un mètre de câble en plus.
    """
    profil = _profil(profondeur)
    total = None
    for (x0, z0), (x1, z1) in zip(profil[:-1], profil[1:]):
        dx = (x1 - x0) * dist_horizontale
        dz = z1 - z0
        segment = (dx ** 2 + dz ** 2) ** 0.5
        total = segment if total is None else total + segment
    return total + profondeur


def longueur_cable_eau_num(dist_m, prof_m):
    """Version purement numérique (contrôles et calcul de masse de fret)."""
    points = [(x, z) for x, z in BATHY_ABS_M[:-1]] + [(1.0, prof_m)]
    return sum(
        math.hypot((x1 - x0) * dist_m, z1 - z0)
        for (x0, z0), (x1, z1) in zip(points[:-1], points[1:])
    ) + prof_m


# ── Clé de répartition du câble entre plateformes ─────────────────────────
# ⚠ RÉVISÉ LE 06/10/2026, retour du relecteur : 1/4 → prorata de la puissance.
#
# Le câble d'export est UN câble qui dessert les quatre plateformes. Jusqu'ici
# chacune en portait un quart, au motif que les quatre sont identiques pour
# tout ce qui dimensionne le câble. Le relecteur demande une allocation
# PHYSIQUE : chaque plateforme porte la part du câble égale à sa part de la
# puissance installée,
#
#     part(Sx) = P_crête(Sx) / P_crête(parc)        (ISO 14044, § 4.3.4.2)
#
# soit 27,9 % pour S1, 19,9 % pour S2, 32,9 % pour S3 et 19,3 % pour S4. La
# somme vaut 1 : le parc porte toujours exactement un câble.
#
# Conséquence à connaître : la puissance étant aussi au dénominateur de
# l'unité fonctionnelle, l'impact du câble PAR kWh devient le même pour les
# quatre plateformes (à la disponibilité des répéteurs près). Le câble ne
# participe plus à l'écart entre configurations.
#
# Doit valoir la somme de `modalites.DONNEES[*]["kwc"]` — contrôlé par
# `modalites.jeux_de_parametres`, qui s'arrête si les deux divergent.
P_PARC_KWC = 39.66


def part_cable(p):
    """Part du câble portée par la plateforme — expression symbolique, sans unité."""
    return p.p_install_kwc / (P_PARC_KWC * U("kWp"))


def part_cable_num(kwc):
    """Même chose en valeur numérique, pour les bilans de masse."""
    return float(kwc) / P_PARC_KWC


def masses(ctx):
    """Masses de câble (cuivre, gaine) en kg — expression symbolique.

    Partagé entre l'inventaire de fabrication et celui de fin de vie. ⚠ Ce sont
    les masses du câble ENTIER : chaque plateforme n'en consomme que sa part,
    au prorata de sa puissance crête (`part_cable`).
    """
    p = ctx.p
    # UN SEUL câble : la partie immergée (longueur 3D) plus la partie enterrée.
    l_totale = (longueur_cable_eau(p.dist_cable_eau_m, p.profondeur_eau_m)
                + p.dist_cable_terre_m)
    # Le cuivre passe par un PARAMÈTRE (et non plus la constante CU_PAR_M) pour
    # que l'analyse d'incertitude puisse le balayer ; `CU_PAR_M` en reste la
    # valeur par défaut, celle de la fiche fabricant. La plage est désormais
    # celle d'une tolérance de fabrication (±5 %) et non d'un changement de
    # tension : le passage à l'échelle en moyenne tension est hors de ce
    # modèle (décision du 16/09/2026).
    # ⚠ Cuivre et enveloppe sont DEUX paramètres indépendants : un tirage peut
    # donc donner une somme différente des 4 995 kg/km de la fiche. C'est
    # assumé — leurs incertitudes sont de natures différentes (le cuivre tient
    # à la section, l'enveloppe à un reste) et les corréler demanderait de
    # modéliser le facteur de câblage lui-même. Au nominal, la somme vaut
    # exactement la fiche. La masse TRANSPORTÉE, elle, ne dépend d'aucun des
    # deux : `masse_cable_totale_kg` part de `TOTAL_PAR_M`.
    return {
        "cuivre": l_totale * p.rho_cuivre_cable_kg_m,
        "gaine": l_totale * p.rho_gaine_cable_kg_m,
    }


def construire(ctx):
    p = ctx.p
    m = masses(ctx)
    m_cuivre, m_gaine = m["cuivre"], m["gaine"]

    act = agb.newActivity(
        ctx.db, NOM, unit="unit",
        exchanges={
            ctx.ei.cuivre: m_cuivre,
            ctx.ei.pehd: m_gaine,
        })
    act.updateMeta(**{config.AXE: "Cable"})

    l_nom = longueur_cable_eau_num(380.0, PROFONDEUR_REFERENCE_M)
    print(f"  câble TOP HORN 4G95 : 380 m horizontal -> {l_nom:.1f} m immergés "
          f"(bathymétrie relevée + descente {PROFONDEUR_REFERENCE_M:.0f} m)")
    print(f"     + {DIST_TERRE_REFERENCE_M:.0f} m enterrés à terre, même câble "
          f"(longueur comptée {l_nom + DIST_TERRE_REFERENCE_M:.1f} m)")
    print(f"     {CU_PAR_M:.3f} kg/m de cuivre + {ENV_PAR_M:.3f} kg/m "
          f"d'enveloppe (= {TOTAL_PAR_M:.3f} − {CU_PAR_M:.3f}, fiche fabricant)")
    return act


# Section enterrée à terre, mesurée sur site le 01/10/2026. Même câble 4G95
# que la partie immergée ; le périmètre de l'étude s'arrête à son extrémité.
DIST_TERRE_REFERENCE_M = 60.0


def masse_cable_totale_kg(dist_eau_m=380.0, dist_terre_m=DIST_TERRE_REFERENCE_M,
                          profondeur_m=PROFONDEUR_REFERENCE_M):
    """Masse totale du câble (cuivre + enveloppe), utile au calcul du fret.

    Un seul câble sur tout le parcours : la longueur immergée en 3D plus la
    longueur enterrée, au même poids linéique.
    """
    l_totale = longueur_cable_eau_num(dist_eau_m, profondeur_m) + dist_terre_m
    return l_totale * TOTAL_PAR_M
