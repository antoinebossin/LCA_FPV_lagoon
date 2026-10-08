"""
Poste « Maintenance » : nettoyage des modules à l'eau douce + trajets bateau.

Modélisé PAR PLATEFORME (un aller-retour par plateforme, une cuve par
plateforme) et sur toute la durée de vie.

- eau douce : 100 L par visite (capacité max de la cuve). Ressource non sous
  stress à Raiatea → pas de facteur de rareté ajouté, le flux alimente déjà la
  catégorie *water use* ;
- gazole : ~0,3 L par visite (Mercury 30 ch, coque alu chargée, 4 A/R × 1 km),
  converti en MJ via un PCI unique (`PCI_DIESEL_MJ_PAR_L = 31`) ;
- fréquence : ~15 visites/an (une maintenance toutes les 3 semaines).

Le total dépend de la durée de vie via `duree_vie_an` : contrairement à
l'ancien notebook, ce n'est plus une constante Python figée à 30 ans, donc la
sensibilité « durée de vie » traite correctement ce poste.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import PCI_DIESEL_MJ_PAR_L, RHO_EAU_KG_PAR_L, U

NOM = config.nom("maintenance (eau douce + bateau)")


def construire(ctx):
    p = ctx.p
    n_visites = p.maint_par_an * p.duree_vie_an            # sans dimension

    eau_kg = n_visites * p.eau_par_visite_l * (RHO_EAU_KG_PAR_L * U("kg/L"))
    diesel_mj = n_visites * p.diesel_par_visite_l * (PCI_DIESEL_MJ_PAR_L * U("MJ/L"))

    act = agb.newActivity(
        ctx.db, NOM, unit="unit",
        exchanges={
            ctx.ei.eau_douce: eau_kg,
            ctx.ei.diesel_bateau: diesel_mj,
        })
    act.updateMeta(**{config.AXE: "Maintenance"})
    return act
