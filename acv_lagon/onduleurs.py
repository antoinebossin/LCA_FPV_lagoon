"""
Poste « Onduleurs » (micro-onduleurs Deye SUN-M80G4) + câblage module→onduleur.

Le parc réel est constitué de micro-onduleurs, un par grappe de modules :
10 (SH51), 14 (SH81), 11 (SH51-UV) et 23 (SH81-UV). On modélise donc la masse
d'onduleurs directement en kg/plateforme (`n_onduleurs × m_onduleur_kg`), et
non via le `kg/kWp` de parasol : c'est la grandeur qu'on a mesurée, et ça
supprime une division/remultiplication par la puissance.

Le remplacement en cours de vie est explicite : `durée_de_vie / durée_de_vie
_onduleur` jeux successifs (15 ans en milieu marin, pour 25 ans de garantie).

Le câblage module→onduleur est ici (et pas dans le poste câble) parce qu'il est
proportionnel au nombre de modules : chaque module est relié par ~1,28 m de
CIC-FESTOON PUR-HF 3G1,5.

────────────────────────────────────────────────────────────────────────────
⚠ CORRECTION DU 16/09/2026 — le « cuivre » du câble module→onduleur

Le modèle portait `CUIVRE_PAR_M_KG = 0,115` et l'imputait entièrement au
dataset CUIVRE. Deux erreurs superposées :

1. 115 g/m n'était pas du cuivre, c'était la masse TOTALE du câble — et la
   fiche donne en réalité 125 kg/km, pas 115 ;
2. l'enveloppe n'était donc comptée nulle part, tout en gonflant le cuivre.

Le cuivre réel se calcule, il ne s'estime pas (méthode commune à tous les
câbles du modèle, cf. `cable.cuivre_par_m`) :

    3 conducteurs × 1,5 mm² × 8 960 kg/m³ × 1,0714 = 43,2 g/m

soit 35 % de la masse du câble — cohérent avec les 73 % du TOP HORN 4G95 :
plus la section est petite, plus la part d'isolant est grande. L'enveloppe
vaut le reste, 81,8 g/m, et rejoint le dataset PEHD comme celle du câble
d'export.

Effet : le cuivre du câblage modules est divisé par 2,7 (2,94 → 1,11 kg sur
SH51), et 1,84 kg d'enveloppe apparaissent là où il n'y avait rien. Sur le
GWP c'est marginal ; sur la toxicité et les ressources métalliques, où le
cuivre pèse, ça compte.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import cable, config, parasol_bridge
from .parametres import U

# ── Câble module → onduleur : CIC-FESTOON PUR-HF 3G1,5 ────────────────────
# Même méthode que le câble d'export : le TOTAL vient de la fiche, le CUIVRE
# de la géométrie, l'ENVELOPPE par différence (cf. `cable.py`).
SECTION_MM2 = 1.5
N_CONDUCTEURS = 3
TOTAL_PAR_M_KG = 0.125                       # fiche fabricant, 125 kg/km
CUIVRE_PAR_M_KG = cable.cuivre_par_m(SECTION_MM2, N_CONDUCTEURS)   # 0,0432
GAINE_PAR_M_KG = TOTAL_PAR_M_KG - CUIVRE_PAR_M_KG                  # 0,0818

# Incertitude de l'enveloppe, par propagation (±2 % sur la fiche, facteur de
# câblage dans [1,00 ; 1,10]) : [0,0781 ; 0,0872] kg/m, soit ±5,5 %.
# Elle n'est PAS érigée en paramètre : sur la configuration la plus câblée
# (SH81-UV, 57,6 m) l'enveloppe pèse 4,7 kg, contre 752 kg pour celle du câble
# d'export. La porter au tirage ajouterait une ligne au tornado pour 0,01 % de
# la variance. La plage est documentée ici et dans l'inventaire ; c'est le bon
# niveau de traitement pour cette masse.
BORNES_GAINE_PAR_M_KG = cable.bornes_enveloppe(
    TOTAL_PAR_M_KG, SECTION_MM2, N_CONDUCTEURS)

NOM = config.nom("onduleurs et cablage modules")


def masses(ctx):
    """Masses d'onduleurs et de câblage module→onduleur (kg), sur 30 ans.

    Partagé avec `fin_de_vie.matieres` : ce qui est fabriqué est ce qui est mis
    au rebut. Le nombre de jeux est arrondi à l'entier supérieur (30/15 = 2 ici,
    l'arrondi ne change donc rien — cf. `parametres.n_jeux`).
    """
    from .parametres import n_jeux

    p = ctx.p
    return {
        "electronique": p.n_onduleurs * p.m_onduleur_kg
                        * n_jeux(p.duree_vie_an, p.duree_vie_onduleur_an),
        "cuivre": p.n_modules * p.l_cable_module_m * (CUIVRE_PAR_M_KG * U("kg/m")),
        "gaine": p.n_modules * p.l_cable_module_m * (GAINE_PAR_M_KG * U("kg/m")),
    }


def construire(ctx):
    """Activité « onduleurs » : fabrication + remplacements + câblage amont."""
    onduleur_par_kg = parasol_bridge.onduleur(ctx)
    m = masses(ctx)

    act = agb.newActivity(
        ctx.db, NOM, unit="unit",
        exchanges={
            onduleur_par_kg: m["electronique"],
            ctx.ei.cuivre: m["cuivre"],
            # L'enveloppe du 3G1,5 rejoint le même proxy PEHD que celle du
            # câble d'export : même limite déclarée (élastomère modélisé en
            # polyoléfine), même dataset, pour ne pas avoir deux conventions.
            ctx.ei.pehd: m["gaine"],
        })
    act.updateMeta(**{config.AXE: "Onduleurs"})
    return act
