"""
Poste « Transport » : camion + porte-conteneurs + goélette inter-îles.

Comme on n'utilise plus le `Full PV system` de parasol, ses trois transports
internes (camion, train, bateau) ne sont plus dans le modèle : le transport est
intégralement décrit ici, une seule fois, avec les distances réelles. Plus de
`transport_distance_boat = 0` pour neutraliser un double comptage.

Trois maillons :

1. **Camion** usine → port d'embarquement (Var → Perpignan, 200 km), sur la
   masse réelle du système.
2. **Porte-conteneurs** Europe → Papeete (~17 000 km), sur la masse réelle.
3. **Goélette** Papeete → île (220 km pour Raiatea), sur la masse réelle. Le
   proxy ecoinvent *ferry* a un facteur d'émission par t.km 5 à 10 fois
   supérieur au porte-conteneurs, ce qui correspond à l'ordre de grandeur
   d'une goélette.

────────────────────────────────────────────────────────────────────────────
ALLOCATION DU FRET : MASSE RÉELLE (changement d'août 2026, demande du reviewer)

Les trois maillons utilisent maintenant LA MÊME grandeur, `m_systeme_t`, la
masse réellement transportée par plateforme. C'est l'allocation classique du
service de transport, celle que porte l'unité du dataset ecoinvent : le
tonne-kilomètre.

L'ancien modèle appliquait au maillon maritime une **allocation par capacité
affrétée** : le parc étant arrivé dans deux conteneurs complets et la cargaison
étant limitée par le volume et non par le poids, on facturait à chaque
plateforme 10,85 t (2 × 21,7 t ÷ 4) au lieu de ses 2,07 t réelles. L'intention
était de ne pas laisser « gratuit » le volume mort payé et transporté.

Ce raisonnement a été écarté. Il revient à inventer une règle d'allocation
maison là où le dataset ecoinvent en impose déjà une, et il gonflait le fret
d'un facteur 5,2 sans qu'aucun référentiel ne le demande. Le paramètre
`m_fret_maritime_t` a donc été SUPPRIMÉ.

Conséquence : le poste Transport baisse fortement (il valait 8,7 g CO2-eq/kWh,
dont l'essentiel sur le maillon maritime). Si l'on veut discuter le taux de
remplissage, cela se fait en analyse de sensibilité sur `m_systeme_t`, pas en
changeant la règle d'allocation.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config

NOM = config.nom("transport vers l'ile")

N_PLATEFORMES = 4


def construire(ctx):
    p = ctx.p
    # Une seule masse pour les trois maillons : la masse réellement embarquée.
    masse = p.m_systeme_t

    exchanges = {
        ctx.ei.fret_maritime: masse * p.dist_maritime_km,
    }
    if ctx.ei.fret_goelette is not None:
        exchanges[ctx.ei.fret_goelette] = masse * p.dist_interile_km
    else:
        print("⚠ dataset 'ferry' introuvable : la goélette est approximée par "
              "le porte-conteneurs (FE/t.km sous-estimé d'un facteur ~5-10).")
        exchanges[ctx.ei.fret_maritime] = masse * (p.dist_maritime_km
                                                   + p.dist_interile_km)

    if ctx.ei.fret_camion is not None:
        exchanges[ctx.ei.fret_camion] = masse * p.dist_camion_km

    act = agb.newActivity(ctx.db, NOM, unit="unit", exchanges=exchanges)
    act.updateMeta(**{config.AXE: "Transport"})
    return act


# ── Poste « Chantier » : RETIRÉ en août 2026, REMIS le 05/10/2026 ──────────
#
# ⚠ LIRE `chantier.py`. Le poste existe de nouveau, mais PAS sous la forme
# critiquée ci-dessous : le prorata du chantier terrestre reste abandonné, et
# ce qui est compté est le geste réel — quelques centaines de mètres de bateau,
# sur le même dataset que la maintenance, exactement ce que le dernier
# paragraphe de cette note recommandait. Le motif du retour est la complétude
# de la frontière du système, pas un changement d'ordre de grandeur.
#
# ── Ce qui suit est la note de retrait d'août 2026, conservée ──────────────
#
# Il existait un poste `chantier d'installation` valorisant 7 673 MJ de gazole
# d'engin de chantier pour une centrale parasol de 570 kWc, mis au prorata de
# la puissance installée (~106 MJ pour 7,9 kWc, soit 0,05 g CO2-eq/kWh).
#
# Il a été supprimé pour deux raisons, la seconde étant la vraie :
#
# 1. le dataset `diesel, burned in building machine` décrit un ENGIN DE
#    CHANTIER TERRESTRE (pelle, grue), pas une opération nautique ;
# 2. surtout, le prorata linéaire n'a pas de sens ici. La mise en place des
#    plateformes de Raiatea a consisté à les REMORQUER sur le lagon avec une
#    petite embarcation. Ce n'est en rien un centième du chantier d'une
#    centrale 72 fois plus puissante : il n'y a ni terrassement, ni génie
#    civil, ni engin lourd. Extrapoler par la puissance revient à importer
#    dans le modèle un chantier qui n'a jamais eu lieu.
#
# Conséquence assumée : l'installation n'est plus comptée du tout. C'est un
# choix conservateur à l'envers, mais l'ordre de grandeur (0,05 g/kWh, soit
# 0,05 % du résultat) le rend sans effet sur les conclusions. À écrire dans
# les limites du rapport.
#
# Si l'on veut un jour la recompter : le geste réel est un ou deux allers
# retours de remorquage, donc quelques litres de gazole sur le MÊME dataset
# que la maintenance (`diesel, burned in fishing vessel`) — à loger dans
# `maintenance.py`, pas dans un poste dédié.
