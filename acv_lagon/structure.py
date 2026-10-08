"""
Poste « Structure » : aluminium de la plateforme, flotteurs, boulonnerie.

parasol ne sait modéliser qu'un montage au sol ou en toiture. La structure
flottante est donc entièrement explicite ici — et l'activité
`[parasol] PV mounting system` n'est jamais référencée dans notre système, ce
qui rend le double comptage impossible (pas de « neutralisation » à faire).

Masses par plateforme (bilan de masse Tracabilité_v2 + feuille Flotteurs) :
  - aluminium : 606 kg (SH51) à 718 kg (SH81), paramètre `m_alu_structure_kg` ;
  - mousse EPS des flotteurs : 115,92 kg PAR JEU ;
  - peau MDPE (Servatene) : 136,08 kg PAR JEU ;
  - visserie inox A4 : 100 kg, pas de remplacement.

Les flotteurs sont remplacés en cours de vie. Le nombre de jeux est arrondi à
l'entier SUPÉRIEUR : 30/20 → **2 jeux**, et non 1,5. Le prorata supposerait que
les 10 ans de vie restants du second jeu profitent à quelqu'un d'autre ; or à
30 ans la plateforme est démantelée et ce second jeu part au rebut à mi-vie.
C'est notre système qui le consomme entièrement. Voir `parametres.n_jeux`.

────────────────────────────────────────────────────────────────────────────
L'ALUMINIUM : LE POINT LE PLUS SENSIBLE DU MODÈLE (chantier août 2026)

Ce poste vaut ~44 g CO2-eq/kWh, soit 54 % du résultat. Deux corrections ont
donc été apportées ici, et nulle part ailleurs elles n'auraient autant d'effet.

1. ORIGINE. L'aluminium était acheté sur `market for aluminium, wrought alloy |
   GLO`, un marché MONDIAL dont l'électrolyse est dominée par le charbon
   chinois. Le paramètre enum `origine_aluminium` a TROIS modalités — GLO
   (mix mondial, gardé pour la comparabilité avec la littérature), RER
   (défaut, origine européenne à taux de recyclé INCHANGÉ) et RER_SUP (la
   même, avec le recyclé déclaré par le producteur : borne basse, scénario)
   — et `resultats.variante_aluminium(ctx, valeurs)` chiffre les écarts.

   ⚠ LE DÉFAUT EST PASSÉ À « RER » LE 25/09/2026. La condition qu'on s'était
   fixée — ne pas changer la référence sans preuve documentaire de l'origine
   des profilés — est remplie. Le dépouillement des certificats de réception
   EN 10204 3.1 (dossier `Docs_inventaire/…/Certificat 3.1_structure`) trace
   la TOTALITÉ de l'aluminium structurel, ≈ 10,3 t, à des usines européennes :

     · tôle 5754-H111 1,5 / 3 / 4 mm  → Profilglass S.p.A., Fano (IT)
     · tôle 5754-H111 6 mm            → Speira GmbH, usine de Hambourg (DE)
     · tube 6060-T66 120x120x4        → PFA S.r.l., Cortenova (IT)
     · tube 6060-T66 120x120x4        → fileur turc, via ThyssenKrupp Schulte

   Italie 63 %, Allemagne 31 %, Turquie 6 %. Pas un kilo hors Europe élargie.
   Le mix mondial n'est donc plus un défaut conservateur : c'est une hypothèse
   que les pièces contredisent. GLO reste disponible en scénario.

   Ce que les certificats N'établissent PAS : le taux de matière recyclée. Un
   certificat 3.1 atteste la composition chimique et les caractéristiques
   mécaniques, pas les données environnementales. La part de recyclé reste donc
   celle du marché mondial — voir `PART_PRIMAIRE_EU` plus bas.

2. ANODISATION. Elle était NÉGLIGÉE, et c'était une limite déclarée du
   rapport. Elle est maintenant comptée : l'anodisation se facture à la
   surface traitée, et pour un profilé extrudé de paroi t anodisé sur ses deux
   faces, S/m = 2/(t·ρ_alu) — soit 0,37 m²/kg à 2 mm de paroi et 0,25 m²/kg à
   3 mm. D'où le paramètre `surface_anodisee_m2_par_kg`, 0,30 par défaut.
   `ANODISATION = False` restitue l'ancien inventaire.

Ce qui RESTE à trancher : la durée de vie de la structure. 30 ans est
aujourd'hui une hypothèse, pas une observation. En milieu lagonaire, c'est
elle — et non les modules, garantis 30 ans par Wismar — qui limite la vie de
l'installation.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import U, n_jeux

NOM = config.nom("structure plateforme (alu + boulonnerie)")
NOM_FLOTTEURS = config.nom("flotteurs (EPS + peau MDPE)")
NOM_ALU = config.nom("aluminium de structure (origine)")

# Compter l'anodisation des profilés ? False = ancien inventaire.
ANODISATION = True


def n_jeux_flotteurs(ctx):
    """Nombre de jeux de flotteurs sur la durée de vie (entier supérieur)."""
    return n_jeux(ctx.p.duree_vie_an, ctx.p.duree_vie_flotteurs_an)


def masses(ctx):
    """Masses de structure par plateforme, sur toute la durée de vie (kg).

    Partagé entre l'inventaire de fabrication (`construire`) et l'inventaire de
    fin de vie (`fin_de_vie.matieres`) : ce qui est fabriqué est exactement ce
    qui est mis au rebut, il ne peut plus y avoir de divergence entre les deux.
    """
    p = ctx.p
    n = n_jeux_flotteurs(ctx)
    return {
        "aluminium": p.m_alu_structure_kg,
        "eps": p.m_eps_flotteurs_kg * n,
        "mdpe": p.m_mdpe_flotteurs_kg * n,
        "inox": p.m_boulonnerie_kg,
    }


# ── Part de métal PRIMAIRE dans l'alliage corroyé ─────────────────────────
#
# Sert à composer la variante européenne, ecoinvent 3.11 n'offrant pas de
# marché régional « wrought alloy » (il n'existe qu'en GLO).
#
# ⚠ CE PARAMÈTRE DÉCIDE DE LA VALIDITÉ DE LA COMPARAISON. Si la variante
# européenne contient plus de secondaire que le marché GLO, l'écart mesuré
# mélange DEUX effets — l'origine du métal ET le taux de recyclage — et on ne
# peut plus conclure sur l'origine seule. C'est la principale faiblesse d'un
# mix composé à la main.
#
# `None` (défaut) = CALIBRATION AUTOMATIQUE sur le marché GLO : on résout la
# part de primaire x telle que
#     FE(marché GLO) = x · FE(primaire mondial) + (1 − x) · FE(secondaire)
# et on l'applique à la variante européenne. Les deux mix ont alors le même
# taux de recyclage, et l'écart ne porte plus que sur l'origine — c'est-à-dire
# sur l'électricité de l'électrolyse, la seule question posée.
#
# Une valeur numérique (ex. 0.65) force la part et court-circuite la
# calibration ; à n'utiliser que si l'on dispose d'une donnée fournisseur.
PART_PRIMAIRE_ALU = None
PART_PRIMAIRE_DEFAUT = 0.65      # repli si la calibration est impossible

# ── Part de primaire de la variante EUROPÉENNE ────────────────────────────
#
# `None` (défaut) = on garde la part du marché mondial, donc le même taux de
# recyclage des deux côtés, et l'écart GLO/RER ne porte QUE sur l'origine du
# métal. C'est la seule lecture qu'on puisse défendre sans donnée extérieure.
#
# Une valeur numérique fait entrer un SECOND effet : plus de métal secondaire
# dans la variante européenne. C'est légitime — l'Europe recycle davantage —
# mais il n'existe AUCUN taux publié de contenu recyclé pour l'aluminium
# corroyé européen. L'Environmental Profile Report 2024 d'European Aluminium
# donne les empreintes de chaque étape (primaire produit en Europe 6,6,
# primaire consommé en Europe 10,1, lingot refondu 0,26, laminage 0,41,
# filage 0,38 kg CO2-eq/kg) et AUCUN contenu recyclé pour le corroyé, parce
# que celui-ci dépend du produit et du producteur : les alliages de fonderie
# absorbent la ferraille contaminée, le corroyé beaucoup moins.
#
# ⚠ Sous cut-off, c'est le paramètre le plus sensible du modèle : la ferraille
# entre vers 0,86 kg CO2-eq/kg contre 18,65 pour l'ingot primaire. Ne le
# renseigner qu'avec une DÉCLARATION FOURNISSEUR, et l'écrire comme telle dans
# l'article. Ordre de grandeur, SH51 : FE(p) ≈ 0,86 + 9,17·p kg CO2-eq/kg et
# le résultat ≈ 55,6 + 24,3·p g CO2-eq/kWh.
#   p = 0,696 (part du marché, défaut)  -> 7,24 kg/kg -> 72,5 g/kWh
#   p = 0,20  (Profilglass, 80 % scrap) -> 2,69 kg/kg -> 60,4 g/kWh
PART_PRIMAIRE_EU = None

# ── Part de primaire de la modalité « RER_SUP » ───────────────────────
#
# Troisième modalité du switch, ajoutée le 25/09/2026 : la variante
# européenne AVEC le contenu recyclé que le producteur déclare. Elle ne
# touche pas au défaut — elle donne la BORNE BASSE, et elle est sourcée.
#
# 0,20 = 80 % de matière secondaire, chiffre que Profilglass (Fano, IT)
# annonce publiquement sur la matière qu'il achète. Profilglass fournit
# 5 763 des ~10 300 kg tracés, soit 56 % de l'aluminium structurel ; la
# modalité l'applique à TOUT l'aluminium, ce qui en fait une borne et non
# une moyenne pondérée — à écrire ainsi dans l'article.
#
# ⚠ TANT QUE LES FOURNISSEURS N'ONT PAS RÉPONDU PAR ÉCRIT, cette modalité
# est un SCÉNARIO, jamais la référence. Le jour où une déclaration écrite
# arrive, on remplace ce nombre par le sien et on le cite.
PART_PRIMAIRE_FOURNISSEUR = 0.20


def part_primaire(ctx, verbeux=True):
    """Part de primaire de l'alliage, calée sur le marché GLO si possible."""
    if PART_PRIMAIRE_ALU is not None:
        return float(PART_PRIMAIRE_ALU)

    fe = {}
    for role in ("aluminium", "aluminium_primaire_glo", "alu_secondaire"):
        act = getattr(ctx.ei, role, None)
        fe[role] = _gwp_par_kg(act) if act is not None else None

    if fe["aluminium_primaire_glo"] is None or fe["alu_secondaire"] is None:
        if verbeux:
            print(f"  ⚠ calibration de la part de primaire impossible "
                  f"(dataset manquant) — repli sur {PART_PRIMAIRE_DEFAUT:.0%}.")
        return PART_PRIMAIRE_DEFAUT

    ecart = fe["aluminium_primaire_glo"] - fe["alu_secondaire"]
    if ecart <= 0:
        if verbeux:
            print(f"  ⚠ calibration incohérente (primaire ≤ secondaire) — "
                  f"repli sur {PART_PRIMAIRE_DEFAUT:.0%}.")
        return PART_PRIMAIRE_DEFAUT

    x = (fe["aluminium"] - fe["alu_secondaire"]) / ecart
    if not 0.0 <= x <= 1.0:
        if verbeux:
            print(f"  ⚠ part de primaire calibrée hors [0 ; 1] ({x:.2f}) — "
                  f"repli sur {PART_PRIMAIRE_DEFAUT:.0%}.")
        return PART_PRIMAIRE_DEFAUT

    if verbeux:
        print(f"  part de primaire calibrée sur le marché GLO : {x:.1%} "
              f"(marché {fe['aluminium']:.2f} = {x:.2f}×"
              f"{fe['aluminium_primaire_glo']:.2f} + {1-x:.2f}×"
              f"{fe['alu_secondaire']:.2f} kg CO2-eq/kg)")
    return x


def _gwp_par_kg(act):
    """GWP100 d'un kg du dataset, ou None si le calcul échoue."""
    try:
        import brightway2 as bw

        from . import config
        lca = bw.LCA({act: 1}, config.GWP)
        lca.lci()
        lca.lcia()
        return float(lca.score)
    except Exception:      # noqa: BLE001
        return None

NOM_ALU_RER = config.nom("aluminium corroye europeen (compose)")
NOM_ALU_RER_SUP = config.nom(
    "aluminium corroye europeen (recycle declare fournisseur)")


def entree_primaire(ctx):
    """Entrée « ingot primaire » du marché GLO et sa part, LUES DANS LA BASE.

    Renvoie (activité, part en kg/kg) ou (None, None).

    On ne suppose plus la part de primaire : on la lit. La recette de
    `market for aluminium, wrought alloy | GLO` en ecoinvent 3.11 est
    0,696 kg d'ingot primaire + 0,304 kg de ferrailles refondues (+ transports).
    """
    for exc in ctx.ei.aluminium.technosphere():
        nom = exc.input["name"].lower()
        if "primary" in nom and "ingot" in nom:
            return exc.input, float(exc["amount"])
    return None, None


def entree_secondaire(ctx):
    """Entrée « métal secondaire » du marché GLO et sa part, LUES DANS LA BASE.

    Miroir exact de `entree_primaire`. On ne CHOISIT pas un dataset de
    ferraille — ce serait faire entrer une hypothèse par la bande, et le
    docstring de `facteurs_aluminium` rappelle les deux pièges classiques
    (produit de référence négatif, dataset de préparation qui n'est pas du
    métal). On prend celui que le marché mondial emploie déjà.

    Règle : parmi les entrées technosphère du marché, on écarte l'ingot
    primaire et les transports, on ne garde que les flux en kg, et on retient
    le plus gros. Renvoie (activité, part en kg/kg) ou (None, None).
    """
    primaire, _ = entree_primaire(ctx)
    cle_primaire = getattr(primaire, "key", None)
    meilleur, part = None, 0.0
    for exc in ctx.ei.aluminium.technosphere():
        entree = exc.input
        if cle_primaire is not None and getattr(entree, "key", None) == cle_primaire:
            continue
        nom = entree["name"].lower()
        if "transport" in nom:
            continue
        if entree.get("unit") not in ("kilogram", "kg"):
            continue
        montant = float(exc["amount"])
        if montant > part:
            meilleur, part = entree, montant
    if meilleur is None:
        return None, None
    return meilleur, part


def _aluminium_europeen(ctx, part_eu=None, nom=None):
    """Alliage corroyé européen = marché GLO dont on SUBSTITUE l'origine.

    ecoinvent 3.11 n'a `market for aluminium, wrought alloy` qu'en GLO. Plutôt
    que de recomposer un mix à la main — ce qui obligeait à supposer la part de
    primaire, et faisait porter à l'écart mesuré deux effets au lieu d'un — on
    part de la recette RÉELLE du marché mondial et on n'échange qu'une chose :
    la géographie de l'électrolyse.

        RER = 1 × [marché GLO]
              − part × [ingot primaire tel qu'employé par ce marché]
              + part × [marché européen de l'ingot primaire]

    Écrit ainsi, TOUT le reste du marché mondial est conservé à l'identique :
    les 30 % de ferrailles refondues, leur sous-mix RoW/RER, et les quatre
    maillons de transport. La comparaison GLO/RER ne porte donc plus QUE sur
    l'origine du métal primaire — c'est-à-dire sur l'électricité de
    l'électrolyse, la seule question posée. C'est aussi valable pour les 16
    catégories d'impact, pas seulement le carbone : on manipule des activités,
    pas des facteurs agrégés.

    Le terme négatif n'est pas un crédit : c'est une soustraction dans une
    combinaison linéaire, la façon propre de dire « le même produit, sans son
    ingrédient mondial ».

    Choix assumé : le côté européen est le MARCHÉ (`market for aluminium,
    primary, ingot | IAI Area, EU27 & EFTA`, 10,03 kg CO2-eq/kg), qui inclut
    les importations hors Europe — et non la seule PRODUCTION européenne, que
    l'Environmental Profile Report 2024 d'European Aluminium situe à 6,6, et
    qui supposerait un métal 100 % fondu en Europe. Un acheteur européen
    achète sur le marché européen, importations comprises. Ce même rapport
    donne 10,1 kg CO2-eq/kg pour le primaire CONSOMMÉ en Europe : le dataset
    ecoinvent employé ici tombe au pour cent près sur la valeur publiée par la
    profession, ce qui vaut contrôle de la brique.

    ── PART DE RECYCLÉ ──────────────────────────────────────────────────
    `PART_PRIMAIRE_EU` permet de donner à la variante européenne une part de
    primaire DIFFÉRENTE de celle du marché mondial. La recette devient alors

        RER(p) = 1              × [marché GLO]
               − part_marché    × [ingot primaire tel qu'employé par ce marché]
               + p              × [marché européen de l'ingot primaire]
               + (part_marché − p) × [entrée secondaire DU MÊME marché]

    Le bilan matière tient : (1 − part_marché) + (part_marché − p) + p = 1 kg
    de métal. Le supplément de recyclé est pris sur la filière que le marché
    emploie déjà, jamais sur un dataset choisi par nous — la seule hypothèse
    nouvelle est donc `p`, et elle est explicite.

    Par défaut `p = part_marché`, le quatrième terme s'annule et l'on retrouve
    exactement la substitution d'origine seule.

    Renvoie None si les briques manquent — l'appelant retombe alors sur GLO.
    """
    primaire_eu = getattr(ctx.ei, "aluminium_primaire", None)
    primaire_glo, part_marche = entree_primaire(ctx)
    if primaire_eu is None or primaire_glo is None:
        return None
    if PART_PRIMAIRE_ALU is not None:
        part_marche = float(PART_PRIMAIRE_ALU)

    # `part_eu` passé en argument = modalité explicite (RER_SUP) ; sinon on
    # prend le réglage de module, et à défaut la part du marché mondial.
    if part_eu is None:
        part_eu = (part_marche if PART_PRIMAIRE_EU is None
                   else float(PART_PRIMAIRE_EU))
    else:
        part_eu = float(part_eu)
    secondaire = None
    if part_eu > part_marche:
        print(f"  ⚠ part de primaire européenne demandée ({part_eu:.1%}) dépasse la part du marché "
              f"({part_marche:.1%}) : il faudrait RETIRER du recyclé au mix "
              "mondial, ce que cette recette ne sait pas faire. On garde la "
              "part du marché.")
        part_eu = part_marche
    elif part_eu < part_marche:
        secondaire, _ = entree_secondaire(ctx)
        cles = {getattr(a, "key", None)
                for a in (ctx.ei.aluminium, primaire_glo, primaire_eu)}
        if secondaire is None or getattr(secondaire, "key", None) in cles:
            print("  ⚠ entrée secondaire du marché introuvable ou confondue "
                  "avec une autre brique — on garde la part du marché "
                  f"({part_marche:.1%}).")
            secondaire, part_eu = None, part_marche

    # ⚠ Avec `units_enabled`, un montant d'échange doit être une GRANDEUR
    # DIMENSIONNÉE, pas un flottant nu — sinon lca_algebraic lève
    # « Unit 'kilogram' expected, and dimensionless amount provided ».
    par_kg = U("kg/kg")
    exchanges = {
        ctx.ei.aluminium: 1.0 * par_kg,
        primaire_glo: -part_marche * par_kg,
        primaire_eu: part_eu * par_kg,
    }
    if secondaire is not None:
        exchanges[secondaire] = (part_marche - part_eu) * par_kg

    act = agb.newActivity(ctx.db, nom or NOM_ALU_RER, unit="kg",
                          exchanges=exchanges)
    act.updateMeta(**{config.AXE: "Structure"})
    print(f"  aluminium européen : recette du marché GLO, part primaire du "
          f"marché {part_marche:.1%} LUE dans la base")
    print(f"     − {primaire_glo['name'][:52]} | {primaire_glo.get('location','')}")
    print(f"     + {primaire_eu['name'][:52]} | {primaire_eu.get('location','')}"
          f"  ({part_eu:.1%})")
    if secondaire is not None:
        print(f"     + {secondaire['name'][:52]} | {secondaire.get('location','')}"
              f"  ({part_marche - part_eu:.1%} de recyclé EN PLUS du marché)")
    else:
        print("       taux de recyclé INCHANGÉ : l'écart GLO/RER ne porte que "
              "sur l'origine du métal")
    return act


def facteurs_aluminium(ctx, methode=None):
    """GWP par kg de chaque option d'aluminium — LE contrôle à faire.

    Un écart GLO/RER de plusieurs dizaines de pour cent sur le résultat final
    ne veut rien dire tant qu'on n'a pas regardé le facteur d'émission AU KG.
    C'est là que se voient les deux pièges de la composition maison :

    * un dataset de secondaire dont le produit de référence est NÉGATIF (les
      activités « treatment of ... scrap » le sont souvent en cut-off) ferait
      basculer sa contribution en CRÉDIT, et l'aluminium européen ressortirait
      artificiellement bon marché ;
    * un dataset de préparation de ferraille (collecte, tri, nettoyage,
      pressage) n'est PAS du métal : il ne porte que la logistique, pas la
      refusion. L'utiliser comme 35 % de l'alliage sous-estime lourdement.

    Repères : un alliage corroyé mondial se situe vers 12-16 kg CO2-eq/kg, un
    ingot primaire européen vers 8-9, de l'aluminium secondaire vers 0,5-1,5.
    Toute valeur hors de ces plages — a fortiori négative — est un bug.

    >>> structure.facteurs_aluminium(ctx)
    """
    import pandas as pd

    from . import config, ecoinvent

    methode = methode or config.GWP
    options = {
        "GLO — market wrought alloy": ctx.ei.aluminium,
        "primaire MONDIAL": getattr(ctx.ei, "aluminium_primaire_glo", None),
        "primaire EUROPE": getattr(ctx.ei, "aluminium_primaire", None),
        "secondaire (scrap)": getattr(ctx.ei, "alu_secondaire", None),
    }
    lignes = []
    for libelle, act in options.items():
        if act is None:
            continue
        try:
            import brightway2 as bw
            lca = bw.LCA({act: 1}, methode)
            lca.lci(); lca.lcia()
            score = float(lca.score)
        except Exception as err:      # noqa: BLE001
            score = float("nan")
            print(f"  ⚠ {libelle} : {type(err).__name__}: {err}")
        lignes.append({
            "option": libelle,
            "dataset": act["name"][:60],
            "loc": act.get("location", ""),
            "signe produit": ecoinvent.signe_dechet(act),
            "kg CO2-eq / kg": round(score, 3),
        })

    df = pd.DataFrame(lignes)

    # Entrée primaire réellement employée par le marché GLO, et sa part
    primaire_glo, part = entree_primaire(ctx)
    if primaire_glo is None:
        return df
    fe_glo_prim = _gwp_par_kg(primaire_glo)
    df.loc[len(df)] = {
        "option": f"→ primaire DANS le marché GLO ({part:.1%})",
        "dataset": primaire_glo["name"][:60],
        "loc": primaire_glo.get("location", ""),
        "signe produit": 1.0, "kg CO2-eq / kg": round(fe_glo_prim, 3)}

    # Entrée secondaire réellement employée par le marché GLO
    secondaire, part_sec = entree_secondaire(ctx)
    fe_sec = _gwp_par_kg(secondaire) if secondaire is not None else None
    if secondaire is not None and fe_sec is not None:
        df.loc[len(df)] = {
            "option": f"→ secondaire DANS le marché GLO ({part_sec:.1%})",
            "dataset": secondaire["name"][:60],
            "loc": secondaire.get("location", ""),
            "signe produit": ecoinvent.signe_dechet(secondaire),
            "kg CO2-eq / kg": round(fe_sec, 3)}

    # Substitution d'origine, et loi de la part de recyclé
    try:
        fe_marche = float(df.loc[df["option"].str.startswith("GLO"),
                                 "kg CO2-eq / kg"].iloc[0])
        fe_prim_eu = float(df.loc[df["option"].str.startswith("primaire EUROPE"),
                                  "kg CO2-eq / kg"].iloc[0])

        def compose(p):
            """FE de l'alliage européen pour une part de primaire p."""
            terme_sec = 0.0 if fe_sec is None else (part - p) * fe_sec
            return fe_marche - part * fe_glo_prim + p * fe_prim_eu + terme_sec

        rer = compose(part)
        df.loc[len(df)] = {
            "option": f"RER, origine substituée (p = {part:.1%})",
            "dataset": NOM_ALU_RER, "loc": "", "signe produit": 1.0,
            "kg CO2-eq / kg": round(rer, 3)}
        df.loc[len(df)] = {
            "option": "→ écart d'ORIGINE seul",
            "dataset": f"{(rer/fe_marche - 1)*100:+.1f} % sur le kg d'alliage",
            "loc": "", "signe produit": 1.0,
            "kg CO2-eq / kg": round(rer - fe_marche, 3)}

        if fe_sec is not None:
            # la recette est affine en p : une droite suffit à tout dire
            b = fe_prim_eu - fe_sec
            a = compose(0.0)
            df.loc[len(df)] = {
                "option": "→ loi de la part de recyclé",
                "dataset": f"FE(p) = {a:.2f} + {b:.2f} x p  "
                           f"(p = part de PRIMAIRE européen)",
                "loc": "", "signe produit": 1.0,
                "kg CO2-eq / kg": float("nan")}
            p_sup = float(PART_PRIMAIRE_FOURNISSEUR)
            df.loc[len(df)] = {
                "option": f"RER_SUP, recyclé déclaré (p = {p_sup:.1%})",
                "dataset": "modalité de scénario — déclaration Profilglass, "
                           "80 % de scrap ; BORNE BASSE, pas la référence",
                "loc": "", "signe produit": 1.0,
                "kg CO2-eq / kg": round(compose(p_sup), 3)}
            if PART_PRIMAIRE_EU is not None:
                p_eu = float(PART_PRIMAIRE_EU)
                df.loc[len(df)] = {
                    "option": f"RER + recyclé forcé (p = {p_eu:.1%})",
                    "dataset": "PART_PRIMAIRE_EU — exige une donnée fournisseur",
                    "loc": "", "signe produit": 1.0,
                    "kg CO2-eq / kg": round(compose(p_eu), 3)}
    except Exception:      # noqa: BLE001
        pass
    return df


def source_aluminium(ctx):
    """Dataset (ou switch GLO/RER) fournissant l'aluminium de structure.

    Si la variante européenne n'existe pas dans cette version d'ecoinvent, on
    la COMPOSE (`_aluminium_europeen`). Et si même ça échoue, on retombe sur le
    mix mondial en le disant très fort — jamais silencieusement.
    """
    glo = ctx.ei.aluminium
    rer = getattr(ctx.ei, "aluminium_rer", None)

    if rer is not None and (rer["name"] == glo["name"]
                            and rer.get("location") == glo.get("location")):
        print("  ⚠ la variante « RER » a résolu sur le MÊME dataset que GLO — "
              "ignorée, on compose à la place.")
        rer = None

    if rer is None:
        rer = _aluminium_europeen(ctx)

    if rer is None:
        print("\n" + "!" * 72)
        print("  ALUMINIUM : AUCUNE VARIANTE EUROPÉENNE DISPONIBLE.")
        print("  Le switch GLO/RER est INACTIF : les deux modalités donneront")
        print("  le MÊME résultat. Lance ecoinvent.diagnostic_aluminium() et")
        print("  complète CANDIDATS['aluminium_rer'] / ['alu_secondaire'].")
        print("!" * 72 + "\n")
        return glo

    # Troisième modalité : la MÊME recette européenne, avec le contenu
    # recyclé déclaré par le producteur. C'est un scénario sourcé, pas le
    # défaut — voir `PART_PRIMAIRE_FOURNISSEUR`.
    rer_sup = None
    try:
        rer_sup = _aluminium_europeen(
            ctx, part_eu=PART_PRIMAIRE_FOURNISSEUR, nom=NOM_ALU_RER_SUP)
    except Exception as err:      # noqa: BLE001
        print(f"  ⚠ modalité RER_SUP impossible ({type(err).__name__}: {err})")
    if rer_sup is None:
        # ⚠ LE SWITCH DOIT RESTER TOTAL : une modalité déclarée dans l'enum
        # mais absente du dict donnerait un aluminium NUL, pas une erreur.
        print("  ⚠ RER_SUP retombe sur RER — la modalité existe mais ne change RIEN.")
        rer_sup = rer

    try:
        switch = agb.newSwitchAct(ctx.db, NOM_ALU, ctx.p.origine_aluminium,
                                  {"GLO": glo, "RER": rer, "RER_SUP": rer_sup})
        switch.updateMeta(**{config.AXE: "Structure"})
        print(f"  aluminium : GLO     = {glo['name']} | {glo.get('location','')}")
        print(f"              RER     = {rer['name']} | {rer.get('location','')}")
        print(f"              RER_SUP = {rer_sup['name']} "
              f"(p = {PART_PRIMAIRE_FOURNISSEUR:.0%} de primaire, déclaré)")
        return switch
    except Exception as err:      # noqa: BLE001
        print(f"  ⚠ switch aluminium impossible ({type(err).__name__}: {err}) — "
              f"mix mondial conservé.")
        return glo


def construire(ctx):
    """Poste « Structure » : ossature aluminium anodisé + boulonnerie inox.

    ⚠ Les FLOTTEURS ne sont plus ici : ils forment leur propre poste
    (`construire_flotteurs`). Les deux étaient auparavant confondus sous
    « Structure », qui pesait 57 % du résultat sans qu'on sache ce qui venait
    du métal et ce qui venait de la mousse. Or ce sont deux matériaux, deux
    durées de vie (30 ans contre 2 jeux de 20 ans) et deux fins de vie
    (export Nouvelle-Zélande contre décharge locale) : les additionner
    masquait l'information la plus utile du modèle.
    """
    p = ctx.p
    m = masses(ctx)
    exchanges = {
        source_aluminium(ctx): m["aluminium"],
        ctx.ei.inox: m["inox"],
    }

    # Anodisation : facturée à la surface développée des profilés.
    anodisation = getattr(ctx.ei, "anodisation", None)
    if ANODISATION and anodisation is not None:
        exchanges[anodisation] = m["aluminium"] * p.surface_anodisee_m2_par_kg
        print(f"  anodisation comptée : {anodisation['name']} "
              f"| {anodisation.get('location','')} "
              f"({anodisation.get('unit','')})")
    elif ANODISATION:
        print("  ⚠ anodisation : aucun dataset « anodising » trouvé — "
              "poste toujours négligé, à garder dans les limites.")

    act = agb.newActivity(ctx.db, NOM, unit="unit", exchanges=exchanges)
    act.updateMeta(**{config.AXE: "Structure"})
    return act


def construire_flotteurs(ctx):
    """Poste « Flotteurs » : mousse EPS + peau MDPE, DEUX jeux sur 30 ans.

    Séparé de la structure métallique depuis août 2026. C'est le poste qui
    porte le seul vrai enjeu environnemental de la fin de vie — ~500 kg de
    polymères sans exutoire local sur un lagon corallien — alors qu'il ne pèse
    presque rien en carbone. Le distinguer permet de le dire.
    """
    m = masses(ctx)
    act = agb.newActivity(
        ctx.db, NOM_FLOTTEURS, unit="unit",
        exchanges={
            ctx.ei.eps: m["eps"],
            ctx.ei.pehd: m["mdpe"],
        })
    act.updateMeta(**{config.AXE: "Flotteurs"})
    print(f"  flotteurs : {n_jeux_flotteurs(ctx)} jeux sur la durée de vie "
          f"(EPS + peau MDPE)")
    return act
