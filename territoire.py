"""
Transposition territoriale : CO₂ évité, temps de retour carbone, 54 îles.

Ce module porte les figures des § 3.4 et § 4.1 de l'article. Elles étaient
jusqu'ici produites hors du package — les valeurs du § 3.4 dans un classeur
Excel (`Tableau_reference_ACV_Raiatea_v2.xlsx`, feuille `CO2_evite_recalcule`),
celles du § 4.1 dans les cellules 71-74 de `ACV_propre_cowork_VF4.ipynb`, avec
les noms de paramètres de l'ancien modèle parasol. Les deux jeux de chiffres
pouvaient donc diverger du modèle sans que rien ne le signale. Ils sont
maintenant recalculés depuis `systeme.impacts`, comme toutes les autres figures.

────────────────────────────────────────────────────────────────────────────
CE QUE LE MODULE CALCULE

1. § 3.4 — CO₂ ÉVITÉ ET TEMPS DE RETOUR, pour les 4 configurations installées
   à Raiatea :

       évité_net (kg/an) = E_nette_an × (FE_mix − GWP_kWh)
       retour   (an)     = empreinte totale sur la vie ÷ évité_net

   `FE_mix` est le facteur d'émission du kWh SUBSTITUÉ, celui du réseau de
   l'île ; `GWP_kWh` est l'empreinte du kWh produit par la plateforme, calculée
   par le modèle. Le CO₂ évité est NET : on retranche ce que la plateforme émet
   elle-même. C'est ce qui fait qu'un raccordement au mix métropolitain
   (0,052 kg CO₂-eq/kWh) donne un évité NÉGATIF — la plateforme y émettrait
   plus qu'elle n'évite. Le résultat est donc un résultat de SUBSTITUTION, pas
   une propriété de la plateforme.

   ⚠ L'énergie utilisée est l'énergie NETTE livrée (`systeme.energie_totale`),
   celle du dénominateur de l'unité fonctionnelle — pas le productible brut.
   Utiliser le brut au numérateur et le net au dénominateur du GWP ferait
   compter deux fois la consommation des auxiliaires. L'écart est faible
   (~0,7 %) mais il n'y a aucune raison de l'introduire.

2. § 4.1 — TRANSPOSITION AUX 54 ÎLES habitées documentées. Trois grandeurs
   changent d'une île à l'autre :

   | Grandeur                  | Effet                                        |
   |---------------------------|----------------------------------------------|
   | productible (kWh/kWc/an)  | dénominateur du GWP **et** énergie produite  |
   | distance goélette (km)    | poste Transport, maillon inter-îles          |
   | FE du mix de l'île        | **uniquement** le CO₂ évité                  |

   Le facteur d'émission du réseau n'entre PAS dans le GWP du kWh solaire :
   aucun poste de l'inventaire ne consomme d'électricité de réseau (la
   consommation des répéteurs est déduite du productible, cf. `systeme.py`).
   Il n'intervient qu'à l'étape de substitution. C'est pourquoi la carte du
   § 4.1 montre un GWP resserré (77,8 à 92,5 g, soit +19 % du meilleur au
   pire site, piloté par le productible et marginalement par la goélette) et
   un CO₂ évité très contrasté (17,2 à 44,1 t/an, ×2,6 — Tuamotu à 1,193
   contre Tahiti à 0,587).

────────────────────────────────────────────────────────────────────────────
CONTRE-VÉRIFICATION DU PRODUCTIBLE — NASA POWER (15/09/2026)

Le productible par île repose sur une simulation PVsyst dont on n'utilise que
le ratio. Pour savoir si CE RATIO tient, on le compare à une source
indépendante : l'irradiation globale horizontale annuelle de NASA POWER
(climatologie SYN1DEG 2001-2020, paramètre `ALLSKY_SFC_SW_DWN`), relevée aux
54 coordonnées et embarquée ci-dessous.

    ratio_nasa(île) = GHI(île) / GHI(Raiatea)

Résultat (`comparer_nasa_power()`) : corrélation de Pearson 0,88, écart absolu
moyen 3,5 %, écart maximal 7,4 %. Les deux sources classent les îles dans le
même ordre — Gambier et Australes en bas, nord des Tuamotu en haut.

Deux écarts SYSTÉMATIQUES, tous deux explicables, et dans des sens opposés :

1. PVsyst est plus RESSERRÉ que l'irradiation (régression ratio_pvsyst ≈
   0,92 × ratio_nasa + 0,05). C'est physique : le productible ne suit pas
   linéairement l'irradiation — les atolls les plus ensoleillés sont aussi les
   plus chauds, et le derating thermique mange une partie du gain. Un ratio
   d'irradiation SURESTIME donc l'écart de productible.

2. Tahiti (−7,4 %) et Moorea (−5,5 %) sont les deux plus gros désaccords, et
   c'est PVsyst qui a probablement raison. NASA POWER travaille sur une maille
   d'environ 1° : elle attribue la même irradiation à Tahiti et Moorea, et la
   même à Bora Bora / Huahine / Raiatea / Tahaa. Elle ne peut pas voir la
   nébulosité orographique des îles hautes, que la simulation site par site
   capte. Une maille qui moyenne de l'océan ne décrit pas un versant sous le
   vent d'un massif de 2 200 m.

Conclusion : le ratio PVsyst est conservé. L'incertitude à en retenir pour le
§ 4.1 est de l'ordre de ±5 % sur le productible d'une île donnée, ce qui se
reporte tel quel sur son GWP (le productible est au dénominateur) — sans
changer l'ordre ni les conclusions. `donnees_iles(source="nasa")` permet de
rejouer toute la section sur l'autre source pour le vérifier.

────────────────────────────────────────────────────────────────────────────
DONNÉES DES ÎLES — PROVENANCE ET LIMITES

Source d'origine : `Iles.xlsx`, feuille « Data PV_syst » — une simulation
PVsyst par île, colonne `FPV2` (production annuelle de la plateforme S2, kWh).
Coordonnées corrigées (signes sud/ouest, coquille Katiu donnée à +16° N) et
doublons retirés. Les données sont EMBARQUÉES dans ce fichier, en dur : le
package ne doit pas dépendre d'un classeur qui vit ailleurs.

⚠ Seul le RATIO île/Raiatea de la simulation est utilisé :

    P₀(île) = P₀(Raiatea, mesuré on-site) × FPV2(île) / FPV2(Raiatea)

Le biais absolu de PVsyst est ainsi neutralisé par le recalage sur la mesure
de Raiatea. En revanche, rien ne garantit que le ratio lui-même soit juste :
il suppose que la simulation se trompe de la même façon partout. La carte de
durée d'ensoleillement du rapport ADEME n'est PAS convertible en productible :
une durée n'est pas une irradiation.

Cette contre-vérification a été faite le 15/09/2026 contre l'irradiation
globale horizontale de NASA POWER (cf. § « CONTRE-VÉRIFICATION » plus bas et
`comparer_nasa_power()`). Conclusion : les deux jeux s'accordent à 3,5 % en
moyenne, 7,4 % au pire, et donnent le même ordre. Le ratio PVsyst est utilisable.

⚠ La distance maritime est un grand cercle × un facteur de détour unique,
calibré sur la seule route réellement connue (Papeete → Uturoa en goélette,
≈ 220 km). Pour les Tuamotu de l'est et les Gambier, la route réelle passe par
des escales et le détour est certainement plus grand : les distances y sont
sous-estimées. L'effet sur le GWP reste marginal (le maillon goélette pèse
moins de 2 % du total), mais c'est à écrire dans les limites.

⚠ Le facteur d'émission n'est PAS redéclaré ici : il est lu dans
`electricite.FE_ARCHIPELS`, seule source de vérité du package (guide des
facteurs d'émission de la Polynésie française, ADEME 2023, tableau 34). Tahiti
y figure séparément de l'archipel de la Société — son mix est très
hydraulique, 0,587 contre 0,914 pour les autres îles Sous-le-Vent.

⚠ Les 54 îles sont des SITES POTENTIELS, pas des projets. Transposer, c'est
supposer qu'on y reconstruirait la même plateforme, avec la même chaîne
d'approvisionnement et le même lagon abrité. Aucune contrainte de bathymétrie,
de houle, de foncier maritime ou de raccordement n'est modélisée.
"""

from __future__ import annotations

import io
import math

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config, electricite, modalites, parametres, systeme
from .parametres import productible_moyen

# ══════════════════════════════════════════════════════════════════════════
# 1. Données des îles
# ══════════════════════════════════════════════════════════════════════════

# Port d'embarquement de la goélette inter-îles.
PAPEETE = (-17.535, -149.570)

# Route de référence, la seule dont la longueur réelle soit connue : Papeete →
# Uturoa (Raiatea), ≈ 220 km par la goélette Hawaiki Nui. C'est aussi la valeur
# par défaut du paramètre `dist_interile_km` (cf. `parametres.py`) : les deux
# sont donc cohérents par construction.
DIST_REFERENCE_KM = 220.0
ILE_REFERENCE = "Raiatea"

_ILES_CSV = """ile;archipel;lat;lon;pvsyst_kwh_an
Tahiti;Société;-17.7823;-149.4346;11630
Moorea;Société;-17.4884;-149.8521;11867
Bora Bora;Société;-16.5117;-151.7508;12962
Huahine;Société;-16.7675;-151.0274;13075
Maupihaa;Société;-16.7761;-153.9501;13189
Maupiti;Société;-16.4409;-152.2677;13316
Raiatea;Société;-16.8173;-151.4159;12940
Tahaa;Société;-16.5834;-151.4743;12832
Raivavae;Australes;-23.8658;-147.6822;11482
Rurutu;Australes;-22.4781;-151.3533;11902
Tubuai;Australes;-23.3433;-149.4858;11665
Marokau;Tuamotu;-17.9650;-142.2228;12962
Napuka;Tuamotu;-14.1674;-141.2681;13239
Pukapuka;Tuamotu;-14.8157;-138.8257;13114
Apataki;Tuamotu;-15.5700;-146.4104;13009
Aratika;Tuamotu;-15.4811;-145.5080;12951
Arutua;Tuamotu;-15.3592;-146.6226;13026
Fakarava;Tuamotu;-16.0584;-145.6197;12946
Kaukura;Tuamotu;-15.6752;-146.8725;13021
Mataiva;Tuamotu;-14.8718;-148.7059;13315
Rangiroa;Tuamotu;-14.9696;-147.6351;13161
Tikehau;Tuamotu;-15.1125;-148.2426;13324
Toau;Tuamotu;-15.8026;-146.1485;13002
Ahe;Tuamotu;-14.5390;-146.3584;13276
Manihi;Tuamotu;-14.4576;-146.0570;13333
Takapoto;Tuamotu;-14.7042;-145.2490;13234
Takaroa;Tuamotu;-17.8433;-140.8513;13306
Amanu;Tuamotu;-17.8433;-140.8513;12727
Anaa;Tuamotu;-17.3487;-145.5189;12786
Fakahina;Tuamotu;-15.9829;-140.1627;13035
Fangatau;Tuamotu;-15.8264;-140.8876;13119
Faaite;Tuamotu;-16.7042;-145.3544;12715
Hao;Tuamotu;-18.1087;-140.9076;12688
Hikueru;Tuamotu;-17.5459;-142.6672;12581
Katiu;Tuamotu;-16.3662;-144.3597;12912
Kauehi;Tuamotu;-15.8287;-145.1154;12912
Makemo;Tuamotu;-16.6260;-143.5721;12724
Niau;Tuamotu;-16.1394;-146.3404;13031
Pukarua;Tuamotu;-18.2702;-137.0611;12648
Raraka;Tuamotu;-16.0920;-144.9523;12993
Raroia;Tuamotu;-16.0401;-142.4723;13045
Reao;Tuamotu;-18.4701;-136.4574;12583
Taenga;Tuamotu;-16.3627;-143.1841;12802
Takume;Tuamotu;-15.8495;-145.2642;12914
Tatakoto;Tuamotu;-17.3429;-138.4428;12773
Tematangi;Tuamotu;-21.6319;-140.6388;11824
Tureia;Tuamotu;-20.7743;-138.5637;12022
Vahitahi;Tuamotu;-18.7784;-138.8520;12626
Vairaatea;Tuamotu;-19.3315;-139.2165;12470
Marutea Sud;Tuamotu;-21.4791;-135.5195;11783
Akamaru;Gambier;-23.1795;-134.9118;11505
Mangareva;Gambier;-23.0999;-134.9782;11424
Taravai;Gambier;-23.1469;-135.0282;11543
Aukena;Gambier;-23.1300;-134.8977;11510"""

# ── Source indépendante de contrôle : NASA POWER ───────────────────────────
# Irradiation globale horizontale annuelle moyenne, kWh/m²/jour.
#
# Relevé le 15/09/2026 sur l'API climatologie de NASA POWER, aux coordonnées
# exactes du tableau ci-dessus. Requête reproductible, une par île :
#
#   https://power.larc.nasa.gov/api/temporal/climatology/point
#       ?parameters=ALLSKY_SFC_SW_DWN&community=RE&format=JSON
#       &latitude=<lat>&longitude=<lon>
#
# Source du jeu : SYN1DEG, climatologie 20 ans (janvier 2001 - décembre 2020),
# API v2.9.7. Les valeurs sont figées ici pour que la vérification soit
# reproductible hors ligne : le package ne doit jamais dépendre du réseau.
#
# ⚠ Maille ~1°. Des îles voisines partagent la même cellule et reçoivent donc
# la MÊME valeur : Tahiti et Moorea ; Bora Bora, Huahine, Raiatea et Tahaa ;
# les quatre Gambier. C'est une limite de la source de contrôle, pas une
# erreur de saisie — et c'est la raison pour laquelle elle ne remplace pas
# PVsyst (cf. le § CONTRE-VÉRIFICATION en tête de module).
_NASA_GHI_KWH_M2_J = {
    "Tahiti": 5.3573, "Moorea": 5.3573, "Bora Bora": 5.5222, "Huahine": 5.5222,
    "Maupihaa": 5.5646, "Maupiti": 5.5975, "Raiatea": 5.5222, "Tahaa": 5.5222,
    "Raivavae": 5.0129, "Rurutu": 5.0712, "Tubuai": 5.0009, "Marokau": 5.6803,
    "Napuka": 5.9518, "Pukapuka": 6.0226, "Apataki": 5.7194, "Aratika": 5.7691,
    "Arutua": 5.7194, "Fakarava": 5.6738, "Kaukura": 5.7194, "Mataiva": 5.7734,
    "Rangiroa": 5.8027, "Tikehau": 5.6947, "Toau": 5.7194, "Ahe": 5.8205,
    "Manihi": 5.8205, "Takapoto": 5.8418, "Takaroa": 5.7000, "Amanu": 5.7000,
    "Anaa": 5.6021, "Fakahina": 5.8812, "Fangatau": 5.8812, "Faaite": 5.6738,
    "Hao": 5.6057, "Hikueru": 5.6803, "Katiu": 5.7017, "Kauehi": 5.7691,
    "Makemo": 5.7271, "Niau": 5.6695, "Pukarua": 5.6820, "Raraka": 5.7017,
    "Raroia": 5.7557, "Reao": 5.7070, "Taenga": 5.7271, "Takume": 5.7691,
    "Tatakoto": 5.7482, "Tematangi": 5.2730, "Tureia": 5.4348, "Vahitahi": 5.6513,
    "Vairaatea": 5.5342, "Marutea Sud": 5.3926, "Akamaru": 5.1890,
    "Mangareva": 5.1890, "Taravai": 5.1665, "Aukena": 5.1890,
}

# Les clés de `electricite.FE_ARCHIPELS` sont écrites sans accent ; le tableau
# des îles, lui, vient d'un classeur français. Une seule table de passage, pour
# ne jamais recopier un facteur d'émission.
_ARCHIPEL_VERS_FE = {
    "Société": "Societe",
    "Australes": "Australes",
    "Tuamotu": "Tuamotu",
    "Gambier": "Gambier",
    "Marquises": "Marquises",
}

# Couleur par archipel — commune aux trois figures du § 4.1.
COULEURS_ARCHIPELS = {
    "Société": "#2980b9",
    "Australes": "#8e44ad",
    "Tuamotu": "#16a085",
    "Gambier": "#d35400",
    "Marquises": "#c0392b",
}

# Libellés anglais pour les figures (l'article est en anglais ; les colonnes
# des tableaux, elles, gardent leurs noms français — cf. `resultats.py`).
LIBELLES_ARCHIPELS_EN = {
    "Société": "Society",
    "Australes": "Austral",
    "Tuamotu": "Tuamotu",
    "Gambier": "Gambier",
    "Marquises": "Marquesas",
}


def distance_grand_cercle_km(lat1, lon1, lat2, lon2) -> float:
    """Distance orthodromique (haversine), rayon terrestre moyen 6 371 km."""
    p = math.pi / 180.0
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * (1 - math.cos((lon2 - lon1) * p)) / 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def facteur_detour(iles: pd.DataFrame | None = None) -> float:
    """Rapport route réelle / grand cercle, calibré sur Papeete → Uturoa.

    Un seul facteur pour tout l'archipel : c'est la seule route dont la
    longueur soit documentée. Voir la limite en tête de module.
    """
    if iles is None:
        iles = _iles_brutes()
    ref = iles.loc[iles["ile"] == ILE_REFERENCE].iloc[0]
    direct = distance_grand_cercle_km(*PAPEETE, ref["lat"], ref["lon"])
    return DIST_REFERENCE_KM / direct


def _iles_brutes() -> pd.DataFrame:
    return pd.read_csv(io.StringIO(_ILES_CSV), sep=";")


def donnees_iles(p0=None, degradation=None, duree_vie=None, source="pvsyst",
                 verbeux=True) -> pd.DataFrame:
    """Tableau des 54 îles : distance goélette, productible, FE du mix.

    Les trois hypothèses de productible (P₀ mesuré, taux de dégradation, durée
    de vie) sont celles de `parametres.py`, relues via `modalites.py` : elles ne
    sont pas redéclarées ici.

    Parameters
    ----------
    source : {"pvsyst", "nasa"}
        Ce qui fournit le RATIO île/Raiatea. « pvsyst » est la référence.
        « nasa » rejoue tout sur le ratio d'irradiation NASA POWER : c'est la
        variante de sensibilité du § 4.1, pas un second résultat. Voir le
        § CONTRE-VÉRIFICATION en tête de module — un ratio d'irradiation
        surestime l'écart de productible, faute de derating thermique.

    >>> iles = territoire.donnees_iles()
    >>> iles.set_index("ile").loc[["Raiatea", "Mangareva"]]
    """
    p0 = parametres.PRODUCTIBLE_P0 if p0 is None else p0
    degradation = (parametres.TAUX_DEGRADATION if degradation is None
                   else degradation)
    duree_vie = (parametres.DUREE_VIE_REFERENCE if duree_vie is None
                 else duree_vie)

    iles = _iles_brutes()
    detour = facteur_detour(iles)
    iles["dist_goelette_km"] = [
        round(distance_grand_cercle_km(*PAPEETE, la, lo) * detour)
        for la, lo in zip(iles["lat"], iles["lon"])]

    manquantes = set(iles["ile"]) - set(_NASA_GHI_KWH_M2_J)
    if manquantes:
        raise KeyError(f"Irradiation NASA POWER absente pour {sorted(manquantes)}. "
                       f"Relève-la (la requête est dans le commentaire de "
                       f"_NASA_GHI_KWH_M2_J) plutôt que de l'interpoler.")
    iles["ghi_nasa_kwh_m2_j"] = [_NASA_GHI_KWH_M2_J[i] for i in iles["ile"]]

    iles["ratio_pvsyst"] = (iles["pvsyst_kwh_an"]
                            / _valeur_reference(iles, "pvsyst_kwh_an"))
    iles["ratio_nasa"] = (iles["ghi_nasa_kwh_m2_j"]
                          / _valeur_reference(iles, "ghi_nasa_kwh_m2_j"))

    if source not in ("pvsyst", "nasa"):
        raise ValueError(f"source = « {source} » ; attendu « pvsyst » ou « nasa ».")
    ratio = iles["ratio_pvsyst"] if source == "pvsyst" else iles["ratio_nasa"]
    iles["source_productible"] = source
    iles["p0_kwh_kwc_an"] = p0 * ratio
    iles["productible_kwh_kwc_an"] = productible_moyen(
        iles["p0_kwh_kwc_an"], degradation, duree_vie).round(1)

    iles["fe_mix"] = [_fe_mix(ile, archipel)
                      for ile, archipel in zip(iles["ile"], iles["archipel"])]

    if verbeux:
        ref = iles.loc[iles["ile"] == ILE_REFERENCE].iloc[0]
        print(f"{len(iles)} îles | détour maritime ×{detour:.2f} | "
              f"productible : ratio {source} | "
              f"contrôle {ILE_REFERENCE} : {ref['dist_goelette_km']:.0f} km, "
              f"P₀ {ref['p0_kwh_kwc_an']:.0f} kWh/kWc/an, "
              f"P̄ {ref['productible_kwh_kwc_an']:.0f}, FE {ref['fe_mix']:.3f}")
    return iles


def _valeur_reference(iles: pd.DataFrame, colonne: str) -> float:
    """Valeur de `colonne` sur l'île de référence — le dénominateur du ratio."""
    return float(iles.loc[iles["ile"] == ILE_REFERENCE, colonne].iloc[0])


def comparer_nasa_power(iles=None, seuil_alerte=10.0, verbeux=True) -> pd.DataFrame:
    """Confronte le ratio PVsyst au ratio d'irradiation NASA POWER.

    Une ligne par île, triée du plus gros désaccord au plus faible. La colonne
    `ecart_%` est l'écart RELATIF des deux ratios : positif, PVsyst est plus
    optimiste que l'irradiation ; négatif, l'inverse.

    Ce n'est pas une validation du productible ABSOLU — celui-ci vient de la
    mesure on-site de Raiatea, pas de PVsyst. C'est une validation du seul
    élément que PVsyst apporte : la façon dont il répartit les îles entre elles.

    >>> tab = territoire.comparer_nasa_power()
    >>> tab.head(5)[["ile", "ratio_pvsyst", "ratio_nasa", "ecart_%"]]
    """
    iles = donnees_iles(verbeux=False) if iles is None else iles.copy()
    iles["ecart_%"] = (iles["ratio_pvsyst"] / iles["ratio_nasa"] - 1.0) * 100.0

    pente, ordonnee = np.polyfit(iles["ratio_nasa"], iles["ratio_pvsyst"], 1)
    pearson = float(np.corrcoef(iles["ratio_pvsyst"], iles["ratio_nasa"])[0, 1])
    spearman = float(iles["ratio_pvsyst"].corr(iles["ratio_nasa"],
                                               method="spearman"))
    tab = iles.reindex(iles["ecart_%"].abs().sort_values(ascending=False).index)
    tab = tab.reset_index(drop=True)
    tab.attrs.update(pearson=pearson, spearman=spearman,
                     pente=float(pente), ordonnee=float(ordonnee))

    if verbeux:
        print(f"PVsyst vs NASA POWER (GHI, SYN1DEG 2001-2020) sur {len(tab)} îles :")
        print(f"  Pearson {pearson:.3f} | Spearman {spearman:.3f} | "
              f"régression pvsyst = {pente:.3f} × nasa + {ordonnee:.3f}")
        print(f"  écart absolu moyen {tab['ecart_%'].abs().mean():.1f} % | "
              f"médian {tab['ecart_%'].abs().median():.1f} % | "
              f"maximal {tab['ecart_%'].abs().max():.1f} %")
        if pente < 0.98:
            print(f"  → PVsyst est plus RESSERRÉ que l'irradiation (pente "
                  f"{pente:.2f}) : attendu, le derating thermique mange une "
                  f"partie du gain sur les sites les plus ensoleillés.")
        gros = tab[tab["ecart_%"].abs() > seuil_alerte]
        if len(gros):
            print(f"  ⚠ {len(gros)} île(s) au-delà de ±{seuil_alerte:.0f} % : "
                  f"{gros['ile'].tolist()}")
        else:
            print(f"  aucune île au-delà de ±{seuil_alerte:.0f} %. "
                  f"Les pires : "
                  + ", ".join(f"{r['ile']} {r['ecart_%']:+.1f} %"
                              for _, r in tab.head(3).iterrows()))
        doublons = (iles.groupby("ghi_nasa_kwh_m2_j")["ile"]
                    .apply(list).loc[lambda s: s.str.len() > 1])
        if len(doublons):
            print(f"  ⚠ maille NASA ~1° : {len(doublons)} groupes d'îles "
                  f"partagent une cellule et donc une irradiation identique — "
                  f"la source de contrôle ne les distingue pas.")
    return tab


def figure_nasa_power(tab: pd.DataFrame, titre=None, n_etiquettes=6):
    """Nuage ratio PVsyst ↔ ratio NASA POWER, avec la 1:1 et la régression."""
    pente = tab.attrs.get("pente")
    ordonnee = tab.attrs.get("ordonnee")
    pearson = tab.attrs.get("pearson")

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(tab["ratio_nasa"], tab["ratio_pvsyst"],
               c=[_couleur_archipel(a) for a in tab["archipel"]],
               s=52, edgecolor="k", lw=0.4, zorder=3)

    bornes = [min(tab["ratio_nasa"].min(), tab["ratio_pvsyst"].min()) - 0.02,
              max(tab["ratio_nasa"].max(), tab["ratio_pvsyst"].max()) + 0.02]
    ax.plot(bornes, bornes, ls="--", color="k", lw=1, zorder=2,
            label="1:1 (perfect agreement)")
    if pente is not None:
        x = np.array(bornes)
        ax.plot(x, pente * x + ordonnee, color="#c0392b", lw=1.6, zorder=2,
                label=f"fit: {pente:.2f}·x + {ordonnee:.2f}")

    for _, ligne in tab.head(int(n_etiquettes)).iterrows():
        ax.annotate(f"{ligne['ile']} ({ligne['ecart_%']:+.0f} %)",
                    (ligne["ratio_nasa"], ligne["ratio_pvsyst"]),
                    fontsize=8, xytext=(5, 3), textcoords="offset points")
    ref = tab[tab["ile"] == ILE_REFERENCE]
    if len(ref):
        ax.annotate(ILE_REFERENCE,
                    (ref["ratio_nasa"].iloc[0], ref["ratio_pvsyst"].iloc[0]),
                    fontsize=8, fontweight="bold", xytext=(5, -12),
                    textcoords="offset points")

    ax.set_xlim(bornes)
    ax.set_ylim(bornes)
    ax.set_aspect("equal")
    ax.set_xlabel("NASA POWER irradiation ratio (GHI, island / Raiatea)")
    ax.set_ylabel("PVsyst yield ratio (island / Raiatea)")
    ax.set_title(titre or
                 "Cross-check of the per-island yield ratio\n"
                 f"PVsyst simulation vs NASA POWER climatology "
                 f"(r = {pearson:.2f}, mean |deviation| "
                 f"{tab['ecart_%'].abs().mean():.1f} %)")
    poignees, labels = _legende_archipels(tab)
    legende = ax.legend(poignees, labels, fontsize=8, loc="upper left")
    ax.add_artist(legende)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(ls=":", alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def _fe_mix(ile: str, archipel: str) -> float:
    """FE du mix consommé sur l'île (kg CO₂-eq/kWh), ADEME PF 2023 tab. 34.

    Tahiti a son propre facteur dans `electricite.FE_ARCHIPELS` (mix très
    hydraulique) : une île prime sur son archipel.
    """
    fe = electricite.FE_ARCHIPELS
    if ile in fe:
        return fe[ile]
    cle = _ARCHIPEL_VERS_FE.get(str(archipel).strip())
    if cle is None or cle not in fe:
        raise KeyError(
            f"Archipel « {archipel} » (île {ile}) sans facteur d'émission. "
            f"Zones connues : {sorted(fe)}. Complète electricite.FE_ARCHIPELS "
            f"plutôt que d'écrire une valeur ici.")
    return fe[cle]


# ══════════════════════════════════════════════════════════════════════════
# 2. Énergie nette livrée — le dénominateur de l'unité fonctionnelle
# ══════════════════════════════════════════════════════════════════════════
def energie_nette_kwh(ctx, valeurs) -> float:
    """kWh NETS livrés sur toute la durée de vie, pour un jeu de paramètres.

    `ctx.energie` est une expression symbolique construite une fois par
    `systeme.construire`. On l'évalue ici pour un jeu de paramètres donné,
    plutôt que de recopier la formule : le CO₂ évité ne peut donc pas diverger
    du dénominateur du GWP.
    """
    expr = ctx.energie
    if not hasattr(expr, "free_symbols"):
        return float(expr)

    import lca_algebraic as agb
    defauts = {nom: param.default for nom, param in agb.all_params().items()}

    remplacements = {}
    manquants = []
    for symbole in expr.free_symbols:
        nom = str(symbole)
        brut = valeurs.get(nom, defauts.get(nom))
        try:
            remplacements[symbole] = float(brut)
        except (TypeError, ValueError):
            # Un paramètre énuméré (mix de fabrication…) n'a pas sa place dans
            # l'énergie : si l'un s'y trouve, c'est un bug de modèle, pas une
            # valeur à deviner.
            manquants.append(nom)
    if manquants:
        raise KeyError(
            f"Impossible d'évaluer l'énergie nette : paramètre(s) sans valeur "
            f"{sorted(manquants)}. Passe-les dans `valeurs`.")
    return float(expr.subs(remplacements))


# ══════════════════════════════════════════════════════════════════════════
# 3. § 3.4 — CO₂ évité et temps de retour carbone (4 configurations)
# ══════════════════════════════════════════════════════════════════════════

# Facteurs d'émission des différents kWh que la plateforme peut substituer
# (kg CO₂-eq/kWh consommé, pertes de réseau incluses). Reprend la feuille
# `CO2_evite_recalcule` du tableau de référence. Le mix réseau de Raiatea est
# celui du modèle (`electricite.FE_RAIATEA`), pas une copie.
FE_SUBSTITUTION = {
    "Réseau Raiatea (ISLV)": electricite.FE_RAIATEA,
    "Diesel local (thermique ISLV)": 0.9086,
    "Mix Polynésie française": 0.672,
    "Groupe électrogène métropole": 0.86,
    "Mix métropole (ADEME ACV)": 0.052,
}

LIBELLES_SUBSTITUTION_EN = {
    "Réseau Raiatea (ISLV)": "Raiatea island grid",
    "Diesel local (thermique ISLV)": "Local diesel genset",
    "Mix Polynésie française": "French Polynesia average mix",
    "Groupe électrogène métropole": "Mainland diesel genset",
    "Mix métropole (ADEME ACV)": "Mainland France grid",
}


def co2_evite(ctx, jeux, fe_mix=None, verbeux=True) -> pd.DataFrame:
    """CO₂ évité annuel et temps de retour carbone des 4 configurations.

    Une ligne par configuration, plus une ligne « Parc complet » qui somme les
    énergies et les empreintes — pas les temps de retour, qui ne s'additionnent
    pas : celui du parc est le rapport des sommes.

    Parameters
    ----------
    fe_mix : float, optional
        Facteur d'émission du kWh substitué. Par défaut le mix réseau de
        Raiatea (`electricite.FE_RAIATEA`, 0,914 kg CO₂-eq/kWh).

    >>> tab = territoire.co2_evite(ctx, jeux)
    >>> territoire.figure_co2_evite(tab)
    """
    fe_mix = electricite.FE_RAIATEA if fe_mix is None else float(fe_mix)

    lignes = []
    for libelle, valeurs in jeux.items():
        if verbeux:
            print("CO₂ évité :", libelle)
        gwp = systeme.gwp(ctx, **valeurs)                    # kg CO₂-eq/kWh
        e_totale = energie_nette_kwh(ctx, valeurs)           # kWh sur la vie
        duree = float(valeurs["duree_vie_an"])
        e_an = e_totale / duree

        empreinte_totale = gwp * e_totale                    # kg CO₂-eq
        evite_brut = e_an * fe_mix                           # kg/an
        evite_net = e_an * (fe_mix - gwp)                    # kg/an

        lignes.append({
            "modalite": libelle,
            "code": modalites.DONNEES.get(libelle, {}).get("code", libelle),
            "p_install_kwc": float(valeurs["p_install_kwc"]),
            "GWP g/kWh": gwp * 1000.0,
            "E nette MWh/an": e_an / 1000.0,
            "FE substitué kg/kWh": fe_mix,
            "Évité brut t/an": evite_brut / 1000.0,
            "Évité net t/an": evite_net / 1000.0,
            "Empreinte totale t": empreinte_totale / 1000.0,
            "Retour carbone an": (empreinte_totale / evite_net
                                  if evite_net > 0 else np.nan),
            "duree_vie_an": duree,
        })

    tab = pd.DataFrame(lignes)

    # Ligne « parc » : somme des énergies et des empreintes, jamais des ratios.
    e_parc = tab["E nette MWh/an"].sum()
    empreinte_parc = tab["Empreinte totale t"].sum()
    evite_net_parc = tab["Évité net t/an"].sum()
    tab.loc[len(tab)] = {
        "modalite": "Parc complet (4 plateformes)",
        "code": "PARC",
        "p_install_kwc": tab["p_install_kwc"].sum(),
        "GWP g/kWh": (empreinte_parc * 1e6
                      / (e_parc * 1000.0 * tab["duree_vie_an"].max())),
        "E nette MWh/an": e_parc,
        "FE substitué kg/kWh": fe_mix,
        "Évité brut t/an": tab["Évité brut t/an"].sum(),
        "Évité net t/an": evite_net_parc,
        "Empreinte totale t": empreinte_parc,
        "Retour carbone an": (empreinte_parc / evite_net_parc
                              if evite_net_parc > 0 else np.nan),
        "duree_vie_an": tab["duree_vie_an"].max(),
    }

    if verbeux:
        ligne = tab.iloc[-1]
        print(f"  parc {ligne['p_install_kwc']:.2f} kWc | "
              f"{ligne['E nette MWh/an']:.1f} MWh/an nets | "
              f"évité net {ligne['Évité net t/an']:.1f} t CO₂-eq/an | "
              f"retour {ligne['Retour carbone an']:.2f} an "
              f"(FE substitué {fe_mix:.3f})")
    return tab


def co2_evite_scenarios(ctx, jeux, scenarios=None, verbeux=True) -> pd.DataFrame:
    """Le même calcul pour plusieurs kWh substitués — parc complet seulement.

    Reproduit la feuille `CO2_evite_recalcule` du tableau de référence, mais
    depuis le modèle vivant. La ligne « Mix métropole » ressort NÉGATIVE : avec
    sa propre empreinte, la plateforme raccordée au réseau français émettrait
    plus qu'elle n'éviterait. C'est un résultat, pas une anomalie.
    """
    scenarios = FE_SUBSTITUTION if scenarios is None else scenarios

    # Un seul calcul d'ACV : le GWP et l'énergie ne dépendent pas du FE
    # substitué. On refait juste l'arithmétique de substitution.
    base = co2_evite(ctx, jeux, fe_mix=1.0, verbeux=verbeux).iloc[-1]
    e_an_kwh = base["E nette MWh/an"] * 1000.0
    gwp = base["GWP g/kWh"] / 1000.0
    empreinte_t = base["Empreinte totale t"]

    lignes = []
    for libelle, fe in scenarios.items():
        evite_net_t = e_an_kwh * (fe - gwp) / 1000.0
        lignes.append({
            "kWh substitué": libelle,
            "FE kg/kWh": fe,
            "Évité brut t/an": e_an_kwh * fe / 1000.0,
            "Évité net t/an": evite_net_t,
            "Net kg/MWh": (fe - gwp) * 1000.0,
            "Retour carbone an": (empreinte_t / evite_net_t
                                  if evite_net_t > 0 else np.nan),
        })
    return pd.DataFrame(lignes)


def figure_co2_evite(tab: pd.DataFrame, titre=None, avec_parc=False):
    """CO₂ évité net et temps de retour, DEUX PANNEAUX (figure 9 de l'article).

    Cette figure portait un double axe : barres de CO₂ évité à gauche,
    courbe de temps de retour à droite. C'est à éviter, et ici plus
    qu'ailleurs. Les deux grandeurs ne sont pas indépendantes — le temps de
    retour EST l'empreinte divisée par le CO₂ évité — de sorte qu'un double
    axe fabrique une relation visuelle entre deux quantités déjà liées par
    construction, et laisse croire à un lecteur pressé qu'il lit une
    corrélation. Deux panneaux sur le même ordre d'abscisse disent la même
    chose sans rien suggérer de faux.

    Le point de la figure reste le même : la configuration la plus sobre en
    carbone par kWh n'est pas celle qui évite le plus de tonnes, parce que
    ce qui évite, c'est l'énergie produite.
    """
    donnees = tab if avec_parc else tab[tab["code"] != "PARC"]
    donnees = donnees.reset_index(drop=True)

    codes = list(donnees["code"])
    couleurs = [config.COULEURS.get(c, "#808080") for c in codes]
    x = range(len(donnees))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.0), sharex=True)

    # ── panneau A : ce que l'installation évite ──────────────────────────
    barres = ax1.bar(x, donnees["Évité net t/an"], color=couleurs,
                     edgecolor="white")
    ax1.set_ylabel("Net avoided emissions (t CO₂-eq / year)")
    ax1.set_ylim(0, float(donnees["Évité net t/an"].max()) * 1.22)
    for barre, (_, ligne) in zip(barres, donnees.iterrows()):
        ax1.text(barre.get_x() + barre.get_width() / 2,
                 ligne["Évité net t/an"],
                 f"{ligne['Évité net t/an']:.1f} t\n"
                 f"{ligne['E nette MWh/an']:.1f} MWh",
                 ha="center", va="bottom", fontsize=8.5)
    ax1.set_title("A. Net avoided emissions", fontsize=11, weight="bold",
                  loc="left")

    # ── panneau B : en combien de temps elle se rembourse ────────────────
    barres2 = ax2.bar(x, donnees["Retour carbone an"], color=couleurs,
                      edgecolor="white")
    ax2.set_ylabel("Carbon payback time (years)")
    ax2.set_ylim(0, float(donnees["Retour carbone an"].max()) * 1.22)
    for barre, v in zip(barres2, donnees["Retour carbone an"]):
        ax2.text(barre.get_x() + barre.get_width() / 2, v, f"{v:.2f} yr",
                 ha="center", va="bottom", fontsize=8.5)
    ax2.set_title("B. Carbon payback time", fontsize=11, weight="bold",
                  loc="left")

    for ax in (ax1, ax2):
        ax.set_xticks(list(x))
        ax.set_xticklabels(codes, fontsize=9)
        ax.grid(axis="y", ls=":", alpha=0.4)
        ax.set_axisbelow(True)

    fe = float(donnees["FE substitué kg/kWh"].iloc[0])
    duree = float(donnees["duree_vie_an"].iloc[0])
    fig.suptitle(titre or
                 "Net avoided emissions and carbon payback, four configurations\n"
                 f"Substituted grid: {fe:.3f} kg CO₂-eq/kWh (ADEME FP 2023) | "
                 f"net electricity delivered | {duree:.0f}-year lifetime",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 4. § 4.1 — Transposition aux 54 îles
# ══════════════════════════════════════════════════════════════════════════
def transposer(ctx, jeux, iles=None, modalite=None, verbeux=True) -> pd.DataFrame:
    """GWP du kWh et CO₂ évité, île par île.

    Parameters
    ----------
    modalite : str or list, optional
        Configuration(s) à transposer — libellé complet (« S2 (SH51…) ») ou
        code (« SH51 »). Par défaut TOUTES : le parc est alors reconstitué
        exactement comme à Raiatea, et le GWP du parc est la moyenne pondérée
        par l'énergie, pas celui d'une seule plateforme. (La cellule 73 du
        notebook VF4 appliquait le GWP de S2 aux 39,66 kWc du parc, ce qui
        surestimait l'empreinte des 32 kWc restants.)

    Renvoie un tableau LARGE : une ligne par île, avec le détail par
    configuration en colonnes `GWP g/kWh <code>`, plus les agrégats du parc.

    >>> tab = territoire.transposer(ctx, jeux)
    >>> tab.nlargest(5, "CO₂ évité net t/an")[["ile", "GWP g/kWh", "CO₂ évité net t/an"]]
    """
    iles = donnees_iles(verbeux=verbeux) if iles is None else iles.copy()
    codes = _modalites_retenues(jeux, modalite)

    productibles = iles["productible_kwh_kwc_an"].astype(float).tolist()
    distances = iles["dist_goelette_km"].astype(float).tolist()

    energie_an_kwh = np.zeros(len(iles))         # kWh nets / an, parc entier
    empreinte_vie_kg = np.zeros(len(iles))       # kg CO₂-eq sur toute la vie
    p_totale_kwc = 0.0

    for libelle in codes:
        valeurs = jeux[libelle]
        code = modalites.DONNEES.get(libelle, {}).get("code", libelle)
        if verbeux:
            print(f"Transposition {code} sur {len(iles)} îles…")

        gwp_kwh = _gwp_par_ile(ctx, valeurs, productibles, distances,
                              verbeux=verbeux)
        iles[f"GWP g/kWh {code}"] = gwp_kwh * 1000.0

        # Énergie nette de CETTE configuration sur CHAQUE île : l'expression
        # de l'unité fonctionnelle, évaluée au productible local.
        duree = float(valeurs["duree_vie_an"])
        e_vie = np.array([
            energie_nette_kwh(ctx, {**valeurs,
                                    "productible_kwh_kwc_an": prod})
            for prod in productibles])

        energie_an_kwh += e_vie / duree
        empreinte_vie_kg += gwp_kwh * e_vie
        p_totale_kwc += float(valeurs["p_install_kwc"])

    # Empreinte annualisée : l'empreinte totale rapportée à l'énergie annuelle
    # donne le GWP du kWh du parc — moyenne pondérée par l'énergie, pas moyenne
    # arithmétique des quatre GWP.
    duree_parc = float(jeux[codes[0]]["duree_vie_an"])
    gwp_parc = empreinte_vie_kg / (energie_an_kwh * duree_parc)

    iles["p_install_kwc"] = p_totale_kwc
    iles["E nette MWh/an"] = energie_an_kwh / 1000.0
    iles["GWP g/kWh"] = gwp_parc * 1000.0
    iles["Empreinte totale t"] = empreinte_vie_kg / 1000.0
    iles["CO₂ évité brut t/an"] = energie_an_kwh * iles["fe_mix"] / 1000.0
    evite_net_kg_an = energie_an_kwh * (iles["fe_mix"] - gwp_parc)
    iles["CO₂ évité net t/an"] = evite_net_kg_an / 1000.0
    iles["Retour carbone an"] = np.where(evite_net_kg_an > 0,
                                         empreinte_vie_kg / evite_net_kg_an,
                                         np.nan)

    if verbeux:
        ref = iles.loc[iles["ile"] == ILE_REFERENCE].iloc[0]
        print(f"  contrôle {ILE_REFERENCE} : {ref['GWP g/kWh']:.1f} g CO₂-eq/kWh, "
              f"{ref['CO₂ évité net t/an']:.1f} t évitées/an pour "
              f"{p_totale_kwc:.2f} kWc")
        print(f"  étendue : GWP {iles['GWP g/kWh'].min():.1f} → "
              f"{iles['GWP g/kWh'].max():.1f} g "
              f"(±{(iles['GWP g/kWh'].max() / iles['GWP g/kWh'].min() - 1) * 100:.0f} %) | "
              f"évité {iles['CO₂ évité net t/an'].min():.1f} → "
              f"{iles['CO₂ évité net t/an'].max():.1f} t/an "
              f"(×{iles['CO₂ évité net t/an'].max() / iles['CO₂ évité net t/an'].min():.2f})")
    return iles


def _modalites_retenues(jeux, modalite) -> list:
    """Normalise l'argument `modalite` en liste de libellés de `jeux`."""
    if modalite is None:
        return list(jeux)
    demandees = [modalite] if isinstance(modalite, str) else list(modalite)
    retenues = []
    for demandee in demandees:
        if demandee in jeux:
            retenues.append(demandee)
            continue
        trouve = [lib for lib in jeux
                  if modalites.DONNEES.get(lib, {}).get("code") == demandee]
        if not trouve:
            raise KeyError(
                f"Modalité « {demandee} » introuvable. Attendu un libellé parmi "
                f"{list(jeux)} ou un code parmi "
                f"{[d['code'] for d in modalites.DONNEES.values()]}.")
        retenues.append(trouve[0])
    return retenues


def _gwp_par_ile(ctx, valeurs, productibles, distances, verbeux=True):
    """GWP (kg CO₂-eq/kWh) pour chaque île — vectorisé, avec contrôle.

    `compute_impacts` accepte des paramètres à valeurs multiples et calcule la
    série en une passe. C'est 50 fois plus rapide qu'une boucle — mais encore
    faut-il que l'unité fonctionnelle, qui dépend elle aussi du productible,
    soit réévaluée à chaque point. Rien ne le garantit dans la signature : on
    le VÉRIFIE sur la première île, en comparant à un calcul scalaire. Au
    moindre écart, on retombe sur la boucle, en le disant.
    """
    n = len(productibles)
    surcharges = {"productible_kwh_kwc_an": [float(x) for x in productibles],
                  "dist_interile_km": [float(x) for x in distances]}

    serie = None
    try:
        res = systeme.impacts(ctx, [config.GWP], **{**valeurs, **surcharges})
        candidate = np.asarray(res.iloc[:, 0], dtype=float)
        if candidate.size == n:
            serie = candidate
        elif verbeux:
            print(f"  ⚠ vectorisation : {candidate.size} résultats pour {n} "
                  f"îles — passage en boucle.")
    except Exception as err:                                   # noqa: BLE001
        if verbeux:
            print(f"  ⚠ vectorisation impossible ({type(err).__name__}: {err}) "
                  f"— passage en boucle.")

    if serie is not None:
        temoin = systeme.gwp(ctx, **{**valeurs,
                                     "productible_kwh_kwc_an": productibles[0],
                                     "dist_interile_km": distances[0]})
        ecart = abs(serie[0] / temoin - 1.0) if temoin else 1.0
        if ecart > 1e-6:
            if verbeux:
                print(f"  ⚠ vectorisation incohérente ({serie[0] * 1000:.2f} g "
                      f"contre {temoin * 1000:.2f} g en calcul scalaire, "
                      f"écart {ecart * 100:.2f} %) — l'unité fonctionnelle "
                      f"n'est pas réévaluée par point. Passage en boucle.")
            serie = None

    if serie is None:
        serie = np.array([
            systeme.gwp(ctx, **{**valeurs,
                                "productible_kwh_kwc_an": prod,
                                "dist_interile_km": dist})
            for prod, dist in zip(productibles, distances)])
    return serie


def _couleur_archipel(archipel) -> str:
    return COULEURS_ARCHIPELS.get(str(archipel).strip(), "#7f8c8d")


def champ_insolation(lon, lat, lon_pts, lat_pts, valeurs,
                     portee_deg=4.0, poids_min=0.05):
    """Interpole l'insolation entre les îles par lissage à noyau gaussien.

    Ce n'est PAS une mesure : les 54 îles sont séparées par des centaines de
    kilomètres d'océan sans station, et tout ce qui est dessiné entre elles est
    reconstruit. Le noyau gaussien a été préféré à une pondération inverse de
    la distance, qui produit un œil-de-bœuf autour de chaque point de mesure et
    donne l'illusion d'une structure locale là où il n'y en a pas.

    La carte est MASQUÉE là où l'information manque : si la somme des poids
    tombe sous `poids_min`, le point est laissé transparent plutôt que rempli
    par extrapolation. Le fond s'estompe donc de lui-même loin des îles, ce qui
    est la lecture honnête.

    Les distances sont corrigées du cosinus de la latitude, sans quoi un degré
    de longitude vaudrait un degré de latitude à 18° S.

    Parameters
    ----------
    lon, lat : ndarray 2-D
        Grille de sortie (issue de `np.meshgrid`).
    portee_deg : float
        Écart-type du noyau, en degrés. 4° ≈ 440 km : l'échelle sur laquelle
        l'irradiation varie réellement dans le Pacifique Sud.
    poids_min : float
        Somme de poids en deçà de laquelle le point est masqué.

    Returns
    -------
    numpy.ma.MaskedArray
    """
    lon_pts = np.asarray(lon_pts, dtype=float)
    lat_pts = np.asarray(lat_pts, dtype=float)
    valeurs = np.asarray(valeurs, dtype=float)

    cos_lat = math.cos(math.radians(float(np.mean(lat_pts))))
    dlon = (lon[..., None] - lon_pts) * cos_lat
    dlat = lat[..., None] - lat_pts
    d2 = dlon ** 2 + dlat ** 2

    poids = np.exp(-d2 / (2.0 * portee_deg ** 2))
    somme = poids.sum(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        champ = (poids * valeurs).sum(axis=-1) / somme
    return np.ma.masked_where(somme < poids_min, champ)


def _fond_insolation(ax, tab, portee_deg=4.0, alpha=0.55, resolution=320):
    """Dessine le champ d'insolation sous la carte et renvoie l'image."""
    if "ghi_nasa_kwh_m2_j" in tab.columns:
        valeurs = tab["ghi_nasa_kwh_m2_j"]
        libelle = "Global horizontal irradiation (kWh m⁻² d⁻¹, NASA POWER)"
    elif "p0_kwh_kwc_an" in tab.columns:
        valeurs = tab["p0_kwh_kwc_an"]
        libelle = "First-year specific yield (kWh kWp⁻¹ yr⁻¹)"
    else:
        raise KeyError("ni 'ghi_nasa_kwh_m2_j' ni 'p0_kwh_kwc_an' dans le "
                       "tableau : impossible de tracer le fond d'insolation")

    marge = 1.5
    lon_min, lon_max = tab["lon"].min() - marge, tab["lon"].max() + marge
    lat_min, lat_max = tab["lat"].min() - marge, tab["lat"].max() + marge
    lon_g, lat_g = np.meshgrid(np.linspace(lon_min, lon_max, resolution),
                               np.linspace(lat_min, lat_max, resolution))
    champ = champ_insolation(lon_g, lat_g, tab["lon"], tab["lat"], valeurs,
                             portee_deg=portee_deg)

    image = ax.imshow(champ, origin="lower", cmap="Blues", alpha=alpha,
                      extent=(lon_min, lon_max, lat_min, lat_max),
                      aspect="auto", zorder=0, interpolation="bilinear")
    return image, libelle


def _boites(textes, rend):
    """Boîtes englobantes des étiquettes, en pixels : [x, y, largeur, hauteur]."""
    b = []
    for t in textes:
        bb = t.get_window_extent(renderer=rend)
        b.append([bb.x0, bb.y0, bb.width, bb.height])
    return np.array(b, dtype=float)


def _poser_cle(fig, entrees, n_colonnes=5, fontsize=6.5):
    """Ajoute une bande sous la figure et y écrit la clé des numéros.

    La figure est AGRANDIE puis tout ce qu'elle contenait — axes principaux et
    barres de couleur — est translaté vers le haut. Réserver la place avec
    `subplots_adjust` ne suffirait pas : les barres de couleur sont des axes à
    part, que `subplots_adjust` ne déplace pas, et la clé viendrait se poser
    dessus.
    """
    par_colonne = int(np.ceil(len(entrees) / n_colonnes))
    hauteur_cle = par_colonne * 0.135 + 0.30          # pouces
    largeur, hauteur = fig.get_size_inches()
    fig.set_size_inches(largeur, hauteur + hauteur_cle, forward=True)

    f = hauteur / (hauteur + hauteur_cle)
    for axe in fig.axes:
        p = axe.get_position()
        axe.set_position([p.x0, p.y0 * f + (1.0 - f), p.width, p.height * f])

    colonnes = [entrees[k:k + par_colonne]
                for k in range(0, len(entrees), par_colonne)]
    for c, colonne in enumerate(colonnes):
        fig.text(0.06 + c * (0.88 / n_colonnes), (1.0 - f) * 0.90,
                 "\n".join(colonne), fontsize=fontsize, va="top", ha="left",
                 linespacing=1.5)
    return fig


def _etiquettes_numeros(ax, noms, ancres, fontsize=5.0, n_colonnes=5,
                       fontsize_liste=6.5, verbeux=True):
    """Numérote les marqueurs et renvoie la clé sous la figure.

    C'est la solution des atlas quand les points sont trop serrés pour porter
    leur nom : le numéro tient DANS le marqueur, la carte ne porte plus aucune
    étiquette flottante, et il n'y a ni chevauchement ni trait de rappel à
    faire traverser la figure. On paie un aller-retour de l'œil entre la carte
    et la clé, mais c'est le seul coût, et il est prévisible.

    La numérotation suit l'ordre ouest -> est, de sorte que la clé se lit dans
    le même sens que la carte.
    """
    ancres = np.asarray(ancres, dtype=float)
    ordre = np.argsort(ancres[:, 0])

    rang = {int(i): k + 1 for k, i in enumerate(ordre)}
    numeros = [ax.text(x, y, str(rang[i]), fontsize=fontsize, ha="center",
                       va="center", zorder=6, color="k",
                       path_effects=[pe.withStroke(linewidth=1.6,
                                                   foreground="white",
                                                   alpha=0.9)])
               for i, (x, y) in enumerate(ancres)]
    # Deux atolls distants de dix kilomètres portent deux numéros au même
    # pixel : on les décolle, sans trait de rappel — à cette distance le lien
    # au marqueur reste évident.
    _placer_etiquettes(ax, numeros, ancres=ancres, fleches=False,
                       rayon_point=0.0, marge=0.8, rappel=0.06,
                       iterations=300, centre=True, verbeux=False)

    entrees = [f"{rang[int(i)]}. {noms[int(i)]}" for i in ordre]
    if verbeux:
        print(f"  {len(entrees)} îles numérotées d'ouest en est ; la clé est "
              f"posée sous la figure une fois la mise en page terminée.")
    return entrees


def _etiquettes_gouttiere(ax, noms, ancres, fontsize=7.0,
                          part_gouttiere=0.22, interligne=1.25,
                          couleur_trait="0.45", verbeux=True):
    """Renvoie les noms dans deux gouttières latérales, reliés par un trait.

    C'est la parade cartographique classique quand la densité de points
    interdit l'étiquetage en place : aucune répulsion ne peut loger 38 noms
    dans la bande des Tuamotu, qui fait six degrés de large à l'écran. Plutôt
    que d'empiler des compromis, on sort les noms de la carte.

    Les axes sont élargis pour ménager une marge libre de chaque côté ; chaque
    île est affectée au bord dont elle est la plus proche, puis les noms d'un
    même bord sont répartis sur des créneaux À PAS CONSTANT, triés par latitude.
    Le pas constant garantit l'absence de chevauchement par construction, et le
    tri par latitude limite les croisements de traits : deux îles voisines du
    nord au sud ont deux étiquettes voisines.

    Parameters
    ----------
    part_gouttiere : float
        Largeur de chaque gouttière, en fraction de la largeur des axes.
    interligne : float
        Espacement des créneaux, en hauteurs de texte. Sous 1,0 les noms se
        toucheraient.
    """
    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()

    ancres = np.asarray(ancres, dtype=float)
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    largeur = x_max - x_min
    marge = largeur * part_gouttiere
    ax.set_xlim(x_min - marge, x_max + marge)

    # Côté d'affectation : le bord le plus proche, ce qui minimise la longueur
    # cumulée des traits.
    milieu = (x_min + x_max) / 2.0
    gauche = ancres[:, 0] < milieu

    sonde = ax.text(x_min, y_min, "Ag", fontsize=fontsize)
    fig.canvas.draw()
    h_px = sonde.get_window_extent(renderer=rend).height
    sonde.remove()
    pas_px = h_px * interligne
    haut_px = ax.bbox.height
    inv = ax.transData.inverted()

    n_traces = 0
    for cote, masque in (("g", gauche), ("d", ~gauche)):
        idx = np.where(masque)[0]
        if not len(idx):
            continue
        # tri nord -> sud : l'ordre vertical des étiquettes suit celui des îles
        idx = idx[np.argsort(-ancres[idx, 1])]
        n = len(idx)
        besoin = pas_px * n
        if besoin > haut_px and verbeux:
            print(f"  ⚠ gouttière {cote} : {n} noms pour {haut_px:.0f} px ; "
                  f"réduis fontsize ou interligne, ou agrandis la figure.")
        # créneaux centrés sur la hauteur des axes
        depart = ax.bbox.y0 + (haut_px - min(besoin, haut_px)) / 2.0
        pas = min(pas_px, haut_px / max(n, 1))
        for rang, i in enumerate(idx):
            y_px = depart + (n - 1 - rang) * pas + pas / 2.0
            y_donnees = inv.transform((ax.bbox.x0, y_px))[1]
            if cote == "g":
                x_donnees = x_min - marge * 0.96
                ha, sens = "left", 1.0
            else:
                x_donnees = x_max + marge * 0.96
                ha, sens = "right", -1.0
            ax.text(x_donnees, y_donnees, noms[i], fontsize=fontsize,
                    ha=ha, va="center", zorder=5)
            # Le trait s'arrête au bord du texte, pas sur la lettre.
            x_fin = x_donnees + sens * largeur * 0.004
            ax.plot([x_fin, ancres[i, 0]], [y_donnees, ancres[i, 1]],
                    lw=0.4, color=couleur_trait, zorder=2.5, alpha=0.75,
                    solid_capstyle="round")
            n_traces += 1

    if verbeux:
        print(f"  {n_traces} noms reportés en gouttière "
              f"({int(gauche.sum())} à gauche, {int((~gauche).sum())} à droite).")
    return True


def _placer_etiquettes(ax, textes, ancres=None, fleches=True, iterations=500,
                       marge=2.4, rayon_point=7.0, rappel=0.008,
                       seuil_fleche=9.0, centre=False, verbeux=True):
    """Écarte les étiquettes qui se chevauchent, sans dépendance extérieure.

    adjustText fait ce travail, mais il n'est pas toujours installé et ses
    signatures changent d'une version à l'autre : on ne peut pas faire reposer
    la lisibilité d'une figure d'article sur sa présence. L'algorithme ci-dessous
    est une séparation de boîtes en coordonnées ÉCRAN, la seule métrique dans
    laquelle « se chevaucher » a un sens — deux étiquettes peuvent être loin
    l'une de l'autre en degrés de longitude et collées à l'écran.

    À chaque itération :

    1. toute paire de boîtes qui se recouvrent est écartée selon l'axe où le
       recouvrement est le plus FAIBLE, donc par le plus court chemin ;
    2. une boîte posée sur un marqueur est repoussée hors du disque ;
    3. un rappel faible ramène chaque étiquette vers son point, sans quoi elles
       dérivent indéfiniment ;
    4. tout est confiné dans les axes.

    Les étiquettes qui ont dû s'éloigner de plus de `seuil_fleche` pixels
    reçoivent un trait de rappel : sans lui, un nom déplacé devient ambigu.

    Parameters
    ----------
    ancres : list[(x, y)], optional
        Points d'attache en coordonnées de données. Par défaut, la position
        initiale de chaque texte — ce qui suppose qu'ils ont été créés par
        `ax.text(x, y, nom)` sur le point lui-même.
    rayon_point : float
        Rayon, en pixels, du disque autour de chaque marqueur dont on chasse
        les étiquettes. À augmenter si les marqueurs sont gros.
    rappel : float
        Force du rappel vers l'ancre, par itération. Trop fort, les
        chevauchements reviennent ; trop faible, les étiquettes s'envolent.
    """
    if not textes:
        return False

    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()

    if ancres is None:
        ancres = [t.get_position() for t in textes]
    anc = ax.transData.transform(np.asarray(ancres, dtype=float))

    for t in textes:
        t.set_ha("left")
        t.set_va("bottom")

    boites = _boites(textes, rend)
    dims = boites[:, 2:4]
    # `centre` sert aux numéros posés DANS les marqueurs : la boîte doit rester
    # centrée sur le point, pas accrochée par son coin.
    depart_relatif = -dims / 2.0 if centre else np.array([4.0, 4.0])
    pos = anc + depart_relatif

    x0, x1 = ax.bbox.x0 + 2, ax.bbox.x1 - 2
    y0, y1 = ax.bbox.y0 + 2, ax.bbox.y1 - 2
    n = len(textes)

    for _ in range(iterations):
        bouge = False
        centres = pos + dims / 2.0

        # 1. paires d'étiquettes
        for i in range(n):
            for j in range(i + 1, n):
                ox = (min(pos[i, 0] + dims[i, 0], pos[j, 0] + dims[j, 0])
                      - max(pos[i, 0], pos[j, 0]) + marge)
                if ox <= 0:
                    continue
                oy = (min(pos[i, 1] + dims[i, 1], pos[j, 1] + dims[j, 1])
                      - max(pos[i, 1], pos[j, 1]) + marge)
                if oy <= 0:
                    continue
                bouge = True
                if ox < oy:          # séparer horizontalement : moins coûteux
                    d = ox / 2.0 * (1.0 if centres[i, 0] >= centres[j, 0] else -1.0)
                    pos[i, 0] += d
                    pos[j, 0] -= d
                else:
                    d = oy / 2.0 * (1.0 if centres[i, 1] >= centres[j, 1] else -1.0)
                    pos[i, 1] += d
                    pos[j, 1] -= d
                centres = pos + dims / 2.0

        # 2. marqueurs : une étiquette ne doit pas couvrir un point
        for i in range(n):
            gx = np.clip(anc[:, 0], pos[i, 0], pos[i, 0] + dims[i, 0])
            gy = np.clip(anc[:, 1], pos[i, 1], pos[i, 1] + dims[i, 1])
            d = np.hypot(anc[:, 0] - gx, anc[:, 1] - gy)
            touches = np.where(d < rayon_point)[0]
            for k in touches:
                v = centres[i] - anc[k]
                norme = np.hypot(*v)
                if norme < 1e-6:
                    v, norme = np.array([1.0, 1.0]), math.sqrt(2.0)
                pos[i] += v / norme * (rayon_point - d[k]) * 0.5
                bouge = True

        # 3. rappel vers l'ancre
        pos += (anc + depart_relatif - pos) * rappel

        # 4. confinement
        pos[:, 0] = np.clip(pos[:, 0], x0, x1 - dims[:, 0])
        pos[:, 1] = np.clip(pos[:, 1], y0, y1 - dims[:, 1])

        if not bouge:
            break

    inv = ax.transData.inverted()
    deplaces = 0
    for i, t in enumerate(textes):
        t.set_position(inv.transform(pos[i]))
        t.set_path_effects([pe.withStroke(linewidth=2.2, foreground="white",
                                          alpha=0.85)])
        if not fleches:
            continue
        centre = pos[i] + dims[i] / 2.0
        if np.hypot(*(centre - anc[i])) < seuil_fleche + max(dims[i]) / 2.0:
            continue
        # Le trait part du bord de la boîte le plus proche du point, pas de son
        # centre : sinon il traverse le texte.
        bx = np.clip(anc[i, 0], pos[i, 0], pos[i, 0] + dims[i, 0])
        by = np.clip(anc[i, 1], pos[i, 1], pos[i, 1] + dims[i, 1])
        (dx, dy), (ax_, ay) = inv.transform([bx, by]), inv.transform(anc[i])
        ax.plot([dx, ax_], [dy, ay], lw=0.45, color="0.35", zorder=3.5,
                solid_capstyle="round")
        deplaces += 1

    if verbeux and deplaces:
        print(f"  {deplaces} étiquette(s) déplacée(s) et reliées à leur point "
              f"sur {len(textes)}.")
    return True




def _legende_archipels(tab, marqueur="o"):
    """Poignées et libellés des SEULS archipels présents dans le tableau.

    La table des couleurs prévoit les Marquises ; aucune des 54 îles n'y est
    (aucune simulation PVsyst fournie). Les lister quand même ferait croire à
    une catégorie vide plutôt qu'absente.
    """
    presents = [str(a).strip() for a in tab["archipel"].unique()]
    poignees, labels = [], []
    for nom, couleur in COULEURS_ARCHIPELS.items():
        if nom in presents:
            poignees.append(plt.Line2D([], [], marker=marqueur, ls="",
                                       color=couleur))
            labels.append(LIBELLES_ARCHIPELS_EN[nom])
    return poignees, labels


# Aire des marqueurs de `figure_carte`, en points². Assez grande pour que la
# teinte se lise, assez petite pour que les Tuamotu ne se recouvrent pas.
TAILLE_MARQUEUR = 110


def figure_carte(tab: pd.DataFrame, titre=None, annoter=None,
                 couleur="gwp", fond=None, etiquettes="numeros",
                 portee_fond_deg=4.0, etiquettes_ecartees=None):
    """Carte des îles : position réelle, couleur au choix, marqueurs égaux.

    ⚠ L'AIRE DES MARQUEURS NE PORTE PLUS LE CO₂ ÉVITÉ (01/10/2026). Elle le
    faisait, et la carte cumulait alors trois variables — position, aire,
    couleur — plus un fond d'insolation, soit quatre canaux à lire ensemble.
    Or le CO₂ évité net et le GWP du kWh racontent la MÊME disparité
    inter-îles, puisque l'un se déduit de l'autre par le facteur d'émission du
    mix local : le second canal ne payait pas sa dette d'encombrement.
    `figure_compromis` reste là pour qui veut voir les deux grandeurs
    ensemble, et `tab` conserve la colonne.

    Ce n'est pas une carte géographique au sens strict — pas de fond de carte,
    pas de projection : un nuage lon/lat, à l'échelle corrigée du cosinus de la
    latitude pour que les distances ne soient pas visuellement fausses.

    Parameters
    ----------
    annoter : int, optional
        Nombre d'îles à étiqueter (les plus grosses contributrices). Par défaut
        toutes — lisible en 300 dpi, chargé à l'écran.
    couleur : {"gwp", "insolation"}
        Grandeur portée par la couleur des marqueurs. « gwp » donne la carte
        du § 4.2 ; « insolation » redessine EXACTEMENT la même carte — mêmes
        positions, mêmes aires de marqueur — en ne changeant que la couleur,
        de sorte que les deux se comparent point par point.

        On ne trace volontairement AUCUN fond interpolé : les 54 îles sont
        séparées par des centaines de kilomètres d'océan sans mesure, et une
        surface interpolée entre elles serait une invention graphique.
    fond : {None, "insolation"}
        Ajoute SOUS la carte, sans rien y changer d'autre, un dégradé bleu du
        gisement solaire, reconstruit entre les îles par lissage à noyau
        gaussien (cf. `champ_insolation`). Le fond s'estompe là où aucune île
        ne renseigne la zone. Il se lit sur sa propre barre de couleur,
        horizontale, distincte de celle du GWP.
    etiquettes : {"gouttiere", "locales", None}
        « gouttiere » (défaut) reporte les noms dans deux colonnes latérales
        reliées par un trait : c'est la seule mise en page qui tienne avec les
        38 atolls des Tuamotu, où aucun placement en place ne peut éviter les
        chevauchements. « locales » garde les noms près de leur point, écartés
        par répulsion — lisible si l'on n'étiquette qu'une sélection
        (cf. `annoter`). None n'étiquette rien.
    portee_fond_deg : float
        Portée du noyau du fond, en degrés. Plus grand = plus lisse.
    """
    lat_moy = float(tab["lat"].mean())

    # Le CO₂ évité net peut être négatif là où le mix substitué serait plus
    # propre que la plateforme. Il ne pilote plus l'aire des marqueurs, donc
    # il n'y a plus rien à borner — mais le cas reste digne d'être signalé.
    negatifs = tab.loc[tab["CO₂ évité net t/an"] <= 0, "ile"].tolist()
    if negatifs:
        print(f"  ⚠ CO₂ évité net ≤ 0 sur {len(negatifs)} île(s) "
              f"({', '.join(negatifs[:5])}{'…' if len(negatifs) > 5 else ''}). "
              f"La carte ne le montre pas : voir le tableau.")

    # La figure est dimensionnée SUR L'ÉTENDUE DES DONNÉES : avec un
    # `set_aspect` imposé, une figure de forme arbitraire laisse de larges
    # bandes blanches au-dessus et en dessous de la boîte des axes.
    largeur_deg = float(tab["lon"].max() - tab["lon"].min())
    hauteur_deg = float(tab["lat"].max() - tab["lat"].min())
    largeur = 12.5
    hauteur = np.clip(largeur * hauteur_deg / max(largeur_deg, 1e-9)
                      / math.cos(math.radians(lat_moy)), 5.0, 11.0)

    if couleur not in ("gwp", "insolation"):
        raise ValueError("couleur doit valoir 'gwp' ou 'insolation', "
                         f"reçu {couleur!r}")
    if couleur == "gwp":
        valeurs_c = tab["GWP g/kWh"]
        palette = "RdYlGn_r"
        libelle_barre = "GWP100 (g CO₂-eq / kWh)"
        sous_titre = "Colour = carbon footprint of the delivered kWh"
    else:
        # L'irradiation NASA POWER est la mesure d'insolation indépendante du
        # modèle ; à défaut, on retombe sur le productible de première année.
        if "ghi_nasa_kwh_m2_j" in tab.columns:
            valeurs_c = tab["ghi_nasa_kwh_m2_j"]
            libelle_barre = ("Global horizontal irradiation "
                             "(kWh m⁻² d⁻¹, NASA POWER)")
        elif "p0_kwh_kwc_an" in tab.columns:
            valeurs_c = tab["p0_kwh_kwc_an"]
            libelle_barre = "First-year specific yield (kWh kWp⁻¹ yr⁻¹)"
        else:
            raise KeyError("ni 'ghi_nasa_kwh_m2_j' ni 'p0_kwh_kwc_an' dans le "
                           "tableau : impossible de colorer par l'insolation")
        # Rampe à une seule teinte, foncé = plus ensoleillé : impossible de la
        # confondre avec la rampe rouge-vert de la carte du GWP.
        palette = "Blues"
        sous_titre = "Colour = solar resource of the host island"

    if fond not in (None, "insolation"):
        raise ValueError("fond doit valoir None ou 'insolation', "
                         f"reçu {fond!r}")

    fig, ax = plt.subplots(figsize=(largeur, hauteur))
    image_fond, libelle_fond = (None, None)
    if fond == "insolation":
        image_fond, libelle_fond = _fond_insolation(
            ax, tab, portee_deg=portee_fond_deg)
    nuage = ax.scatter(tab["lon"], tab["lat"], s=TAILLE_MARQUEUR,
                       c=valeurs_c, cmap=palette,
                       edgecolor="k", lw=0.4, alpha=0.88, zorder=3)

    if annoter is None:
        a_annoter = tab
    else:
        a_annoter = tab.nlargest(int(annoter), "CO₂ évité net t/an")
        a_annoter = pd.concat([a_annoter,
                               tab[tab["ile"] == ILE_REFERENCE]]).drop_duplicates()
    if etiquettes_ecartees is not None:      # ancien nom de l'argument
        etiquettes = "locales" if etiquettes_ecartees else None
    ancres = list(zip(a_annoter["lon"], a_annoter["lat"]))
    cle_numeros = None
    if etiquettes == "numeros":
        cle_numeros = _etiquettes_numeros(ax, list(a_annoter["ile"]), ancres)
    elif etiquettes == "gouttiere":
        _etiquettes_gouttiere(ax, list(a_annoter["ile"]), ancres)
    elif etiquettes == "locales":
        textes = [ax.text(ligne["lon"], ligne["lat"], ligne["ile"],
                          fontsize=6.5, zorder=4)
                  for _, ligne in a_annoter.iterrows()]
        _placer_etiquettes(ax, textes, ancres=ancres, rayon_point=11.0)
    elif etiquettes is not None:
        raise ValueError("etiquettes doit valoir 'numeros', 'gouttiere', "
                         f"'locales' ou None, reçu {etiquettes!r}")

    ax.scatter(PAPEETE[1], PAPEETE[0], marker="*", s=260, color="k", zorder=5)
    ax.annotate("Papeete (shipping hub)", (PAPEETE[1], PAPEETE[0]), fontsize=8,
                fontweight="bold", xytext=(8, -12), textcoords="offset points")

    barre = plt.colorbar(nuage, ax=ax, pad=0.015)
    barre.set_label(libelle_barre)
    if image_fond is not None:
        barre_fond = plt.colorbar(image_fond, ax=ax, orientation="horizontal",
                                  pad=0.09, shrink=0.55, aspect=34)
        barre_fond.set_label(libelle_fond, fontsize=8)
        barre_fond.ax.tick_params(labelsize=7)

    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_aspect(1.0 / math.cos(math.radians(lat_moy)))
    ax.grid(ls=":", alpha=0.35)
    ax.set_axisbelow(True)
    if fond == "insolation":
        sous_titre += ("\nBackground: solar resource interpolated between the "
                       "islands (Gaussian kernel, "
                       f"{portee_fond_deg:.0f}° — reconstructed, not measured)")
    ax.set_title(titre or
                 "Territorial transposition — 54 inhabited islands of "
                 "French Polynesia\n" + sous_titre, fontsize=10)

    # Plus de légende de taille : tous les marqueurs ont la même aire, il n'y
    # a donc rien à décoder. Le coin inférieur gauche est rendu à la carte.
    plt.tight_layout()
    if cle_numeros:
        _poser_cle(fig, cle_numeros)
    return fig


def figure_gwp_iles(tab: pd.DataFrame, titre=None):
    """Barres horizontales : empreinte du kWh, île par île, triée."""
    donnees = tab.sort_values("GWP g/kWh").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9.5, max(6.0, 0.27 * len(donnees))))
    ax.barh(range(len(donnees)), donnees["GWP g/kWh"],
            color=[_couleur_archipel(a) for a in donnees["archipel"]])
    ax.set_yticks(range(len(donnees)))
    ax.set_yticklabels(donnees["ile"], fontsize=7.5)
    ax.invert_yaxis()

    reference = float(
        donnees.loc[donnees["ile"] == ILE_REFERENCE, "GWP g/kWh"].iloc[0])
    ax.axvline(reference, ls="--", color="k", lw=1.1, zorder=3)
    for etiquette in ax.get_yticklabels():
        if etiquette.get_text() == ILE_REFERENCE:
            etiquette.set_fontweight("bold")

    ax.set_xlabel("GWP100 (g CO₂-eq / kWh)")
    ax.set_xlim(donnees["GWP g/kWh"].min() * 0.96,
                donnees["GWP g/kWh"].max() * 1.02)
    ax.set_title(titre or
                 "Carbon footprint of the delivered kWh by host island\n"
                 "Only two parameters vary: annual yield (PVsyst ratio, "
                 "on-site calibrated) and inter-island shipping distance")

    poignees = [plt.Rectangle((0, 0), 1, 1, color=couleur)
                for couleur in COULEURS_ARCHIPELS.values()
                if couleur in {_couleur_archipel(a) for a in donnees["archipel"]}]
    labels = [LIBELLES_ARCHIPELS_EN[nom]
              for nom, couleur in COULEURS_ARCHIPELS.items()
              if couleur in {_couleur_archipel(a) for a in donnees["archipel"]}]
    poignees.append(plt.Line2D([], [], ls="--", color="k"))
    labels.append(f"{ILE_REFERENCE} ({reference:.1f} g)")
    ax.legend(poignees, labels, fontsize=8, loc="lower right")
    ax.grid(axis="x", ls=":", alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def figure_co2_evite_iles(tab: pd.DataFrame, titre=None):
    """Barres horizontales : CO₂ évité net, île par île, triée.

    La couleur reste l'archipel, mais c'est bien le facteur d'émission du mix
    qui ordonne la figure : Tuamotu (1,193) devant Australes (1,065), Tahiti
    (0,587) dernier malgré un bon productible.
    """
    donnees = tab.sort_values("CO₂ évité net t/an",
                             ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9.5, max(6.0, 0.27 * len(donnees))))
    ax.barh(range(len(donnees)), donnees["CO₂ évité net t/an"],
            color=[_couleur_archipel(a) for a in donnees["archipel"]])
    ax.set_yticks(range(len(donnees)))
    ax.set_yticklabels(donnees["ile"], fontsize=7.5)
    ax.invert_yaxis()

    reference = float(donnees.loc[donnees["ile"] == ILE_REFERENCE,
                                  "CO₂ évité net t/an"].iloc[0])
    ax.axvline(reference, ls="--", color="k", lw=1.1, zorder=3)
    for etiquette in ax.get_yticklabels():
        if etiquette.get_text() == ILE_REFERENCE:
            etiquette.set_fontweight("bold")

    puissance = float(donnees["p_install_kwc"].iloc[0])
    ax.set_xlabel("Net avoided emissions (t CO₂-eq / year)")
    ax.set_title(titre or
                 f"Net avoided emissions by host island — {puissance:.1f} kWc array\n"
                 "Driven by the island grid emission factor (ADEME FP 2023) "
                 "far more than by the yield")

    poignees, labels = [], []
    presents = {_couleur_archipel(a) for a in donnees["archipel"]}
    for nom, couleur in COULEURS_ARCHIPELS.items():
        if couleur in presents:
            fe = _fe_mix("", nom)
            poignees.append(plt.Rectangle((0, 0), 1, 1, color=couleur))
            labels.append(f"{LIBELLES_ARCHIPELS_EN[nom]} — {fe:.3f} kg/kWh")
    poignees.append(plt.Line2D([], [], ls="--", color="k"))
    labels.append(f"{ILE_REFERENCE} ({reference:.1f} t/yr)")
    ax.legend(poignees, labels, fontsize=8, loc="lower right",
              title="Substituted grid", title_fontsize=8)
    ax.grid(axis="x", ls=":", alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def figure_compromis(tab: pd.DataFrame, titre=None, n_etiquettes=None,
                     etiquettes_ecartees=True):
    """Nuage empreinte du kWh ↔ CO₂ évité — la figure de lecture du § 4.1.

    Elle n'est pas dans l'article, mais c'est elle qui montre le point : les
    deux grandeurs ne sont pas alignées. Une île peut produire un kWh un peu
    plus cher en carbone et éviter beaucoup plus, parce qu'elle remplace un
    réseau plus sale.

    Parameters
    ----------
    n_etiquettes : int, optional
        Par défaut None : TOUTES les îles sont nommées. Un entier n'étiquette
        que les n plus grosses contributrices, plus Raiatea et Tahiti.
    etiquettes_ecartees : bool
        Passe les noms à adjustText pour supprimer les chevauchements. Avec
        54 étiquettes le placement prend quelques secondes.
    """
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.scatter(tab["GWP g/kWh"], tab["CO₂ évité net t/an"],
               c=[_couleur_archipel(a) for a in tab["archipel"]],
               s=48, edgecolor="k", lw=0.4, zorder=3)

    if n_etiquettes is None:
        a_nommer = tab
        taille_police = 6.5
    else:
        seuil = tab["CO₂ évité net t/an"].nlargest(int(n_etiquettes)).min()
        a_nommer = tab[(tab["CO₂ évité net t/an"] >= seuil)
                       | tab["ile"].isin([ILE_REFERENCE, "Tahiti"])]
        taille_police = 8
    textes = [ax.text(ligne["GWP g/kWh"], ligne["CO₂ évité net t/an"],
                      ligne["ile"], fontsize=taille_police, zorder=4)
              for _, ligne in a_nommer.iterrows()]
    if etiquettes_ecartees:
        _placer_etiquettes(ax, textes,
                           ancres=list(zip(a_nommer["GWP g/kWh"],
                                           a_nommer["CO₂ évité net t/an"])),
                           rayon_point=6.0)

    ax.set_xlabel("GWP100 of the delivered kWh (g CO₂-eq / kWh)")
    ax.set_ylabel("Net avoided emissions (t CO₂-eq / year)")
    ax.set_title(titre or
                 "Footprint of the kWh vs. emissions avoided — by host island")
    poignees, labels = _legende_archipels(tab)
    ax.legend(poignees, labels, fontsize=8)
    ax.grid(ls=":", alpha=0.4)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════
# 5. Tout d'un coup
# ══════════════════════════════════════════════════════════════════════════
def figures(ctx, jeux, iles=None, verbeux=True) -> dict:
    """Les figures des § 3.4 et § 4.1, en un appel.

    Renvoie {nom de fichier (sans extension): Figure}. Les tableaux sont
    accessibles séparément via `co2_evite` et `transposer` : cette fonction ne
    sert qu'à produire les images.

    >>> figs = territoire.figures(ctx, jeux)
    >>> figs["F8_co2_evite_retour"]
    """
    tab_co2 = co2_evite(ctx, jeux, verbeux=verbeux)
    tab_iles = transposer(ctx, jeux, iles=iles, verbeux=verbeux)
    tab_nasa = comparer_nasa_power(iles=tab_iles, verbeux=verbeux)
    return {
        "F8_co2_evite_retour": figure_co2_evite(tab_co2),
        "F9_carte_iles": figure_carte(tab_iles),
        "F9b_carte_fond_insolation": figure_carte(tab_iles,
                                                  fond="insolation"),
        "F10_gwp_par_ile": figure_gwp_iles(tab_iles),
        "F11_co2_evite_par_ile": figure_co2_evite_iles(tab_iles),
        "F12_compromis_iles": figure_compromis(tab_iles),
        "F15_controle_nasa_power": figure_nasa_power(tab_nasa),
    }
