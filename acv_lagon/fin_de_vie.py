"""
Poste « Fin de vie » des modules — modèle cradle-to-grave.

════════════════════════════════════════════════════════════════════════════
LES TROIS MODALITÉS ET LEUR CHOIX MÉTHODOLOGIQUE

Le paramètre enum `fin_de_vie` sélectionne l'une des trois modalités
ci-dessous. Les deux dernières décrivent LE MÊME SCÉNARIO PHYSIQUE (les mêmes
panneaux partent au même recycleur néo-zélandais) : ce qui les distingue n'est
pas la réalité industrielle, c'est la **règle d'allocation** appliquée au
recyclage. Les présenter côte à côte, c'est afficher l'incertitude
méthodologique au lieu de la cacher derrière un choix implicite.

┌─ « enfouissement » — FILIÈRE ACTUELLE ──────────────────────── RÉFÉRENCE ──┐
│ Scénario physique : la filière TELLE QU'ELLE EXISTE aujourd'hui.           │
│   • métaux propres (alu, inox, acier, cuivre) → remis à la filière au      │
│     point de collecte Fenua Ma, 220 km de goélette, puis SORTIE DU         │
│     SYSTÈME : sous cut-off une ferraille qui a un marché est un produit,   │
│     elle ne porte ni charge ni crédit au-delà ;                            │
│   • DEEE (onduleurs) → export France, 17 000 km, transport et traitement   │
│     imputés : un déchet électronique est un service, pas une ressource ;   │
│   • modules PV et polymères (EPS, MDPE, HMPE, PA6, caoutchouc) → aucun     │
│     exutoire nulle part, décharge à Raiatea, ventilée par fraction.        │
│ Choix méthodo : cut-off, comme la base. Aucun crédit n'est accordé.        │
│                                                                            │
│ ⚠ CORRECTION DU 01/10/2026. Cette modalité enfouissait AUSSI les métaux,   │
│ y compris ~700 kg d'aluminium — alors que la section PÉRIMÈTRE ci-dessous  │
│ affirme elle-même qu'un alu propre ne s'enfouit pas en Polynésie et que    │
│ Fenua Ma l'exporte. Le scénario « statu quo » modélisait donc un flux qui  │
│ n'a pas lieu. Ce n'était pas de la prudence : ISO 14044 demande de la      │
│ représentativité, et un majorant est une borne, pas une référence.         │
│                                                                            │
│ Conséquence heureuse : les métaux partant dans les DEUX scénarios, la      │
│ comparaison avec le recyclage isole la seule décision encore ouverte —     │
│ le sort des modules — au lieu de la mélanger à celui de la structure.      │
│                                                                            │
│ La clé reste « enfouissement » pour ne pas casser les appels existants,    │
│ mais elle n'enfouit plus que ce qui n'a nulle part où aller.               │
└────────────────────────────────────────────────────────────────────────────┘

┌─ « recyclage_cutoff » ─────────────────── RÉFÉRENCE POUR LE RECYCLAGE ─────┐
│ Scénario physique : goélette (220 km) + fret maritime vers Auckland        │
│ (4 000 km) + démantèlement/tri mécanique + mise en décharge du refus.      │
│ Choix méthodo : SIMPLE CUT-OFF, alias « recycled content approach »,       │
│ alias « allocation 100/0 » (Wang 2025, Table 10).                          │
│                                                                            │
│ Principe : le détenteur du déchet porte tout ce qui va JUSQU'AU point de   │
│ substitution — collecte, transport, démantèlement, tri, décharge du refus  │
│ — et RIEN au-delà. L'affinage de la matière secondaire (etching du         │
│ silicium, purification du verre) et le bénéfice de la matière vierge       │
│ évitée sont portés par CELUI QUI ACHÈTE le secondaire.                     │
│                                                                            │
│ POURQUOI C'EST LA RÉFÉRENCE ICI : on travaille sur ecoinvent-3.11-CUTOFF.  │
│ Dans ce system model, le contenu recyclé entrant dans nos matériaux amont  │
│ ne porte déjà que le coût du procédé de recyclage, pas celui de la matière │
│ vierge : le bénéfice du recyclage est DÉJÀ attribué à l'aval. Ajouter en   │
│ plus un crédit d'avoided burden en fin de vie compte le même bénéfice aux  │
│ deux bouts de la chaîne. C'est une incohérence de system model, pas un     │
│ choix discutable — et c'est exactement le point soulevé par le reviewer.   │
│                                                                            │
│ CONSÉQUENCE À ASSUMER : en cut-off l'impact de la fin de vie est           │
│ INTÉGRALEMENT POSITIF. Le recyclage ressort donc plus lourd en GWP que     │
│ l'enfouissement (4 000 km de fret + électricité de procédé contre une      │
│ décharge locale quasi gratuite en carbone). Ce n'est PAS un verdict contre │
│ le recyclage : c'est la traduction comptable du fait que son bénéfice est  │
│ crédité au sidérurgiste/verrier aval, pas à nous. Les catégories           │
│ ressources et toxicité, elles, peuvent basculer dans l'autre sens.         │
└───────────────────────────────────────────────────────────────────────────┘

┌─ « recyclage_closed_loop » ──────────── BORNE BASSE / SENSIBILITÉ ─────────┐
│ Scénario physique : identique au précédent, plus l'affinage de la matière  │
│ secondaire (`KWH_AFFINAGE_PAR_T`).                                         │
│ Choix méthodo : CLOSED-LOOP ALLOCATION, alias « end-of-life approach »,    │
│ alias « allocation 0/100 » (ISO 14044/14067, PAS 2050, GHG Protocol,       │
│ IEA-PVPS Task 12).                                                         │
│                                                                            │
│ Principe : 100 % du recyclage est alloué au produit AMONT (nous), et en    │
│ contrepartie 100 % de la production de matière vierge évitée nous est      │
│ créditée — d'où les échanges NÉGATIFS. C'est le modèle « avoided burden ». │
│                                                                            │
│ À QUOI IL SERT : Wang (2025, §III.3.3.2.2) montre que cut-off et           │
│ closed-loop donnent systématiquement les résultats EXTRÊMES — haut et bas  │
│ — quelles que soient les hypothèses de taux, et recommande de les          │
│ appliquer EN PARALLÈLE pour encadrer l'incertitude de choix méthodologique.│
│ Sur son cas d'étude tandem PSK/Si l'écart atteint 162 → 212 kg CO2-eq/kWc, │
│ soit 31 %. C'est aussi la recommandation conjointe du GHG Protocol, de la  │
│ PAS 2050 et de l'IEA-PVPS Task 12. On ne choisit donc pas entre les deux : │
│ ON PUBLIE L'INTERVALLE.                                                    │
│                                                                            │
│ ⚠ NE PAS PRÉSENTER CETTE MODALITÉ COMME LE RÉSULTAT PRINCIPAL. Combinée à  │
│ une base cutoff, elle double-compte. Elle a valeur de borne, pas de        │
│ référence.                                                                 │
│                                                                            │
│ ET C'EST UNE BORNE GÉNÉREUSE, pour deux raisons cumulatives qu'il faut     │
│ écrire dans le rapport :                                                   │
│  1. l'aluminium ENTRANT est acheté sur `market for aluminium, wrought      │
│     alloy | GLO`, qui contient déjà du secondaire à prix cut-off, alors    │
│     que le crédit SORTANT est celui de l'ingot PRIMAIRE. La closed-loop    │
│     stricte au sens d'ISO 14044 exigerait de facturer aussi l'entrée au    │
│     primaire (Wang 2025, éq. 7 : « R1 has no impact on the LCA results »). │
│     Ne pas le faire gonfle le bénéfice net ;                               │
│  2. `SUBST["aluminium"] = 1.00` suppose une substitution 1:1 sans          │
│     downcycling.                                                           │
│ Les deux poussent dans le même sens. La borne basse est donc OPTIMISTE :   │
│ le vrai bénéfice d'un recyclage réel se situe au-dessus.                   │
└───────────────────────────────────────────────────────────────────────────┘

NON IMPLÉMENTÉ, ET POURQUOI — la Circular Footprint Formula (CFF, guide PEF
de la Commission) est l'approche que Wang recommande *par défaut* : elle évite
les extrêmes et pondère par un facteur marché A et un facteur de dégradation
qualité Qs/Qp tabulés en Annexe C du guide PEF (A = 0,2 pour l'alu, le verre
et le cuivre). Mais l'appliquer correctement suppose de piloter aussi **R1**,
le contenu recyclé EN ENTRÉE de fabrication, donc de surcharger les datasets
matériaux amont — pas seulement la fin de vie. Pour un poste qui pèse peu dans
ce système, le rapport effort/bénéfice ne le justifie pas : la CFF est citée
en discussion, l'intervalle cut-off ↔ closed-loop tient lieu d'encadrement.

════════════════════════════════════════════════════════════════════════════
LES MODALITÉS D'INCINÉRATION (ajout des 04 et 05/10/2026)

QUESTION POSÉE : les 504 kg de polymères des flotteurs (231,8 kg de mousse EPS
+ 272,2 kg de peau MDPE, deux jeux sur trente ans) sont enfouis sur place dans
la référence, faute d'exutoire. Et si on les brûlait ?

CE QUE LE SCÉNARIO CHANGE, ET RIEN D'AUTRE : la référence, à ceci près que ces
deux fractions-là partent en incinération d'ordures ménagères. Tout le reste
est inchangé — les métaux sortent toujours au point de collecte, les modules
restent toujours à Raiatea, les onduleurs partent toujours en DEEE. Une
sensibilité ne vaut que si elle ne bouge qu'une chose à la fois.

⚠ CE N'EST PAS LA PEAU DU CÂBLE. `matieres()` agrège sous la clé « mdpe » la
peau des flotteurs (272,2 kg) ET les gaines du câble d'export et des liaisons
onduleur (~152 kg). Router la clé entière vers l'incinérateur brûlerait aussi
des gaines enfouies avec le câble, qu'on ne déterre pas. On prélève donc la
masse des flotteurs par `structure.masses(ctx)` et on la RETIRE du refus, le
reste du MDPE continuant en décharge. C'est la raison d'être de
`_masses_a_incinerer()` et de `FRACTIONS_AGREGEES` : la clé matière est trop
grossière pour la question posée.

DEUX LOTS DE MATIÈRE, ET POURQUOI LE SECOND
  * « flotteurs »  — EPS + peau MDPE des flotteurs, 504 kg. La question posée.
  * « polymeres »  — les mêmes, plus l'élastique SBR de l'ancrage (~9,5 kg).
    Ce second lot existe pour s'aligner sur Seitz et al. 2026 (Environ. Sci.
    Technol. 60(21):14949), qui incinèrent les élastomères en fin de vie et
    harmonisent l'ensemble des ACV FPV publiées. L'écart entre les deux lots
    est marginal en masse — c'est un alignement de convention, pas un
    résultat : il permet de dire que la comparaison avec cette référence
    porte sur le même périmètre de fin de vie.
    Les cordes HMPE et la poulie PA6 restent en décharge : ce ne sont ni des
    flotteurs ni des élastomères. Les ajouter est une ligne dans
    `INCINERATION_SCENARIOS`.

POURQUOI DEUX VARIANTES PAR LOT, ET LAQUELLE PUBLIER
Ce n'est plus seulement un raisonnement : c'est ce que l'IEA PRESCRIT.

IEA-PVPS T12-18:2020, § 3.2.5 p. 21, mot pour mot :
    « It is recommended to perform several analyses on material recycling
      using the recycled content (cut-off) allocation approach as DEFAULT and
      the end-of-life (avoided burden) recycling approach IN A SENSITIVITY
      ANALYSIS. »

Le cut-off en référence, l'avoided burden en sensibilité. C'est exactement
l'architecture de ce fichier, pour le recyclage comme pour l'incinération :
« incineration_flotteurs » est le résultat, « ..._valorisee » est la borne.

Et IEA-PVPS T12-12:2017 (Wambach & Heath), Table 3 p. 14, va dans le même
sens pour les polymères en particulier. Le rapport constate la pratique réelle
— « The polymers are used for energetic recovery in waste-to-energy plants in
compliance with European laws. In other countries the polymer fraction may be
landfilled. » — ce qui décrit précisément notre paire référence/sensibilité
(décharge à Raiatea contre incinération). Mais il ajoute : « The energetic
recovery process is not part of the LCI », et classe « Energetic use of
polymers » parmi les procédés NON INCLUS.

Autrement dit : l'inventaire de référence de l'IEA pour les polymères de PV
NE CRÉDITE PAS l'énergie récupérée. La variante créditée n'est donc pas une
option neutre qu'on pourrait publier à la place — c'est un écart à la
convention, à présenter comme tel.

Exactement le même partage que cut-off / closed-loop, pour la même raison.
  * « incineration_flotteurs » — CUT-OFF, cohérent avec la base. Dans le
    system model cut-off, l'électricité et la chaleur d'un incinérateur sont
    des co-produits COUPÉS : ils quittent le système sans charge, à la
    disposition de qui les consomme. Le détenteur du déchet porte donc toute
    la combustion et ne reçoit rien. → MODALITÉ À PUBLIER.
  * « incineration_flotteurs_valorisee » — l'électricité récupérée est
    créditée contre le réseau au fioul de Raiatea (0,914 kg CO₂-eq/kWh).
    C'est de l'avoided burden, et la même objection s'applique qu'au
    closed-loop : si nous prenons le crédit et qu'un autre consomme la même
    électricité coupée, le bénéfice est compté deux fois. → BORNE BASSE.

CE QU'IL FAUT ATTENDRE DU RÉSULTAT, ET C'EST CONTRE-INTUITIF
Un polyéthylène enfoui ne se dégrade pas : son carbone fossile reste dans le
sol, et la décharge se comporte comme un STOCKAGE. L'incinérer libère la
totalité de ce carbone — 3,14 kg CO₂ par kg de PE, 3,38 par kg de PS, c'est de
la stœchiométrie, pas une hypothèse. Brûler les flotteurs ALOURDIT donc le
bilan climatique, et la valorisation ne rattrape qu'une partie de l'écart : le
rendement électrique d'un petit incinérateur insulaire est de l'ordre de 13 %
(cf. `RENDEMENT_ELEC_INCINERATION`), on ne récupère pas 40 MJ/kg en
électricité utile.

POURQUOI C'EST UN SCÉNARIO PROSPECTIF, ET IL FAUT L'ÉCRIRE
La Polynésie française n'a AUCUN incinérateur en service : les déchets non
recyclables vont en centre d'enfouissement technique (Paihoro, 34 000 t/an
d'ordures ménagères pour les Îles du Vent via Fenua Ma), et Raiatea a sa
propre décharge. Un projet de pôle de valorisation énergétique existe au site
de Nive'e (70 000 t/an, ~20 milliards F CFP, horizon douze ans), mais il
était encore à l'étude en 2025. Cette modalité répond donc à « que se
passerait-il si », pas à « que fait-on ». À présenter comme telle, sans quoi
un relecteur aura raison de la rejeter.

════════════════════════════════════════════════════════════════════════════
POURQUOI L'ENFOUISSEMENT EST VENTILÉ PAR FRACTION (correction v22)

L'ancienne version appliquait UN dataset unique à toute la masse du module.
Les seuls candidats disponibles en ecoinvent 3.11 étant des « waste plastic,
consumer electronics », on faisait traiter ~390 kg de verre plat comme du
plastique d'électronique grand public. D'où :
  * une écotoxicité surestimée et hypersensible au dataset retenu (+163 %
    entre deux candidats), qui avait obligé à épingler arbitrairement l'un
    d'eux ;
  * un inventaire indéfendable en revue : la composition du déchet ne
    correspondait pas à celle du produit fabriqué.
La ventilation par `COMPO` supprime les deux problèmes d'un coup, et le refus
de tri du scénario recyclage réutilise exactement la même mécanique.

════════════════════════════════════════════════════════════════════════════
D'OÙ VIENNENT LES MASSES ? (commentaire 5 du reviewer)

  masse enfouie d'une matière k    = m_panneaux_kg × COMPO[k]
  masse recyclée d'une matière k   = m_panneaux_kg × COMPO[k] × RECUP[k]
  crédit (closed-loop uniquement)  = masse recyclée × SUBST[k]

* `m_panneaux_kg` = nombre de modules × masse unitaire des fiches CS Wismar
  (26,0 kg pour le Diamond M108, 22,0 kg pour les Excellent M54/M32) ;
* `COMPO` = composition massique d'un module bi-verre c-Si (Phénix NZ,
  Latunussa et al. 2016 « FRELP », IEA-PVPS T12) ;
* `RECUP` = taux de récupération annoncés par le recycleur (Phénix,
  « jusqu'à 98 % ») ;
* `SUBST` = facteur de qualité de substitution (downcycling). ⚠ La closed-loop
  allocation *stricte* au sens d'ISO 14044 crédite 1:1, sans dégradation de
  qualité (la dégradation appartient à la CFF et à l'open-loop). Mettre tous
  les `SUBST` à 1 donne donc la borne basse stricte ; les valeurs retenues ici
  sont un compromis prudent, à annoncer comme tel.

⚠ Cohérence entrée/sortie : `checks.verifier_masse_panneaux()` compare
`m_panneaux_kg` à la masse implicite de l'inventaire de fabrication (verre +
cadre + EVA + backsheet évalués sur les mêmes paramètres). Un écart supérieur à
15 % signale que la fabrication et la fin de vie ne décrivent pas le même
module — c'est précisément le point soulevé par le reviewer.
"""

from __future__ import annotations

import lca_algebraic as agb

from . import config
from .parametres import U

NOM_ENFOUISSEMENT = config.nom("[EoL] filiere actuelle (Polynesie)")
NOM_RECYCLAGE_CUTOFF = config.nom("[EoL] recyclage NZ - cut-off")
NOM_RECYCLAGE_CL = config.nom("[EoL] recyclage NZ - closed-loop (credits)")
NOM_SWITCH = config.nom("fin de vie des panneaux")

# Modalités d'incinération, en TABLE DÉCLARATIVE : nom -> (fractions brûlées,
# créditer l'électricité). Ajouter une variante est une ligne, pas un bloc de
# code — et retirer les deux variantes créditées, si elles encombrent, l'est
# aussi. Les flotteurs seuls d'abord (la question initiale), puis les flotteurs
# + l'élastomère d'ancrage, pour s'aligner sur Seitz et al. 2026.
INCINERATION_SCENARIOS = {
    "incineration_flotteurs":           (("eps", "mdpe"), False),
    "incineration_flotteurs_valorisee": (("eps", "mdpe"), True),
    "incineration_polymeres":           (("eps", "mdpe", "caoutchouc"), False),
    "incineration_polymeres_valorisee": (("eps", "mdpe", "caoutchouc"), True),
}

MODALITES = (("enfouissement", "recyclage_cutoff", "recyclage_closed_loop")
             + tuple(INCINERATION_SCENARIOS))

# Les trois premières sont les modalités HISTORIQUES : ce sont elles que
# `resultats.comparer_fin_de_vie()` et `resultats.SCENARIOS_EOL` affichent, et
# rien de ce qui suit ne change les figures existantes. Les deux dernières sont
# une SENSIBILITÉ ajoutée le 04/10/2026, à lire avec
# `resultats.sensibilite_incineration()`.
MODALITES_PRINCIPALES = MODALITES[:3]
MODALITES_INCINERATION = tuple(INCINERATION_SCENARIOS)

# Renseigné par `construire()`. Les rôles d'incinération étant les seuls rôles
# OPTIONNELS de la résolution ecoinvent, les deux modalités correspondantes
# peuvent être indisponibles sur une base donnée ; ce drapeau évite que
# `resultats.sensibilite_incineration()` sorte alors un tableau de zéros.
INCINERATION_DISPONIBLE = None

LIBELLES = {
    "enfouissement": "Filière actuelle (métaux exportés, modules enfouis)",
    "recyclage_cutoff": "Recyclage NZ — cut-off",
    "recyclage_closed_loop": "Recyclage NZ — closed-loop (crédits)",
    "incineration_flotteurs": "Flotteurs incinérés — cut-off",
    "incineration_flotteurs_valorisee": "Flotteurs incinérés — électricité créditée",
    "incineration_polymeres": "Flotteurs + élastomère incinérés — cut-off",
    "incineration_polymeres_valorisee": "Flotteurs + élastomère — électricité créditée",
}

METHODO = {
    "enfouissement": "Filière telle qu'elle existe : métaux propres remis à "
                     "la filière au point de collecte (cut-off, donc ni charge "
                     "ni crédit au-delà), DEEE exportés en France, modules et "
                     "polymères enfouis faute d'exutoire. RÉFÉRENCE.",
    "recyclage_cutoff": "Simple cut-off (100/0). Cohérent avec la base "
                        "ecoinvent-cutoff. RÉFÉRENCE POUR LE RECYCLAGE. Impact "
                        "intégralement positif : le bénéfice va à l'utilisateur "
                        "du secondaire.",
    "recyclage_closed_loop": "Closed-loop allocation (0/100), avoided burden. "
                             "BORNE BASSE de sensibilité méthodologique — "
                             "double-compte avec une base cutoff, ne pas "
                             "publier comme résultat principal.",
    "incineration_flotteurs": "Référence, mais les 504 kg de polymères des "
                              "flotteurs partent en incinération d'ordures "
                              "ménagères au lieu de la décharge locale. "
                              "Cut-off : l'électricité et la chaleur "
                              "récupérées quittent le système sans charge, "
                              "donc sans crédit pour nous. SENSIBILITÉ "
                              "PROSPECTIVE — la Polynésie n'a pas "
                              "d'incinérateur.",
    "incineration_flotteurs_valorisee": "Même scénario physique, mais "
                              "l'électricité récupérée est créditée contre le "
                              "réseau au fioul de Raiatea (avoided burden). "
                              "BORNE BASSE : même objection méthodologique que "
                              "le closed-loop face à une base cut-off.",
    "incineration_polymeres": "Comme « incineration_flotteurs », plus "
                              "l'élastique SBR de l'ancrage (~9,5 kg). Lot "
                              "aligné sur Seitz et al. 2026, qui incinèrent "
                              "les élastomères : l'écart de masse est marginal, "
                              "c'est un alignement de CONVENTION qui permet de "
                              "dire que la comparaison avec cette référence "
                              "porte sur le même périmètre de fin de vie. "
                              "Cordes HMPE et poulie PA6 restent enfouies.",
    "incineration_polymeres_valorisee": "Même lot, électricité créditée. "
                              "BORNE BASSE, même objection que ci-dessus.",
}

PERIMETRE = """
════════════════════════════════════════════════════════════════════════════
PÉRIMÈTRE : TOUT LE SYSTÈME (extension août 2026)

Jusqu'ici la fin de vie ne traitait QUE les modules. Le système était annoncé
cradle-to-grave, mais 606 kg d'aluminium de structure, ~232 kg d'EPS, ~272 kg
de MDPE, le cuivre du câble, la visserie inox, l'ancrage et les onduleurs
n'atteignaient jamais la tombe. Incohérence de frontières, et surtout : le plus
gros gisement de crédit du système — l'aluminium — était absent.

Les filières retenues ne sont pas des hypothèses de confort, elles suivent la
réalité polynésienne (guide des déchets des entreprises de PF, Fenua Ma) :

* **métaux non ferreux et ferreux** — aluminium, inox, acier, cuivre. Le guide
  PF est explicite : « ces déchets, non souillés, présentent un potentiel de
  valorisation et doivent donc être orientés vers des filières de recyclage
  (export vers l'étranger en l'absence de filière de valorisation locale) ».
  Fenua Ma exporte les métaux vers la **Nouvelle-Zélande** — la même route que
  nos modules. L'aluminium n'est PAS un déchet inerte et ne s'enfouit pas : au
  cours de la ferraille, 600 kg d'alu marin partent d'eux-mêmes.
* **modules PV** — DEEE, export Nouvelle-Zélande (recycleur Phénix).
* **onduleurs et électronique** — DEEE. Fenua Ma les exporte vers la
  **France**, d'où une distance bien plus longue (17 000 km).
* **EPS, MDPE, polyester, caoutchouc, verre** — aucune filière locale :
  décharge à Raiatea, ventilée par fraction matière.

⚠ POINT À METTRE EN AVANT DANS LE RAPPORT. En GWP, l'EPS ne pèse rien. Mais
c'est le seul flux de cette fin de vie qui pose une vraie question
environnementale : ~232 kg de polystyrène expansé sans aucun exutoire, sur un
lagon corallien, renouvelés tous les 20 ans. Le chiffre carbone ne le dira pas
— l'analyse qualitative, si.

════════════════════════════════════════════════════════════════════════════
"""

# ── Hypothèses (toutes documentées, toutes modifiables ici) ────────────────
COMPO = {              # fraction massique d'un module bi-verre c-Si (somme = 1)
    "verre": 0.75,     # 2 vitres
    "aluminium": 0.10,  # cadre
    "polymeres": 0.06,  # EVA + boîte de jonction (non recyclés)
    "silicium": 0.04,   # cellules
    "cuivre": 0.010,    # rubans + connecteurs
    "argent": 0.0005,   # métallisation
    # ── Plomb et étain SORTIS du fourre-tout « autres » (05/10/2026) ──────
    # Fractions reprises de IEA-PVPS T12-12:2017 (Wambach & Heath, « Life
    # Cycle Inventory of Current Photovoltaic Module Recycling »), Table 2
    # p. 12, composition d'un module standard 60 cellules : Pb 0,033 g/Wp
    # = 0,04 % de la masse, Sn 0,056 g/Wp = 0,07 %.
    #
    # POURQUOI ÇA COMPTE MALGRÉ DES MASSES DÉRISOIRES (0,21 kg de plomb et
    # 0,36 kg d'étain pour 520 kg de modules) : la toxicité ne suit pas la
    # masse. Les facteurs de caractérisation du plomb en toxicité humaine et
    # en écotoxicité sont supérieurs de plusieurs ordres de grandeur à ceux de
    # l'aluminium. Laisser 0,21 kg de plomb dans un poste « divers » routé sur
    # une décharge d'aluminium, c'est rendre invisible le seul métal vraiment
    # toxique du module.
    #
    # ⚠ CE QUE CE CHIFFRE N'EST PAS. La Table 2 décrit un module de 2013. Les
    # modules récents réduisent ou suppriment le plomb des soudures, et les
    # modules CS de Wismar n'ont PAS été vérifiés sur ce point. 0,04 % est donc
    # un MAJORANT plausible en attendant une déclaration fournisseur, à
    # demander avec le reste de la traçabilité. Si la réponse est « sans
    # plomb », cette ligne tombe à 0 et c'est un résultat en soi.
    #
    # Les deux fractions sont PRÉLEVÉES sur « autres » (0,0395 -> 0,0384) : la
    # composition n'est pas rebasée sur la table IEA, aucune autre ligne ne
    # bouge, et la somme reste exactement 1. Un seul changement à la fois.
    "plomb": 0.0004,    # soudures des rubans d'interconnexion
    "etain": 0.0007,    # soudures, idem
    "autres": 0.0384,   # colles, encapsulant de boîte de jonction, divers
}

RECUP = {              # taux de récupération annoncés par le recycleur
    "verre": 0.95, "aluminium": 0.95, "polymeres": 0.00,
    "silicium": 0.65, "cuivre": 0.90, "argent": 0.90, "autres": 0.50,
    # Le plomb des soudures n'est PAS récupéré dans les filières c-Si
    # documentées : il se disperse entre la fraction métaux non ferreux et la
    # fraction polymère incinérée. 0 est ici le choix représentatif, pas un
    # choix prudent — et c'est ce qui fait que le recyclage ne le fait pas
    # disparaître. L'étain suit « autres », faute de donnée propre.
    "plomb": 0.00, "etain": 0.50,
}

SUBST = {              # qualité de substitution du secondaire (1 = 1:1)
    "verre": 0.90,     # calcin
    "aluminium": 1.00,
    "polymeres": 0.00,
    "silicium": 0.50,  # qualité métallurgique, pas solaire
    "cuivre": 1.00, "argent": 1.00, "autres": 0.50,
    "plomb": 0.00, "etain": 0.50,
}

# Vers quelle filière de décharge part chaque fraction du module.
# Les rôles sont résolus dans ecoinvent.DECHARGE ; si l'un manque dans ta
# version de la base, sa masse bascule sur `ROLE_REPLI` avec un avertissement.
FILIERE = {
    "verre": "decharge_verre",
    "aluminium": "decharge_metal",
    "inox": "decharge_metal",
    "acier": "decharge_metal",
    "polymeres": "decharge_plastique",   # EVA + boîte de jonction du module
    "eps": "decharge_plastique",
    "mdpe": "decharge_plastique",
    "hmpe": "decharge_plastique",        # corde d'ancrage
    "pa6": "decharge_plastique",         # poulie d'ancrage
    "caoutchouc": "decharge_plastique",  # élastique Seaflex
    # ⚠ CORRECTION DU 15/09/2026. Les quatre fractions ci-dessous partaient sur
    # « waste plastic, consumer electronics » — c'est-à-dire que 9 % de la masse
    # du module, qui est MÉTALLIQUE (cellules silicium, rubans cuivre,
    # métallisation argent, étain), était traitée comme du plastique
    # d'électronique grand public. C'est exactement le travers que la
    # ventilation par fraction de la v22 avait corrigé pour le verre, et qui
    # subsistait ici. Elles rejoignent donc la filière métal.
    "silicium": "decharge_metal",
    # ⚠ PAS DE DÉCHARGE PAR MÉTAL DANS ecoinvent 3.11 (vérifié le 05/10/2026
    # dans Activity Browser) : ni pour le cuivre, ni pour l'étain, ni pour le
    # plomb — la base ne propose que l'incinération municipale. Et ce n'est pas
    # un trou : la description du dataset d'incinération du cuivre l'énonce,
    # « pure, isolated copper fractions will not be disposed in incinerators,
    # but rather go to recycling ». Une fraction métallique pure n'a pas de voie
    # d'élimination modélisée parce qu'elle n'en a pas dans la réalité.
    #
    # Ces fractions restent donc sur `decharge_metal`, comme avant. C'est une
    # approximation — le lixiviat de l'aluminium pour celui du plomb — et elle
    # est à déclarer dans les limites. Les masses en jeu sont de 0,208 kg de
    # plomb, 0,364 d'étain et 0,260 d'argent par plateforme.
    #
    # ⚠ Le cuivre n'est de toute façon PAS enfoui au scénario de référence :
    # ses 411,7 kg sortent au point de collecte avec la ferraille. Il n'y
    # revient que comme refus de tri du recyclage (5 %, ~20,6 kg).
    "cuivre": "decharge_metal",
    "etain": "decharge_metal",
    "plomb": "decharge_metal",
    "argent": "decharge_metal",
    "autres": "decharge_metal",
    # Seule l'électronique des répéteurs reste en filière DEEE : un boîtier CPL
    # est bien du plastique chargé, pas du métal massif.
    "electronique": "decharge_deee",
}
ROLE_REPLI = "enfouissement"   # toujours résolu (ecoinvent.DISPOSAL)

# ── Repli PAR FRACTION, avant le repli générique ──────────────────────────
# `ROLE_REPLI` est une décharge de PLASTIQUE : y renvoyer un métal dont le rôle
# dédié manque serait pire que l'état d'avant. Pour les fractions dont la
# filière est optionnelle, on se replie donc d'abord sur `decharge_metal` —
# exactement ce que faisait le modèle jusqu'au 05/10/2026 — et le repli
# générique ne sert plus que de dernier filet.
# ── Filières d'export réelles (Polynésie française) ────────────────────────
# Destination de chaque matière quand on est dans un scénario « filière
# réelle ». « local » = pas d'exutoire, décharge à Raiatea.
DESTINATION = {
    "aluminium": "nz", "inox": "nz", "acier": "nz", "cuivre": "nz",
    "verre": "nz", "silicium": "nz", "argent": "nz",     # partent AVEC les modules
    "polymeres": "nz",                                    # idem, refus de tri sur place
    "autres": "nz",
    "plomb": "nz", "etain": "nz",                         # soudures, avec les modules
    "electronique": "france",                             # DEEE, filière Fenua Ma
    "eps": "local", "mdpe": "local",
    "hmpe": "local", "pa6": "local", "caoutchouc": "local",
}

# Taux de récupération PAR MATIÈRE une fois dans la filière d'export.
# Complète RECUP (qui ne couvrait que le module) pour les matières du reste du
# système. Un métal massif propre se récupère bien mieux qu'une fraction de
# laminé PV, d'où des taux plus élevés.
RECUP_SYSTEME = {
    "aluminium": 0.95, "inox": 0.90, "acier": 0.90, "cuivre": 0.95,
    "electronique": 0.50,
    "eps": 0.0, "mdpe": 0.0, "hmpe": 0.0, "pa6": 0.0, "caoutchouc": 0.0,
}
SUBST_SYSTEME = {
    "aluminium": 1.00, "inox": 0.90, "acier": 0.90, "cuivre": 1.00,
    "electronique": 0.30,      # récupération de métaux, forte dégradation
    "eps": 0.0, "mdpe": 0.0, "hmpe": 0.0, "pa6": 0.0, "caoutchouc": 0.0,
}

DIST_GOELETTE_KM = 220.0        # Raiatea -> Papeete (regroupement)
DIST_NZ_KM = 4000.0             # Papeete -> Auckland (métaux et modules)
DIST_FRANCE_KM = 17000.0        # Papeete -> France (DEEE, filière Fenua Ma)
DIST_EXPORT_KM = {"nz": DIST_NZ_KM, "france": DIST_FRANCE_KM, "local": 0.0}

# Électricité du procédé, scindée de part et d'autre du point de substitution.
# C'est CE découpage qui matérialise le cut-off dans l'inventaire :
KWH_DEMANTELEMENT_PAR_T = 250.0  # dépose cadre + JB, délamination, tri mécanique
                                 # → AVANT le point de substitution, donc porté
                                 #   par le détenteur du déchet dans LES DEUX
                                 #   modèles (ordre de grandeur FRELP).
KWH_AFFINAGE_PAR_T = 0.0         # etching du silicium, purification du verre
                                 # → APRÈS le point de substitution : exclu en
                                 #   cut-off, inclus en closed-loop. Laissé à 0
                                 #   faute de donnée primaire ; renseigner
                                 #   depuis Latunussa et al. 2016 si besoin.

# ── Incinération des flotteurs (scénario de sensibilité) ──────────────────
#
# Quelles fractions partent au feu. Volontairement une CONSTANTE et non un
# paramètre : élargir le scénario aux autres polymères sans exutoire (corde
# HMPE, poulie PA6, élastique SBR, ~12 kg à eux trois) se fait en ajoutant
# leurs clés ici — mais ils ne sont pas des flotteurs, et la question posée
# portait sur les flotteurs.
FILIERE_INCINERATION = {
    "eps": "incineration_eps",
    "mdpe": "incineration_mdpe",
    "caoutchouc": "incineration_caoutchouc",   # élastique SBR de l'ancrage
}

# ── Clés matière que `matieres()` AGRÈGE sur plusieurs postes ─────────────
# Le piège est ici, et il ne se voit pas à la lecture de `FILIERE` : « mdpe »
# additionne la peau des flotteurs (272,2 kg) et les gaines du câble d'export
# et des liaisons onduleur (~152 kg). Brûler la clé entière brûlerait des
# gaines qui restent enfouies avec le câble — on ne déterre pas un câble
# sous-marin pour en récupérer l'enveloppe. Pour ces clés on retourne donc à
# la source du poste concerné.
#
# « eps » ne vient que de `structure`, « caoutchouc » que de `ancrage` : leurs
# clés sont exactes, elles ne figurent pas ici.
FRACTIONS_AGREGEES = {"mdpe": "structure"}

# Pouvoir calorifique inférieur, MJ/kg. Valeurs d'usage pour des polymères
# purs et secs ; elles ne servent QU'À chiffrer le crédit d'électricité de la
# modalité « valorisee », jamais la combustion elle-même — celle-ci est portée
# par le dataset ecoinvent, qui a sa propre stœchiométrie.
PCI_MJ_PAR_KG = {"eps": 40.0, "mdpe": 43.0, "caoutchouc": 35.0}

# Rendement ÉLECTRIQUE NET d'un incinérateur insulaire, déduit du projet
# polynésien de Nive'e : 70 000 t/an d'ordures ménagères pour 30,3 GWh bruts
# dont 26 GWh livrés au réseau. À 10 MJ/kg de PCI pour des OM, cela donne
#   η_brut = 109 TJ / 700 TJ = 15,6 %   puis   η_net = 15,6 × 26/30,3 = 13,4 %.
#
# ⚠ TROIS FAIBLESSES À ASSUMER si ce chiffre est cité :
#   1. la source de presse écrit « 30,3 GW par an », lu ici comme 30,3 GWh ;
#   2. le PCI des OM polynésiennes n'est pas documenté, 10 MJ/kg est une
#      valeur d'usage ;
#   3. un four calé sur des OM à 10 MJ/kg ne tourne pas au même rendement
#      alimenté en polymères purs à 40 — en pratique on les co-incinère, d'où
#      le choix de garder le rendement du four et non un rendement idéalisé.
# C'est pour ces trois raisons que la modalité créditée est une BORNE et pas
# un résultat : elle dit « au mieux », pas « voilà ».
RENDEMENT_ELEC_INCINERATION = 0.134

# Électricité nette récupérée par kg brûlé, kWh/kg. Dérivée, pas saisie.
KWH_ELEC_PAR_KG = {
    matiere: PCI_MJ_PAR_KG[matiere] * RENDEMENT_ELEC_INCINERATION / 3.6
    for matiere in FILIERE_INCINERATION
}

assert set(FILIERE_INCINERATION) <= set(PCI_MJ_PAR_KG), \
    "toute fraction incinérée doit avoir un PCI"

assert abs(sum(COMPO.values()) - 1.0) < 1e-9, "COMPO doit sommer à 1"

FRACTION_REFUS = sum(COMPO[k] * (1 - RECUP[k]) for k in COMPO)
TAUX_RECUP_MOYEN = sum(COMPO[k] * RECUP[k] for k in COMPO)


# ══════════════════════════════════════════════════════════════════════════
# Construction
# ══════════════════════════════════════════════════════════════════════════
def construire(ctx):
    """Renvoie (activité switch, {modalité: activité}) pour les cinq modalités.

    Trois modalités principales (enfouissement, recyclage cut-off, recyclage
    closed-loop) plus deux de sensibilité sur l'incinération des flotteurs,
    ces dernières construites seulement si les datasets d'incinération ont été
    résolus — cf. `INCINERATION_DISPONIBLE`.
    """
    scenarios = {
        # La clé « enfouissement » est CONSERVÉE pour ne pas casser les appels
        # existants, mais elle ne décrit plus un enfouissement général : les
        # métaux partent, seuls les modules et les polymères restent.
        "enfouissement": _filiere(ctx, NOM_ENFOUISSEMENT,
                                  modules_exportes=False, crediter=False),
        "recyclage_cutoff": _filiere(ctx, NOM_RECYCLAGE_CUTOFF,
                                     modules_exportes=True, crediter=False),
        "recyclage_closed_loop": _filiere(ctx, NOM_RECYCLAGE_CL,
                                          modules_exportes=True, crediter=True),
    }

    # ── Sensibilité du 04/10/2026 : les flotteurs au feu ──────────────────
    # La RÉFÉRENCE, à ceci près que les polymères des flotteurs partent en
    # incinération au lieu de la décharge locale. Un seul paramètre change.
    #
    # ⚠ LE SWITCH EXIGE UNE ACTIVITÉ PAR VALEUR DE L'ENUM. Si les datasets
    # d'incinération manquent, on ne peut donc pas simplement omettre ces deux
    # modalités : on les fait pointer sur la référence, et on le dit assez
    # fort pour qu'un tableau identique à la référence ne soit pas lu comme un
    # résultat. C'est le seul endroit du modèle où un repli est toléré, parce
    # que l'alternative est de faire échouer tout le run pour une variante.
    global INCINERATION_DISPONIBLE
    INCINERATION_DISPONIBLE = getattr(ctx.ei, "incineration_eps", None) is not None
    if INCINERATION_DISPONIBLE:
        for cle, (fractions, crediter_energie) in INCINERATION_SCENARIOS.items():
            scenarios[cle] = _filiere(
                ctx, config.nom(f"[EoL] {LIBELLES[cle]}"),
                modules_exportes=False, crediter=False,
                fractions_incinerees=fractions,
                crediter_energie=crediter_energie)
    else:
        for cle in MODALITES_INCINERATION:
            scenarios[cle] = scenarios["enfouissement"]

    switch = agb.newSwitchAct(ctx.db, NOM_SWITCH, ctx.p.fin_de_vie, scenarios)
    switch.updateMeta(**{config.AXE: "FinDeVie"})

    print(f"  fin de vie : SYSTÈME ENTIER (modules + structure + flotteurs + "
          f"ancrage + câble + onduleurs)")
    print(f"    modules seuls : récupération moyenne {TAUX_RECUP_MOYEN*100:.1f} % "
          f"| refus {FRACTION_REFUS*100:.1f} %")
    # On imprime le routage de la RÉFÉRENCE, pas le dictionnaire brut : depuis
    # le 01/10/2026 la destination d'une matière dépend du scénario, et afficher
    # DESTINATION tel quel laissait croire que les modules partaient déjà.
    groupes = {}
    for matiere in sorted(matieres_du_systeme()):
        if matiere in FERRAILLE:
            cle = "ferraille, sortie au point de collecte"
        else:
            cle = {"nz": "export Nouvelle-Zélande",
                   "france": "export France (DEEE)",
                   "local": "décharge locale, pas d'exutoire"}[
                       _destination(matiere, modules_exportes=False)]
        groupes.setdefault(cle, []).append(matiere)
    print("    RÉFÉRENCE — filière telle qu'elle existe :")
    for cle, mats in sorted(groupes.items()):
        print(f"      {cle:<40} {', '.join(mats)}")
    print("    PROSPECTIF — les modules partent en plus en Nouvelle-Zélande "
          f"({DIST_GOELETTE_KM:.0f} + {DIST_NZ_KM:.0f} km)")
    print(f"  {len(MODALITES_PRINCIPALES)} modalités principales : "
          f"{', '.join(MODALITES_PRINCIPALES)} "
          f"(référence = « enfouissement », qui n'enfouit plus les métaux)")
    if not INCINERATION_DISPONIBLE:
        print("    ⚠⚠ incinération des flotteurs INDISPONIBLE : les deux "
              "modalités pointent sur la RÉFÉRENCE et ne disent donc RIEN. "
              "Lance ecoinvent.diagnostic_incineration(), corrige "
              "ecoinvent.INCINERATION, reconstruis.")
    else:
        print(f"    + {len(MODALITES_INCINERATION)} modalités "
              f"d'incinération (sensibilité prospective) :")
        for cle, (fractions, credit) in INCINERATION_SCENARIOS.items():
            print(f"      {cle:36s} {'+'.join(fractions)}"
                  f"{'  [électricité créditée]' if credit else ''}")
        print(f"      valorisation à {RENDEMENT_ELEC_INCINERATION*100:.1f} % "
              f"électrique nets")
    return switch, scenarios


def _decharge(ctx, masses_par_fraction, exchanges=None):
    """Ajoute à `exchanges` la mise en décharge d'un dict {fraction: masse}.

    Regroupe les fractions qui partagent la même filière, applique la
    convention de signe propre à chaque dataset, et bascule sur le rôle de
    repli (en le signalant) toute fraction dont la filière est introuvable.
    """
    from . import ecoinvent

    exchanges = {} if exchanges is None else exchanges
    for fraction, masse in masses_par_fraction.items():
        role = FILIERE.get(fraction, ROLE_REPLI)
        dataset = getattr(ctx.ei, role, None)
        if dataset is None:
            dataset = getattr(ctx.ei, ROLE_REPLI)
            if role not in _REPLIS_SIGNALES:
                print(f"    ⚠ filière « {role} » introuvable dans "
                      f"{config.EI} — fraction « {fraction} » repliée sur le "
                      f"dataset générique. Lance "
                      f"ecoinvent.diagnostic_decharge() pour compléter "
                      f"ecoinvent.DECHARGE.")
                _REPLIS_SIGNALES.add(role)
        signe = ecoinvent.signe_dechet(dataset)
        exchanges[dataset] = exchanges.get(dataset, 0) + signe * masse
    return exchanges


_REPLIS_SIGNALES = set()


def _masses_a_incinerer(ctx, fractions, m=None) -> dict:
    """Masse réellement brûlée, fraction par fraction, sur la durée de vie (kg).

    Pour une clé listée dans `FRACTIONS_AGREGEES`, on ne lit PAS `matieres()`
    mais la fonction `masses()` du poste d'origine : « mdpe » y mélange la peau
    des flotteurs et les gaines du câble, et seule la première part au feu.
    Pour les autres, la clé matière est exacte et `matieres()` suffit.

    Les masses renvoyées sont des expressions symboliques, pas des nombres :
    `structure.masses()` compte déjà les deux jeux de flotteurs de la durée de
    vie, et les paramètres restent libres pour le Monte-Carlo.
    """
    from . import structure

    m = matieres(ctx) if m is None else m
    sources = {"structure": structure.masses(ctx)}

    masses = {}
    for fraction in fractions:
        if fraction in FRACTIONS_AGREGEES:
            masses[fraction] = sources[FRACTIONS_AGREGEES[fraction]][fraction]
        elif fraction in m:
            masses[fraction] = m[fraction]
    return masses


def _incinerer(ctx, masses_par_fraction, exchanges, crediter_energie=False):
    """Ajoute à `exchanges` l'incinération d'un dict {fraction: masse}.

    Même mécanique que `_decharge`, à deux différences près :
      * le dataset est épinglé par `FILIERE_INCINERATION`, polymère par
        polymère, et il n'y a PAS de rôle de repli — brûler du polystyrène
        dans un dataset de plastique moyen ferait perdre les 10 % d'écart de
        stœchiométrie et de PCI qui justifient d'avoir deux rôles ;
      * si `crediter_energie`, l'électricité nette récupérée est portée en
        échange NÉGATIF sur le réseau au fioul local (avoided burden).

    Lève LookupError si le dataset manque, plutôt que de se replier en
    silence : cette modalité a un coût méthodologique assumé, elle ne doit pas
    pouvoir tourner sur un dataset choisi par défaut.
    """
    from . import ecoinvent

    for fraction, masse in masses_par_fraction.items():
        role = FILIERE_INCINERATION[fraction]
        dataset = getattr(ctx.ei, role, None)
        if dataset is None:
            raise LookupError(
                f"Rôle « {role} » introuvable : les modalités "
                f"d'incinération ne peuvent pas être construites. "
                f"Lance ecoinvent.diagnostic_incineration() pour voir les noms "
                f"réels de ta base, puis corrige ecoinvent.INCINERATION. "
                f"Les trois modalités principales, elles, ne dépendent pas de "
                f"ce rôle et restent utilisables."
            )
        signe = ecoinvent.signe_dechet(dataset)
        _ajouter(exchanges, dataset, signe * masse)

        if crediter_energie:
            # ⚠ Crédit contre le réseau AU FIOUL de Raiatea, pas contre un mix
            # moyen : c'est bien cette électricité-là qu'un incinérateur
            # polynésien déplacerait. C'est aussi ce qui rend le crédit gros —
            # 0,914 kg CO₂-eq/kWh — et donc la borne basse large.
            if ctx.ei.elec_fioul is None:
                raise LookupError("elec_fioul introuvable : pas de crédit "
                                  "d'électricité possible.")
            kwh = masse * (KWH_ELEC_PAR_KG[fraction] * U("kWh/kg"))
            _ajouter(exchanges, ctx.ei.elec_fioul, -kwh)
    return exchanges


def matieres(ctx) -> dict:
    """Masse de CHAQUE matière du système entier, en fin de vie (kg).

    C'est le pendant exact des inventaires de fabrication : chaque poste expose
    désormais une fonction `masses(ctx)`, et on la réutilise ici. Ce qui est
    fabriqué est donc, par construction, ce qui est mis au rebut — plus aucune
    divergence possible entre les deux bouts du cycle de vie.
    """
    from . import ancrage, cable, onduleurs, structure, systeme

    p = ctx.p
    m = {k: p.m_panneaux_kg * COMPO[k] for k in COMPO}      # modules

    s = structure.masses(ctx)                                # structure
    m["aluminium"] = m.get("aluminium", 0) + s["aluminium"]
    m["inox"] = s["inox"]
    m["eps"] = s["eps"]
    m["mdpe"] = s["mdpe"]

    a = ancrage._masses(p)                                   # ancrage
    # La corde est en HMPE depuis le 15/09/2026, plus en polyester : elle change
    # donc de famille ici aussi, sans quoi la fabrication et la fin de vie
    # décriraient deux matériaux différents.
    m["hmpe"] = a["corde"]
    m["caoutchouc"] = a["elastique"]
    m["pa6"] = a["poulie"]
    m["acier"] = a["chaine"] + a["ancres"] + a["manille"]

    c = cable.masses(ctx)                                    # câble (prorata P)
    part = cable.part_cable(p)
    m["cuivre"] = m.get("cuivre", 0) + c["cuivre"] * part
    m["mdpe"] = m["mdpe"] + c["gaine"] * part

    o = onduleurs.masses(ctx)                                # onduleurs
    m["electronique"] = o["electronique"]
    m["cuivre"] = m["cuivre"] + o["cuivre"]
    # L'enveloppe du câble module→onduleur suit la même filière que celle du
    # câble d'export (16/09/2026) : ce qui est fabriqué est ce qui est jeté.
    m["mdpe"] = m["mdpe"] + o["gaine"]

    # NB : les répéteurs portent déjà leur propre fin de vie DEEE dans
    # `repeteurs.py` — on ne les reprend pas ici, sous peine de double compte.
    return m


def _recup(matiere):
    return RECUP_SYSTEME.get(matiere, RECUP.get(matiere, 0.0))


def _subst(matiere):
    return SUBST_SYSTEME.get(matiere, SUBST.get(matiere, 0.0))


# ── Matières dont la destination DÉPEND DU SCÉNARIO ───────────────────────
# Le module PV n'a aucune filière en Polynésie : dans le scénario de référence
# il reste à Raiatea, et ses fractions avec lui. C'est le SEUL flux que le
# scénario prospectif déplace, et c'est ce qui rend la comparaison lisible —
# auparavant les deux scénarios différaient par une dizaine de choses à la fois.
# « plomb » et « etain » y figurent depuis le 05/10/2026 : sans cela leur
# destination retombait sur le défaut « local » dans LES DEUX scénarios, et le
# scénario de recyclage n'emportait pas les soudures avec les modules.
MATIERES_MODULE = ("verre", "silicium", "argent", "polymeres", "autres",
                   "plomb", "etain")

# ── Ferraille propre : elle quitte le système au POINT DE COLLECTE ─────────
# ⚠ DÉCISION DU 01/10/2026, et c'est une correction, pas un raffinement.
#
# Sous cut-off, le détenteur du déchet porte ce qui va JUSQU'AU point de
# substitution et rien au-delà. Pour un métal propre qui a un marché, ce point
# est atteint très tôt : une ferraille d'aluminium est un produit, pas un
# déchet. On impute donc le regroupement jusqu'à Papeete — ce qu'il faut bien
# faire pour s'en défaire — et rien de plus : ni le fret vers le repreneur, ni
# la refonte, ni aucun crédit.
#
# Ne pas facturer l'enfouissement de ces métaux n'est PAS s'attribuer un
# bénéfice de recyclage : c'est cesser d'imputer une charge qui n'a pas lieu.
# Le guide des déchets des entreprises de PF impose d'orienter les métaux
# propres vers une filière, et Fenua Ma les exporte effectivement. La version
# précédente les enfouissait tous — 700 kg d'aluminium compris — ce qui n'était
# pas une hypothèse prudente mais un flux inventé. ISO 14044 demande de la
# représentativité, pas du pessimisme.
#
# En closed-loop le point de substitution est reporté en aval : la ferraille
# porte alors toute la chaîne ET reçoit le crédit de primaire évité. Même
# réalité industrielle, autre règle d'allocation — c'est exactement ce que les
# deux modalités sont censées encadrer.
FERRAILLE = ("aluminium", "inox", "acier", "cuivre")


def matieres_du_systeme() -> tuple:
    """Les clés de matière que `matieres()` produit, sans avoir besoin de ctx.

    Sert aux impressions de contrôle et à la documentation : `matieres(ctx)`
    demande un contexte Brightway construit, ce qui est trop cher pour un print.
    """
    return tuple(dict.fromkeys(tuple(COMPO) + tuple(DESTINATION)))


def _destination(matiere, modules_exportes: bool) -> str:
    """Où part une matière, compte tenu du scénario."""
    if matiere in MATIERES_MODULE and not modules_exportes:
        return "local"
    return DESTINATION.get(matiere, "local")


def _filiere(ctx, nom, modules_exportes: bool, crediter: bool,
             fractions_incinerees: tuple = (),
             crediter_energie: bool = False):
    """Construit une modalité de fin de vie.

    Les trois modalités décrivent la MÊME réalité industrielle. Deux choses les
    distinguent : le sort des modules — seul flux sans exutoire à ce jour — et
    la place du point de substitution, qui dépend de la matière (tôt pour une
    ferraille propre, après démantèlement et tri pour un laminé PV).

    Parameters
    ----------
    modules_exportes : bool
        False = filière telle qu'elle existe aujourd'hui, les modules restent
        à Raiatea. True = scénario prospectif, ils partent au recycleur.
    crediter : bool
        Allocation closed-loop : l'affinage aval entre dans le périmètre et la
        production primaire évitée est créditée (échanges négatifs).
    fractions_incinerees : tuple
        Clés matière PRÉLEVÉES sur le refus de décharge et envoyées en
        incinération — cf. `INCINERATION_SCENARIOS`. Pour « mdpe », seule la
        peau des flotteurs part au feu : les gaines du câble et des liaisons
        onduleur restent enfouies avec le câble, qu'on ne déterre pas (cf.
        `FRACTIONS_AGREGEES`).
    crediter_energie : bool
        Avec `fractions_incinerees`, crédite l'électricité nette récupérée
        contre le réseau au fioul local. Avoided burden, donc BORNE BASSE.
    """
    m = matieres(ctx)
    exchanges, refus = {}, {}
    tonne = 1000.0 * U("kg/ton")

    # ── logistique et procédé, matière par matière ────────────────────────
    for matiere, masse in m.items():
        destination = _destination(matiere, modules_exportes)
        masse_t = masse / tonne

        if destination == "local":
            refus[matiere] = masse          # pas d'exutoire : 100 % en décharge
            continue

        # Regroupement Raiatea -> Papeete, porté dans tous les cas.
        _ajouter(exchanges, ctx.ei.fret_goelette or ctx.ei.fret_maritime,
                 masse_t * (DIST_GOELETTE_KM * U("km")))

        if matiere in FERRAILLE and not crediter:
            continue          # point de substitution atteint : sortie du système

        _ajouter(exchanges, ctx.ei.fret_maritime,
                 masse_t * (DIST_EXPORT_KM[destination] * U("km")))

        # démantèlement / tri (+ affinage si closed-loop)
        kwh = KWH_DEMANTELEMENT_PAR_T + (KWH_AFFINAGE_PAR_T if crediter else 0.0)
        _ajouter(exchanges, ctx.ei.elec_nz, masse_t * (kwh * U("kWh/ton")))

        # refus de tri : revient en décharge (ici, sur place à destination)
        refus[matiere] = masse * (1 - _recup(matiere))

    # ── flotteurs au feu : on PRÉLÈVE leur masse sur le refus ─────────────
    # Prélever et non ajouter : sans la soustraction, les 504 kg seraient
    # comptés deux fois — une fois enfouis, une fois brûlés — et le scénario
    # paraîtrait catastrophique pour une raison purement comptable.
    if fractions_incinerees:
        brules = _masses_a_incinerer(ctx, fractions_incinerees, m)
        for fraction, masse in brules.items():
            refus[fraction] = refus.get(fraction, 0) - masse
        _incinerer(ctx, brules, exchanges, crediter_energie)

    _decharge(ctx, refus, exchanges)

    # ── crédits de substitution (closed-loop UNIQUEMENT) ──────────────────
    if crediter:
        primaires = {
            "verre": ctx.ei.verre_plat,
            "aluminium": ctx.ei.aluminium_primaire,
            "silicium": ctx.ei.silicium_mg,
            "cuivre": ctx.ei.cuivre,
            "argent": ctx.ei.argent,
            "inox": ctx.ei.inox,
            "acier": ctx.ei.acier,
            "electronique": ctx.ei.electronique,
            # ⚠ NI PLOMB NI ÉTAIN, VOLONTAIREMENT. Il n'y a pas de dataset de
            # métal primaire épinglé pour eux, et surtout `RECUP["plomb"] = 0`
            # : un plomb de soudure non récupéré ne peut pas créditer un plomb
            # primaire évité. L'étain, lui, aurait droit à un crédit (RECUP
            # 0,50 × SUBST 0,50) le jour où un dataset sera épinglé ; en
            # attendant, son absence ici est une SOUS-ESTIMATION du bénéfice
            # closed-loop, de l'ordre de 0,09 kg d'étain par plateforme.
            # ⚠ `masses_recyclees()` affiche pourtant cette colonne créditée :
            # le tableau annonce donc un crédit que l'inventaire ne donne pas.
            # Écart assumé et borné, à lever avec le dataset.
        }
        for matiere, dataset in primaires.items():
            coef = _recup(matiere) * _subst(matiere)
            if coef <= 0 or dataset is None or matiere not in m:
                continue
            if _destination(matiere, modules_exportes) == "local":
                continue                    # pas récupéré, donc pas de crédit
            # échange NÉGATIF = production primaire évitée
            _ajouter(exchanges, dataset, -m[matiere] * coef)

    act = agb.newActivity(ctx.db, nom, unit="unit", exchanges=exchanges)
    act.updateMeta(**{config.AXE: "FinDeVie"})
    return act


def _ajouter(exchanges, dataset, montant):
    """Cumule un montant sur un dataset (un dict ne peut pas avoir 2 fois la
    même clé — piège classique quand plusieurs matières partagent une filière)."""
    if dataset is None:
        return
    exchanges[dataset] = exchanges.get(dataset, 0) + montant


# ══════════════════════════════════════════════════════════════════════════
# Aide à la rédaction du rapport
# ══════════════════════════════════════════════════════════════════════════
def bilan_systeme(ctx, valeurs, modules_exportes=False, crediter=False) -> dict:
    """Tableau de fin de vie du SYSTÈME ENTIER, matière par matière.

    ⚠ La colonne de distance donne le transport RÉELLEMENT IMPUTÉ par
    `_filiere`, pas la distance parcourue par la matière. Les deux diffèrent
    pour la ferraille : sous cut-off elle quitte le système au point de
    collecte, donc seuls les 220 km de goélette lui sont facturés même si le
    métal continue ensuite vers la Nouvelle-Zélande. La version précédente
    affichait 4 000 km, ce que le modèle ne facture pas — un tableau de SI qui
    aurait contredit l'inventaire.

    Le leg de regroupement était aussi omis pour TOUT LE MONDE : l'électronique
    s'affichait à 17 000 km alors que le modèle lui compte 220 + 17 000.

    >>> pd.DataFrame(fin_de_vie.bilan_systeme(ctx, jeux[REF])).T.round(1)
    """
    import lca_algebraic as agb

    from .parametres import magnitude

    lignes = {}
    for matiere, expr in matieres(ctx).items():
        try:
            masse = float(agb.compute_expr_value(magnitude(expr), valeurs))
        except Exception:      # noqa: BLE001
            masse = float("nan")
        destination = _destination(matiere, modules_exportes)
        sortie_anticipee = matiere in FERRAILLE and not crediter

        if destination == "local":
            km = 0.0
            libelle = "decharge Raiatea"
            recup = 0.0
        elif sortie_anticipee:
            km = DIST_GOELETTE_KM
            libelle = "filiere metaux (sortie au point de collecte)"
            recup = _recup(matiere)
        else:
            km = DIST_GOELETTE_KM + DIST_EXPORT_KM[destination]
            libelle = {"nz": "Nouvelle-Zelande",
                       "france": "France (DEEE)"}[destination]
            recup = _recup(matiere)

        lignes[matiere] = {
            "masse (kg)": masse,
            "destination": libelle,
            "km transport imputes": km,
            # Taux ANNONCÉ par le repreneur : documentaire, il décrit ce qui
            # arrive à la matière, pas ce que l'inventaire facture.
            "taux recup (%)": recup * 100,
            # Ces deux colonnes, elles, décrivent l'INVENTAIRE. Pour une
            # ferraille sortie au point de collecte, il ne facture ni
            # récupération ni enfouissement : la perte de tri appartient au
            # repreneur comme le reste. D'où NaN plutôt qu'un chiffre qui
            # laisserait croire qu'on enfouit 5 % de l'aluminium.
            "recupere (kg)": float("nan") if sortie_anticipee else masse * recup,
            "enfoui (kg)": float("nan") if sortie_anticipee
                           else masse * (1 - recup),
            "credite closed-loop (kg)": masse * recup * _subst(matiere),
        }
    return lignes


def masses_recyclees(m_panneaux_kg: float, n_modules: int = None) -> dict:
    """Détail matière par matière : masse enfouie, récupérée, créditée.

    ⚠ `m_panneaux_kg` est la masse de TOUS LES MODULES D'UNE PLATEFORME, pas
    celle d'un module. Pour la modalité S2 c'est 20 modules × 26 kg = 520 kg,
    d'où 390 kg de verre — soit bien 19,5 kg par module, cohérent avec les
    2 × 2 mm de verre trempé des fiches CS Wismar. Les colonnes portaient
    « dans le module », ce qui rendait le tableau incompréhensible : elles sont
    renommées, et une colonne par module est ajoutée si `n_modules` est fourni.

    >>> fin_de_vie.masses_recyclees(jeux[REF]["m_panneaux_kg"],
    ...                             jeux[REF]["n_modules"])
    """
    lignes = {}
    for matiere in COMPO:
        entrant = m_panneaux_kg * COMPO[matiere]
        recupere = entrant * RECUP[matiere]
        ligne = {
            "part massique (%)": COMPO[matiere] * 100,
            "plateforme (kg)": entrant,
        }
        if n_modules:
            ligne["par module (kg)"] = entrant / float(n_modules)
        ligne.update({
            "filiere de decharge": FILIERE.get(matiere, ROLE_REPLI),
            "recupere (kg)": recupere,
            "refus enfoui (kg)": entrant - recupere,
            "credite closed-loop (kg)": recupere * SUBST[matiere],
        })
        lignes[matiere] = ligne
    return lignes


def expliquer():
    """Rappelle en clair ce que représente chaque modalité (pour le notebook).

    ⚠ Les libellés sont lus en `.get()` et non en `[]`. Une fonction
    d'EXPLICATION ne doit pas pouvoir faire tomber un notebook parce qu'une
    modalité a été ajoutée à `MODALITES` sans sa notice : elle doit le DIRE.
    C'est exactement ce qui est arrivé le 05/10/2026 avec les deux modalités
    « polymeres », ajoutées à LIBELLES mais pas à METHODO.
    """
    print("Modalités du paramètre « fin_de_vie » :\n")
    orphelines = [c for c in MODALITES if c not in METHODO or c not in LIBELLES]
    for cle in MODALITES:
        print(f"  {cle}")
        print(f"    {LIBELLES.get(cle, '(libellé manquant)')}")
        print(f"    {METHODO.get(cle, '(notice manquante)')}\n")
    if orphelines:
        print(f"⚠ {len(orphelines)} modalité(s) sans notice complète : "
              f"{', '.join(orphelines)}. Complète LIBELLES et METHODO.\n")
    print("Règle de publication : « enfouissement » et « recyclage_cutoff » "
          "sont les deux\nscénarios à présenter comme résultats. "
          "« recyclage_closed_loop » n'est PAS un\nrésultat, c'est la borne "
          "basse de l'incertitude méthodologique — à afficher\ncomme "
          "intervalle autour du cut-off (Wang 2025 ; GHG Protocol ; "
          "IEA-PVPS T12).")
