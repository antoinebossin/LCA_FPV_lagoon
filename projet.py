"""
Initialisation du projet Brightway + lca_algebraic.

Une seule fonction publique : `initialiser()`. Elle
  1. ouvre le projet Brightway,
  2. active (si possible) le contrôle des unités de lca_algebraic,
  3. remet à zéro NOTRE base de premier plan et NOS paramètres,
  4. crée les briques parasol dont on a besoin,
  5. renvoie un objet `Contexte` que tous les autres modules consomment.

Le `Contexte` est le seul état partagé du package : pas de variable globale
qui traîne d'une cellule à l'autre comme dans l'ancien notebook.
"""

from __future__ import annotations

import brightway2 as bw
import lca_algebraic as agb

from . import config


# Unités absentes du registre Pint mais utilisées par parasol et par nous.
# `kWp` est déclaré comme dimension à part entière (une puissance crête n'est
# pas une puissance) — c'est ce qui permet à `units_enabled=True` de marcher.
UNITES_A_DEFINIR = ["kWp", "kWc", "Wp", "kVA"]


class Contexte:
    """État du modèle : base, paramètres, activités."""

    def __init__(self, db, unites):
        self.db = db
        self.unites = unites
        self.conf = None        # contexte parasol_lca
        self.par = None         # paramètres parasol résolus (module parasol_bridge)
        self.p = None           # nos paramètres (module parametres)
        self.ei = None          # activités ecoinvent de fond (module ecoinvent)
        self.postes = {}        # nom de poste -> activité
        self.elec_locale = None  # électricité du réseau de l'île (calée ADEME)
        self.systeme = None     # [fpv_lagon] Full PV system
        self.energie = None     # expression sympy : kWh produits sur la durée de vie

    # -- petits raccourcis, pour éviter de répéter db_name partout ---------
    def act(self, nom_activite, **kwargs):
        return agb.findActivity(nom_activite, db_name=self.db, single=True, **kwargs)

    def __repr__(self):
        return (f"<Contexte db={self.db!r} unites={self.unites} "
                f"postes={sorted(self.postes)}>")


def _definir_unites():
    for unite in UNITES_A_DEFINIR:
        try:
            agb.define_separate_unit(unite)
        except Exception:
            pass  # déjà définie


def initialiser(unites: bool | None = None, reset: bool = True,
                db: str | None = None) -> Contexte:
    """Ouvre le projet, prépare la base de travail et crée les briques parasol.

    Parameters
    ----------
    unites :
        Contrôle des unités de lca_algebraic. `True` par défaut, et il faut le
        laisser ainsi : parasol-lca passe des `pint.Quantity` à lca_algebraic,
        donc en mode « sans unités » ses propres constructeurs échouent
        (« Amount should be either a constant number or a Sympy expression.
        Was : pint.Quantity »).
    reset :
        Remet la base de premier plan et les paramètres à zéro. À laisser à
        True : garantit que l'état de la base correspond exactement au code.

    ⚠ En cas d'échec, on ne réessaie PAS dans un autre mode : une initialisation
    interrompue laisse une base à moitié construite, et les erreurs suivantes
    masquent la première (seule la première compte). Corrige, puis relance
    simplement la cellule.
    """
    db = db or config.DB
    if unites is None:
        unites = True

    bw.projects.set_current(config.PROJET_BW)
    _definir_unites()
    agb.Settings.units_enabled = unites

    ctx = _construire_socle(unites, reset, db)
    print(f"Contrôle des unités lca_algebraic : "
          f"{'ACTIVÉ' if unites else 'désactivé'}")
    return ctx


def _construire_socle(mode_unites: bool, reset: bool, db: str) -> Contexte:
    from . import parasol_bridge, parametres, ecoinvent

    if reset:
        agb.resetDb(db)
        agb.resetParams(db)
    agb.setForeground(db)

    ctx = Contexte(db, mode_unites)

    # 1. briques parasol (panneau, onduleur, mix électrique) + leurs paramètres
    ctx.conf, ctx.par = parasol_bridge.preparer(ctx)

    # 2. nos paramètres
    ctx.p = parametres.declarer(ctx)

    # 3. activités ecoinvent de fond (résolues une seule fois)
    ctx.ei = ecoinvent.resoudre()

    return ctx


def parametres_projet(afficher_orphelins=True):
    """Tous les paramètres présents dans le projet Brightway, ORPHELINS COMPRIS.

    Pourquoi cette fonction : Activity Browser affiche les paramètres du PROJET,
    pas ceux du modèle courant. Or `initialiser()` ne remet à zéro que ceux de
    NOTRE base (`agb.resetParams(db)`) — les paramètres laissés par d'anciennes
    versions du notebook (noms anglais : `productible`, `d_camion`,
    `cable_distance_sea_m`…) survivent dans le projet et s'affichent dans AB à
    côté des nôtres. D'où des valeurs déroutantes, comme un « productible » à
    1750 qui n'est utilisé par rien.

    La colonne `statut` distingue :
      * `modèle`   — déclaré par le code actuel (acv_lagon ou parasol) ;
      * `enum`     — sous-paramètre booléen d'un enum du modèle ;
      * `ORPHELIN` — vestige d'une version antérieure, sans effet sur le calcul
                     mais source de confusion dans Activity Browser.

    >>> projet.parametres_projet()
    """
    import pandas as pd
    from bw2data.parameters import (ActivityParameter, DatabaseParameter,
                                    ProjectParameter)

    connus = set(agb.all_params())
    enums = [n for n, p in agb.all_params().items()
             if getattr(p, "values", None)]

    def statut(nom):
        if nom in connus:
            return "modèle"
        if any(nom.startswith(e + "_") for e in enums):
            return "enum"
        return "ORPHELIN"

    lignes = []
    for modele, portee in ((ProjectParameter, "projet"),
                           (DatabaseParameter, "base"),
                           (ActivityParameter, "activité")):
        try:
            for p in modele.select():
                nom = p.name
                lignes.append({
                    "paramètre": nom,
                    "portée": portee,
                    "groupe": getattr(p, "database", None) or getattr(p, "group", ""),
                    "valeur": p.amount,
                    "statut": statut(nom),
                })
        except Exception:      # noqa: BLE001
            continue

    df = pd.DataFrame(lignes)
    if df.empty:
        print("Aucun paramètre trouvé dans le projet.")
        return df
    df = df.sort_values(["statut", "paramètre"]).reset_index(drop=True)

    n_orph = int((df["statut"] == "ORPHELIN").sum())
    if n_orph and afficher_orphelins:
        print(f"⚠ {n_orph} paramètre(s) ORPHELIN(S) dans le projet Brightway. "
              f"Ils n'influencent AUCUN calcul du modèle actuel — le système "
              f"construit son unité fonctionnelle avec `p_install_kwc`, "
              f"`productible_kwh_kwc_an` et `duree_vie_an` (cf. "
              f"systeme.energie_totale) — mais ils s'affichent dans Activity "
              f"Browser et prêtent à confusion.\n"
              f"  Pour les supprimer : projet.purger_parametres_orphelins()")
    return df


def purger_parametres_orphelins(confirmer=False):
    """Supprime du projet Brightway les paramètres d'anciennes versions.

    ⚠ Irréversible. Passe `confirmer=True` après avoir relu la liste renvoyée
    par `parametres_projet()`. Les paramètres du modèle courant et les
    sous-paramètres d'enum sont préservés.
    """
    from bw2data.parameters import ProjectParameter

    df = parametres_projet(afficher_orphelins=False)
    orphelins = df.loc[(df["statut"] == "ORPHELIN") & (df["portée"] == "projet"),
                       "paramètre"].tolist()
    if not orphelins:
        print("Aucun paramètre orphelin à supprimer.")
        return []
    if not confirmer:
        print(f"{len(orphelins)} orphelin(s) : {', '.join(sorted(orphelins))}\n"
              f"Relance avec confirmer=True pour les supprimer.")
        return orphelins
    for nom in orphelins:
        ProjectParameter.delete().where(ProjectParameter.name == nom).execute()
    print(f"{len(orphelins)} paramètre(s) orphelin(s) supprimé(s).")
    return orphelins


def purger_cache():
    """Vide le cache d'expressions symboliques de lca_algebraic.

    Utile uniquement si on modifie une activité APRÈS un premier calcul.
    Avec ce package on reconstruit toujours la base de zéro : en pratique
    l'appel n'est plus nécessaire (c'était le contournement du bug
    « poste structure non compté » de l'ancien notebook).
    """
    from lca_algebraic.cache import clear_caches
    clear_caches(local=True, disk=True)


def exporter_base_statique(valeurs: dict, unites: bool | None = None) -> Contexte:
    """Reconstruit le modèle dans une base SÉPARÉE puis y fige les paramètres.

    Le résultat est lisible dans Activity Browser. La base de travail n'est pas
    touchée : c'est ce qui manquait à l'ancien notebook, où `freezeParams`
    contaminait toutes les analyses suivantes et imposait un mécanisme de
    photographie/restauration des échanges.
    """
    from . import systeme

    ctx_statique = initialiser(unites=unites, reset=True, db=config.DB_STATIQUE)
    systeme.construire(ctx_statique)
    agb.freezeParams(config.DB_STATIQUE, **valeurs)
    print(f"Base statique « {config.DB_STATIQUE} » prête pour Activity Browser.")
    return ctx_statique
