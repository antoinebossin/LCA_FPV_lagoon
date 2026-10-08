"""
Résolution des activités ecoinvent de fond.

Un seul endroit où l'on écrit un nom de dataset ecoinvent. Chaque entrée liste
des candidats (nom, localisation) : le premier trouvé gagne, et le choix est
imprimé au run. Un dataset mal choisi ne peut donc plus se cacher dans une
cellule au milieu du notebook.

⚠ Le dataset d'enfouissement est ÉPINGLÉ (voir `DISPOSAL`) : les candidats
ecoinvent 3.11 diffèrent d'un facteur > 100 sur l'écotoxicité, et l'ancien
choix « par ordre d'itération de la base » n'était pas reproductible.
"""

from __future__ import annotations

from types import SimpleNamespace

import lca_algebraic as agb

from . import config

# ══════════════════════════════════════════════════════════════════════════
# Activités de fond — ÉPINGLÉES (version finale, 15/09/2026)
# ══════════════════════════════════════════════════════════════════════════
#
# Un rôle = UN dataset, nom ET géographie explicites, tels qu'observés dans
# ecoinvent 3.11 cut-off au run du 15/09/2026. Plus de liste de candidats, plus
# de balayage de secours : ce qui produit les chiffres du papier est écrit ici,
# et si un dataset manque, le run s'arrête au lieu d'en choisir un autre.
#
# POURQUOI LE BALAYAGE A ÉTÉ SUPPRIMÉ. Il était précieux pour DÉCOUVRIR ce que
# contenait la base, mais il choisissait « le premier par ordre alphabétique
# parmi ceux qui contiennent ces mots-clés ». Trois choix réels qu'il avait
# faits, tous faux et tous silencieux :
#   * decharge_plastique -> « waste plastic PLASTER » — un enduit, pas du
#     déchet plastique. C'est là que partaient les 504 kg de flotteurs ;
#   * enfouissement -> « residues, MSWI » — des mâchefers d'incinération ;
#   * decharge_metal -> une variante CH quand RoW existait.
# Aucun de ces choix n'apparaissait comme un problème : le run était vert.
#
# COMMENT AJOUTER OU CORRIGER UN RÔLE. `ecoinvent.chercher("mot-clé")` liste ce
# qui existe dans TA base ; `diagnostic_decharge()` et `diagnostic_aluminium()`
# donnent les inventaires complets par famille. On lit, on choisit, on épingle
# ici. C'est le seul endroit du package où l'on écrit un nom de dataset.
#
# ⚠ Ces noms valent pour ecoinvent 3.11 cut-off. Un changement de version peut
# les renommer : le run le dira immédiatement, par une LookupError explicite.

# ⚠ L'UNITÉ FAIT PARTIE DE L'IDENTIFIANT, au même titre que le nom et la
# localisation. En ecoinvent 3.11 plusieurs procédés multi-produits portent le
# MÊME nom et la MÊME géographie sous des unités différentes : la mise en
# décharge d'un déchet existe en kilogramme (le traitement) mais aussi en
# mégajoule et en kilowattheure (l'énergie récupérée du biogaz). Sans filtre
# d'unité, `findActivity(..., single=True)` en trouve trois et refuse de
# choisir — d'où des « introuvable » sur des datasets qui existent bel et bien,
# et que `diagnostic_decharge()` affiche pourtant.
KG, M2, MJ, KWH, TKM = ("kilogram", "square meter", "megajoule",
                        "kilowatt hour", "ton kilometer")

# rôle -> (nom exact, localisation exacte, unité exacte)
ACTIVITES = {
    # ── Matériaux ─────────────────────────────────────────────────────────
    # Aluminium de structure : 45 % du GWP, le dataset le plus sensible du
    # modèle. Le marché mondial est le seul « wrought alloy » de la 3.11 ; la
    # variante européenne est COMPOSÉE par `structure._aluminium_europeen`,
    # qui substitue l'origine du métal primaire dans la recette réelle du
    # marché mondial. Il n'y a donc pas de rôle « aluminium_rer ».
    "aluminium":        ("market for aluminium, wrought alloy", "GLO", KG),
    "eps":              ("market for polystyrene, expandable", "GLO", KG),
    "pehd":             ("market for polyethylene, high density, granulate", "GLO", KG),
    "inox":             ("market for steel, chromium steel 18/8", "GLO", KG),
    "acier":            ("market for steel, low-alloyed", "GLO", KG),
    "caoutchouc":       ("market for synthetic rubber", "GLO", KG),
    # Polyamide 6 — poulie d'ancrage (« Plastic Block » de la fiche Seaflex).
    # Seule la géographie RER existe en 3.11.
    "pa6":              ("market for nylon 6", "RER", KG),
    "cuivre":           ("market for copper, cathode", "GLO", KG),
    "verre_plat":       ("market for flat glass, uncoated", "RER", KG),
    "silicium_mg":      ("market for silicon, metallurgical grade", "GLO", KG),
    "argent":           ("market for silver", "GLO", KG),

    # ── Aluminium : briques de la variante européenne et du diagnostic ────
    # `aluminium_primaire` est le SEUL des trois qui entre dans un inventaire
    # (via la substitution d'origine). Les deux autres ne servent qu'à
    # `structure.facteurs_aluminium()`, le contrôle au kg.
    "aluminium_primaire":     ("market for aluminium, primary, ingot",
                               "IAI Area, EU27 & EFTA", KG),
    "aluminium_primaire_glo": ("market for aluminium, primary, ingot", "RoW", KG),
    # ⚠ DIAGNOSTIC SEULEMENT. Ce dataset ne décrit que la COLLECTE, le tri, le
    # nettoyage et le pressage de la ferraille — pas la refusion. D'où les
    # ~0,3 kg CO2-eq/kg qu'il affiche, là où de l'aluminium secondaire réel se
    # situe vers 0,5-1,5. Ne jamais l'utiliser comme fraction d'un alliage.
    "alu_secondaire":   ("treatment of aluminium scrap, post-consumer, "
                         "by collecting, sorting, cleaning, pressing", "RER", KG),
    # Anodisation des profilés — facturée à la SURFACE traitée (m²), pas à la
    # masse.
    "anodisation":      ("anodising, aluminium sheet", "RER", M2),

    # ── Fluides et énergie ────────────────────────────────────────────────
    "eau_douce":        ("market for tap water", "RoW", KG),
    "diesel_bateau":    ("diesel, burned in fishing vessel", "GLO", MJ),
    # Base du mix insulaire : production au fioul, recalée sur le facteur
    # d'émission ADEME Polynésie 2023 dans `electricite.py` (ecoinvent n'a pas
    # de mix « PF »). Le calage porte sur le CARBONE seulement.
    "elec_fioul":       ("electricity production, oil", "RoW", KWH),
    # Mix néo-zélandais : électricité du procédé de recyclage exporté.
    "elec_nz":          ("market for electricity, medium voltage", "NZ", KWH),

    # ── Électronique ──────────────────────────────────────────────────────
    "electronique":     ("market for electronics, for control units", "GLO", KG),
    "deee":             ("market for electronics scrap", "GLO", KG),

    # ── Transport : des SERVICES en t·km ──────────────────────────────────
    # Jamais « market for container ship », qui est le NAVIRE, en unité
    # « unit ». L'unité est vérifiée par `tests.t_unites_datasets`.
    "fret_maritime":    ("market for transport, freight, sea, container ship, "
                         "heavy fuel oil", "GLO", TKM),
    # Proxy de la goélette inter-îles : le ferry a un FE par t·km 5 à 10 fois
    # supérieur au porte-conteneurs, ce qui est le bon ordre de grandeur.
    "fret_goelette":    ("market for transport, freight, sea, ferry, "
                         "heavy fuel oil", "GLO", TKM),
    "fret_camion":      ("market for transport, freight, lorry, unspecified", "RER", TKM),
}

# ── Mise en décharge, PAR FRACTION MATIÈRE ────────────────────────────────
#
# ARCHÉTYPE RETENU : « sanitary landfill » pour les quatre fractions, décision
# du 15/09/2026. C'est une décharge GÉRÉE, avec collecte de lixiviat — le choix
# homogène et conservateur. La 3.11 offre aussi « inert material landfill »
# (confinement de déchet inerte, contexte suisse) et « unsanitary landfill »
# (non gérée, déclinée par classe de pluviométrie) ; mélanger les trois selon
# ce que le balayage trouvait rendait la comparaison entre fractions
# incohérente. À rediscuter si l'on documente le site réel de Raiatea.
#
# Ces quatre rôles sont OBLIGATOIRES : la ventilation par fraction est le cœur
# de la correction v22 (un dataset unique appliqué à toute la masse du module
# faisait traiter 390 kg de verre plat comme du plastique d'électronique, et
# rendait l'écotoxicité hypersensible au choix de dataset, +163 % entre deux
# candidats).
DECHARGE = {
    # Les deux vitres du module.
    "decharge_verre":     ("treatment of waste glass, sanitary landfill",
                           "GLO", KG),
    # Cadre alu, boulonnerie inox, chaîne, ancre, manille — et, depuis le
    # 15/09/2026, les fractions métalliques du module (silicium, cuivre,
    # argent, « autres »). Voir `fin_de_vie.FILIERE`.
    #
    # ⚠ RoW et pas CH : pas de raison d'importer un contexte suisse pour une
    # décharge polynésienne. Et surtout KG : ce même nom existe AUSSI en
    # mégajoule et en kilowattheure — ce sont les co-produits énergétiques du
    # procédé (valorisation du biogaz de décharge), pas le traitement d'une
    # masse. C'est cette homonymie qui faisait échouer la résolution.
    "decharge_metal":     ("treatment of waste aluminium, sanitary landfill",
                           "RoW", KG),
    # EVA, boîte de jonction, mousse EPS, peau MDPE, corde HMPE, poulie PA6,
    # élastique SBR.
    "decharge_plastique": ("treatment of waste plastic, mixture, sanitary landfill",
                           "RoW", KG),
    # Électronique des répéteurs uniquement : un boîtier CPL est bien du
    # plastique chargé, pas du métal massif.
    "decharge_deee":      ("treatment of waste plastic, consumer electronics, "
                           "sanitary landfill, wet infiltration class (500mm)",
                           "GLO", KG),
}


# ── Incinération, POUR LE SCÉNARIO DE SENSIBILITÉ DES FLOTTEURS ───────────
#
# Ces rôles ne servent QUE les modalités « incineration_flotteurs » de
# `fin_de_vie.py`. Ils sont épinglés comme les autres, mais sur des datasets
# polymère par polymère et non sur « plastic, mixture » : la mousse est du
# polystyrène et la peau du polyéthylène, et leur pouvoir calorifique comme
# leur stœchiométrie de combustion diffèrent de 10 %. Mélanger les deux dans
# un dataset moyen de plastique ferait exactement l'erreur que la ventilation
# par fraction de la v22 a corrigée côté décharge.
#
# POURQUOI POLYMÈRE PAR POLYMÈRE, ET PAS « plastic, mixture »
# La base offre `treatment of waste plastic, mixture, municipal incineration` en
# RoW, ce qui serait géographiquement plus proche de la Polynésie que le GLO des
# datasets purs. On ne le retient PAS, et c'est un arbitrage, pas une négligence :
#
#   * un mélange de plastiques contient du PVC. Son incinération émet donc du
#     chlore et des précurseurs de dioxines que de l'EPS, du MDPE et du SBR purs
#     NE PEUVENT PAS produire — il n'y a pas un atome de chlore dans ces trois
#     polymères. L'utiliser fabriquerait une chimie qui n'existe pas dans nos
#     flotteurs, et gonflerait la toxicité ;
#   * le flux qui domine le résultat, lui, est le CO2 fossile de combustion. Il
#     est purement stœchiométrique et IDENTIQUE dans les deux cas. Le dataset
#     moyen n'apporte donc rien là où ça compte, et fausse le reste.
#
# La chimie l'emporte sur la géographie. L'écart GLO/RoW ne porte que sur
# l'efficacité du traitement des fumées, soit un effet de second ordre sur un
# résultat dominé par le CO2.
#
# ⚠ L'INCOHÉRENCE DE LOCALISATION EST IMPOSÉE PAR LA BASE, pas choisie : les
# deux polymères purs n'existent qu'en GLO, et le caoutchouc n'existe PAS en GLO
# (RoW ou « Europe without Switzerland »). On prend donc GLO, GLO, RoW. À écrire
# dans les limites plutôt qu'à cacher.
#
# Pas de variante CH ni « FAE » (extraction des cendres volantes) : pas de raison
# d'importer un standard d'épuration suisse pour un hypothétique incinérateur
# polynésien. Et KG, parce que ces mêmes noms existent aussi en mégajoule et en
# kilowattheure (les co-produits énergétiques du procédé) : c'est cette
# homonymie qui fait échouer la résolution.
#
# CE QUE L'IEA PRESCRIT SUR LE CHOIX DU DATASET : RIEN.
# IEA-PVPS T12-18:2020, § 3.2.6 p. 21-22 : « The IEA PVPS Task 12 does not
# recommend any particular LCI database. » Le choix ne peut donc pas s'adosser à
# une prescription — il s'argumente sur la représentativité, comme ci-dessus.
#
#       >>> from acv_lagon import ecoinvent
#       >>> ecoinvent.diagnostic_incineration()   # pour revérifier un jour
# ✓ NOMS ET LOCALISATIONS VÉRIFIÉS SUR LA BASE le 05/10/2026, par
# `diagnostic_incineration()`. Ce ne sont plus des hypothèses. Deux corrections
# par rapport au premier jet :
#
#   * la mousse part sur « waste EXPANDED polystyrene » et non sur « waste
#     polystyrene ». Les deux existent en GLO, et le second aurait décrit du
#     polystyrène compact. Pour 231,8 kg de mousse de flotteur, le dataset
#     expansé est le bon : masse identique, mais procédé de collecte et
#     comportement en four différents ;
#   * les trois rôles sont en GLO ou RoW selon ce que la base offre, pas en RoW
#     partout comme épinglé d'abord. La 3.11 ne propose les deux polymères
#     qu'en GLO (plus une variante « FAE », extraction des cendres volantes,
#     réservée au contexte CH — écartée : pas de raison d'importer un standard
#     d'épuration suisse pour un hypothétique four polynésien).
#
# Les trois datasets ont un flux de référence NÉGATIF (signe -1) : c'est
# `signe_dechet` qui le gère dans `fin_de_vie._incinerer`.
INCINERATION = {
    "incineration_eps":  ("treatment of waste expanded polystyrene, "
                          "municipal incineration", "GLO", KG),
    "incineration_mdpe": ("treatment of waste polyethylene, "
                          "municipal incineration", "GLO", KG),
    # Élastique SBR de l'ancrage Seaflex. Ajouté le 05/10/2026 pour aligner la
    # sensibilité sur Seitz et al. 2026, qui incinèrent les élastomères.
    # Seul rôle des trois à exister en RoW — la base l'offre aussi en « Europe
    # without Switzerland », écarté pour la même raison que les variantes CH.
    "incineration_caoutchouc": ("treatment of waste rubber, unspecified, "
                                "municipal incineration", "RoW", KG),
}


# Rôle de repli de `fin_de_vie._decharge`. Avec les quatre rôles ci-dessus tous
# obligatoires, il ne devrait JAMAIS servir ; il reste par sécurité, et sert
# aussi à fixer la convention de signe des déchets (`signe_dechet`).
DISPOSAL = ("treatment of waste plastic, mixture, sanitary landfill", "RoW", KG)


def _chercher_exact(nom_act, loc, unite):
    """findActivity avec filtre d'unité, quelle que soit la version de la lib.

    `unit=` existe dans les versions récentes de lca_algebraic ; s'il n'est pas
    accepté, on filtre nous-mêmes sur la base. Ce n'est pas un repli sur un
    AUTRE dataset — c'est la même cible, cherchée autrement.
    """
    try:
        return agb.findActivity(nom_act, db_name=config.EI, loc=loc,
                                unit=unite, single=True)
    except TypeError:
        pass
    trouves = [a for a in _base()
               if a["name"] == nom_act
               and a.get("location") == loc
               and str(a.get("unit", "")) == unite]
    if len(trouves) == 1:
        return trouves[0]
    raise LookupError(f"{len(trouves)} correspondance(s) exactes")


def _trouver(role, cible):
    """Résout UNE cible (nom, localisation, unité). Échoue bruyamment sinon."""
    nom_act, loc, unite = cible
    try:
        act = _chercher_exact(nom_act, loc, unite)
    except Exception as err:      # noqa: BLE001
        raise LookupError(
            f"Rôle « {role} » : « {nom_act} | {loc} | {unite} » introuvable dans "
            f"{config.EI} ({type(err).__name__}). Les activités sont ÉPINGLÉES "
            f"depuis la VF : aucun repli automatique n'est tenté, pour qu'un "
            f"dataset ne puisse plus être choisi à ta place. "
            f"Lance ecoinvent.chercher('{nom_act.split(',')[0]}') pour voir ce "
            f"qui existe réellement, puis corrige ecoinvent.ACTIVITES."
        ) from err
    print(f"  {role:18s} -> {act['name']} | {act.get('location','')} "
          f"| {act.get('unit','')}")
    return act


_CACHE_BASE = None


def _base():
    global _CACHE_BASE
    if _CACHE_BASE is None:
        import brightway2 as bw
        _CACHE_BASE = list(bw.Database(config.EI))
    return _CACHE_BASE


def chercher(motif, unite=None, limite=30):
    """Liste les datasets de la base dont le nom contient `motif`.

    À utiliser quand un rôle reste introuvable :

    >>> ecoinvent.chercher("freight, sea")
    """
    motif = motif.lower()
    for act in sorted(_base(), key=lambda a: a["name"]):
        if motif not in act["name"].lower():
            continue
        if unite and unite not in str(act.get("unit", "")).lower():
            continue
        print(f"  {act['name']} | {act.get('location','')} | {act.get('unit','')}")
        limite -= 1
        if limite <= 0:
            print("  ...")
            return


def resoudre() -> SimpleNamespace:
    """Résout toutes les activités de fond et les renvoie dans un namespace.

    Tous les rôles sont obligatoires : un dataset manquant arrête le run.
    """
    print(f"Activités ecoinvent de fond ({config.EI}, épinglées) :")
    ei = SimpleNamespace()
    for role, cible in ACTIVITES.items():
        setattr(ei, role, _trouver(role, cible))

    print("  décharges par fraction matière :")
    for role, cible in DECHARGE.items():
        setattr(ei, role, _trouver(role, cible))
    ei.enfouissement = _trouver("enfouissement", DISPOSAL)

    # Incinération : rôles OPTIONNELS, seule exception à la règle « tout rôle
    # est obligatoire ». Ils ne servent qu'une modalité de sensibilité ; faire
    # échouer tout le run parce qu'un nom de dataset d'incinération diffère
    # dans une version de la base punirait les trois modalités principales
    # pour une variante accessoire. L'échec est reporté au moment où la
    # modalité est effectivement construite, avec un message qui dit quoi
    # faire (cf. `fin_de_vie._incinerer`).
    print("  incinération (scénario de sensibilité, optionnel) :")
    for role, cible in INCINERATION.items():
        try:
            setattr(ei, role, _trouver(role, cible))
        except LookupError:
            setattr(ei, role, None)
            print(f"    ⚠ {role:18s} -> INTROUVABLE. Les modalités "
                  f"« incineration_flotteurs » seront indisponibles. Lance "
                  f"ecoinvent.diagnostic_incineration() et corrige "
                  f"ecoinvent.INCINERATION.")

    # Convention déchets ecoinvent : certains traitements ont un flux de
    # référence NÉGATIF ; il faut alors les appeler avec un montant négatif,
    # sinon le procédé tourne à l'envers et son impact devient négatif.
    ei.signe_dechet = signe_dechet(ei.enfouissement)
    ei.signe_deee = signe_dechet(ei.deee)
    print(f"  signe du flux déchet : enfouissement {ei.signe_dechet:+.0f}, "
          f"DEEE {ei.signe_deee:+.0f}")

    return ei


def signe_dechet(act):
    """+1 ou -1 selon la convention de signe du produit de référence.

    Beaucoup de datasets `treatment of ...` ont un produit de référence à
    -1 kg : le déchet est un *output négatif*. Pour en traiter 1 kg il faut
    alors écrire un échange de -1 kg, sinon le procédé tourne à l'envers et son
    impact ressort négatif — le fameux « crédit » qui n'en est pas un.
    """
    if act is None:
        return 1.0
    prod = next(iter(act.production()), None)
    return -1.0 if (prod is not None and prod.get("amount", 1) < 0) else 1.0


# rétrocompatibilité
_signe_dechet = signe_dechet

# Ancien nom : `CANDIDATS` était un dict rôle -> LISTE de candidats. Il n'y a
# plus qu'une cible par rôle ; l'alias garde la forme « liste » pour ne pas
# casser une cellule qui l'inspecterait.
CANDIDATS = {role: [(nom, loc)] for role, (nom, loc, _u) in ACTIVITES.items()}


def verifier(verbeux=True) -> dict:
    """Pré-vol : chaque activité épinglée se résout-elle VRAIMENT ?

    À lancer AVANT `projet.initialiser()` quand une cible a changé. Les pins
    sont vérifiés un par un, sans rien construire, et chaque échec est
    accompagné de ce qui existe réellement dans la base autour de ce nom — ce
    qui évite l'aller-retour « je corrige, je relance tout, ça casse ailleurs ».

    Ce contrôle existe parce que `diagnostic_decharge()` affiche un nom et une
    localisation qui ne suffisent pas toujours à `findActivity` : une virgule,
    un suffixe de classe d'infiltration, une localisation homonyme, et la
    résolution échoue.

    >>> from acv_lagon import ecoinvent
    >>> ecoinvent.verifier()
    """
    cibles = dict(ACTIVITES)
    cibles.update(DECHARGE)
    cibles["enfouissement"] = DISPOSAL

    echecs = {}
    for role, (nom_act, loc, unite) in cibles.items():
        try:
            act = _chercher_exact(nom_act, loc, unite)
            if verbeux:
                print(f"  ✓ {role:20s} {act['name']} | {act.get('location','')} "
                      f"| {act.get('unit','')}")
        except Exception as err:      # noqa: BLE001
            echecs[role] = (nom_act, loc, f"{type(err).__name__}: {err}")
            if verbeux:
                print(f"  ✗ {role:20s} « {nom_act} | {loc} | {unite} » "
                      f"— {type(err).__name__}")

    if echecs and verbeux:
        print("\nCe qui existe réellement, autour de chaque cible manquante "
              "(NOM | GÉOGRAPHIE | UNITÉ — les trois comptent) :")
        for role, (nom_act, loc, _) in echecs.items():
            motif = " ".join(nom_act.replace("treatment of ", "")
                             .replace("market for ", "").split(",")[0].split()[:3])
            print(f"\n── {role} — recherche « {motif} » " + "─" * 30)
            for act in sorted(_base(), key=lambda a: a["name"]):
                if motif.lower() in act["name"].lower():
                    print(f"    {act['name']} | {act.get('location','')} "
                          f"| {act.get('unit','')}")
    if verbeux:
        print(f"\n{len(cibles) - len(echecs)}/{len(cibles)} cibles résolues.")
    return echecs


def diagnostic_aluminium():
    """Liste tous les datasets d'aluminium et d'anodisation de la base.

    À lancer une fois pour choisir en connaissance de cause la variante
    européenne : `CANDIDATS["aluminium_rer"]` est une liste d'hypothèses, pas
    une certitude sur ta version d'ecoinvent.

    >>> ecoinvent.diagnostic_aluminium()
    """
    for titre, motifs, unite in [
            ("MARCHÉS ALUMINIUM (kg)", ("market for aluminium",), "kilogram"),
            ("PRODUCTION ALUMINIUM (kg)", ("aluminium production",), "kilogram"),
            ("ANODISATION (m²)", ("anodising",), "square meter"),
            ("TRAITEMENT DE SURFACE ALU", ("aluminium", "coating"), None)]:
        print(f"\n── {titre} " + "─" * 40)
        n = 0
        for act in sorted(_base(), key=lambda a: (a["name"], str(a.get("location", "")))):
            nom = act["name"].lower()
            if not all(m in nom for m in motifs):
                continue
            if unite and unite not in str(act.get("unit", "")):
                continue
            print(f"  {act['name']} | {act.get('location','')} | {act.get('unit','')}")
            n += 1
            if n >= 25:
                print("  ...")
                break
        if n == 0:
            print("  (aucun)")


def diagnostic_incineration():
    """Liste les datasets d'incinération de polymères présents dans la base.

    À lancer UNE FOIS avant d'utiliser les modalités « incineration_flotteurs »,
    pour caler `INCINERATION` sur ta version d'ecoinvent :

    >>> from acv_lagon import ecoinvent
    >>> ecoinvent.diagnostic_incineration()

    Le signe imprimé est celui de `signe_dechet` : beaucoup de datasets
    `treatment of ...` portent un produit de référence à -1 kg, et c'est lui
    qui décide du signe de l'échange à écrire.
    """
    for famille, motifs in [
            ("POLYSTYRÈNE (mousse EPS)", ("polystyrene", "incineration")),
            ("POLYÉTHYLÈNE (peau MDPE)", ("polyethylene", "incineration")),
            ("CAOUTCHOUC (élastique SBR)", ("rubber", "incineration")),
            ("PLASTIQUE EN MÉLANGE", ("plastic, mixture", "incineration")),
            ("ORDURES MÉNAGÈRES", ("municipal solid waste", "incineration"))]:
        print(f"\n── {famille} " + "─" * 46)
        n = 0
        for act in sorted(_base(), key=lambda a: (a["name"], str(a.get("location", "")))):
            nom_bas = act["name"].lower()
            if all(m in nom_bas for m in motifs) and "kilogram" in str(act.get("unit", "")):
                print(f"  {act['name']} | {act.get('location','')} "
                      f"| signe {signe_dechet(act):+.0f}")
                n += 1
                if n >= 20:
                    print("  ...")
                    break
        if n == 0:
            print("  (aucun en kilogramme — essaie ecoinvent.chercher"
                  "('incineration') sans filtre d'unité)")


def diagnostic_decharge():
    """Liste les datasets de mise en décharge réellement présents dans la base.

    À lancer une fois pour caler `DECHARGE` sur TA version d'ecoinvent :

    >>> from acv_lagon import ecoinvent
    >>> ecoinvent.diagnostic_decharge()
    """
    for famille, motifs in [("VERRE", ("glass", "landfill")),
                            ("ALUMINIUM", ("aluminium", "landfill")),
                            ("CUIVRE", ("copper", "landfill")),
                            ("ÉTAIN", ("tin", "landfill")),
                            ("PLOMB", ("lead", "landfill")),
                            ("ARGENT", ("silver", "landfill")),
                            ("PLASTIQUE", ("plastic", "landfill")),
                            ("DEEE", ("electronic", "landfill")),
                            ("INERTE", ("inert waste", "landfill")),
                            # Replis si la famille « sanitary landfill » ne
                            # couvre pas un métal : ecoinvent y loge les
                            # résidus chargés en métaux lourds.
                            ("RESIDUS (repli metaux)",
                             ("residual material landfill",)),
                            ("DECHET DANGEREUX (repli)", ("hazardous waste",)),
                            # Et, pour le module entier : un dataset de
                            # traitement de panneau PV serait PLUS
                            # REPRÉSENTATIF que toute ventilation par fraction,
                            # puisqu'il porte l'inventaire réel du laminé.
                            ("PANNEAU PV (le plus representatif)",
                             ("photovoltaic",))]:
        print(f"\n── {famille} " + "─" * 50)
        n = 0
        for act in sorted(_base(), key=lambda a: a["name"]):
            nom_bas = act["name"].lower()
            # Le filtre d'unité est levé pour les familles de repli et pour
            # le PV : ces datasets existent en m², en unité ou en kilogramme
            # selon les versions, et filtrer sur le kilogramme les ferait tous
            # disparaître — c'est exactement ce qui fait croire qu'un dataset
            # n'existe pas.
            large = motifs[0] in ("residual material landfill",
                                  "hazardous waste", "photovoltaic")
            if not large and "kilogram" not in str(act.get("unit", "")):
                continue
            if all(m in nom_bas for m in motifs):
                print(f"  {act['name']} | {act.get('location','')} "
                      f"| {act.get('unit','')} | signe {signe_dechet(act):+.0f}")
                n += 1
                if n >= 25:
                    print("  ...")
                    break
        if n == 0:
            print("  (aucun)")
