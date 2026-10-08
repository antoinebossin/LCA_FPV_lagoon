"""
Poste « Répéteurs wifi » : fabrication et fin de vie DEEE.
La CONSOMMATION d'usage, elle, est traitée au dénominateur (voir ci-dessous).

Deux répéteurs CPL TP-Link AV1000 par plateforme, ~0,12 kg d'électronique
active chacun, remplacés tous les 10 ans en milieu marin, alimentés en continu
(~3 W pièce).

════════════════════════════════════════════════════════════════════════════
POURQUOI LA CONSOMMATION EST SORTIE DE L'INVENTAIRE (correction août 2026)

Le modèle facturait les 1 577 kWh consommés sur 30 ans au facteur d'émission du
réseau de Raiatea (0,914 kg CO2-eq/kWh, mix fioul) : 1 441 kg CO2-eq, soit
**6,25 g CO2-eq/kWh, 7 % du résultat total** — plus que le poste Panneaux. Pour
deux boîtiers CPL, c'était manifestement absurde.

L'arithmétique n'était pourtant pas fausse, et la donnée d'entrée non plus :
2 × 3 W en continu, c'est réaliste pour un kit CPL+wifi AV1000 (4 à 6 W pièce en
service selon les fiches TP-Link, moins en veille). Le vrai problème était le
CHOIX DE MODÉLISATION.

Ces 52,6 kWh/an sont une consommation AUXILIAIRE de la centrale — au même titre
que la veille des onduleurs ou le monitoring. Or les lignes directrices
IEA-PVPS Task 12 définissent l'unité fonctionnelle comme le kWh **NET livré au
réseau** : les auxiliaires se déduisent du productible, ils ne s'achètent pas au
réseau. Les compter comme un achat revenait à les valoriser à 0,914 kg/kWh — le
mix fioul de l'île — au lieu des ~0,086 kg/kWh de l'électricité que la
plateforme produit elle-même. Un facteur 10 sur le même kWh.

Effet : 52,6 kWh sur 7 687 kWh produits par an, soit **0,68 % du productible**.
Le poste passe de 6,25 g à ~0,6 g d'effet net. C'est l'ordre de grandeur qu'on
attend de deux boîtiers CPL, et c'est aussi ce qui rend le résultat comparable
à la littérature (IEA T12), qui traite les auxiliaires de la même façon.

À VÉRIFIER SUR SITE, car cela change le raisonnement :
* si les répéteurs sont alimentés PAR LA PLATEFORME, la déduction du
  productible est exactement juste ;
* s'ils sont à terre sur le réseau de l'île, la déduction reste la convention
  la plus proche de l'IEA T12 — mais il faut l'écrire dans les hypothèses ;
* et s'ils ne servent QUE aux capteurs scientifiques (FSU1/FSU2/WS) et non au
  monitoring de la centrale, ils sortent carrément des frontières : une
  centrale FPV commerciale n'en a pas. `AUXILIAIRE = False` les retire alors
  totalement de l'énergie nette.

La fabrication et la fin de vie DEEE, elles, restent bien dans l'inventaire.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import HEURES_PAR_AN, U

NOM = config.nom("repeteurs wifi")


# Les répéteurs sont-ils un auxiliaire DE LA CENTRALE (leur consommation se
# déduit du productible) ou de l'instrumentation scientifique (hors frontières) ?
# True = auxiliaire, c'est le choix par défaut, le plus prudent.
AUXILIAIRE = True


def consommation_kwh(ctx):
    """Consommation d'usage sur toute la durée de vie, en kWh (expression).

    Utilisée par `systeme.energie_totale` pour calculer le kWh NET livré :
    c'est le dénominateur de l'unité fonctionnelle qui porte cette
    consommation, pas l'inventaire. Voir le docstring du module.
    """
    p = ctx.p
    if not AUXILIAIRE:
        return 0.0
    return (p.n_repeteurs * p.p_repeteur_kw
            * (HEURES_PAR_AN * U("hour/year")) * p.duree_vie_an)


def construire(ctx):
    p = ctx.p
    n_jeux = p.duree_vie_an / p.duree_vie_repeteur_an
    m_electronique = p.n_repeteurs * p.m_repeteur_kg * n_jeux

    # ⚠ PAS d'échange d'électricité ici : la consommation d'usage est un
    # auxiliaire de la centrale, déduit du productible dans
    # `systeme.energie_totale`. La compter ici reviendrait à l'acheter au mix
    # fioul de l'île (0,914 kg/kWh) au lieu du kWh que la plateforme produit
    # elle-même — un facteur 10 sur le même kWh.
    exchanges = {
        ctx.ei.electronique: m_electronique,
    }
    if ctx.ei.deee is not None:
        exchanges[ctx.ei.deee] = ctx.ei.signe_deee * m_electronique

    act = agb.newActivity(ctx.db, NOM, unit="unit", exchanges=exchanges)
    act.updateMeta(**{config.AXE: "Repeteurs"})
    return act
