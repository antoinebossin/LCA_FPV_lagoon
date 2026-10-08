"""
Constantes globales du modèle ACV « plateforme PV flottante — lagon de Raiatea ».

C'est le SEUL endroit où l'on écrit un nom de base, un préfixe ou une liste de
méthodes. Tout le reste du package importe depuis ici.
"""

# ── Brightway / ecoinvent ──────────────────────────────────────────────────
PROJET_BW = "PV-project"
EI_VERSION = "3.11"
EI = f"ecoinvent-{EI_VERSION}-cutoff"
BIOSPHERE = f"ecoinvent-{EI_VERSION}-biosphere"

# Base de premier plan (foreground) : nos activités + les briques parasol.
DB = "fpv-lagon"

# Base figée exportable vers Activity Browser (facultatif).
DB_STATIQUE = "fpv-lagon-static"

# ── Préfixes ───────────────────────────────────────────────────────────────
# Réponse au reviewer : nos activités portent un tag DIFFÉRENT de [parasol],
# pour qu'on distingue d'un coup d'œil ce qui vient de parasol-lca et ce qui
# est spécifique au projet.
PREFIXE = "[fpv_lagon] "
PREFIXE_PARASOL = "[parasol] "


def nom(suffixe: str) -> str:
    """Nom complet d'une de NOS activités."""
    return PREFIXE + suffixe


# ── Axe de contribution ────────────────────────────────────────────────────
# Chaque activité de 1er niveau du système porte un attribut `phase`.
# `compute_impacts(..., axis="phase")` ventile alors l'impact par poste, sans
# aucune analyse de contribution maison (fonctionnalité native lca_algebraic).
AXE = "phase"

PHASES = [
    "Panneaux",
    "Onduleurs",
    "Structure",      # ossature aluminium anodisé + boulonnerie inox
    "Flotteurs",      # mousse EPS + peau MDPE — séparés de la structure en
                      # août 2026 : deux matériaux, deux durées de vie, deux
                      # filières de fin de vie. Les confondre masquait le
                      # poids réel du métal.
    "Ancrage",
    "Cable",
    "Maintenance",
    "Repeteurs",
    "Transport",
    "Chantier",       # montage sur le lagon + démontage en fin de vie.
                      # REMIS le 05/10/2026, après retrait en août 2026 : ce
                      # n'est plus le prorata d'un chantier terrestre de
                      # 570 kWc mais le geste réel, quelques centaines de
                      # mètres de bateau, sur le dataset de la maintenance.
                      # Le motif est la COMPLÉTUDE de la frontière, pas le
                      # chiffre — cf. le docstring de chantier.py.
    "FinDeVie",
]

# ── Méthodes d'impact : EF v3.1 (référentiel ADEME / CYCLECO) ──────────────
METHODES_EF = [
    ("EF v3.1", "climate change", "global warming potential (GWP100)"),
    ("EF v3.1", "ozone depletion", "ozone depletion potential (ODP)"),
    ("EF v3.1", "ionising radiation: human health", "human exposure efficiency relative to u235"),
    ("EF v3.1", "photochemical oxidant formation: human health", "tropospheric ozone concentration increase"),
    ("EF v3.1", "particulate matter formation", "impact on human health"),
    ("EF v3.1", "acidification", "accumulated exceedance (AE)"),
    ("EF v3.1", "eutrophication: freshwater", "fraction of nutrients reaching freshwater end compartment (P)"),
    ("EF v3.1", "eutrophication: marine", "fraction of nutrients reaching marine end compartment (N)"),
    ("EF v3.1", "eutrophication: terrestrial", "accumulated exceedance (AE)"),
    ("EF v3.1", "ecotoxicity: freshwater", "comparative toxic unit for ecosystems (CTUe)"),
    ("EF v3.1", "human toxicity: carcinogenic", "comparative toxic unit for human (CTUh)"),
    ("EF v3.1", "human toxicity: non-carcinogenic", "comparative toxic unit for human (CTUh)"),
    ("EF v3.1", "land use", "soil quality index"),
    ("EF v3.1", "material resources: metals/minerals", "abiotic depletion potential (ADP): elements (ultimate reserves)"),
    ("EF v3.1", "energy resources: non-renewable", "abiotic depletion potential (ADP): fossil fuels"),
    ("EF v3.1", "water use", "user deprivation potential (deprivation-weighted water consumption)"),
]

GWP = METHODES_EF[0]

# ── Méthodes d'impact : ReCiPe 2016 endpoint (H) — LECTURE SECONDAIRE ──────
# ⚠ CE N'EST PAS UNE AGRÉGATION DES RÉSULTATS EF, et il faut l'écrire dans
# l'article. EF v3.1 n'a PAS de niveau endpoint : le rapport de référence du
# JRC est explicite, « the inputs and outputs from the life cycle inventory are
# aggregated in 16 midpoint characterised impact categories ». Pour obtenir des
# aires de protection il faut donc une AUTRE méthode, ici ReCiPe 2016, dont la
# modélisation diffère de celle d'EF sur toute la chaîne. Les deux lectures
# portent sur le MÊME inventaire mais ne sont pas convertibles l'une en l'autre.
#
# Perspective (H), « hierarchist » : celle par défaut de ReCiPe et celle de la
# quasi-totalité des ACV publiées, donc la seule qui rende nos chiffres
# comparables. (I) est optimiste à horizon court — et, dans notre base, elle
# n'expose que 11 sous-catégories d'ecosystem quality au lieu de 12, il lui
# manque `water use: terrestrial ecosystems`. (E) est précautionneuse à horizon
# long. Les deux relèvent de la sensibilité, pas du résultat principal.
#
# Variante AVEC émissions de long terme (pas « no LT »), par cohérence avec nos
# résultats EF qui sont en variante standard. L'écart n'était que de 0 % sur le
# GWP ; sur l'écotoxicité il ne le sera pas, le lessivage de décharge étant
# précisément une émission au-delà de 100 ans.
RECIPE_H = "ReCiPe 2016 v1.03, endpoint (H)"

METHODES_RECIPE_H = [
    (RECIPE_H, "total: human health", "human health"),
    (RECIPE_H, "total: ecosystem quality", "ecosystem quality"),
    (RECIPE_H, "total: natural resources", "natural resources"),
]

# Les sous-catégories, UNIQUEMENT pour le contrôle « total == somme » de
# `endpoint.verifier`. Elles ne sont pas destinées à être publiées : les publier
# reviendrait à refaire du midpoint avec une deuxième méthode.
METHODES_RECIPE_H_DETAIL = {
    "human health": [
        (RECIPE_H, "human health", s) for s in (
            "climate change: human health", "human toxicity: carcinogenic",
            "human toxicity: non-carcinogenic", "ionising radiation",
            "ozone depletion", "particulate matter formation",
            "photochemical oxidant formation: human health",
            "water use: human health")],
    "ecosystem quality": [
        (RECIPE_H, "ecosystem quality", s) for s in (
            "acidification: terrestrial", "climate change: freshwater ecosystems",
            "climate change: terrestrial ecosystems", "ecotoxicity: freshwater",
            "ecotoxicity: marine", "ecotoxicity: terrestrial",
            "eutrophication: freshwater", "eutrophication: marine", "land use",
            "photochemical oxidant formation: terrestrial ecosystems",
            "water use: aquatic ecosystems", "water use: terrestrial ecosystems")],
    "natural resources": [
        (RECIPE_H, "natural resources", s) for s in (
            "energy resources: non-renewable, fossil",
            "material resources: metals/minerals")],
}

# Repli si la métadonnée d'unité manque dans la base.
UNITES_RECIPE = {
    "human health": "DALY",
    "ecosystem quality": "species·yr",
    "natural resources": "USD2013",
}

# ⚠ LES TROIS NE S'ADDITIONNENT PAS. DALY, species·yr et USD2013 n'ont aucune
# commune mesure. ReCiPe propose bien une pondération en score unique, mais elle
# est lourdement chargée en jugements de valeur et n'est pas livrée avec les
# méthodes de la base. On publie TROIS indicateurs, jamais leur somme.

# ── Couleurs des 4 modalités (identiques au rapport) ───────────────────────
COULEURS = {
    "SH81": "#F6CF71",     # S1 — opaque 19 %
    "SH51": "#66C5CC",     # S2 — opaque 51 %
    "SH81-UV": "#5A9E6B",  # S3 — semi-transparent 19 %
    "SH51-UV": "#FE88B1",  # S4 — semi-transparent 51 %
}

# ── Références littérature (g CO2-eq/kWh) pour les graphes de comparaison ──
REFS_LITTERATURE = {
    "FPV inland\n(IEA T12 2024)": 49.0,
    "PV au sol\n(IEA T12 2024)": 38.0,
    "FPV Thaïlande\n(Cromratie 2021)": 73.3,
}
