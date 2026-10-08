"""
Pont vers parasol-lca : on ne prend QUE les briques dont on a besoin.

Réponse aux commentaires 3 et 4 du reviewer :

* on n'utilise PAS `[parasol] Full PV system` — on assemble le nôtre
  (`systeme.py`), ce qui rend structurellement impossible le double comptage ;
* on n'utilise PAS `[parasol] photovoltaics, electric installation per kg` :
  ce poste (câblage forfaitaire ecoinvent 3 kWp) ferait doublon avec notre
  câble sous-marin + câblage module→onduleur, dont les hypothèses sont
  spécifiques au site ;
* on n'utilise PAS `[parasol] PV mounting system` : parasol ne modélise qu'un
  montage sol/toiture, notre structure flottante est explicite (`structure.py`).

Briques réellement reprises :
  - le panneau PV « adjusted » (paramétré : verre, cadre, argent, wafer, mix
    électrique de fabrication…) ;
  - l'onduleur au kg, interpolé entre 2,5 kW et 500 kW selon la puissance ;
  - le mix électrique de fabrication (activité switch).

Ce module résout aussi les NOMS des paramètres parasol, qui changent selon la
version (`Power_plant_capacity` vs `power_plant_installed_capacity`…). Le reste
du package manipule les objets `ParamDef`, jamais les chaînes de caractères.
"""

from __future__ import annotations

from types import SimpleNamespace

import lca_algebraic as agb

from . import config

# ── Noms candidats des paramètres parasol, par rôle ────────────────────────
# Le premier trouvé dans agb.all_params() gagne.
#
# ⚠ Seuls figurent ici les paramètres réellement créés par les BRIQUES qu'on
# reprend (panneau, onduleur, mix électrique). Les paramètres « système » de
# parasol — puissance de centrale, rendement, durée de vie, productible — ne
# sont instanciés que par son `Full PV system` et ses modèles d'impact, que
# nous ne construisons pas. On les déclare donc nous-mêmes dans
# `parametres.py` (`p_install_kwc`, `rendement_module`, `duree_vie_an`,
# `productible_kwh_kwc_an`), ce qui a l'avantage d'être indépendant de la
# version de parasol installée.
CANDIDATS_PARAMS = {
    "epaisseur_verre": ["glass_thickness", "Glass_thickness"],
    "cadre_alu_surfacique": ["aluminium_frame_surfacic_weight",
                             "Aluminium_frame_surfacic_weight"],
    "bifacial": ["has_bifacial_modules", "Bifaciale_modules", "bifaciale_modules"],
    "mix_fabrication": ["manufacturing_electricity_mix", "Manufacturing_electricity_mix"],
    "argent": ["silver_content", "Silver_content"],
    "epaisseur_wafer": ["wafer_thickness", "Wafer_thickness"],
    "taux_recyclage": ["recycling_rate", "Recycling_rate"],
    # Puissance UNITAIRE de l'onduleur : elle pilote l'interpolation de la
    # composition matière entre le modèle 2,5 kW et le modèle 500 kW. Pour des
    # micro-onduleurs il faut y mettre la puissance d'UN micro-onduleur
    # (Deye SUN-M80G4 ≈ 0,8 kW), surtout pas celle de la plateforme.
    "puissance_onduleur": ["inverter_power_capacity", "Inverter_power_capacity",
                           "Power_plant_capacity", "power_plant_installed_capacity"],
}

# ── Noms candidats des activités parasol reprises ──────────────────────────
CANDIDATS_PANNEAU = [
    f"{config.PREFIXE_PARASOL}photovoltaic panel production, single-Si wafer - adjusted",
    f"{config.PREFIXE_PARASOL}photovoltaic panel production, mono-Si wafer - adjusted",
    f"{config.PREFIXE_PARASOL}photovoltaic panel production, multi-Si wafer - adjusted",
]
CANDIDATS_ONDULEUR = [
    f"{config.PREFIXE_PARASOL}Inverter production, P kW per kg",
]
CANDIDATS_ELEC = [
    f"{config.PREFIXE_PARASOL}electricity",
]

# Activités parasol volontairement écartées (tracées ici pour le rapport).
ECARTEES = [
    f"{config.PREFIXE_PARASOL}Full PV system",
    f"{config.PREFIXE_PARASOL}PV mounting system",
    f"{config.PREFIXE_PARASOL}photovoltaics, electric installation per kg",
    f"{config.PREFIXE_PARASOL}PV impact per kWp installed",
    f"{config.PREFIXE_PARASOL}PV impact per kWh",
]


def preparer(ctx):
    """Crée les briques parasol nécessaires et résout ses paramètres.

    Returns
    -------
    (conf, par) : contexte parasol_lca, namespace de paramètres résolus
    """
    conf = _creer_briques(ctx.db)
    par = _resoudre_params()
    _verifier(par)
    return conf, par


def _creer_briques(db):
    """Construit uniquement panneau + onduleur + mix électrique si possible.

    On tente d'abord les constructeurs internes de parasol (`_ensure_*`), ce
    qui évite de créer son `Full PV system`, son montage générique et son
    installation électrique. Si l'API interne a changé, on retombe sur
    `parasol_lca.create()` : les activités inutiles existent alors dans la base
    mais ne sont référencées nulle part dans notre modèle — elles n'entrent
    donc dans aucun calcul.
    """
    import parasol_lca

    conf = parasol_lca.ParasolLCA.from_dict({
        "target_database": db,
        "version": config.EI_VERSION,
        "biosphere": config.BIOSPHERE,
        "technosphere": config.EI,
    })

    faits = _construire_briques_ciblees(conf)
    if faits:
        print(f"Briques parasol créées à la carte : {', '.join(faits)}")
        print("  (Full PV system, montage générique et installation électrique "
              "NON créés)")
    else:
        print("⚠ constructeurs internes de parasol non identifiés dans cette "
              "version -> repli sur parasol_lca.create().")
        print("  Tout est créé, mais notre système ne référence que le panneau, "
              "l'onduleur et le mix électrique : aucun double comptage.")
        print("  Pour passer en mode ciblé, lance parasol_bridge.inspecter() et "
              "complète CONSTRUCTEURS.")
        parasol_lca.create(conf)

    return conf


# Mots-clés permettant de retrouver les constructeurs internes de parasol,
# dont les noms varient selon la version (`_ensure_pv_panel`,
# `_ensure_panel_adjusted`, `_ensure_pv_panels`…).
CONSTRUCTEURS = {
    "mix électrique": ["electricity"],
    "panneau": ["panel"],
    "onduleur": ["inverter"],
}
# Constructeurs à ne JAMAIS appeler : ils créent ce qu'on remplace.
INTERDITS = ["pv_system", "impact_model", "mounting", "electrical_installation"]


def _construire_briques_ciblees(conf):
    """Appelle uniquement les `_ensure_*` correspondant à nos trois briques."""
    try:
        from parasol_lca import _activities as pa
    except Exception:
        return []

    disponibles = [n for n in dir(pa) if n.startswith("_ensure")]
    faits = []
    for libelle, motifs in CONSTRUCTEURS.items():
        candidats = [n for n in disponibles
                     if any(m in n.lower() for m in motifs)
                     and not any(i in n.lower() for i in INTERDITS)]
        for nom_fonction in candidats:
            try:
                getattr(pa, nom_fonction)(conf)
                faits.append(f"{libelle} ({nom_fonction})")
                break
            except TypeError:
                continue          # signature différente : on essaie le suivant
            except Exception as err:   # noqa: BLE001
                print(f"  ⚠ {nom_fonction} a échoué ({type(err).__name__}: {err})")
                continue

    # Il faut au moins le panneau ET l'onduleur, sinon on repasse par create()
    if len(faits) < len(CONSTRUCTEURS):
        return []
    return faits


def inspecter():
    """Affiche l'API de la version de parasol-lca installée.

    À lancer si le mode ciblé ne s'active pas : la sortie dit quels
    constructeurs et quels paramètres existent réellement.
    """
    import parasol_lca
    from parasol_lca import _activities as pa, _parameters as pp

    print("parasol_lca :", getattr(parasol_lca, "__version__", "version inconnue"),
          "|", getattr(parasol_lca, "__file__", ""))
    print("\nConstructeurs d'activités (_activities) :")
    for nom_fonction in sorted(n for n in dir(pa) if n.startswith("_ensure")):
        print("   ", nom_fonction)
    print("\nConstructeurs de paramètres (_parameters) :")
    for nom_fonction in sorted(n for n in dir(pp) if n.startswith("_ensure")):
        print("   ", nom_fonction)


# Bornes d'INCERTITUDE resserrées sur les paramètres parasol qu'on utilise.
# Celles de parasol sont des plages de validité génériques (l'onduleur va de
# 2,5 kW à 500 kW) : laissées telles quelles, elles dominent artificiellement
# le tornado et le Monte-Carlo, qui les prennent pour de l'incertitude.
BORNES_PARASOL = {
    "puissance_onduleur": (0.5, 2.0),        # micro-onduleur Deye ≈ 0,8 kW
    "cadre_alu_surfacique": (1.0, 2.0),      # kg/m², cadre d'un module c-Si
}


def _resoudre_params():
    """Associe chaque rôle au ParamDef réellement présent dans le registre."""
    tous = agb.all_params()
    par = SimpleNamespace()
    par._noms = {}
    par._manquants = []

    for role, candidats in CANDIDATS_PARAMS.items():
        trouve = next((c for c in candidats if c in tous), None)
        if trouve is None:
            setattr(par, role, None)
            par._manquants.append((role, candidats))
        else:
            param = tous[trouve]
            if role in BORNES_PARASOL:
                param.min, param.max = BORNES_PARASOL[role]
            # units_enabled : on manipule la grandeur avec son unité
            valeur = param.with_unit() if agb.Settings.units_enabled else param
            setattr(par, role, valeur)
            par._noms[role] = trouve

    return par


def _verifier(par):
    if par._manquants:
        print("⚠ paramètres parasol introuvables (version différente ?) :")
        for role, candidats in par._manquants:
            print(f"    {role:22s} — essayés : {candidats}")
    print("Paramètres parasol résolus : "
          + ", ".join(f"{r}→{n}" for r, n in sorted(par._noms.items())))


def panneau(ctx):
    """Activité panneau PV de parasol (m²)."""
    return _premier(ctx, CANDIDATS_PANNEAU, "panneau PV parasol")


def onduleur(ctx):
    """Activité onduleur de parasol (kg), interpolée selon la puissance."""
    return _premier(ctx, CANDIDATS_ONDULEUR, "onduleur parasol")


def mix_electrique(ctx):
    """Activité switch du mix électrique de fabrication (kWh)."""
    return _premier(ctx, CANDIDATS_ELEC, "mix électrique parasol")


def _premier(ctx, candidats, libelle):
    for nom_act in candidats:
        try:
            act = agb.findActivity(nom_act, db_name=ctx.db, single=True)
            print(f"  {libelle:26s} -> {act['name']}")
            return act
        except Exception:
            continue
    raise LookupError(
        f"Aucune activité trouvée pour « {libelle} ». Candidats : {candidats}. "
        "Liste les activités de la base avec resultats.lister_activites(ctx).")


def valeurs_parasol(par, **roles):
    """Traduit un dict {rôle: valeur} en {nom_de_paramètre_parasol: valeur}.

    C'est ce qui permet aux modalités (`modalites.py`) de ne jamais écrire un
    nom de paramètre parasol en dur.

    >>> valeurs_parasol(par, p_install=7.9, duree_vie=30)
    {'Power_plant_capacity': 7.9, 'Power_plant_lifetime': 30}
    """
    sortie = {}
    for role, valeur in roles.items():
        nom_param = par._noms.get(role)
        if nom_param is None:
            raise KeyError(
                f"Rôle « {role} » non résolu dans cette version de parasol-lca "
                f"(candidats : {CANDIDATS_PARAMS.get(role)})")
        sortie[nom_param] = valeur
    return sortie


def valeurs_possibles(par, role):
    """Valeurs admises par un paramètre enum de parasol.

    >>> parasol_bridge.valeurs_possibles(ctx.par, "mix_fabrication")
    ['CN', 'RER', 'US', ...]
    """
    nom_param = par._noms.get(role)
    if nom_param is None:
        raise KeyError(f"Rôle « {role} » non résolu.")
    param = agb.all_params().get(nom_param)
    return list(getattr(param, "values", []) or [])


def figer_puissance_onduleur(par, puissance_kw=0.8):
    """Fige la puissance unitaire de l'onduleur sur la fiche fabricant.

    Deye SUN-M80G4-EU-Q0 : puissance nominale de sortie **800 W**, masse 3 kg,
    durée de vie de conception 25 ans, garantie 15 ans (fiche Deye). Ce n'est
    pas une grandeur incertaine, c'est une caractéristique de catalogue : elle
    n'a rien à faire dans un tornado ni dans un Monte-Carlo.

    Ce paramètre pilote l'interpolation, par parasol, de la composition matière
    de l'onduleur entre un modèle 2,5 kW et un modèle 500 kW.

    ⚠ LIMITE À DÉCLARER. 0,8 kW est SOUS la borne basse de l'interpolation
    (2,5 kW) : parasol extrapole donc, ou plus probablement sature. C'est ce
    qu'indiquait le tornado, où `inverter_power_capacity` balayait [0,5 ; 2]
    avec une amplitude de 0,000 % — le paramètre ne pilotait rien. Figer la
    valeur rend cette limite explicite au lieu de la laisser passer pour de la
    sensibilité nulle. Le vrai correctif serait un inventaire d'onduleur
    explicite, construit sur la fiche Deye plutôt que sur l'interpolation.
    """
    from lca_algebraic.params import DistributionType

    nom_param = par._noms.get("puissance_onduleur")
    param = agb.all_params().get(nom_param)
    if param is None:
        print("⚠ paramètre de puissance d'onduleur introuvable — non figé.")
        return None

    ancien = param.default
    param.default = puissance_kw
    param.min = param.max = puissance_kw
    # FIXED est ici le bon choix : contrairement aux axes de scénario, on ne
    # compare jamais deux puissances d'onduleur. Le paramètre ne doit donc plus
    # être ni tiré au sort, ni surchargé.
    param.distrib = DistributionType.FIXED
    print(f"  onduleur : {nom_param} = {puissance_kw} kW figé "
          f"(était {ancien}) — Deye SUN-M80G4-EU-Q0, 800 W de sortie nominale")
    return puissance_kw


def figer_mix_fabrication(par, preferences=("DE", "Germany", "RER", "EU",
                                            "ENTSOE", "Europe")):
    """Fixe le mix électrique de FABRICATION des modules, et le sort du tirage.

    Deux problèmes réglés d'un coup.

    1. LA VALEUR. Les modules sont assemblés par CS Wismar, en Allemagne. Or
       le défaut du paramètre parasol est « CN » (mix chinois, très
       carboné) — ce qui n'a rien à voir avec notre chaîne. On retient la
       première valeur disponible dans `preferences`, en privilégiant un mix
       allemand s'il existe, sinon un mix européen.

    2. LA PORTÉE. Passer la valeur dans le dict de `modalites.py` ne suffisait
       PAS : `resultats._figer_hors_analyse` ne recalait que les valeurs
       numériques, et `oat_matrix` / le Monte-Carlo partent des valeurs PAR
       DÉFAUT des paramètres. Résultat, le résultat principal tournait sur le
       mix européen pendant que TOUTE l'analyse de sensibilité tournait sur le
       mix chinois — sans le moindre message. On écrit donc la valeur dans le
       `default` du paramètre.

    On met aussi sa distribution à FIXED : le lieu d'assemblage est un FAIT
    documenté (fiches CS Wismar), pas une incertitude. Le laisser variable
    faisait tirer au sort un pays de fabrication à chaque échantillon du
    Monte-Carlo, ce qui gonflait artificiellement la variance et polluait les
    indices de Sobol. Pour explorer un autre lieu de fabrication, c'est un
    SCÉNARIO : on passe la valeur explicitement à `systeme.impacts()`.
    """
    from lca_algebraic.params import DistributionType

    nom_param = par._noms.get("mix_fabrication")
    param = agb.all_params().get(nom_param)
    if param is None:
        print("⚠ paramètre de mix de fabrication introuvable — non figé.")
        return None

    admises = list(getattr(param, "values", []) or [])
    choix = next((v for v in preferences if v in admises), None)
    if choix is None:
        print(f"⚠ aucune des valeurs {preferences} n'existe pour "
              f"« {nom_param} ». Valeurs admises : {admises}. "
              f"Défaut inchangé ({param.default}).")
        return None

    ancien = param.default
    param.default = choix
    # ⚠ PAS de `distrib = FIXED` ici : cela rendrait le paramètre NON
    # MODIFIABLE, et un scénario « fabriqué ailleurs » deviendrait impossible à
    # calculer. Le mix figure dans `parametres.SCENARIOS` : il est figé
    # TEMPORAIREMENT par `parametres.scenarios_figes()`, le temps du tirage
    # aléatoire seulement.
    print(f"  mix de fabrication : {nom_param} = « {choix} » "
          f"(était « {ancien} ») — défaut du paramètre, hors tirage aléatoire. "
          f"Valeurs admises : {admises}")
    return choix
