"""
Les 4 modalités du démonstrateur : données terrain, et rien d'autre.

Toutes les valeurs mesurées ou relevées sur le parc de Raiatea sont ici, avec
leur source. Ce fichier ne contient AUCUNE logique de modèle : il produit des
dictionnaires `{nom_de_paramètre: valeur}` que l'on passe à
`systeme.impacts(ctx, **modalite)`.

| Code | Nom       | Modules | Wc/mod | kWc  | Surface | Type              |
|------|-----------|---------|--------|------|---------|-------------------|
| S1   | SH81      | 28      | 395    | 11,06| 1,99 m² | opaque 19 %       |
| S2   | SH51      | 20      | 395    | 7,90 | 1,99 m² | opaque 51 %       |
| S3   | SH81-UV   | 45      | 290    | 13,05| 1,70 m² | semi-transp. 19 % |
| S4   | SH51-UV   | 45      | 170    | 7,65 | 1,70 m² | semi-transp. 51 % |

Sources : QUESTIONNAIRE_PV_SELON_REFERENTIEL_ADEME_CYCLECO (feuille ICV),
fiches CS Wismar, bilan de masse Tracabilité_v2.
"""

from __future__ import annotations

from . import ancrage, cable, parametres, parasol_bridge, transport
from .parametres import productible_moyen

# ── Hypothèses communes ────────────────────────────────────────────────────
# ⚠ SOURCE UNIQUE : ces trois constantes sont déclarées dans `parametres.py`,
# qui en dérive AUSSI les bornes du paramètre `productible_kwh_kwc_an`. Les
# redéclarer ici ferait diverger le nominal de sa propre plage — c'est
# exactement le bug corrigé en août 2026 (nominal 973 hors de [1000 ; 1200]).
# ⚠ Alias de compatibilité : plusieurs modules font encore
# `modalites.P0_PRODUCTIBLE`. Il est figé au chargement — ne PAS s'en servir
# dans du code appelé après une édition de `parametres.py` (cf. la note de
# `jeux_de_parametres`). Lire `parametres.PRODUCTIBLE_P0` à la place.
from .parametres import PRODUCTIBLE_P0 as P0_PRODUCTIBLE          # noqa: E402
from .parametres import TAUX_DEGRADATION                          # noqa: E402
from .parametres import DUREE_VIE_REFERENCE as DUREE_VIE_ANS      # noqa: E402
EPAISSEUR_VERRE_MM = 4       # bi-verre (2 × 2 mm)

# Mix électrique de FABRICATION des modules. Les CS Wismar sont assemblés à
# Wismar, en Allemagne (fiches techniques Doc_panneaux_Wismar). Le défaut de
# parasol est « CN » — sans rapport avec notre chaîne. On laisse
# `parasol_bridge.figer_mix_fabrication` choisir la meilleure valeur disponible
# dans la version de parasol installée, en privilégiant un mix allemand, et
# surtout l'écrire dans le DEFAULT du paramètre : sans quoi l'analyse de
# sensibilité et le Monte-Carlo repartent sur le mix chinois (cf. le docstring
# de cette fonction).
PREFERENCES_MIX = ("DE", "Germany", "RER", "EU", "ENTSOE", "Europe")
PART_CADRE_ALU = 0.11        # 11 % de la masse du module (répartition c-Si type)

# Puissance d'UN micro-onduleur (Deye SUN-M80G4). parasol interpole la
# composition matière de l'onduleur entre un modèle 2,5 kW et un modèle 500 kW :
# il faut donc lui donner la puissance unitaire de l'appareil, pas celle de la
# plateforme. Avec 0,8 kW on reste du côté « petit onduleur », ce qui est le
# cas réel — l'ancien modèle passait la puissance de la centrale (7,9 kWc), ce
# qui décalait l'interpolation vers un onduleur central.
PUISSANCE_MICRO_ONDULEUR_KW = 0.8

# Surfaces de cellule
A_M10_HALF = 0.182 * 0.091   # Diamond M108, half-cut  -> 0,016562 m²
A_M2_FULL = 0.156 * 0.156    # Excellent M54 / M32     -> 0,024336 m²
A_M6_FULL = 0.166 * 0.166    # borne haute, non retenue (à confirmer par mesure)

# ── Données brutes par modalité ────────────────────────────────────────────
# (nom lisible, puissance kWc, rendement kWc/m², surface module m², masse
#  module kg, nb modules, nb cellules/module, surface cellule m², nb onduleurs,
#  aluminium de structure kg, masse totale de structure kg)
DONNEES = {
    "S1 (SH81, opaque 19%)": dict(
        code="SH81", kwc=11.06, rendement=0.198, surface_module=1.99,
        masse_module=26.0, n_modules=28, n_cellules=108, aire_cellule=A_M10_HALF,
        n_onduleurs=14, alu_structure=718.418, structure_totale=1061.0),
    "S2 (SH51, opaque 51%)": dict(
        code="SH51", kwc=7.90, rendement=0.198, surface_module=1.99,
        masse_module=26.0, n_modules=20, n_cellules=108, aire_cellule=A_M10_HALF,
        n_onduleurs=10, alu_structure=606.416, structure_totale=949.0),
    "S3 (SH81-UV, semi-transp. 19%)": dict(
        code="SH81-UV", kwc=13.05, rendement=0.1706, surface_module=1.70,
        masse_module=22.0, n_modules=45, n_cellules=54, aire_cellule=A_M2_FULL,
        n_onduleurs=23, alu_structure=679.318, structure_totale=1022.0),
    "S4 (SH51-UV, semi-transp. 51%)": dict(
        code="SH51-UV", kwc=7.65, rendement=0.100, surface_module=1.70,
        masse_module=22.0, n_modules=45, n_cellules=32, aire_cellule=A_M2_FULL,
        n_onduleurs=11, alu_structure=679.318, structure_totale=1022.0),
}

ORDRE = list(DONNEES)


# ⚠ NE PAS LIER LA CONSTANTE AU CHARGEMENT DU MODULE.
#
# `from .parametres import PRODUCTIBLE_P0` fige la valeur au moment de l'import,
# et un argument par défaut la fige au moment du `def`. Avec `%autoreload 2`,
# éditer `parametres.py` recharge parametres SEULEMENT : ce module-ci n'a pas
# changé, il n'est pas rechargé, et il continue d'utiliser l'ancienne valeur.
# On lit donc `parametres.PRODUCTIBLE_P0` À L'APPEL, à travers le module.
def jeux_de_parametres(ctx, duree_vie=None, p0=None,
                       degradation=None, verbeux=True) -> dict:
    """Construit le dict {libellé: {paramètre: valeur}} des 4 modalités."""
    p0 = parametres.PRODUCTIBLE_P0 if p0 is None else p0
    degradation = (parametres.TAUX_DEGRADATION if degradation is None
                   else degradation)
    duree_vie = (parametres.DUREE_VIE_REFERENCE if duree_vie is None
                 else duree_vie)
    p_moyen = productible_moyen(p0, degradation, duree_vie)
    # Masses numériques nécessaires au bilan de transport. Elles sont calculées
    # PAR LEUR MODULE D'ORIGINE, à partir des valeurs par défaut déclarées dans
    # `parametres.py` — aucune constante n'est recopiée ici (cf. le docstring
    # de `ancrage.masse_kg`).
    masse_ancrage = ancrage.masse_kg()
    masse_cable = cable.masse_cable_totale_kg()
    # La clé du câble est P/P_parc (06/10/2026) : elle n'a de sens que si
    # P_parc est bien la somme des plateformes décrites ici.
    p_parc = sum(d["kwc"] for d in DONNEES.values())
    if abs(p_parc - cable.P_PARC_KWC) > 1e-6:
        raise ValueError(f"cable.P_PARC_KWC = {cable.P_PARC_KWC} alors que les "
                         f"modalités totalisent {p_parc:.2f} kWc : la clé de "
                         f"répartition du câble ne sommerait pas à 1.")

    # Mix de fabrication : figé une fois pour toutes dans le DEFAULT du
    # paramètre parasol, pour que le résultat principal ET la sensibilité
    # décrivent bien des modules assemblés en Allemagne.
    mix = parasol_bridge.figer_mix_fabrication(ctx.par, PREFERENCES_MIX)
    parasol_bridge.figer_puissance_onduleur(ctx.par, PUISSANCE_MICRO_ONDULEUR_KW)

    if verbeux:
        print(f"Productible 1re année {p0:.0f} kWh/kWc/an -> "
              f"moyen sur {duree_vie} ans : {p_moyen:.1f} kWh/kWc/an "
              f"(dégradation linéaire {degradation*100:.2f} %/an)")

    jeux = {}
    for libelle, d in DONNEES.items():
        masse_cable_part = masse_cable * cable.part_cable_num(d["kwc"])
        masse_systeme_kg = (d["structure_totale"] + masse_ancrage + masse_cable_part
                            + d["n_modules"] * d["masse_module"]
                            + d["n_onduleurs"] * 3.0)

        # paramètres portés par parasol (noms résolus, jamais écrits en dur)
        valeurs = parasol_bridge.valeurs_parasol(
            ctx.par,
            epaisseur_verre=EPAISSEUR_VERRE_MM,
            cadre_alu_surfacique=d["masse_module"] * PART_CADRE_ALU / d["surface_module"],
            bifacial=False,
            # `mix_fabrication` n'est PLUS passé ici : il est figé dans le
            # `default` du paramètre par `figer_mix_fabrication` ci-dessus.
            # Le repasser déclenchait un « marked as FIXED, but passed in
            # parameters : ignored » à chaque appel de compute_impacts.
            # Idem pour `puissance_onduleur`, figé par
            # `figer_puissance_onduleur` ci-dessus.
        )

        # nos paramètres
        valeurs.update({
            "p_install_kwc": d["kwc"],
            "rendement_module": d["rendement"],
            "duree_vie_an": duree_vie,
            "productible_kwh_kwc_an": round(p_moyen, 1),
            "packing_cellules": d["n_cellules"] * d["aire_cellule"] / d["surface_module"],
            "n_modules": d["n_modules"],
            "n_onduleurs": d["n_onduleurs"],
            "m_alu_structure_kg": d["alu_structure"],
            "m_panneaux_kg": d["n_modules"] * d["masse_module"],
            "m_systeme_t": round(masse_systeme_kg / 1000.0, 4),
        })
        jeux[libelle] = valeurs

    if verbeux:
        _resume(jeux)
    return jeux


def _resume(jeux):
    masse_parc = sum(j["m_systeme_t"] for j in jeux.values())
    print(f"Masse réelle du parc : {masse_parc:.2f} t "
          f"(allocation du fret : masse réelle, en tonne-kilomètre)")
    for libelle, v in jeux.items():
        print(f"  {libelle:34s} packing {v['packing_cellules']:.2f} | "
              f"panneaux {v['m_panneaux_kg']:.0f} kg | "
              f"alu {v['m_alu_structure_kg']:.0f} kg | "
              f"système {v['m_systeme_t']:.2f} t")


def code(libelle: str) -> str:
    """« S2 (SH51, opaque 51%) » -> « SH51 » (pour les étiquettes de figures)."""
    return DONNEES[libelle]["code"]
