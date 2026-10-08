"""
ACV d'une plateforme photovoltaïque flottante — lagon de Raiatea.

Modèle paramétrique construit sur brightway2 + lca_algebraic + parasol-lca.
Unité fonctionnelle : 1 kWh injecté sur le réseau, frontières berceau-tombe.

Organisation (un fichier = une responsabilité) :

    config.py           constantes (bases, préfixes, méthodes d'impact, couleurs)
    projet.py           initialisation Brightway + contexte partagé
    parasol_bridge.py   briques reprises à parasol-lca, résolution de ses noms
    parametres.py       TOUS nos paramètres lca_algebraic, avec unités
    ecoinvent.py        résolution des datasets de fond (un seul endroit)
    electricite.py      mix réseau de l'île, calé sur le FE ADEME Polynésie

    panneaux.py         poste modules PV
    onduleurs.py        poste micro-onduleurs + câblage modules
    structure.py        poste aluminium, flotteurs, boulonnerie
    ancrage.py          poste corde / élastique / chaîne / ancres
    cable.py            poste câble terre-mer (longueur 3D bathymétrique)
    maintenance.py      poste nettoyage (eau douce + bateau)
    repeteurs.py        poste répéteurs wifi
    transport.py        poste fret (camion, conteneurs, goélette)
    fin_de_vie.py       poste fin de vie — 3 modalités : enfouissement,
                        recyclage NZ cut-off (référence), recyclage NZ
                        closed-loop (borne de sensibilité méthodologique)

    systeme.py          assemblage du « Full PV system » + calculs
    modalites.py        données terrain des 4 plateformes
    checks.py           garde-fous
    resultats.py        tableaux, figures, sensibilité

    endpoint.py         lecture ReCiPe 2016 endpoint (H) — SECONDAIRE, en
                        parallèle du midpoint EF v3.1, jamais à sa place.
                        Trois aires de protection en unités incommensurables
                        (DALY, species·yr, USD2013) : on ne les additionne pas.
                        Lire son en-tête avant d'en citer un chiffre, en
                        particulier sur ce que « ecosystem quality » ne
                        contient pas (`land use` oui, `sea use` non).

Démarrage type, depuis ACV_main.ipynb :

    from acv_lagon import projet, systeme, modalites, resultats, config
    ctx = projet.initialiser()
    systeme.construire(ctx)
    jeux = modalites.jeux_de_parametres(ctx)
    df = resultats.comparer_modalites(ctx, jeux)

⚠ Les fichiers de ce dossier sont faits pour être IMPORTÉS, pas exécutés. Si tu
en ouvres un « comme un notebook » et que tu lances ses cellules, les imports
relatifs (`from . import config`) échouent avec « attempted relative import with
no known parent package » : c'est normal, il n'y a pas de paquet parent quand on
exécute un fichier isolément. Pour inspecter un module, ouvre-le dans l'éditeur
texte, et teste-le depuis le notebook :

    from acv_lagon import structure
    structure.construire(ctx)
"""

__version__ = "1.0"
