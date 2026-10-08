"""
Poste « Ancrage » : corde + élastique Seaflex + chaîne + ancres écologiques.

Modèle par LIGNE d'ancrage, × `n_ancres` lignes par plateforme :

| Élément  | Longueur / quantité / ligne | Matériau             |
|----------|-----------------------------|----------------------|
| Corde    | tan(63°) × profondeur       | HMPE (proxy PEHD)    |
| Élastique| 2,3 m (constant, doc)       | caoutchouc SBR       |
| Chaîne   | 1 m                         | acier galvanisé      |
| Ancre    | 1 ancre / ligne             | acier galvanisé      |
| Poulie   | 1 / ligne                   | PA6 (Seaflex Block)  |
| Manille  | 1 / ligne                   | acier galvanisé      |

La longueur de corde dépend de la profondeur d'eau : c'est le même paramètre
`profondeur_eau_m` qui pilote la corde ET la longueur 3D du câble sous-marin
(cf. `cable.py`). Une seule profondeur dans tout le modèle.

────────────────────────────────────────────────────────────────────────────
POURQUOI CE MODULE EXPOSE AUSSI UNE MASSE NUMÉRIQUE (`masse_kg`)

L'ancrage joue deux rôles dans le modèle :

1. un POSTE D'IMPACT — `construire()` produit un inventaire symbolique dont
   les masses sont des expressions des paramètres lca_algebraic. Elles restent
   formelles jusqu'au `compute_impacts`, ce qui permet au tornado et au
   Monte-Carlo de les balayer ;
2. un CONTRIBUTEUR AU BILAN DE MASSE — l'ancrage entre dans `m_systeme_t`, la
   masse embarquée en goélette, qui est elle-même un paramètre du modèle. Il
   faut donc pouvoir en donner une valeur NUMÉRIQUE au moment où l'on
   construit le dict de paramètres, avant toute évaluation du graphe : on ne
   peut pas mettre une expression symbolique dans la valeur d'un paramètre
   qu'elle alimenterait.

Ces deux besoins partagent désormais UNE SEULE formule (`_masses`), évaluée
soit sur les paramètres symboliques (`ctx.p`), soit sur leurs valeurs par
défaut lues dans le registre lca_algebraic. Avant, `modalites.py` recopiait à
la main les huit constantes de `parametres.py` : rien ne garantissait qu'elles
restent synchronisées, et une correction de `rho_corde_kg_m` aurait modifié
l'inventaire sans toucher la masse transportée, en silence.

────────────────────────────────────────────────────────────────────────────
INVENTAIRE ARRÊTÉ LE 15/09/2026 — ce qui a changé et pourquoi

1. CORDE EN HMPE, plus en polyester. La ligne de mouillage est fournie par
   Seaflex ; sa fiche matière ne connaît qu'un « Main cable » en HMPE gainé
   TPU, pas de corde polyester. Faute de dataset UHMWPE/HMPE en ecoinvent 3.11,
   on reste sur le PEHD granulé : il porte le polymère mais pas le filage
   gel-spun, très électro-intensif.

   ⚠ MASSE LINÉIQUE RECALÉE le 16/09/2026. `rho_corde_kg_m` valait 0,17 kg/m,
   calé sur du POLYESTER. À diamètre égal une HMPE est plus légère dans le
   rapport des densités : 0,17 × 0,97/1,38 = 0,12 kg/m. La corde passe donc de
   4,004 à 2,826 kg par plateforme (−1,178 kg). Valeur à confirmer par PESÉE
   d'un mètre sur site — elle est déduite, pas mesurée.

2. POULIE ET MANILLE comptées, une de chaque par ligne. Ce sont les seules
   pièces de quincaillerie réellement montées : les autres postes du BoM
   Seaflex (plaques d'attache, boulonnerie, crimps, cosse, bouchons) n'ont pas
   été utilisés sur cette installation. La poulie est le « Block_50 »,
   0,089 kg, que la fiche Seaflex donne en PA6 — pas en métal. La manille est
   le « Shackle_50FVZ », 0,385 kg : le suffixe FVZ (feuerverzinkt) et la fiche
   (« Shackle (galvanized) : Black MC355 ») disent acier GALVANISÉ, contre la
   mention « Stainless steel A4 » du brouillon ; la masse de 385 g colle à
   l'acier (ρ 7,85), pas à l'inox.

   La colonne « Weight » du BoM Seaflex est une masse TOTALE pour la quantité
   indiquée, PAR LIGNE d'ancrage — recoupé par densité sur six pièces
   normalisées, et confirmé par le fait que le code divise déjà 2,3653 kg par
   2,3 m pour obtenir `rho_elastique_kg_m` = 1,03.

L'ancrage vaut ainsi 61,998 kg par plateforme : 61,280 avant l'ajout de la
quincaillerie, 63,176 avec la poulie et la manille mais la corde encore en
polyester, 61,998 une fois la corde recalée en HMPE.

Limite qui demeure : la GALVANISATION n'est comptée nulle part. Chaîne, ancre
et manille sont modélisées en acier bas allié NU. Ajouter un échange
« zinc coating, pieces » (en m²) fermerait ce trou.
"""

from __future__ import annotations

from types import SimpleNamespace

import lca_algebraic as agb

from . import config
from .parametres import TAN_ANCRAGE

NOM = config.nom("lignes d'ancrage")

# Paramètres dont dépend la masse d'ancrage. Sert à relire leurs valeurs par
# défaut dans le registre lca_algebraic — donc dans `parametres.py`, seule
# source de vérité.
PARAMS = ("profondeur_eau_m", "rho_corde_kg_m", "n_ancres", "l_elastique_m",
          "rho_elastique_kg_m", "l_chaine_m", "rho_chaine_kg_m", "m_ancre_kg",
          "m_poulie_kg", "m_manille_kg")


def _masses(p):
    """Masse de chaque élément d'ancrage, POUR LA PLATEFORME ENTIÈRE (kg).

    Fonctionne indifféremment avec des paramètres lca_algebraic (expressions
    symboliques) ou avec de simples flottants : c'est ce qui permet de n'écrire
    la formule qu'une fois.
    """
    return {
        "corde": TAN_ANCRAGE * p.profondeur_eau_m * p.rho_corde_kg_m * p.n_ancres,
        "elastique": p.l_elastique_m * p.rho_elastique_kg_m * p.n_ancres,
        "chaine": p.l_chaine_m * p.rho_chaine_kg_m * p.n_ancres,
        "ancres": p.m_ancre_kg * p.n_ancres,
        "poulie": p.m_poulie_kg * p.n_ancres,
        "manille": p.m_manille_kg * p.n_ancres,
    }


def construire(ctx):
    m = _masses(ctx.p)

    # Chaîne, ancres et manilles pointent sur le même dataset acier : on somme
    # les trois masses (un dict d'exchanges ne peut pas avoir deux fois la même
    # clé). La corde HMPE partage le dataset PEHD avec la peau des flotteurs et
    # la gaine du câble, mais ce sont trois ACTIVITÉS distinctes : aucun
    # conflit de clé, et aucun double comptage.
    exchanges = {
        ctx.ei.pehd: m["corde"],
        ctx.ei.caoutchouc: m["elastique"],
        ctx.ei.acier: m["chaine"] + m["ancres"] + m["manille"],
    }

    pa6 = getattr(ctx.ei, "pa6", None)
    if pa6 is not None:
        exchanges[pa6] = m["poulie"]
    else:
        print(f"  ⚠ ancrage : aucun dataset « nylon 6 » trouvé — les poulies PA6 "
              f"({_defaut('m_poulie_kg') * _defaut('n_ancres'):.3f} kg/plateforme) "
              f"ne sont PAS comptées. Lance ecoinvent.chercher('nylon') et "
              f"complète CANDIDATS['pa6'].")

    act = agb.newActivity(ctx.db, NOM, unit="unit", exchanges=exchanges)
    act.updateMeta(**{config.AXE: "Ancrage"})
    return act


def masses_kg(**surcharges) -> dict:
    """Détail des masses d'ancrage en kg, sur les valeurs PAR DÉFAUT.

    Les défauts sont relus dans le registre lca_algebraic, donc dans
    `parametres.py` : aucune constante n'est recopiée ici. Toute valeur peut
    être surchargée par mot-clé (utile pour un scénario à autre profondeur).

    >>> ancrage.masses_kg(profondeur_eau_m=5.0)
    """
    valeurs = {nom: _defaut(nom) for nom in PARAMS}
    inconnus = set(surcharges) - set(PARAMS)
    if inconnus:
        raise KeyError(f"Paramètre(s) sans effet sur l'ancrage : "
                       f"{sorted(inconnus)}. Attendus : {list(PARAMS)}")
    valeurs.update(surcharges)
    return _masses(SimpleNamespace(**valeurs))


def masse_kg(**surcharges) -> float:
    """Masse totale d'ancrage d'une plateforme, en kg (valeurs par défaut).

    C'est CETTE fonction qu'appelle `modalites.py` pour composer `m_systeme_t`.
    """
    return float(sum(masses_kg(**surcharges).values()))


def _defaut(nom: str) -> float:
    """Valeur par défaut d'un paramètre, lue dans le registre lca_algebraic."""
    params = agb.all_params()
    if nom not in params:
        raise KeyError(
            f"Paramètre « {nom} » absent du registre lca_algebraic. "
            f"Les paramètres doivent être déclarés (parametres.declarer) avant "
            f"tout appel à ancrage.masse_kg().")
    return float(params[nom].default)
