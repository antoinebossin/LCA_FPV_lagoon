"""
Tous NOS paramètres lca_algebraic, déclarés en un seul endroit.

Règles suivies (elles répondent au commentaire 2 du reviewer) :

* toute grandeur qui pilote une masse, une longueur ou une fréquence est un
  VRAI paramètre lca_algebraic — jamais une variable Python injectée dans une
  chaîne de caractères. Conséquence : `compute_impacts`, `oat_matrix` et le
  Monte-Carlo natifs les voient tous, sans patch a posteriori ;
* chaque paramètre porte son unité. Avec `units_enabled=True`, lca_algebraic
  vérifie la compatibilité avec l'unité de l'activité cible : les erreurs du
  type « des litres dans un flux en kg » deviennent impossibles ;
* les paramètres que parasol fournit déjà (puissance, rendement, durée de vie,
  productible, verre, cadre alu, argent, mix électrique) ne sont PAS
  redéclarés : on réutilise les siens via `ctx.par` (cf. parasol_bridge).

⚠ SENS DES BORNES min/max. lca_algebraic les utilise comme **plage
d'incertitude** : `oat_matrix`, `incer_stochastic_matrix` et notre tornado
balaient exactement cet intervalle. Ce ne sont donc PAS des bornes de validité.
Écrire `p_install_kwc ∈ [1 ; 5000] kWc` — techniquement vrai — produirait un
tornado où la puissance installée pèse 650 % et écraserait tout le reste.

Règle retenue : `min`/`max` = plage dans laquelle la valeur réelle a une chance
raisonnable de se trouver, compte tenu de ce qu'on sait aujourd'hui. Pour un
paramètre mesuré (nombre de modules, puissance de plaque) c'est étroit ; pour
une hypothèse (masse linéique de corde, durée de vie des flotteurs) c'est large.
Explorer une AUTRE configuration (1 ha, autre île, onduleur central) n'est pas
de l'incertitude : c'est un scénario, et ça se fait en passant la valeur
explicitement à `systeme.impacts()`.

"""

from __future__ import annotations

import math
from contextlib import contextmanager
from types import SimpleNamespace

import lca_algebraic as agb
from lca_algebraic.params import DistributionType

# ── Constantes physiques (pas de raison de les faire varier) ───────────────
ANGLE_ANCRAGE_DEG = 63.0                       # géométrie Seaflex
TAN_ANCRAGE = math.tan(math.radians(ANGLE_ANCRAGE_DEG))
RHO_EAU_KG_PAR_L = 1.0                         # eau douce
PCI_DIESEL_MJ_PAR_L = 31.0                     # PCI gazole — valeur de référence unique
HEURES_PAR_AN = 24 * 365

# ── Productible : source unique des constantes ────────────────────────────
#
# ⚠ PIÈGE CORRIGÉ (août 2026). Les bornes du paramètre étaient exprimées sur le
# productible de PREMIÈRE ANNÉE (1000-1200, mode 1025), alors que le paramètre
# lui-même porte le productible MOYEN sur la durée de vie, dégradation incluse
# — c'est `modalites.jeux_de_parametres` qui y injecte `productible_moyen()`.
# Le nominal valait donc 973, soit HORS de sa propre plage [1000 ; 1200], ce
# qui se voyait sur le tornado : la barre ne contenait pas le point nominal.
#
# Correction : les valeurs de référence sont déclarées ici en 1ʳᵉ ANNÉE (les
# seules qui aient un sens physique et qu'on mesure), et les bornes du
# paramètre en sont DÉRIVÉES par le même facteur de dégradation que celui
# appliqué au nominal. Les deux ne peuvent plus diverger.
# ⚠ RÉVISÉ LE 26/09/2026 : 1 025 → 1 096 kWh/kWc/an.
#
# Le 1 025 sortait d'une chaîne qui comptait comme production réelle des
# journées qui n'en étaient pas. Quatre défauts, tous corrigés dans
# `irradiance/version_actuelle/productible_corrige.py` :
#
#   1. TRONCATURE TÉLÉMÉTRIQUE. `Etdy_ge0` est un compteur cumulé remis à
#      zéro à minuit et le pipeline en prenait le max() : quand le flux
#      Solarman s'arrêtait à midi, la journée était enregistrée à sa valeur
#      de midi. 51 jours concernés. L'énergie avait bien été produite.
#   2. ONDULEURS MUETS. Les 21 onduleurs morts depuis le 18/02/2026
#      REPORTENT 0,00 kWh : ils étaient comptés comme présents et tiraient
#      leur modalité vers le bas au lieu d'être remplacés par leurs voisins.
#   3. COUPURES DE SITE. 10 jours où les 38 onduleurs sains sont tous bas ET
#      tous d'accord entre eux à ±0,1 près — signature d'une coupure du
#      site, pas d'un défaut de matériel. Plus deux arrêts de la plateforme
#      S1 (26/01→04/02 et 28/03→15/04/2026).
#   4. MOIS INCOMPLET. Avril 2026, dont l'export s'arrête le 26, comptait
#      pour un mois entier : −13 % sur ce mois.
#
# Contrôle : le R² de la régression productible ↔ irradiance passe de 0,33 à
# 0,695 et la RMSE de 24,0 à 11,5 %, alors qu'AUCUNE correction ne vise le R².
#
# Les cinq onduleurs chroniquement bas (indice médian < 0,80) sont GARDÉS :
# ils produisent réellement moins, et le dénominateur décrit ce qui sort du
# système. Les relever donnerait 1 138 — scénario, pas référence.
#
# Effet de bord heureux : le nominal tombe désormais au MILIEU de [1000 ; 1200]
# au lieu d'en toucher la borne basse. La loi triangulaire du Monte-Carlo
# n'est plus dissymétrique vers le haut, défaut signalé en septembre.
#
# Note : `economie.PRODUCTIBLE_CLASSEUR` garde 1 025, parce que `verifier_lcoe`
# doit continuer à rejouer le classeur d'Antoine, qui a été bâti sur 1 025.
PRODUCTIBLE_P0_PLEINE_DISPO = 1096.0   # kWh/kWc/an, 1ʳᵉ année, 100 % de disponibilité

# ── Disponibilité de la centrale ───────────────────────────────────────────
# AJOUTÉ LE 06/10/2026, retour du relecteur.
#
# Le 1 096 ci-dessus est un productible RECONSTRUIT à pleine disponibilité :
# chaque onduleur absent ou arrêté un jour donné est remplacé par la moyenne
# de ses voisins (§ 2.4 de l'article). Il ne décrit donc pas une centrale
# réelle, qui connaît des arrêts — pannes, maintenance, coupures réseau.
# Le relecteur demande d'appliquer un taux de disponibilité de 97 % en
# RÉFÉRENCE, et de garder 100 % (le productible reconstruit tel quel) en
# sensibilité. Cf. `resultats.sensibilite_disponibilite`.
#
# Comme la dégradation, c'est un choix de SCÉNARIO, pas une incertitude : il
# n'est pas tiré au Monte-Carlo. Il décale TOUTE la loi du productible (mode,
# bornes et écart-type), parce que l'incertitude de mesure porte sur le
# productible à pleine disponibilité et que la disponibilité s'applique
# ensuite. Garder les bornes à 1 000-1 200 avec un mode à 1 063 aurait
# tronqué la loi à 1,3 σ en bas et 2,7 σ en haut : un Monte-Carlo biaisé vers
# le haut, exactement le défaut corrigé le 26/09.
TAUX_DISPONIBILITE = 0.97                # référence — demande du relecteur
TAUX_DISPONIBILITE_VARIANTES = {
    "Availability 97 %, reference": TAUX_DISPONIBILITE,
    "Full availability (reconstructed)": 1.00,
}

# Productible de 1ʳᵉ année EFFECTIF = reconstruit × disponibilité. C'est la
# constante que lit tout le reste du paquet (modalites, territoire, economie,
# litterature) : un seul point d'entrée, rien d'autre à modifier.
PRODUCTIBLE_P0 = PRODUCTIBLE_P0_PLEINE_DISPO * TAUX_DISPONIBILITE      # 1063.1
PRODUCTIBLE_P0_MIN = 1000.0 * TAUX_DISPONIBILITE   # chaîne non corrigée + variabilité interannuelle
PRODUCTIBLE_P0_MAX = 1200.0 * TAUX_DISPONIBILITE   # parc pleinement disponible (1 138) + bonne année
PRODUCTIBLE_P0_STD = 50.0 * TAUX_DISPONIBILITE     # ±1 σ
# ── Dégradation des modules ────────────────────────────────────────────────
# ⚠ RÉVISÉ LE 06/10/2026 : 0,70 → 0,35 %/an, retour du relecteur.
#
# La référence redevient la garantie linéaire du fabricant (Sonnenstrom,
# 0,35 %/an), et la sensibilité couvre 0,5 / 0,7 / 1,0 %/an : les deux
# valeurs de la guideline Task 12 et une borne haute à 1 %/an. L'argument
# ci-dessous (02/10) reste celui qui justifie de PUBLIER la sensibilité : la
# guideline ne reconnaît pas une garantie comme preuve, et l'article doit
# donc montrer ce que donnent ses valeurs par défaut.
#
# ── Historique : RÉVISÉ LE 02/10/2026 : 0,35 → 0,70 %/an ──────────────────
#
# On prenait jusqu'ici la garantie linéaire du fabricant (Sonnenstrom,
# 0,35 %/an). Les lignes directrices de référence du domaine disent autre
# chose, et elles sont explicites sur la charge de la preuve :
#
#   « Assume a linear degradation of 0.7 %-points per year unless long-term
#     scientific evidence and independently verified test results prove a
#     different value. »
#   « Use an annual degradation rate of 0.5 %-points (instead of 0.7
#     %-points) in a sensitivity analysis, resulting in an average reduction
#     in the annual yield of 7.5 %. »
#
#   Frischknecht R., Stolz P., Heath G., Raugei M., Sinha P., de
#   Wild-Scholten M. (2020), « Methodology Guidelines on Life Cycle
#   Assessment of Photovoltaic Electricity », 4e édition, IEA PVPS Task 12,
#   rapport T12-18:2020, § 3.1.4 Degradation, p. 14.
#
# Une garantie commerciale n'est pas un « independently verified test result »,
# et une année de télémétrie ne permet pas d'établir un taux de dégradation :
# la clause d'échappatoire ne nous est pas ouverte. D'où 0,70 %/an en
# référence, les deux autres valeurs étant publiées en sensibilité (cf.
# `resultats.sensibilite_degradation`).
#
# EFFET : le productible moyen sur 30 ans tombe de 1 040 à 985 kWh/kWc/an,
# soit +5,7 % sur TOUTES les intensités — le productible est au dénominateur
# de l'unité fonctionnelle, et rien d'autre ne bouge.
#
# ⚠ Ce qui ne suit PAS automatiquement : le LCOE. Son dénominateur
# énergétique vit dans le notebook, pas dans ce package. Changer le taux ici
# sans le reporter là-bas publierait une intensité carbone calculée à 0,70 %
# et un coût actualisé calculé à 0,35 %.
#
# Note sur la formule. La guideline annonce « 10,5 % de réduction moyenne »
# pour 0,7 %/an sur 30 ans, soit d*n/2. On conserve d*(n-1)/2, qui est la
# moyenne EXACTE des années 1 à n quand la première ne subit pas encore de
# dégradation (n = 1 -> P0). L'écart entre conventions vaut 0,35 point.
TAUX_DEGRADATION_GARANTIE = 0.0035      # garantie linéaire Sonnenstrom
TAUX_DEGRADATION = TAUX_DEGRADATION_GARANTIE   # RÉFÉRENCE depuis le 06/10/2026
TAUX_DEGRADATION_SENSIBILITE = 0.0050   # variante de sensibilité de la guideline
TAUX_DEGRADATION_IEA = 0.0070           # valeur par défaut IEA PVPS Task 12
TAUX_DEGRADATION_HAUT = 0.0100          # borne haute demandée par le relecteur

# Les quatre scénarios publiés, dans l'ordre du tableau de l'article. La
# PREMIÈRE entrée est la référence : `sensibilite_degradation` calcule les
# écarts par rapport à elle.
TAUX_DEGRADATION_VARIANTES = {
    "Module warranty, reference": TAUX_DEGRADATION,
    "IEA Task 12, sensitivity": TAUX_DEGRADATION_SENSIBILITE,
    "IEA Task 12, default": TAUX_DEGRADATION_IEA,
    "High degradation": TAUX_DEGRADATION_HAUT,
}
DUREE_VIE_REFERENCE = 30         # ans — durée sur laquelle la moyenne est prise


# Facteur moyenne/1ʳᵉ année : P̄ = P₀ · (1 − d·(n−1)/2)
FACTEUR_DEGRADATION = 1 - TAUX_DEGRADATION * (DUREE_VIE_REFERENCE - 1) / 2


def _f(ctx, nom, default, mini, maxi, unite, description,
       distrib=DistributionType.TRIANGLE, **extra):
    """Raccourci `newFloatParam` avec unité et base imposées.

    `**extra` transmet les paramètres propres à certaines lois : `std` pour
    NORMAL et LOGNORMAL, `a`/`b` pour BETA.
    """
    return agb.newFloatParam(
        nom, default=default, min=mini, max=maxi, unit=unite,
        description=description, dbname=ctx.db, distrib=distrib,
        group=description.split(" — ")[0] if " — " in description else None,
        **extra,
    )


def declarer(ctx) -> SimpleNamespace:
    """Déclare tous nos paramètres et les renvoie dans un namespace."""
    p = SimpleNamespace()

    # ── Système ───────────────────────────────────────────────────────────
    # Ces quatre paramètres décrivent la centrale. parasol ne les crée QUE
    # lorsqu'on construit son `Full PV system` et ses modèles d'impact — ce que
    # l'on ne fait pas. On les déclare donc ici : le modèle devient de ce fait
    # indépendant de la version de parasol installée.
    p.p_install_kwc = _f(
        ctx, "p_install_kwc", 7.90, 7.5, 8.3, "kWp",
        "Systeme — puissance crête installée sur la plateforme")
    p.rendement_module = _f(
        ctx, "rendement_module", 0.198, 0.188, 0.208, "kWp/m**2",
        "Systeme — rendement surfacique du module (kWc par m² de module)")
    p.duree_vie_an = _f(
        ctx, "duree_vie_an", 30, 20, 30, "year",
        "Systeme — durée de vie de l'installation (garantie produit 20 ans)")
    # ── Productible : LOI NORMALE TRONQUÉE, calée sur les mesures ──────────
    # C'était le 2ᵉ contributeur du tornado (39 %) avec des bornes 830-1240,
    # soit ±21 % — beaucoup trop large pour une grandeur MESURÉE sur site
    # pendant des mois. On resserre sur [1000 ; 1200], mode 1096 (mesure de
    # 1ʳᵉ année corrigée), loi normale tronquée d'écart-type PRODUCTIBLE_STD.
    #
    # ⚠ Trois pièges documentés ici plutôt que découverts plus tard.
    #
    # 1. `default` sert À LA FOIS de valeur nominale et de moyenne de la loi.
    #    Le nominal du modèle DOIT rester le productible moyen sur 30 ans
    #    (dégradation incluse), pas la mesure de 1ʳᵉ année : c'est
    #    `modalites.jeux_de_parametres` qui l'écrase par `productible_moyen()`.
    #    Le 1096 ci-dessous n'est donc que le centre de la loi.
    # 2. La troncature de lca_algebraic a une imprécision connue : la borne
    #    haute est calculée `(max - min)/std` au lieu de `(max - default)/std`
    #    (params.py, DistributionType.NORMAL). Le tirage peut donc dépasser
    #    `max` de (default - min). Négligeable (0,03 % des tirages), mais à
    #    savoir avant de s'étonner d'un échantillon hors bornes.
    # 3. ⚠ CE PIÈGE A DISPARU LE 26/09/2026, et c'est le seul effet de bord
    #    heureux de la révision du productible. Avec le mode à 1025, la loi
    #    était tronquée à 0,5 σ à gauche et 3,5 σ à droite : très asymétrique,
    #    moyenne des tirages nettement au-dessus du mode, donc un Monte-Carlo
    #    qui ne pouvait aller que dans le bon sens. À 1096, la troncature est
    #    à 1,9 σ de chaque côté : la loi est quasi symétrique et le tirage
    #    explore autant la baisse que la hausse.
    p.productible_kwh_kwc_an = _f(
        ctx, "productible_kwh_kwc_an",
        PRODUCTIBLE_P0 * FACTEUR_DEGRADATION,          # 1009.2 (97 %, 0,35 %/an)
        PRODUCTIBLE_P0_MIN * FACTEUR_DEGRADATION,      # 920.8
        PRODUCTIBLE_P0_MAX * FACTEUR_DEGRADATION,      # 1104.9
        "kWh/kWp/year",
        "Systeme — productible annuel MOYEN, dégradation linéaire incluse "
        f"(1ʳᵉ année {PRODUCTIBLE_P0_MIN:.0f}-{PRODUCTIBLE_P0_MAX:.0f}, "
        f"mode {PRODUCTIBLE_P0:.0f} ; × {FACTEUR_DEGRADATION:.4f})",
        distrib=DistributionType.NORMAL,
        std=PRODUCTIBLE_P0_STD * FACTEUR_DEGRADATION)

    # ── Panneaux ──────────────────────────────────────────────────────────
    # Surface de cellules par m² de module : c'est ce qui distingue un module
    # opaque (packing ~0,90) d'un module semi-transparent (0,46 à 0,77).
    p.packing_cellules = _f(
        ctx, "packing_cellules", 0.90, 0.80, 0.95, "dimensionless",
        "Panneaux — m² de cellules par m² de module (pilote le silicium)")

    # ── Onduleurs (micro-onduleurs Deye SUN-M80G4) ────────────────────────
    p.n_onduleurs = _f(
        ctx, "n_onduleurs", 10, 9, 11, "dimensionless",
        "Onduleurs — nombre de micro-onduleurs par plateforme")
    p.m_onduleur_kg = _f(
        ctx, "m_onduleur_kg", 3.0, 2.5, 3.5, "kg",
        "Onduleurs — masse unitaire (datasheet Deye SUN-M80G4)")
    p.duree_vie_onduleur_an = _f(
        ctx, "duree_vie_onduleur_an", 15, 10, 25, "year",
        "Onduleurs — durée de vie en milieu marin (garantie 25 ans, dégradée)")
    p.l_cable_module_m = _f(
        ctx, "l_cable_module_m", 1.28, 1.0, 1.6, "m",
        "Onduleurs — longueur moyenne du câble module→onduleur (mesurée)")
    p.n_modules = _f(
        ctx, "n_modules", 20, 19, 21, "dimensionless",
        "Panneaux — nombre de modules par plateforme")

    # ── Structure flottante ───────────────────────────────────────────────
    # Masse EN KG PAR PLATEFORME, directement issue du bilan de masse.
    # (L'ancien modèle passait par des kg/m² de module puis remultipliait par
    #  une surface : source de l'erreur de normalisation ±35 % corrigée en v11.)
    # Masse PESÉE, pas estimée (bilan de masse Tracabilité_v2, au gramme près).
    # Les bornes valaient [400 ; 900], soit ±41 % : c'est ce qui la plaçait en
    # 2ᵉ position du tornado avec 35 % d'amplitude. Une plage de ±41 % sur une
    # grandeur mesurée revient à déclarer qu'on ne la connaît pas — et ça
    # écrasait les paramètres réellement incertains. Resserré à ±5 %, ce qui
    # couvre la tolérance de pesée et les variations de longueur de profilé.
    p.m_alu_structure_kg = _f(
        ctx, "m_alu_structure_kg", 606.416, 576.1, 636.7, "kg",
        "Structure — aluminium de la plateforme (bilan de masse Tracabilité_v2, "
        "masse mesurée : plage ±5 %)")
    p.m_eps_flotteurs_kg = _f(
        ctx, "m_eps_flotteurs_kg", 115.92, 58.0, 174.0, "kg",
        "Structure — mousse EPS des flotteurs, PAR JEU (feuille Flotteurs)")
    p.m_mdpe_flotteurs_kg = _f(
        ctx, "m_mdpe_flotteurs_kg", 136.08, 68.0, 204.0, "kg",
        "Structure — peau MDPE des flotteurs, PAR JEU (feuille Flotteurs)")
    p.m_boulonnerie_kg = _f(
        ctx, "m_boulonnerie_kg", 100.0, 50.0, 150.0, "kg",
        "Structure — visserie inox A4 (bilan de masse)")
    # Anodisation des profilés — jusqu'ici négligée, c'était une limite déclarée.
    # L'anodisation se facture à la SURFACE traitée. Pour un profilé extrudé de
    # paroi t anodisé sur ses deux faces : S/m = 2/(t·ρ_alu). Soit 0,37 m²/kg à
    # t = 2 mm et 0,25 m²/kg à t = 3 mm — d'où le défaut de 0,30 et la plage.
    # À affiner en mesurant l'épaisseur de paroi réelle d'un profilé.
    p.surface_anodisee_m2_par_kg = _f(
        ctx, "surface_anodisee_m2_par_kg", 0.30, 0.20, 0.40, "m**2/kg",
        "Structure — surface anodisée par kg de profilé alu (géométrie)")
    p.duree_vie_flotteurs_an = _f(
        ctx, "duree_vie_flotteurs_an", 20, 10, 30, "year",
        "Structure — durée de vie des flotteurs avant remplacement")

    # ── Ancrage ───────────────────────────────────────────────────────────
    p.profondeur_eau_m = _f(
        ctx, "profondeur_eau_m", 3.0, 2.0, 5.0, "m",
        "Ancrage — profondeur d'eau : pilote la corde ET la longueur de câble")
    p.n_ancres = _f(
        ctx, "n_ancres", 4, 4, 5, "dimensionless",
        "Ancrage — nombre de lignes d'ancrage par plateforme")
    p.l_elastique_m = _f(
        ctx, "l_elastique_m", 2.3, 2.0, 2.6, "m",
        "Ancrage — longueur d'élastique Seaflex par ligne (constante doc)")
    p.l_chaine_m = _f(
        ctx, "l_chaine_m", 1.0, 0.8, 1.5, "m",
        "Ancrage — longueur de chaîne par ligne")
    # RECALÉ SUR L'HMPE le 16/09/2026. La valeur précédente (0,17 kg/m) venait
    # d'une corde POLYESTER ; la ligne Seaflex est en HMPE, et à diamètre égal
    # une HMPE est plus légère dans le rapport des densités :
    #
    #     0,17 × 0,97 / 1,38 = 0,1195 → 0,12 kg/m
    #
    # Garder 0,17 en mode n'était pas « conservateur », c'était passer
    # l'essentiel du tirage sur une valeur qu'on savait fausse : la borne basse
    # couvrait le bon cas, mais la loi triangulaire y met peu de masse. La
    # plage [0,10 ; 0,18] garde « la corde est plus grosse que prévu » et
    # abandonne « elle est en polyester », qui n'est plus vrai.
    #
    # ⚠ Reste à PESER un mètre de corde sur site : c'est ce qui clôt la
    # question. L'ancrage pèse ~2 % du GWP, donc l'enjeu est faible, mais la
    # valeur doit être mesurée et non déduite d'un rapport de densités.
    p.rho_corde_kg_m = _f(
        ctx, "rho_corde_kg_m", 0.12, 0.10, 0.18, "kg/m",
        "Ancrage — masse linéique corde HMPE ~16 mm (0,17 polyester × "
        "0,97/1,38 ; à confirmer par pesée)")
    p.rho_elastique_kg_m = _f(
        ctx, "rho_elastique_kg_m", 1.03, 0.70, 1.40, "kg/m",
        "Ancrage — masse linéique élastique Seaflex (calée sur le BoM)")
    p.rho_chaine_kg_m = _f(
        ctx, "rho_chaine_kg_m", 2.20, 1.50, 3.00, "kg/m",
        "Ancrage — masse linéique chaîne acier galvanisé ~10 mm")
    p.m_ancre_kg = _f(
        ctx, "m_ancre_kg", 9.75, 5.0, 15.0, "kg",
        "Ancrage — masse unitaire d'une ancre écologique (39 kg / 4 ancres)")
    # Les deux seules pièces de quincaillerie Seaflex réellement montées. Masses
    # relevées au BoM (colonne « Weight » = masse totale pour la quantité, par
    # ligne d'ancrage) ; plages étroites, ce sont des pièces de catalogue.
    p.m_poulie_kg = _f(
        ctx, "m_poulie_kg", 0.089, 0.06, 0.15, "kg",
        "Ancrage — poulie PA6 par ligne (« Block_50 », fiche Seaflex)")
    p.m_manille_kg = _f(
        ctx, "m_manille_kg", 0.385, 0.30, 0.50, "kg",
        "Ancrage — manille acier galvanisé par ligne (« Shackle_50FVZ », FVZ = "
        "feuerverzinkt ; la galvanisation elle-même n'est pas comptée)")

    # ── Câble de liaison terre-mer ────────────────────────────────────────
    p.dist_cable_eau_m = _f(
        ctx, "dist_cable_eau_m", 380.0, 190.0, 570.0, "m",
        "Cable — distance HORIZONTALE plateforme→plage (feuille Cablage)")
    # Masse linéique de cuivre du câble posé. La valeur est celle du FABRICANT,
    # pas une estimation : TOP HORN 4G95, Copper Index 912 kg/km par
    # conducteur × 4 conducteurs = 3,648 kg/m.
    #
    # ⚠ La plage a été RESSERRÉE le 16/09/2026, de [0,30 ; 4,60] à ±5 %. La
    # borne basse de 0,30 décrivait un câble moyenne tension : c'était un
    # levier de passage à l'échelle glissé dans une loi d'incertitude. Deux
    # choses s'y mélangeaient — ce qu'on ignore sur CE câble, et ce qu'on
    # pourrait construire autrement — et la seconde élargissait la bande
    # publiée d'un facteur qui n'a rien à y faire, tout en plaçant le câble en
    # tête du tornado par la seule largeur de sa plage.
    #
    # Le passage à l'échelle est abandonné dans ce modèle (décision du
    # 16/09/2026) : on décrit le parc installé, avec les valeurs constructeur.
    # Le ±5 % couvre ce qui est réellement incertain ici : le facteur de
    # câblage (mesuré à 1,0714, cf. `tests.t_cable_fiche_fabricant`) et
    # l'arrondi de la fiche.
    p.rho_cuivre_cable_kg_m = _f(
        ctx, "rho_cuivre_cable_kg_m", 3.648, 3.47, 3.83, "kg/m",
        "Cable — cuivre par mètre de TOP HORN 4G95, sur TOUT le parcours "
        "(4 × 912 kg/km, Copper Index fabricant)")
    # Enveloppe du TOP HORN : isolation + gaine, obtenue PAR DIFFÉRENCE
    # (4 995 − 3 648 = 1 347 kg/km). Le fabricant ne la publie pas ; elle
    # hérite donc de l'incertitude du total (tolérance de fabrication, ±2 %)
    # ET de celle du facteur de câblage, qui n'est pas publié non plus et que
    # l'on borne à [1,00 ; 1,10]. Les deux se composent dans le mauvais sens —
    # un total bas avec un cuivre haut donne l'enveloppe la plus basse — d'où
    # une plage nettement asymétrique, calculée par `cable.bornes_enveloppe`.
    p.rho_gaine_cable_kg_m = _f(
        ctx, "rho_gaine_cable_kg_m", 1.347, 1.15, 1.69, "kg/m",
        "Cable — isolation et gaine du TOP HORN 4G95, par différence "
        "(4 995 − cuivre) ; plage = propagation du ±2 % de la fiche et du "
        "facteur de câblage [1,00 ; 1,10]")
    # ⚠ FRONTIÈRE DU SYSTÈME, révisée le 01/10/2026 après relevé sur site :
    # 60 m enterrés, INCLUS. L'étude s'arrête là où s'arrête le câble d'export.
    #
    # Historique, parce que cette valeur a déjà bougé deux fois :
    #   174 m — valeur initiale, décrivant un enfouissement qui n'existe pas ;
    #     0 m — coupure au littoral, envisagée puis abandonnée ;
    #    60 m — longueur MESURÉE de la section enterrée.
    #
    # Pourquoi la frontière tombe ici et pas ailleurs : les 380 m immergés et
    # les 60 m enterrés sont LE MÊME CÂBLE, un TOP HORN 4G95 posé d'un bout à
    # l'autre et dédié à cette seule installation. Il se termine à la fin de la
    # section enterrée ; au-delà, la liaison change de câble et de mode de pose.
    # La frontière suit donc une discontinuité PHYSIQUE de l'objet — la fin du
    # câble d'export — et non un repère géographique ou une commodité de calcul.
    # C'est ce qu'il faut écrire au § 2.2, pas « on s'arrête à la plage ».
    #
    # Figé dans `incertitude.PARAMS_FIGES` : une longueur mesurée au décamètre
    # appartient à la famille des grandeurs RELEVÉES, comme les dénombrements.
    p.dist_cable_terre_m = _f(
        ctx, "dist_cable_terre_m", 60.0, 55.0, 65.0, "m",
        "Cable — section enterrée à terre, incluse dans le périmètre. 60 m "
        "mesurés sur site ; même câble 4G95 que la section immergée. Le "
        "périmètre s'arrête à son extrémité")

    # ── Maintenance ───────────────────────────────────────────────────────
    # ⚠ CE PARAMÈTRE EST HORS DU TIRAGE D'INCERTITUDE (16/09/2026).
    # 15 visites par an n'est pas une inconnue, c'est le protocole retenu : on
    # le CONNAÎT. Il figure donc dans `incertitude.PARAMS_FIGES`, au même titre
    # que la durée de vie.
    #
    # Les bornes ci-dessous ne décrivent donc plus une incertitude mais
    # l'ÉTENDUE DU SCÉNARIO : 15 (protocole) à 26 (une visite tous les quinze
    # jours), chiffrée par `resultats.variante_maintenance`. Le paramètre reste
    # un float ordinaire — le déclarer FIXED ferait ignorer en silence la
    # surcharge du scénario (lca_algebraic émet « marked as FIXED, but passed
    # in parameters : ignored »).
    #
    # Avant cette décision, le mode 15 dans [12 ; 26] donnait une moyenne de
    # tirage de 17,7 visites/an : la variante de protocole était comptée deux
    # fois, et poussait la médiane du Monte-Carlo au-dessus du nominal.
    p.maint_par_an = _f(
        ctx, "maint_par_an", 15, 15, 26, "1/year",
        "Maintenance — visites de nettoyage par an. 15 = protocole retenu ; "
        "les bornes décrivent le SCÉNARIO (jusqu'à 26), pas une incertitude")
    p.eau_par_visite_l = _f(
        ctx, "eau_par_visite_l", 100.0, 90.0, 100.0, "L",
        "Maintenance — eau douce par visite (capacité max de la cuve)")
    p.diesel_par_visite_l = _f(
        ctx, "diesel_par_visite_l", 0.3, 0.2, 0.45, "L",
        "Maintenance — gazole du bateau par visite (Mercury 30 ch, 4 A/R)")

    # ── Répéteurs wifi ────────────────────────────────────────────────────
    p.n_repeteurs = _f(
        ctx, "n_repeteurs", 2, 1, 3, "dimensionless",
        "Repeteurs — nombre de répéteurs wifi par plateforme")
    p.m_repeteur_kg = _f(
        ctx, "m_repeteur_kg", 0.12, 0.08, 0.20, "kg",
        "Repeteurs — masse d'électronique active par répéteur (proxy)")
    p.p_repeteur_kw = _f(
        ctx, "p_repeteur_kw", 0.003, 0.002, 0.005, "kW",
        "Repeteurs — puissance en fonctionnement continu")
    p.duree_vie_repeteur_an = _f(
        ctx, "duree_vie_repeteur_an", 10, 7, 15, "year",
        "Repeteurs — durée de vie avant remplacement (milieu marin)")

    # ── Transport ─────────────────────────────────────────────────────────
    p.dist_camion_km = _f(
        ctx, "dist_camion_km", 200.0, 150.0, 300.0, "km",
        "Transport — camion usine→port (Var→Perpignan)")
    p.dist_maritime_km = _f(
        ctx, "dist_maritime_km", 17000.0, 16000.0, 18000.0, "km",
        "Transport — porte-conteneurs Europe→Papeete")
    p.dist_interile_km = _f(
        ctx, "dist_interile_km", 220.0, 180.0, 300.0, "km",
        "Transport — goélette Papeete→Raiatea. Le scénario multi-îles balaie "
        "0 à 1600 km, mais c'est un SCÉNARIO : on le passe explicitement à "
        "systeme.impacts(), on ne le met pas dans l'incertitude")
    # `m_fret_maritime_t` a été SUPPRIMÉ (août 2026). Le fret maritime était
    # alloué par CAPACITÉ AFFRÉTÉE (10,85 t = 2 conteneurs ÷ 4 plateformes) au
    # lieu de la masse réelle. Écarté à la demande du reviewer : c'est une
    # règle d'allocation maison là où le tonne-kilomètre d'ecoinvent en impose
    # déjà une. Voir la note en tête de `transport.py`.
    p.m_systeme_t = _f(
        ctx, "m_systeme_t", 2.07, 1.8, 2.4, "ton",
        "Transport — masse réelle transportée par plateforme. Sert aux TROIS "
        "maillons : camion, porte-conteneurs et goélette")

    # ── Chantier ──────────────────────────────────────────────────────────
    # Poste REMIS le 05/10/2026. L'ancien `diesel_chantier_mj` (prorata d'un
    # chantier terrestre de 570 kWc) reste supprimé : ce qui est compté ici est
    # le geste réel, du bateau, sur le dataset de la maintenance.
    p.dist_montage_m = _f(
        ctx, "dist_montage_m", 500.0, 300.0, 2000.0, "m",
        "Chantier — distance parcourue par le bateau pour mettre UNE "
        "plateforme en place (rive -> site). 500 m = la configuration de "
        "Raiatea ; la borne haute couvre un site plus éloigné du passage")
    p.dist_demontage_m = _f(
        ctx, "dist_demontage_m", 500.0, 300.0, 2000.0, "m",
        "Chantier — idem au démontage, en fin de vie. Paramètre DISTINCT du "
        "montage : un démontage se fait rarement dans les mêmes conditions "
        "qu'une pose")
    # ⚠ C'EST CE PARAMÈTRE QUI PORTE LE POSTE, PAS LA DISTANCE.
    # Le transit ne décrit pas le chantier : positionner la plateforme, mouiller
    # quatre ancres, tendre les élastiques et vérifier en plongée se fait moteur
    # en charge SANS parcourir de distance. 30 min par opération à ~20 L/h, soit
    # 10 L, retenu le 05/10/2026 : le poste pèse alors 20,1 L et 0,35 % du
    # résultat, contre 0,001 % au transit seul. Cf. `chantier.expliquer()`, qui
    # sort les trois périmètres côte à côte.
    #
    # La borne haute (40 L) couvre la demi-journée de vedette ; la borne basse
    # est 0, c'est-à-dire le périmètre « transit seul ».
    p.diesel_manoeuvre_l = _f(
        ctx, "diesel_manoeuvre_l", 10.0, 0.0, 40.0, "L",
        "Chantier — gazole brûlé EN STATION PAR OPÉRATION (manœuvre, mouillage "
        "des ancres, plongée), que la distance ne capture pas. Compté deux "
        "fois : une pose, une dépose")

    # ── Fin de vie ────────────────────────────────────────────────────────
    p.m_panneaux_kg = _f(
        ctx, "m_panneaux_kg", 520.0, 470.0, 570.0, "kg",
        "FinDeVie — masse de modules PV par plateforme (n_modules × fiche CS)")

    # Trois modalités. Les deux dernières décrivent LE MÊME scénario physique
    # (mêmes panneaux, même recycleur néo-zélandais) sous DEUX RÈGLES
    # D'ALLOCATION différentes — cf. le docstring de fin_de_vie.py :
    #   * recyclage_cutoff       simple cut-off (100/0), cohérent avec la base
    #                            ecoinvent-cutoff → RÉFÉRENCE ;
    #   * recyclage_closed_loop  closed-loop / avoided burden (0/100) → BORNE
    #                            BASSE de sensibilité méthodologique, pas un
    #                            résultat publiable seul.
    from . import fin_de_vie as _fdv

    p.fin_de_vie = agb.newEnumParam(
        "fin_de_vie",
        # ⚠ LA LISTE EST LUE DEPUIS `fin_de_vie.MODALITES` et non recopiée :
        # c'est la seule façon qu'ajouter une modalité là-bas ne laisse pas ce
        # paramètre en arrière. La duplication s'était déjà payée une fois.
        values=list(_fdv.MODALITES),
        default="enfouissement",
        description="FinDeVie — enfouissement (statu quo Polynésie), recyclage "
                    "NZ en cut-off (référence) ou en closed-loop (borne de "
                    "sensibilité méthodologique) ; + incinération des "
                    "flotteurs, créditée ou non, en sensibilité prospective",
        # `_f()` déduit le groupe du préfixe de la description ; `newEnumParam`
        # est appelé en direct, il faut donc le donner explicitement — sans
        # quoi ce paramètre était le seul du modèle sans groupe, et sortait
        # non classé dans `lister_parametres()` et les tableaux de sensibilité.
        group="FinDeVie",
        dbname=ctx.db)

    # Origine de l'aluminium de structure. Comme `fin_de_vie`, c'est un AXE DE
    # SCÉNARIO (quelle chaîne d'approvisionnement décrit-on ?), pas une
    # incertitude : il est donc figé hors tirage aléatoire et se compare
    # explicitement avec `resultats.variante_aluminium()`.
    p.origine_aluminium = agb.newEnumParam(
        "origine_aluminium",
        values=["GLO", "RER", "RER_SUP"],
        default="RER",
        description="Structure — origine de l'aluminium : RER (variante "
                    "européenne, DÉFAUT depuis le 25/09/2026) ou GLO (mix "
                    "mondial, conservé en scénario). Les certificats de "
                    "réception EN 10204 3.1 des fournisseurs tracent la "
                    "totalité de l'aluminium structurel à des usines "
                    "européennes — tôle 5754 de Profilglass (Fano, IT) et "
                    "Speira (Hambourg, DE), tube 6060 de PFA (Cortenova, IT) "
                    "et d'un fileur turc. Le mix mondial, à 69,6 % de "
                    "primaire pondéré par la fonte chinoise, n'est donc plus "
                    "un défaut conservateur mais une hypothèse que les pièces "
                    "contredisent. RER_SUP est la MÊME variante européenne "
                    "avec le contenu recyclé déclaré par le producteur "
                    "(Profilglass, 80 % de scrap, soit p = 20 % de primaire) : "
                    "c'est une BORNE BASSE de scénario, pas la référence, "
                    "tant qu'aucune déclaration écrite n'est au dossier.",
        group="Structure",
        dbname=ctx.db)
    # ⚠ NE PAS mettre `distrib = FIXED` ici : voir `scenarios_figes` plus bas.

    # ⚠ HORS TIRAGE ALÉATOIRE (août 2026). `fin_de_vie` n'est pas une
    # incertitude, c'est un AXE DE SCÉNARIO : trois règles d'allocation qui
    # décrivent trois conventions comptables, pas trois états possibles du
    # monde. Le laisser variable faisait tirer au sort une convention à chaque
    # échantillon du Monte-Carlo, sur une plage de 37 à 83 g CO2-eq/kWh — la
    # distribution obtenue était trimodale et l'écart-type n'avait aucun sens.
    # Il pesait 55 % dans la matrice OAT, écrasant tous les vrais paramètres.
    # Les trois modalités sont déjà comparées explicitement par
    # `resultats.comparer_fin_de_vie()` : c'est là qu'elles doivent être lues.
    # ⚠ MAIS PAS `distrib = FIXED` EN PERMANENCE : voir `scenarios_figes`.

    return p


# ══════════════════════════════════════════════════════════════════════════
# Axes de SCÉNARIO
# ══════════════════════════════════════════════════════════════════════════
#
# Ces paramètres décrivent des CHOIX (quelle règle d'allocation ? quelle chaîne
# d'approvisionnement ? quel lieu de fabrication ?), pas des incertitudes. Ils
# ne doivent donc pas entrer dans le tirage aléatoire du Monte-Carlo, où ils
# produiraient une distribution multimodale sans signification.
#
# ⚠ PIÈGE, appris à nos dépens (août 2026). La tentation est de leur mettre
# `distrib = DistributionType.FIXED` une fois pour toutes. C'EST FAUX : dans
# lca_algebraic, FIXED ne signifie pas « exclu du tirage » mais « NON
# MODIFIABLE ». Un paramètre FIXED passé à `compute_impacts` est ignoré, avec
# un simple warning — et toutes les comparaisons de scénarios retournent alors
# la même valeur trois fois :
#
#     [WARNING] Param 'fin_de_vie' is marked as FIXED, but passed in
#               parameters : ignored
#
# La parade : les figer TEMPORAIREMENT, le temps du tirage seulement.
# Paramètres dont la valeur nominale CHANGE d'une configuration à l'autre : ce
# ne sont pas des grandeurs incertaines communes aux quatre plateformes, mais
# des mesures propres à chacune. Leurs min/max décrivent donc une incertitude
# RELATIVE (la tolérance de pesée, ±5 % sur l'aluminium), pas un intervalle
# absolu — sinon le tornado balaie l'écart ENTRE configurations, qui est un
# scénario et non une incertitude, et le Monte-Carlo tire l'aluminium de S1
# (718 kg) dans les bornes de S2 (576-637 kg).
#
# Lu par `tests.t_nominal_dans_les_bornes` et par `incertitude.py`, qui en
# dérive la liste des paramètres à recentrer sur la configuration tirée.
PARAMS_PAR_MODALITE = (
    "m_alu_structure_kg", "m_panneaux_kg", "p_install_kwc", "rendement_module",
    "packing_cellules", "n_modules", "n_onduleurs", "m_systeme_t",
)

SCENARIOS = ("fin_de_vie", "origine_aluminium", "manufacturing_electricity_mix",
             # `diesel_manoeuvre_l` est le SEUL flottant de cette liste, et
             # c'est voulu : il ne décrit pas une incertitude sur une quantité
             # mais un CHOIX DE PÉRIMÈTRE — compte-t-on le seul transit du
             # bateau, ou les heures de manœuvre du chantier ? Le laisser dans
             # le tirage ferait échantillonner un périmètre au hasard entre 0
             # et 40 L, c'est-à-dire la même faute que le tirage au sort d'une
             # convention d'allocation sur `fin_de_vie`. Il se compare
             # explicitement, avec `chantier.expliquer()`.
             "diesel_manoeuvre_l")


@contextmanager
def scenarios_figes(noms=None):
    """Fige les axes de scénario le temps d'une analyse stochastique.

    `oat_matrix` et `incer_stochastic_matrix` ne tirent au sort que les
    paramètres dont la distribution n'est pas FIXED (`_variable_params`). On les
    fige donc à l'entrée et on RESTAURE leur distribution à la sortie, y
    compris si l'analyse lève une exception.

    >>> with scenarios_figes() as figes:
    ...     agb.incer_stochastic_matrix(...)
    """
    import lca_algebraic as agb

    noms = SCENARIOS if noms is None else noms
    registre = agb.all_params()
    memoire = {}
    for nom in noms:
        param = registre.get(nom)
        if param is None:
            continue
        memoire[nom] = param.distrib
        param.distrib = DistributionType.FIXED
    try:
        yield tuple(memoire)
    finally:
        for nom, distrib in memoire.items():
            registre[nom].distrib = distrib


# ── Utilitaires ────────────────────────────────────────────────────────────
def U(nom_unite):
    """Facteur porteur d'unité : `Quantity(1, unité)` si le contrôle des unités
    est actif, `1.0` sinon.

    Permet d'écrire une constante dimensionnée sans casser le mode « sans
    unités » :

    >>> eau_kg = p.eau_par_visite_l * (RHO_EAU_KG_PAR_L * U("kg/L"))
    """
    if agb.Settings.units_enabled:
        from lca_algebraic.units import unit_registry
        return unit_registry.Quantity(1.0, nom_unite)
    return 1.0


# ── Nombre de jeux d'un composant remplacé en cours de vie ─────────────────
#
# Tu as raison : 2 jeux de flotteurs, pas 1,5.
#
# L'ancien calcul faisait `durée_système / durée_composant` = 30/20 = 1,5, au
# PRORATA. Cela suppose implicitement que les 10 années de vie restantes du
# second jeu sont transférées à un autre utilisateur, qui en porterait la part
# d'impact. Or il n'y a pas d'autre utilisateur : à 30 ans la plateforme est
# démantelée et le second jeu de flotteurs part au rebut avec le reste, à
# mi-vie. C'est donc bien NOTRE système qui consomme deux jeux entiers, et qui
# doit en porter la fabrication ET la fin de vie.
#
# C'est exactement le même raisonnement que le cut-off en fin de vie : on
# n'accorde de crédit que si quelqu'un reprend réellement le flux.
#
# Cas concernés : seuls les flotteurs (30/20). Les onduleurs (30/15 = 2) et les
# répéteurs (30/10 = 3) tombent déjà juste, l'arrondi ne les change pas.
#
# `ARRONDI_JEUX = False` restitue l'ancien prorata, pour chiffrer l'écart.
ARRONDI_JEUX = True


def n_jeux(duree_systeme, duree_composant, arrondi=None):
    """Nombre de jeux d'un composant, arrondi à l'entier SUPÉRIEUR.

    On n'achète pas 1,5 jeu de flotteurs : on en achète 2, et on jette le
    second à mi-vie.
    """
    import sympy

    arrondi = ARRONDI_JEUX if arrondi is None else arrondi
    ratio = magnitude(duree_systeme) / magnitude(duree_composant)
    if not arrondi:
        return ratio
    return sympy.ceiling(ratio)


def magnitude(x):
    """Retire l'unité d'une grandeur (Quantity Pint) et renvoie le sympy nu.

    Utile pour construire l'unité fonctionnelle : `compute_impacts` attend là
    une expression scalaire, pas une grandeur dimensionnée.
    """
    return getattr(x, "magnitude", x)


def productible_moyen(p0, taux_degradation, n_annees):
    """Productible annuel MOYEN sur n années, dégradation linéaire.

    parasol calcule E = durée_de_vie × productible, sans dégradation. On lui
    passe donc la moyenne : P̄ = P₀·(1 − d·(n−1)/2), qui donne exactement la
    même énergie cumulée que la somme année par année (vérifié : n=1 → P₀).
    """
    return p0 * (1 - taux_degradation * (n_annees - 1) / 2)
