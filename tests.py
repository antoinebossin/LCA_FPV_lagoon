"""
Batterie de tests du modèle — à lancer après toute modification.

    from acv_lagon import tests
    tests.tout(ctx, jeux, REF)

Chaque test est indépendant, renvoie OK / ÉCHEC / IGNORÉ, et n'interrompt
jamais la série : on veut le tableau complet, pas la première erreur.

Ces tests ne vérifient PAS que les hypothèses sont bonnes — ça, c'est le travail
de revue. Ils vérifient que le modèle fait bien ce qu'on croit qu'il fait :
conservation des masses, conservation des impacts, homogénéité des unités,
reproductibilité, monotonies attendues. C'est-à-dire exactement la classe
d'erreurs qui ne se voit pas dans un résultat plausible.
"""

from __future__ import annotations

import math

import lca_algebraic as agb

from . import (config, electricite, fin_de_vie, incertitude, litterature,
               panneaux, resultats, systeme, territoire)
from .modalites import DONNEES

TOL = 0.01          # 1 % — tolérance générale
TOL_MASSE = 0.15    # 15 % — inventaire parasol vs fiche fabricant


class _R:
    """Résultat d'un test."""

    def __init__(self, nom):
        self.nom, self.etat, self.message = nom, "OK", ""

    def echec(self, message):
        self.etat, self.message = "ÉCHEC", message
        return self

    def ignore(self, message):
        self.etat, self.message = "IGNORÉ", message
        return self

    def ok(self, message=""):
        self.message = message
        return self


# ══════════════════════════════════════════════════════════════════════════
# 1. Inventaire — conservation de la matière
# ══════════════════════════════════════════════════════════════════════════
def t_composition_somme():
    """La composition massique du module somme bien à 1."""
    r = _R("COMPO somme à 1")
    ecart = abs(sum(fin_de_vie.COMPO.values()) - 1.0)
    if ecart > 1e-9:
        return r.echec(f"somme = {sum(fin_de_vie.COMPO.values()):.6f}")
    return r.ok()


def t_masse_module(ctx, jeux):
    """La masse implicite de l'inventaire parasol == la fiche CS Wismar.

    C'est le contrôle du reviewer : ce qui part en fin de vie doit être ce qui
    a été fabriqué. Un écart signale que l'inventaire de fabrication et
    `m_panneaux_kg` décrivent deux modules différents.
    """
    r = _R("masse module : inventaire vs fiche")
    pires = []
    for libelle, valeurs in jeux.items():
        kg_m2, _ = panneaux.masse_module_implicite(ctx, valeurs)
        if kg_m2 <= 0:
            return r.ignore("masse implicite non évaluable")
        surface = DONNEES.get(libelle, {}).get("surface_module", 1.99)
        declaree = valeurs["m_panneaux_kg"] / float(valeurs["n_modules"])
        ecart = (kg_m2 * surface - declaree) / declaree
        pires.append((abs(ecart), libelle, ecart))
    pires.sort(reverse=True)
    pire, libelle, signe = pires[0]
    if pire > TOL_MASSE:
        return r.echec(f"{libelle} : {signe*100:+.1f} % (> {TOL_MASSE*100:.0f} %)")
    return r.ok(f"pire écart {signe*100:+.1f} % ({libelle})")


def t_masse_systeme(ctx, jeux):
    """`m_systeme_t` == somme des masses effectivement décrites dans le modèle.

    Si le transport porte une masse différente de celle des composants, une
    partie du système voyage gratuitement — ou deux fois.
    """
    from . import ancrage, cable

    r = _R("m_systeme_t == somme des masses")
    ecarts = []
    for libelle, valeurs in jeux.items():
        d = DONNEES.get(libelle)
        if d is None:
            continue
        attendu = (d["structure_totale"] + ancrage.masse_kg()
                   + cable.masse_cable_totale_kg() * cable.part_cable_num(d["kwc"])
                   + d["n_modules"] * d["masse_module"]
                   + d["n_onduleurs"] * float(valeurs.get("m_onduleur_kg", 3.0)))
        declare = float(valeurs["m_systeme_t"]) * 1000.0
        ecarts.append(((attendu - declare) / declare, libelle))
    if not ecarts:
        return r.ignore("aucune modalité reconnue")
    pire = max(ecarts, key=lambda e: abs(e[0]))
    if abs(pire[0]) > TOL:
        return r.echec(f"{pire[1]} : {pire[0]*100:+.2f} %")
    return r.ok(f"pire écart {pire[0]*100:+.2f} %")


# ══════════════════════════════════════════════════════════════════════════
# 2. Calcul — conservation de l'impact
# ══════════════════════════════════════════════════════════════════════════
def t_contribution_exacte(ctx, valeurs):
    """La ventilation EXACTE somme au total (elle le doit par construction)."""
    r = _R("contribution exacte : somme == total")
    df = resultats.contribution_directe(ctx, valeurs, [config.GWP])
    colonne = df.columns[0]
    if "*ecart*" not in df.index:
        return r.ignore("pas de ligne *ecart*")
    total = float(df.loc["*total*", colonne])
    ecart = float(df.loc["*ecart*", colonne])
    if abs(ecart / total) > 1e-6:
        return r.echec(f"résidu {ecart/total*100:.4f} % du total")
    return r.ok(f"résidu {ecart/total*100:.2e} %")


def t_axe_non_attribue(ctx, valeurs, seuil=0.02):
    """La ventilation PAR AXE laisse-t-elle un résidu `_other_` ?

    Test informatif : un `_other_` élevé n'est pas un bug du modèle mais une
    limite de l'algorithme d'axe de lca_algebraic, qui ne sait pas imputer une
    activité de premier plan partagée entre deux postes tagués.
    """
    r = _R("axe : part non attribuée")
    df = resultats.contribution(ctx, valeurs, [config.GWP], verifier=False)
    _, total, reste = resultats.totaux_axe(df)
    if total is None or reste is None:
        return r.ignore("pas de ligne de total/résidu")
    part = float(abs(reste.iloc[0] / total.iloc[0]))
    if part > seuil:
        return r.echec(f"{part*100:.1f} % non attribué — utilise "
                       f"contribution(..., exacte=True) pour le rapport")
    return r.ok(f"{part*100:.2f} % non attribué")


def t_axe_deterministe(ctx, valeurs):
    """La ventilation par axe est-elle REPRODUCTIBLE d'un appel à l'autre ?

    Constaté en août 2026 : sur deux exécutions du MÊME modèle donnant le même
    total au chiffre près, la répartition entre Panneaux, Onduleurs, Repeteurs
    et `_other_` changeait de plusieurs g CO2-eq/kWh. L'attribution des
    activités partagées dépend de l'ordre de parcours du graphe. Un tableau de
    contribution non reproductible n'a rien à faire dans un rapport.
    """
    r = _R("axe : reproductibilité")
    a = resultats.contribution(ctx, valeurs, [config.GWP], verifier=False)
    b = resultats.contribution(ctx, valeurs, [config.GWP], verifier=False)
    col = a.columns[0]
    communs = [i for i in a.index if i in b.index]
    pire, poste = 0.0, None
    total = float(abs(a.loc["*sum*", col])) if "*sum*" in a.index else 1.0
    for i in communs:
        d = abs(float(a.loc[i, col]) - float(b.loc[i, col])) / total
        if d > pire:
            pire, poste = d, i
    if pire > 1e-6:
        return r.echec(f"« {poste} » varie de {pire*100:.2f} % entre deux appels")
    return r.ok("stable")


def t_unite_fonctionnelle(ctx, valeurs):
    """impact_par_kWh × énergie_totale == impact absolu du système."""
    r = _R("unité fonctionnelle cohérente")
    par_kwh = systeme.gwp(ctx, **valeurs)
    absolu = float(agb.compute_impacts(ctx.systeme, [config.GWP],
                                       **valeurs).iloc[0, 0])
    energie = float(agb.compute_expr_value(
        getattr(ctx.energie, "magnitude", ctx.energie), valeurs))
    ecart = (par_kwh * energie - absolu) / absolu
    if abs(ecart) > 1e-6:
        return r.echec(f"{ecart*100:.4f} % — l'UF n'est pas appliquée proprement")
    return r.ok(f"E = {energie:.0f} kWh sur la durée de vie")


def t_reproductibilite(ctx, valeurs):
    """Deux appels identiques donnent exactement le même résultat."""
    r = _R("résultat reproductible")
    a, b = systeme.gwp(ctx, **valeurs), systeme.gwp(ctx, **valeurs)
    if a != b:
        return r.echec(f"{a:.9f} != {b:.9f}")
    return r.ok(f"{a*1000:.3f} g CO2-eq/kWh")


# ══════════════════════════════════════════════════════════════════════════
# 3. Comportement — monotonies et signes attendus
# ══════════════════════════════════════════════════════════════════════════
def t_monotonie_duree_vie(ctx, valeurs):
    """Allonger la durée de vie doit BAISSER l'impact par kWh."""
    r = _R("monotonie : durée de vie ↑ → g/kWh ↓")
    court = systeme.gwp(ctx, **{**valeurs, "duree_vie_an": 20})
    long_ = systeme.gwp(ctx, **{**valeurs, "duree_vie_an": 30})
    if not long_ < court:
        return r.echec(f"20 ans = {court*1000:.1f} g, 30 ans = {long_*1000:.1f} g")
    return r.ok(f"{court*1000:.1f} → {long_*1000:.1f} g")


def t_monotonie_productible(ctx, valeurs):
    """Plus de productible doit BAISSER l'impact par kWh."""
    r = _R("monotonie : productible ↑ → g/kWh ↓")
    bas = systeme.gwp(ctx, **{**valeurs, "productible_kwh_kwc_an": 830})
    haut = systeme.gwp(ctx, **{**valeurs, "productible_kwh_kwc_an": 1240})
    if not haut < bas:
        return r.echec(f"830 = {bas*1000:.1f} g, 1240 = {haut*1000:.1f} g")
    return r.ok(f"{bas*1000:.1f} → {haut*1000:.1f} g")


def t_monotonie_alu(ctx, valeurs):
    """Plus d'aluminium de structure doit AUGMENTER l'impact."""
    r = _R("monotonie : aluminium ↑ → impact ↑")
    bas = systeme.gwp(ctx, **{**valeurs, "m_alu_structure_kg": 400})
    haut = systeme.gwp(ctx, **{**valeurs, "m_alu_structure_kg": 900})
    if not haut > bas:
        return r.echec(f"400 kg = {bas*1000:.1f} g, 900 kg = {haut*1000:.1f} g")
    return r.ok(f"{bas*1000:.1f} → {haut*1000:.1f} g")


def t_eol_signes(ctx, valeurs):
    """Cohérence des trois modalités de fin de vie.

    * en cut-off, la fin de vie n'accorde AUCUN crédit → impact ≥ enfouissement
      seul n'est pas garanti, mais l'impact du poste doit rester POSITIF ;
    * la closed-loop, qui crédite la matière vierge évitée, doit donner un
      total ≤ celui du cut-off. Si ce n'est pas le cas, les crédits sont mal
      signés (piège classique de la convention déchets d'ecoinvent).
    """
    r = _R("fin de vie : ordre cut-off / closed-loop")
    val = {cle: systeme.gwp_g(ctx, **{**valeurs, "fin_de_vie": cle})
           for cle in fin_de_vie.MODALITES}
    if not val["recyclage_closed_loop"] <= val["recyclage_cutoff"] + 1e-9:
        return r.echec(f"closed-loop ({val['recyclage_closed_loop']:.2f} g) > "
                       f"cut-off ({val['recyclage_cutoff']:.2f} g) — "
                       f"crédits mal signés ?")
    return r.ok(" | ".join(f"{k.split('_')[-1]} {v:.2f} g" for k, v in val.items()))


def t_pas_d_impact_negatif(ctx, valeurs):
    """Aucune catégorie ne doit être négative au scénario de référence."""
    r = _R("aucun impact négatif (enfouissement)")
    res = systeme.impacts(ctx, config.METHODES_EF,
                          **{**valeurs, "fin_de_vie": "enfouissement"}).iloc[0]
    negatifs = [str(i)[:40] for i, v in res.items() if v < 0]
    if negatifs:
        return r.echec(f"{len(negatifs)} catégorie(s) < 0 : {negatifs[:3]}")
    return r.ok(f"{len(res)} catégories, toutes ≥ 0")


def t_homogeneite_modalites(ctx, jeux):
    """Les 4 modalités restent dans un rapport plausible (facteur < 3)."""
    r = _R("modalités dans un ordre de grandeur cohérent")
    vals = {lib: systeme.gwp_g(ctx, **v) for lib, v in jeux.items()}
    rapport = max(vals.values()) / min(vals.values())
    if rapport > 3.0:
        return r.echec(f"rapport max/min = {rapport:.1f} — vérifie les données "
                       f"de modalité : {vals}")
    return r.ok(" | ".join(f"{k.split(' ')[0]} {v:.0f}" for k, v in vals.items())
                + f"  (max/min {rapport:.2f})")


# ══════════════════════════════════════════════════════════════════════════
# 4. Datasets de fond
# ══════════════════════════════════════════════════════════════════════════
UNITES_ATTENDUES = {
    "aluminium": "kilogram", "eps": "kilogram", "pehd": "kilogram",
    "inox": "kilogram", "acier": "kilogram",
    "caoutchouc": "kilogram", "cuivre": "kilogram", "verre_plat": "kilogram",
    "pa6": "kilogram",
    "silicium_mg": "kilogram", "argent": "kilogram",
    "aluminium_primaire": "kilogram", "eau_douce": "kilogram",
    "electronique": "kilogram",
    "diesel_bateau": "megajoule",
    "elec_fioul": "kilowatt hour",
    "elec_nz": "kilowatt hour",
    "fret_maritime": "ton kilometer", "fret_goelette": "ton kilometer",
    "fret_camion": "ton kilometer",
}


def t_unites_datasets(ctx):
    """Chaque rôle ecoinvent pointe sur un dataset de la bonne unité.

    Le piège que ce test attrape : `market for container ship` est un NAVIRE
    (unité « unit »), pas un service de transport (« ton kilometer »). Une
    confusion de ce type passe inaperçue et fausse l'ordre de grandeur.
    """
    r = _R("unités des datasets de fond")
    mauvais = []
    for role, attendue in UNITES_ATTENDUES.items():
        act = getattr(ctx.ei, role, None)
        if act is None:
            continue
        reelle = str(act.get("unit", "")).lower()
        if attendue not in reelle:
            mauvais.append(f"{role} : « {reelle} » au lieu de « {attendue} »")
    if mauvais:
        return r.echec(" ; ".join(mauvais))
    return r.ok(f"{len(UNITES_ATTENDUES)} rôles vérifiés")


def t_decharges_resolues(ctx):
    """Les filières de décharge par fraction sont-elles toutes résolues ?"""
    r = _R("filières de décharge par fraction")
    manquants = [role for role in set(fin_de_vie.FILIERE.values())
                 if getattr(ctx.ei, role, None) is None]
    if manquants:
        return r.echec(f"repli générique pour {manquants} — lance "
                       f"ecoinvent.diagnostic_decharge()")
    return r.ok("toutes résolues")


# Déplacé dans `parametres.py` : `incertitude.py` en a besoin lui aussi, et
# deux copies d'une même liste finissent toujours par diverger.
from . import parametres                             # noqa: E402
from .parametres import PARAMS_PAR_MODALITE          # noqa: E402


def t_nominal_dans_les_bornes(ctx, jeux):
    """Chaque valeur nominale tombe-t-elle DANS la plage déclarée du paramètre ?

    Bug vécu : `productible_kwh_kwc_an` avait des bornes [1000 ; 1200]
    exprimées sur la 1ʳᵉ année, alors que le nominal injecté était le
    productible MOYEN (973, dégradation incluse) — donc hors de sa propre
    plage. Le tornado affichait une barre qui ne contenait pas son point
    nominal. Symptôme discret, conséquence sérieuse : la sensibilité était
    évaluée sur un intervalle qui n'encadrait pas le résultat publié.
    """
    r = _R("nominal dans les bornes déclarées")
    registre = agb.all_params()
    fautes = []
    for libelle, valeurs in jeux.items():
        for nom, valeur in valeurs.items():
            param = registre.get(nom)
            if param is None or not isinstance(valeur, (int, float)):
                continue
            mini, maxi = getattr(param, "min", None), getattr(param, "max", None)
            if mini is None or maxi is None:
                continue
            if nom in PARAMS_PAR_MODALITE:
                # Plage RELATIVE : min/max décrivent l'incertitude AUTOUR de la
                # valeur de la configuration courante, pas un intervalle absolu
                # commun aux quatre. On vérifie donc que la demi-largeur
                # déclarée reste plausible, pas que la valeur y tombe.
                defaut = float(param.default)
                if defaut <= 0:
                    continue
                demi = max(maxi - defaut, defaut - mini) / defaut
                if not (0.01 <= demi <= 0.60):
                    fautes.append(f"{nom} : demi-plage {demi:.0%} hors "
                                  f"[1 % ; 60 %] — incertitude invraisemblable")
                continue
            if not (mini - 1e-9 <= valeur <= maxi + 1e-9):
                fautes.append(f"{nom} = {valeur:.4g} hors [{mini:.4g} ; "
                              f"{maxi:.4g}] ({libelle.split(' ')[0]})")
    if fautes:
        return r.echec(" ; ".join(sorted(set(fautes))[:4]))
    return r.ok(f"{len(jeux)} modalités vérifiées ; "
                f"{len(PARAMS_PAR_MODALITE)} paramètres en plage relative")


def t_facteur_aluminium(ctx):
    """Le facteur d'émission AU KG de chaque option d'aluminium est-il crédible ?

    Un écart GLO/RER spectaculaire sur le résultat final peut venir d'un vrai
    effet d'origine… ou d'un dataset de secondaire à produit de référence
    négatif, qui transformerait 35 % de l'alliage en crédit. Ce test regarde le
    facteur au kg, seul endroit où la différence entre les deux se voit.

    Repères : alliage corroyé mondial 12-16 kg CO2-eq/kg, ingot primaire
    européen 8-9, secondaire 0,5-1,5.
    """
    from . import structure

    r = _R("aluminium : facteurs d'émission au kg")
    try:
        df = structure.facteurs_aluminium(ctx)
    except Exception as err:      # noqa: BLE001
        return r.ignore(f"{type(err).__name__}: {err}")
    if df.empty:
        return r.ignore("aucune option résolue")

    anomalies = []
    for _, ligne in df.iterrows():
        option, fe = ligne["option"], ligne["kg CO2-eq / kg"]
        # Les lignes « → » sont des ANNOTATIONS (part lue, écart) et non des
        # facteurs d'émission : l'écart d'origine est négatif par construction.
        if option.startswith("→") or fe != fe:      # NaN
            continue
        if fe <= 0:
            anomalies.append(f"{option} = {fe:.2f} (≤ 0 !)")
        elif option.startswith("GLO") and not 8 <= fe <= 25:
            anomalies.append(f"{option} = {fe:.2f} hors 8-25")
        # Le primaire MONDIAL monte à ~21 (électrolyse au charbon), l'européen
        # tourne vers 10 : une seule plage large couvre les deux.
        elif option.startswith("primaire") and not 5 <= fe <= 30:
            anomalies.append(f"{option} = {fe:.2f} hors 5-30")
    if anomalies:
        return r.echec(" ; ".join(anomalies))
    resume = " | ".join(f"{l['option'][:18]} {l['kg CO2-eq / kg']:.1f}"
                        for _, l in df.iterrows())
    return r.ok(resume)


def t_cable_fiche_fabricant():
    """Les masses linéiques du câble collent-elles à la fiche TOP HORN 4G95 ?

    Trois pièges, dont deux déjà attrapés :
    * `CU_PAR_M` valait 4,600 kg/m, soit 5,04 conducteurs de 95 mm², alors que
      le CCTP Sunzil spécifie 4 × 1 × 95 mm². Un nombre ENTIER de conducteurs
      est la signature d'un câble réel ;
    * le modèle décrivait DEUX câbles (un FESTOONFLEX en mer, un 5 G 6 à terre),
      alors que c'est le même TOP HORN qui continue enterré. Les constantes
      `CU_TERRE` et `PE_TERRE` ne doivent plus exister ;
    * l'enveloppe est obtenue PAR DIFFÉRENCE. Le garde-fou décisif est que le
      cuivre ne peut pas dépasser la masse du cuivre PLEIN de la section : à
      8,96 g/cm³, 95 mm² pèsent 0,851 kg/m, et le facteur de câblage d'un
      conducteur souple classe 5 reste sous ~1,10.
    """
    from . import cable

    r = _R("câble : masses linéiques vs fiche TOP HORN")
    cu_1x95 = 0.912          # kg/m, Copper Index fabricant pour 1 × 95 mm²
    cu_plein = 95e-6 * 8960          # 95 mm² × 8 960 kg/m³ = 0,851 kg/m

    if hasattr(cable, "CU_TERRE") or hasattr(cable, "PE_TERRE"):
        return r.echec("CU_TERRE / PE_TERRE existent encore : le modèle décrit "
                       "toujours deux câbles au lieu d'un seul TOP HORN")

    n_cond = cable.CU_PAR_M / cu_1x95
    if abs(n_cond - round(n_cond)) > 0.02:
        return r.echec(f"CU_PAR_M = {cable.CU_PAR_M} → {n_cond:.2f} conducteurs "
                       f"de 95 mm² : ce n'est pas un nombre entier")
    if round(n_cond) != 4:
        return r.echec(f"{round(n_cond)} conducteurs modélisés, le CCTP en "
                       f"spécifie 4 (« 4 × 1 × 95 mm² »)")

    facteur = (cable.CU_PAR_M / round(n_cond)) / cu_plein
    if not 1.0 <= facteur <= 1.10:
        return r.echec(f"facteur de câblage {facteur:.3f} hors [1,00 ; 1,10] : "
                       f"{cable.CU_PAR_M / round(n_cond):.3f} kg/m par "
                       f"conducteur contre {cu_plein:.3f} kg/m de cuivre plein")

    env = cable.TOTAL_PAR_M - cable.CU_PAR_M
    if abs(cable.ENV_PAR_M - env) > 1e-9:
        return r.echec(f"ENV_PAR_M = {cable.ENV_PAR_M} au lieu de {env:.3f} "
                       f"(masse totale moins cuivre)")
    if not 0.15 <= env / cable.TOTAL_PAR_M <= 0.45:
        return r.echec(f"enveloppe à {env / cable.TOTAL_PAR_M:.0%} de la masse "
                       f"du câble : invraisemblable pour un 4G95 élastomère")

    return r.ok(f"4 × 1 × 95 mm², un seul câble : {cable.CU_PAR_M:.3f} kg/m de "
                f"cuivre (câblage ×{facteur:.3f}) + {env:.3f} kg/m d'enveloppe "
                f"({env / cable.TOTAL_PAR_M:.0%})")


def t_cables_methode_commune():
    """Les DEUX câbles suivent-ils la même méthode : total fiche, cuivre calculé,
    enveloppe par différence ?

    Le piège attrapé le 16/09/2026 : `onduleurs.CUIVRE_PAR_M_KG` valait 0,115 —
    la masse TOTALE du câble prise pour du cuivre, et l'enveloppe comptée nulle
    part. Le garde-fou décisif est le même pour les deux câbles : le cuivre ne
    peut pas dépasser la masse du cuivre PLEIN de la section, et la part de
    cuivre doit décroître quand la section décroît (plus la section est petite,
    plus la part d'isolant est grande).
    """
    from . import cable, onduleurs

    r = _R("câbles : total fiche, cuivre calculé, gaine par différence")

    # La méthode doit reproduire le seul cas où le fabricant donne les deux
    # nombres : le Copper Index du TOP HORN.
    calcule = cable.cuivre_par_m(cable.SECTION_MM2, cable.N_CONDUCTEURS)
    if abs(calcule - cable.CU_PAR_M) > 0.005:
        return r.echec(f"la méthode donne {calcule:.4f} kg/m pour le TOP HORN "
                       f"alors que le Copper Index fabricant dit "
                       f"{cable.CU_PAR_M:.4f} : le facteur de câblage "
                       f"({cable.FACTEUR_CABLAGE}) ne colle plus")

    cas = [("TOP HORN 4G95", cable.SECTION_MM2, cable.N_CONDUCTEURS,
            cable.TOTAL_PAR_M, cable.CU_PAR_M, cable.ENV_PAR_M),
           ("module→onduleur 3G1,5", onduleurs.SECTION_MM2,
            onduleurs.N_CONDUCTEURS, onduleurs.TOTAL_PAR_M_KG,
            onduleurs.CUIVRE_PAR_M_KG, onduleurs.GAINE_PAR_M_KG)]

    parts = {}
    for nom, section, n_cond, total, cu, env in cas:
        plein = section * 1e-6 * 8960 * n_cond
        if cu > plein * cable.FACTEUR_CABLAGE_MAX + 1e-9:
            return r.echec(f"{nom} : {cu:.4f} kg/m de cuivre pour {n_cond} × "
                           f"{section:g} mm², au-dessus du cuivre plein "
                           f"({plein:.4f}) × {cable.FACTEUR_CABLAGE_MAX} — "
                           f"c'est une masse TOTALE prise pour du cuivre")
        if abs((total - cu) - env) > 1e-9:
            return r.echec(f"{nom} : gaine {env:.4f} au lieu de "
                           f"{total - cu:.4f} kg/m (total moins cuivre)")
        if env <= 0:
            return r.echec(f"{nom} : gaine négative ou nulle ({env:.4f})")
        parts[nom] = cu / total

    if parts["TOP HORN 4G95"] <= parts["module→onduleur 3G1,5"]:
        return r.echec(
            f"part de cuivre : {parts['TOP HORN 4G95']:.0%} sur le 4G95 contre "
            f"{parts['module→onduleur 3G1,5']:.0%} sur le 3G1,5. Une petite "
            f"section est majoritairement de l'isolant : la hiérarchie est "
            f"inversée, donc au moins un des deux totaux est faux")

    return r.ok(" | ".join(f"{nom} {part:.0%} de cuivre"
                           for nom, part in parts.items()))


def t_ancrage_quincaillerie():
    """Poulie et manille sont-elles comptées, et l'ancrage fait-il le bon total ?

    Garde-fou sur la décision du 15/09/2026 : seules DEUX pièces de
    quincaillerie Seaflex ont été montées, une poulie PA6 et une manille
    galvanisée par ligne. Les masses viennent du BoM, dont la colonne
    « Weight » est une masse TOTALE par ligne d'ancrage.
    """
    from . import ancrage

    r = _R("ancrage : quincaillerie et total")
    m = ancrage.masses_kg()

    manquants = [k for k in ("corde", "elastique", "chaine", "ancres",
                             "poulie", "manille") if k not in m]
    if manquants:
        return r.echec(f"flux absents de ancrage._masses() : {manquants}")

    attendus = {"poulie": 4 * 0.089, "manille": 4 * 0.385}
    for cle, attendu in attendus.items():
        if abs(float(m[cle]) - attendu) > 1e-6:
            return r.echec(f"{cle} : {float(m[cle]):.4f} kg au lieu de "
                           f"{attendu:.4f} (BoM Seaflex × 4 lignes)")

    # 61,998 kg = quincaillerie comptée ET corde recalée en HMPE (16/09/2026).
    # Les deux jalons précédents : 61,280 sans la quincaillerie, 63,176 avec la
    # quincaillerie mais la corde encore calée sur du polyester.
    total = ancrage.masse_kg()
    if abs(total - 61.9982) > 1e-3:
        return r.echec(f"ancrage total {total:.4f} kg au lieu de 61,9982 "
                       f"(61,280 sans quincaillerie ; 63,176 avec la corde "
                       f"polyester)")
    corde = float(m["corde"])
    if abs(corde - 2.8262) > 1e-3:
        return r.echec(f"corde {corde:.4f} kg au lieu de 2,8262 — "
                       f"rho_corde_kg_m est-il revenu à 0,17 (polyester) ?")
    return r.ok(f"{total:.3f} kg/plateforme, corde HMPE {corde:.3f} kg, "
                f"poulie et manille comptées")


def t_activites_epinglees(ctx):
    """Chaque rôle pointe-t-il sur le dataset EXACT qui est épinglé ?

    Garde-fou de la VF. Tant qu'un balayage de secours existait, un dataset
    pouvait être remplacé en silence par un homonyme approximatif — c'est ainsi
    que la filière plastique s'était retrouvée sur « waste plastic PLASTER ».
    Le balayage est supprimé ; ce test vérifie en plus que ce qui a été résolu
    est bien ce qui est écrit dans `ecoinvent.ACTIVITES` et `ecoinvent.DECHARGE`.
    """
    from . import ecoinvent

    r = _R("activités épinglées : nom et géographie")
    cibles = dict(ecoinvent.ACTIVITES)
    cibles.update(ecoinvent.DECHARGE)
    cibles["enfouissement"] = ecoinvent.DISPOSAL

    ecarts = []
    for role, (nom_attendu, loc_attendue, unite_attendue) in cibles.items():
        act = getattr(ctx.ei, role, None)
        if act is None:
            ecarts.append(f"{role} : non résolu")
            continue
        # L'unité fait partie de l'identifiant : en 3.11 un même nom et une même
        # géographie existent en kg, MJ et kWh pour les procédés de décharge
        # avec valorisation du biogaz.
        if (act["name"] != nom_attendu
                or act.get("location") != loc_attendue
                or str(act.get("unit", "")) != unite_attendue):
            ecarts.append(f"{role} : « {act['name']} | {act.get('location')} | "
                          f"{act.get('unit')} » au lieu de « {nom_attendu} | "
                          f"{loc_attendue} | {unite_attendue} »")
    if ecarts:
        return r.echec(" ; ".join(ecarts[:3]))
    return r.ok(f"{len(cibles)} rôles conformes (nom, géographie ET unité)")


def t_anodisation(ctx):
    """L'anodisation est-elle bien comptée, et sur une surface plausible ?"""
    from . import structure

    r = _R("anodisation des profilés alu")
    if not structure.ANODISATION:
        return r.ignore("désactivée (structure.ANODISATION = False)")
    if getattr(ctx.ei, "anodisation", None) is None:
        return r.echec("aucun dataset « anodising » résolu — poste négligé")
    s = float(agb.all_params()["surface_anodisee_m2_par_kg"].default)
    # bornes géométriques : profilé de 1 à 5 mm de paroi, anodisé 2 faces
    if not 0.15 <= s <= 0.75:
        return r.echec(f"{s:.2f} m²/kg hors des bornes géométriques plausibles")
    return r.ok(f"{s:.2f} m²/kg — paroi équivalente {2/(s*2700)*1000:.1f} mm")


def t_scenarios_surchargeables():
    """Les axes de scénario doivent rester MODIFIABLES hors tirage aléatoire.

    Régression vécue en août 2026 : leur mettre `distrib = FIXED` en permanence
    les rendait ignorés par `compute_impacts` (« marked as FIXED, but passed in
    parameters : ignored »), et les trois modalités de fin de vie renvoyaient
    trois fois la même valeur. Le bon mécanisme est le gel TEMPORAIRE
    (`parametres.scenarios_figes`), vérifié par le test suivant.
    """
    from lca_algebraic.params import DistributionType

    from . import parametres

    r = _R("scénarios surchargeables (pas FIXED en permanence)")
    figes = [nom for nom in parametres.SCENARIOS
             if nom in agb.all_params()
             and agb.all_params()[nom].distrib == DistributionType.FIXED]
    if figes:
        return r.echec(f"FIXED en permanence, donc non comparable(s) : "
                       f"{', '.join(figes)}")
    return r.ok(f"{len(parametres.SCENARIOS)} axes de scénario surchargeables")


def t_gel_temporaire():
    """Le gel temporaire fige bien, puis restaure bien."""
    from lca_algebraic.params import DistributionType

    from . import parametres

    r = _R("gel temporaire des scénarios")
    registre = agb.all_params()
    avant = {n: registre[n].distrib for n in parametres.SCENARIOS if n in registre}
    with parametres.scenarios_figes():
        pendant = {n: registre[n].distrib for n in avant}
    apres = {n: registre[n].distrib for n in avant}

    pas_figes = [n for n, d in pendant.items() if d != DistributionType.FIXED]
    pas_restaures = [n for n in avant if avant[n] != apres[n]]
    if pas_figes:
        return r.echec(f"non figé(s) pendant le tirage : {', '.join(pas_figes)}")
    if pas_restaures:
        return r.echec(f"non restauré(s) après : {', '.join(pas_restaures)}")
    return r.ok(f"{len(avant)} axes figés puis restaurés")


def t_scenarios_ont_un_effet(ctx, valeurs):
    """Chaque axe de scénario change-t-il RÉELLEMENT le résultat ?

    Un scénario qui ne fait rien est presque toujours un bug silencieux :
    dataset introuvable, switch inactif, paramètre ignoré. C'est exactement ce
    qui s'est passé deux fois de suite sur `origine_aluminium`.
    """
    r = _R("les scénarios ont un effet")
    axes = {"fin_de_vie": fin_de_vie.MODALITES,
            "origine_aluminium": ("GLO", "RER", "RER_SUP")}
    inertes = []
    for nom, modalites_ in axes.items():
        if nom not in agb.all_params():
            continue
        vals = {m: systeme.gwp(ctx, **{**valeurs, nom: m}) for m in modalites_}
        if max(vals.values()) - min(vals.values()) < 1e-9:
            inertes.append(f"{nom} ({vals[modalites_[0]]*1000:.2f} g partout)")
    if inertes:
        return r.echec("sans effet : " + " ; ".join(inertes))
    return r.ok(f"{len(axes)} axes actifs")


def t_auxiliaires(ctx, valeurs, seuil=0.05):
    """Les auxiliaires (répéteurs) restent-ils marginaux devant le productible ?

    Ils sont déduits du kWh net livré, conformément à l'IEA-PVPS Task 12. S'ils
    dépassent quelques pour cent du productible, ce n'est plus un auxiliaire :
    il faut les modéliser comme une charge à part entière.
    """
    from . import repeteurs

    r = _R("auxiliaires < 5 % du productible")
    brute = float(agb.compute_expr_value(
        getattr(systeme.energie_totale(ctx, nette=False), "magnitude",
                systeme.energie_totale(ctx, nette=False)), valeurs))
    aux_expr = repeteurs.consommation_kwh(ctx)
    aux = float(agb.compute_expr_value(
        getattr(aux_expr, "magnitude", aux_expr), valeurs)) if aux_expr else 0.0
    part = aux / brute
    if part > seuil:
        return r.echec(f"{part*100:.2f} % du productible ({aux:.0f} kWh)")
    return r.ok(f"{aux:.0f} kWh sur {brute:.0f} kWh, soit {part*100:.2f} %")


def t_mix_fabrication(ctx):
    """Le mix de fabrication est-il bien celui du lieu d'assemblage ?

    Piège attrapé : le défaut parasol est « CN ». Le passer dans le dict de
    modalité ne suffit pas, car l'OAT et le Monte-Carlo partent des valeurs PAR
    DÉFAUT des paramètres. Le résultat principal et la sensibilité tournaient
    donc sur deux mix différents.
    """
    r = _R("mix de fabrication (défaut du paramètre)")
    nom = ctx.par._noms.get("mix_fabrication")
    param = agb.all_params().get(nom)
    if param is None:
        return r.ignore("paramètre introuvable")
    if str(param.default).upper() in ("CN", "CHINA"):
        return r.echec(f"défaut = « {param.default} » alors que les modules "
                       f"sont assemblés en Allemagne")
    return r.ok(f"défaut = « {param.default} »")


# ══════════════════════════════════════════════════════════════════════════
# Transposition territoriale et littérature
# ══════════════════════════════════════════════════════════════════════════
def t_iles_coherentes():
    """Le tableau des îles se recale bien sur Raiatea, et rien n'est inventé.

    Trois pièges, tous déjà rencontrés dans la version notebook : un signe de
    latitude inversé (Katiu donnée à +16° N), un facteur d'émission recopié à
    la main au lieu d'être lu dans `electricite`, et un calibrage de distance
    qui ne retombe plus sur les 220 km de la route Papeete → Uturoa.
    """
    r = _R("îles cohérentes")
    iles = territoire.donnees_iles(verbeux=False)

    if len(iles) != 54:
        return r.echec(f"{len(iles)} îles au lieu de 54")
    if not iles["ile"].is_unique:
        doublons = iles.loc[iles["ile"].duplicated(), "ile"].tolist()
        return r.echec(f"doublons : {doublons}")
    if (iles["lat"] >= 0).any() or (iles["lon"] >= 0).any():
        mauvaises = iles.loc[(iles["lat"] >= 0) | (iles["lon"] >= 0), "ile"]
        return r.echec(f"coordonnée hors hémisphère sud-ouest : "
                       f"{mauvaises.tolist()}")

    ref = iles.set_index("ile").loc[territoire.ILE_REFERENCE]
    if abs(ref["dist_goelette_km"] - territoire.DIST_REFERENCE_KM) > 1:
        return r.echec(f"calibrage du détour : {ref['dist_goelette_km']:.0f} km "
                       f"au lieu de {territoire.DIST_REFERENCE_KM:.0f}")
    from .parametres import PRODUCTIBLE_P0 as P0_PRODUCTIBLE   # lu à l'appel
    if abs(ref["p0_kwh_kwc_an"] - P0_PRODUCTIBLE) > 1e-6:
        return r.echec(f"recalage on-site : P₀ Raiatea = "
                       f"{ref['p0_kwh_kwc_an']:.1f} au lieu de "
                       f"{P0_PRODUCTIBLE:.1f}")

    connus = set(electricite.FE_ARCHIPELS.values())
    inconnus = sorted(set(iles["fe_mix"]) - connus)
    if inconnus:
        return r.echec(f"facteur(s) d'émission absent(s) de "
                       f"electricite.FE_ARCHIPELS : {inconnus}")
    return r.ok(f"54 îles, détour ×{territoire.facteur_detour():.2f}, "
                f"{iles['fe_mix'].nunique()} FE distincts")


def t_nasa_power_coherent(seuil_ecart=10.0, pearson_min=0.70):
    """Le ratio PVsyst par île tient face à une source d'irradiation indépendante.

    Ce test ne valide pas le productible ABSOLU — il vient de la mesure on-site
    de Raiatea. Il valide la seule chose que PVsyst apporte : la répartition des
    îles entre elles. Si quelqu'un corrige une coordonnée, ajoute une île ou
    retouche la colonne `pvsyst_kwh_an`, c'est ici que ça se voit.

    Les deux sources sont d'accord sur l'ordre (corrélation) et à moins de
    10 % près île par île. Au-delà, ce n'est plus un désaccord de méthode :
    c'est une erreur de saisie quelque part.
    """
    r = _R("productible : PVsyst vs NASA POWER")
    tab = territoire.comparer_nasa_power(verbeux=False)

    pearson = tab.attrs.get("pearson")
    if pearson is None or pearson < pearson_min:
        return r.echec(f"corrélation {pearson:.3f} < {pearson_min:.2f} : les "
                       f"deux sources ne classent plus les îles pareil")

    hors = tab[tab["ecart_%"].abs() > seuil_ecart]
    if len(hors):
        pire = hors.iloc[0]
        return r.echec(f"{len(hors)} île(s) au-delà de ±{seuil_ecart:.0f} % — "
                       f"pire : {pire['ile']} {pire['ecart_%']:+.1f} %")

    ref = tab[tab["ile"] == territoire.ILE_REFERENCE]
    if len(ref) != 1 or abs(float(ref["ecart_%"].iloc[0])) > 1e-9:
        return r.echec("l'île de référence doit avoir un écart nul par "
                       "construction (les deux ratios y valent 1)")

    return r.ok(f"r = {pearson:.2f} | écart absolu moyen "
                f"{tab['ecart_%'].abs().mean():.1f} %, max "
                f"{tab['ecart_%'].abs().max():.1f} % ({tab['ile'].iloc[0]}) | "
                f"pente {tab.attrs['pente']:.2f}")


def t_co2_evite_coherent(ctx, jeux):
    """CO₂ évité et temps de retour se déduisent bien de la même énergie.

    Le piège : prendre le productible BRUT au numérateur du CO₂ évité et
    l'énergie NETTE au dénominateur du GWP. La consommation des auxiliaires
    serait alors comptée deux fois, et le temps de retour légèrement flatté.
    """
    r = _R("CO₂ évité cohérent")
    tab = territoire.co2_evite(ctx, jeux, verbeux=False)
    fe = float(tab["FE substitué kg/kWh"].iloc[0])

    for _, ligne in tab[tab["code"] != "PARC"].iterrows():
        e_an_kwh = ligne["E nette MWh/an"] * 1000.0
        gwp = ligne["GWP g/kWh"] / 1000.0

        attendu = e_an_kwh * (fe - gwp) / 1000.0
        if abs(ligne["Évité net t/an"] - attendu) > TOL * abs(attendu):
            return r.echec(f"{ligne['code']} : évité net "
                           f"{ligne['Évité net t/an']:.2f} contre "
                           f"{attendu:.2f} t/an recalculé")

        # L'énergie du tableau doit être celle de l'unité fonctionnelle.
        e_uf = territoire.energie_nette_kwh(ctx, jeux[ligne["modalite"]])
        if abs(e_an_kwh * ligne["duree_vie_an"] - e_uf) > TOL * e_uf:
            return r.echec(f"{ligne['code']} : énergie du tableau "
                           f"{e_an_kwh * ligne['duree_vie_an']:,.0f} kWh "
                           f"≠ unité fonctionnelle {e_uf:,.0f} kWh")

        retour = ligne["Empreinte totale t"] * 1000.0 / (attendu * 1000.0)
        if abs(ligne["Retour carbone an"] - retour) > TOL * retour:
            return r.echec(f"{ligne['code']} : retour "
                           f"{ligne['Retour carbone an']:.2f} contre "
                           f"{retour:.2f} an")

    parc = tab[tab["code"] == "PARC"].iloc[0]
    quatre = tab[tab["code"] != "PARC"]
    if not (quatre["GWP g/kWh"].min() <= parc["GWP g/kWh"]
            <= quatre["GWP g/kWh"].max()):
        return r.echec(f"GWP du parc {parc['GWP g/kWh']:.1f} g hors de "
                       f"[{quatre['GWP g/kWh'].min():.1f} ; "
                       f"{quatre['GWP g/kWh'].max():.1f}]")
    return r.ok(f"parc : {parc['Évité net t/an']:.1f} t/an évitées, "
                f"retour {parc['Retour carbone an']:.2f} an")


def t_politique_tirage(ctx, jeux):
    """Le Monte-Carlo tire ce qu'il doit tirer, et rien d'autre.

    Deux bugs que ce test rend impossibles :

    1. échantillonner un DÉNOMBREMENT. Le modèle produirait « 19,4 modules »,
       et la bande d'incertitude publiée contiendrait une variance inventée ;
    2. échantillonner une masse propre à une configuration DANS LES BORNES
       D'UNE AUTRE. Les bornes du registre sont celles de S2 : lancé sur S1,
       l'ancien tirage aurait cherché 718 kg d'aluminium dans [576 ; 637].
    """
    r = _R("politique de tirage Monte-Carlo")
    libelle = next(l for l in jeux if DONNEES.get(l, {}).get("code") == "SH81")
    X, Y = incertitude.echantillon(ctx, jeux[libelle], n=60, seed=0,
                                   verbeux=False)

    if len(X) != 60 or len(Y) != 60:
        return r.echec(f"{len(X)} tirages et {len(Y)} résultats pour 60 demandés")

    tires = set(X.columns)
    fuites = tires & set(incertitude.PARAMS_FIGES)
    if fuites:
        return r.echec(f"paramètre(s) figé(s) pourtant tiré(s) : {sorted(fuites)}")
    scenarios = tires & set(parametres.SCENARIOS)
    if scenarios:
        return r.echec(f"axe(s) de scénario tiré(s) : {sorted(scenarios)}")

    # Règle de sécurité : ce que la configuration renseigne est une donnée.
    # Sans elle, les paramètres parasol injectés par `modalites.py` (épaisseur
    # de verre, cadre alu surfacique…) étaient tirés sur la loi générique de
    # parasol, ce qui jetait nos mesures.
    jetees = (tires & set(jeux[libelle])
              - set(incertitude.PARAMS_RELATIFS)
              - set(incertitude.PARAMS_ECHANTILLONNES))
    if jetees:
        return r.echec(f"donnée(s) de la configuration remplacée(s) par un "
                       f"tirage : {sorted(jetees)}")
    if not set(incertitude.PARAMS_ECHANTILLONNES) <= tires:
        manquants = sorted(set(incertitude.PARAMS_ECHANTILLONNES) - tires)
        return r.echec(f"paramètre(s) à tirer malgré la modalité, non tiré(s) : "
                       f"{manquants}")

    registre = agb.all_params()
    for nom in incertitude.PARAMS_RELATIFS:
        if nom not in X.columns or nom not in jeux[libelle]:
            continue
        param = registre[nom]
        echelle = float(jeux[libelle][nom]) / float(param.default)
        attendu = (param.min * echelle, param.max * echelle)
        obtenu = (float(X[nom].min()), float(X[nom].max()))
        if obtenu[0] < attendu[0] - 1e-6 or obtenu[1] > attendu[1] + 1e-6:
            return r.echec(
                f"{nom} : tiré dans [{obtenu[0]:.4g} ; {obtenu[1]:.4g}] alors "
                f"que la configuration impose [{attendu[0]:.4g} ; "
                f"{attendu[1]:.4g}] (valeur {jeux[libelle][nom]:.4g})")
        if abs(float(X[nom].mean()) / float(jeux[libelle][nom]) - 1) > 0.15:
            return r.echec(f"{nom} : moyenne tirée {X[nom].mean():.4g} loin de "
                           f"la valeur de la configuration "
                           f"{jeux[libelle][nom]:.4g}")

    if not tires:
        return r.echec("aucun paramètre tiré — la bande d'incertitude serait nulle")
    donnees = len(set(jeux[libelle]) - tires)
    return r.ok(f"{len(tires)} tirés, {len(incertitude.PARAMS_FIGES)} figés, "
                f"{len(incertitude.PARAMS_RELATIFS)} recentrés, "
                f"{donnees} tenus pour données de la configuration")


def t_litterature_harmonisation():
    """L'harmonisation est bien une renormalisation, pas une correction.

    Trois contrôles, dans l'ordre d'importance :

    1. la formule — pour CHAQUE référence, harmonisé = publié × productible
       ÷ productible de référence. Si un seul écart apparaît, la fonction fait
       autre chose que changer de dénominateur ;
    2. les deux productibles recalculés depuis les articles le 15/09/2026. Les
       valeurs du classeur (1 550 et 1 933) sont des pièges documentés : le
       premier n'est nulle part dans Cromratie, le second divise la production
       de Cirata par sa limite AC de contrat (145 MWac) et non par sa puissance
       crête (192,5 MWp). Ce test existe pour qu'elles ne reviennent pas ;
    3. le kg Al/kWc de NOS plateformes, qui doit venir de `modalites.DONNEES`.
       La figure du manuscrit divisait une seule masse (606,4 kg) par les
       quatre puissances : une seule des quatre valeurs était juste.
    """
    r = _R("littérature harmonisée")
    tab = litterature.harmoniser(verbeux=False)
    reference = tab.attrs["productible_ref"] * tab.attrs["duree_ref"]

    # 1. la formule
    for _, ligne in tab.dropna(subset=["GWP harmonisé g/kWh"]).iterrows():
        attendu = (ligne["GWP publié g/kWh"] * ligne["Productible kWh/kWc/an"]
                   * ligne["Durée de vie an"] / reference)
        if abs(ligne["GWP harmonisé g/kWh"] - attendu) > 0.05:
            return r.echec(f"{ligne['cle']} : harmonisé "
                           f"{ligne['GWP harmonisé g/kWh']:.2f} contre "
                           f"{attendu:.2f} recalculé")

    # 2. les productibles relus dans les articles
    attendus = {"Cromratie": (1166.5, "175 GWh/an ÷ 150 MW crête, Tab. 1"),
                "Budi": (1455.5, "7 005 878 243 kWh ÷ 25 ans ÷ 192,5 MWp"),
                "Frehner": (1388.0, "94 g/kWh publiés → 130,5 g harmonisés")}
    indexe = tab.set_index("cle")
    for cle, (attendu, origine) in attendus.items():
        if cle not in indexe.index:
            return r.echec(f"référence « {cle} » disparue du benchmark")
        valeur = float(indexe.loc[cle, "Productible kWh/kWc/an"])
        if abs(valeur - attendu) > 1.0:
            return r.echec(f"{cle} : productible {valeur:.0f} au lieu de "
                           f"{attendu:.0f} kWh/kWc/an ({origine})")

    # 3. l'aluminium de NOS plateformes vient du modèle
    alu = litterature.aluminium_par_kwc()
    for donnees in DONNEES.values():
        attendu = donnees["alu_structure"] / donnees["kwc"]
        if abs(alu[donnees["code"]] - attendu) > 1e-9:
            return r.echec(f"{donnees['code']} : {alu[donnees['code']]:.1f} "
                           f"kg Al/kWc au lieu de {attendu:.1f}")
    if len({round(v, 3) for v in alu.values()}) != len(alu):
        return r.echec("deux configurations affichent le même kg Al/kWc — "
                       "signe qu'une seule masse d'aluminium est divisée par "
                       "les quatre puissances (le bug de la figure du manuscrit)")

    # 4. la typologie est complète : une couleur par catégorie utilisée
    sans_couleur = sorted(set(tab["categorie"]) - set(litterature.COULEURS_CATEGORIES))
    if sans_couleur:
        return r.echec(f"catégorie(s) sans couleur : {sans_couleur}")

    supposes = tab.loc[tab["fiabilite"] != "solide", "cle"].tolist()
    return r.ok(f"{len(tab)} références, "
                f"{int(tab['dans_article'].sum())} dans la figure, "
                f"harmonisées à {tab.attrs['productible_ref']:.0f} kWh/kWc/an"
                + (f" — sur hypothèse : {supposes}" if supposes else ""))


# ══════════════════════════════════════════════════════════════════════════
# Exécution
# ══════════════════════════════════════════════════════════════════════════
def tout(ctx, jeux, ref=None, verbeux=True):
    """Lance toute la batterie et renvoie un DataFrame de résultats."""
    import pandas as pd

    ref = ref or next(iter(jeux))
    valeurs = jeux[ref]

    plan = [
        (t_composition_somme, ()),
        (t_masse_module, (ctx, jeux)),
        (t_masse_systeme, (ctx, jeux)),
        (t_contribution_exacte, (ctx, valeurs)),
        (t_axe_non_attribue, (ctx, valeurs)),
        (t_axe_deterministe, (ctx, valeurs)),
        (t_unite_fonctionnelle, (ctx, valeurs)),
        (t_reproductibilite, (ctx, valeurs)),
        (t_monotonie_duree_vie, (ctx, valeurs)),
        (t_monotonie_productible, (ctx, valeurs)),
        (t_monotonie_alu, (ctx, valeurs)),
        (t_eol_signes, (ctx, valeurs)),
        (t_pas_d_impact_negatif, (ctx, valeurs)),
        (t_homogeneite_modalites, (ctx, jeux)),
        (t_nominal_dans_les_bornes, (ctx, jeux)),
        (t_facteur_aluminium, (ctx,)),
        (t_cable_fiche_fabricant, ()),
        (t_cables_methode_commune, ()),
        (t_ancrage_quincaillerie, ()),
        (t_activites_epinglees, (ctx,)),
        (t_anodisation, (ctx,)),
        (t_scenarios_surchargeables, ()),
        (t_gel_temporaire, ()),
        (t_scenarios_ont_un_effet, (ctx, valeurs)),
        (t_auxiliaires, (ctx, valeurs)),
        (t_unites_datasets, (ctx,)),
        (t_decharges_resolues, (ctx,)),
        (t_mix_fabrication, (ctx,)),
        (t_iles_coherentes, ()),
        (t_nasa_power_coherent, ()),
        (t_co2_evite_coherent, (ctx, jeux)),
        (t_politique_tirage, (ctx, jeux)),
        (t_litterature_harmonisation, ()),
    ]

    lignes = []
    for fonction, args in plan:
        try:
            res = fonction(*args)
        except Exception as err:            # noqa: BLE001
            res = _R(fonction.__name__).echec(f"{type(err).__name__}: {err}")
        lignes.append({"test": res.nom, "etat": res.etat, "detail": res.message})
        if verbeux:
            marque = {"OK": "✓", "ÉCHEC": "✗", "IGNORÉ": "–"}[res.etat]
            print(f" {marque} {res.nom:<42} {res.message}")

    df = pd.DataFrame(lignes)
    n_ko = int((df["etat"] == "ÉCHEC").sum())
    if verbeux:
        print(f"\n{len(df) - n_ko}/{len(df)} tests passés"
              + (f" — {n_ko} ÉCHEC(S)" if n_ko else " — tout est vert"))
    return df
