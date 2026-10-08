"""
Électricité du réseau de l'île, calée sur le facteur d'émission polynésien.

Pourquoi une activité maison ? ecoinvent n'a pas de mix « PF ». Sans dataset
local, la consommation prélevée sur le réseau (répéteurs wifi aujourd'hui,
d'autres usages demain) est modélisée par un mix mondial ou européen, très loin
de la réalité d'un réseau insulaire au fioul : 0,914 kg CO₂-eq/kWh à Raiatea
contre ~0,6 pour le mix mondial et 0,08 pour le mix français.

Méthode : on part d'un dataset ecoinvent de production électrique **au fioul**
— techniquement représentatif d'une centrale thermique d'île — et on l'échelle
d'un facteur `k` tel que le GWP de l'activité vaille exactement le facteur
d'émission du guide ADEME Polynésie française 2023 (tableau 34), pertes de
réseau incluses.

⚠ Limite à écrire dans le rapport : le calage porte sur le **carbone**. Les
autres catégories d'impact (toxicité, eutrophisation, ressources) sont celles
du dataset fioul multipliées par `k` — représentatives d'un mix thermique, mais
non calées sur des données polynésiennes. Si un poste électrique devenait
dominant sur une de ces catégories, il faudrait construire un vrai mix.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import U

NOM = config.nom("electricite reseau, Raiatea")

# Facteurs d'émission du mix consommé (kg CO₂-eq/kWh, pertes incluses).
# Source : guide des facteurs d'émission de la Polynésie française, ADEME 2023,
# tableau 34. Utilisés aussi pour le CO₂ évité par archipel.
FE_ARCHIPELS = {
    "Tahiti": 0.587,      # part d'hydraulique importante
    "Societe": 0.914,     # îles de la Société hors Tahiti — dont Raiatea
    "Australes": 1.065,
    "Tuamotu": 1.193,
    "Gambier": 1.045,
    "Marquises": 0.974,
}

FE_RAIATEA = FE_ARCHIPELS["Societe"]


def construire(ctx, fe_cible: float = FE_RAIATEA):
    """Crée l'activité « 1 kWh soutiré sur le réseau de Raiatea »."""
    source = ctx.ei.elec_fioul
    fe_source = _facteur_emission(source)

    if fe_source is None or fe_source <= 0:
        print(f"⚠ GWP du dataset source non calculable : pas de calage, "
              f"on utilise {source['name']} tel quel.")
        facteur = 1.0
    else:
        facteur = fe_cible / fe_source
        print(f"  électricité Raiatea : {source['name']} "
              f"({fe_source:.3f} kg CO2e/kWh) × {facteur:.3f} "
              f"-> {fe_cible:.3f} kg CO2e/kWh (ADEME PF 2023)")

    act = agb.newActivity(
        ctx.db, NOM, unit="kWh",
        exchanges={source: facteur * U("kWh/kWh")})
    return act


def _facteur_emission(act):
    """GWP100 d'un kWh du dataset, calculé une fois à la construction."""
    import brightway2 as bw
    try:
        lca = bw.LCA({act: 1}, config.GWP)
        lca.lci()
        lca.lcia()
        return float(lca.score)
    except Exception as err:      # noqa: BLE001
        print(f"⚠ calcul du GWP de {act['name']} impossible "
              f"({type(err).__name__}: {err})")
        return None
