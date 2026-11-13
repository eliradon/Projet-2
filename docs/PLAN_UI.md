# Plan du UI — Prédicteur de PV (HP) de Pokémon

Projet 2 INF1007 · Volet 3 (interface graphique). Spécification que Claude Code doit suivre pour construire l'interface dans le dépôt `Projet-2`. Ce plan est aligné sur l'état réel du dépôt (analysé le 2026-11-12).

## 0. Consignes pour Claude Code (à lire en premier)

1. **Fichiers interdits de modification : `Pokemon.csv` et `predicteur.py`.** Ne pas les éditer, renommer, déplacer ni reformater. Tout le reste se fait dans de nouveaux fichiers, plus `UI.py` (vide pour l'instant) et `requirements.txt`. Si une étape semble exiger de toucher à l'un des deux, arrête-toi et demande.
2. **Garder la structure à plat** (tout à la racine) : `predicteur.py` cherche `Pokemon.csv` à côté de lui, on ne crée donc pas de dossier `src/`.
3. **L'interface appelle la logique, elle ne la contient pas** : aucune validation, aucun calcul, aucune lecture de fichier dans les widgets.
4. **Rien n'est codé en dur** : champs, bornes, types et marge d'erreur viennent du JSON de métadonnées (section 7).
5. **Aucun plantage, aucun traceback visible** : toute erreur devient un message en français dans la fenêtre. Jamais de `except` nu.
6. Chaque fonction : docstring (reçoit / renvoie / échoue quand) + annotations de type.
7. Avance par petites étapes (section 9), un commit par étape, et explique chaque étape : l'étudiant doit pouvoir justifier chaque ligne à l'oral.

## 1. État du dépôt et ce que ça impose

| Constat dans le dépôt | Conséquence pour l'interface |
|---|---|
| `predicteur.py` est un script sans fonction : à l'import, il lit le CSV, fait une validation croisée (20 plis), entraîne `model` (régression linéaire) et affiche des `print`. Durée ≈ 1,5 s. | On ne l'importe **qu'une fois**, dans `modele.py`, pour sauvegarder le modèle. L'application charge ensuite le fichier sauvegardé. |
| Il ne sauvegarde ni le modèle ni de métadonnées. | `modele.py` (nouveau) fait `joblib.dump(predicteur.model, …)` et écrit le JSON, sans toucher à `predicteur.py`. |
| Les colonnes de type sont créées depuis un `set` : **leur ordre change à chaque exécution** (vérifié sur deux lancements). | Ne jamais coder l'ordre des colonnes. Le lire dans `model.feature_names_in_` et le stocker dans les métadonnées. |
| Encodage : colonnes `Attack, Speed, Defense, Sp. Atk, Sp. Def, Legendary` (0/1), puis une colonne par type valant `(Type 1 == t) + (Type 2 == t)`. Type 2 absent = aucune colonne à 1 pour lui. | `Modele.predire()` reconstruit exactement cette ligne. |
| Métriques retenues dans `DECISIONS.md` : R² et **MAE** (RMSE écarté). Valeurs actuelles : MAE ≈ 14,6 PV, R² ≈ 0,24. Lues dans `predicteur.mae_scores` et `predicteur.r2_scores`. | L'indice de confiance affiché est la MAE, pas la RMSE. |
| Types en anglais dans le CSV (`Fire`, `Water`…). 18 types, 386 Pokémon sans Type 2, aucun avec Type 1 = Type 2. | Dictionnaire d'affichage anglais → français dans `apparence.py` ; la valeur envoyée au modèle reste l'anglais. |
| Bornes réelles : Attaque 5–190, Défense 5–230, Att. Spé. 10–194, Déf. Spé. 20–230, Vitesse 5–180, PV 1–255. | Calculées depuis `predicteur.data` et écrites dans les métadonnées. |
| `UI.py` existe, vide et non suivi par Git. Pas de `main.py`, de tests, de README ni de CI. | `UI.py` contient l'interface ; `main.py` est créé comme point d'entrée. |

## 2. Ce que fait l'écran

L'utilisateur décrit un Pokémon, clique sur **Prédire**, et l'application affiche les PV estimés.

| Rôle | Variable (colonne du CSV) | Widget |
|---|---|---|
| Entrée | Attaque (`Attack`), Défense (`Defense`), Att. Spé. (`Sp. Atk`), Déf. Spé. (`Sp. Def`), Vitesse (`Speed`) | curseur + champ de saisie synchronisés |
| Entrée | Type 1 (obligatoire), Type 2 (optionnel, « Aucun ») | listes déroulantes |
| Entrée | Légendaire (`Legendary`) | interrupteur |
| **Sortie** | **PV (`HP`)** | ligne en lecture seule, remplie par la prédiction |

## 3. Technologie

**CustomTkinter** + Matplotlib via `FigureCanvasTkAgg`. Widgets : `CTkSwitch`, `CTkSlider` (couleur de barre modifiable), `CTkEntry`, `CTkOptionMenu`, `CTkTabview`, `ttk.Treeview` pour le tableau. À noter dans `DECISIONS.md` (validation D).

## 4. Disposition de la fenêtre

Fenêtre ~1280 × 860, redimensionnable, titre « Prédicteur de PV — Pokémon ». Deux onglets : **Prédiction** et **Historique**. **La maquette (section 10) fait foi** pour la disposition, les couleurs et les libellés.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Prédicteur de PV — Pokémon                    [ Prédiction ][ Historique ]│
├───────────────────────────────────────┬──────────────────────────────────┤
│ Légendaire ?   (●━━)  Non             │  Profil du Pokémon (radar 6 axes)│
│ PV         90   ━━━━━━━━░░░░░░░░░░    │                                  │
│ Attaque   [ 50] ━━━━●─────────────    │                                  │
│ Défense   [110] ━━━━━━━━━━●───────    ├──────────────────────────────────┤
│ Att. Spé. [130] ━━━━━━━━━━━━●─────    │  Où se situe la prédiction ?     │
│ Déf. Spé. [130] ━━━━━━━━━━━━●─────    │  (histogramme des PV + ligne     │
│ Vitesse   [ 90] ━━━━━━━━●─────────    │   verticale + bande ± MAE)       │
│ Type 1 [FEU ▾]   Type 2 [VOL ▾]       │                                  │
│ ⚠ messages d'erreur (rouge)           │                                  │
│ [ Prédire ]  [ Réinitialiser ]        │                                  │
│ « Ce Pokémon aurait environ 90 PV. »  │                                  │
└───────────────────────────────────────┴──────────────────────────────────┘
```

## 5. Composants

### 5.1 Ligne de statistique (× 5)
- Libellé à droite, gris ; valeur dans un **champ éditable** ; curseur à droite. Curseur et champ synchronisés dans les deux sens. Bornes et valeur par défaut (médiane) lues dans les métadonnées.
- Le champ éditable est nécessaire : avec un curseur seul, on ne peut pas produire de saisie vide ou non numérique, et la démo doit en montrer une.
- Couleur de la barre selon la valeur :

| Valeur | Couleur | Hex |
|---|---|---|
| < 30 | rouge | `#F34444` |
| 30–59 | orange | `#FF7F0F` |
| 60–89 | jaune | `#FFDD57` |
| 90–119 | vert clair | `#A0E515` |
| 120–149 | vert | `#23CD5E` |
| ≥ 150 | turquoise | `#00C2B8` |

`couleur_pour_valeur(valeur: float) -> str` va dans `apparence.py` (testable aux bornes 29/30, 59/60…).

### 5.2 Ligne PV (sortie)
Même gabarit, non modifiable : barre de progression sans poignée. Avant prédiction : « — », barre vide. Après : valeur arrondie à l'entier, barre colorée. Une régression linéaire peut sortir une valeur négative ou absurde pour des saisies extrêmes : afficher au minimum 1.

### 5.3 Interrupteur « Légendaire ? »
`CTkSwitch`, vert quand activé, désactivé par défaut, avec « Oui » / « Non » à côté.

### 5.4 Types
- Deux listes déroulantes remplies par les métadonnées, libellés en français (`NOMS_TYPES_FR` : Bug→Insecte, Dark→Ténèbres, Dragon→Dragon, Electric→Électrik, Fairy→Fée, Fighting→Combat, Fire→Feu, Flying→Vol, Ghost→Spectre, Grass→Plante, Ground→Sol, Ice→Glace, Normal→Normal, Poison→Poison, Psychic→Psy, Rock→Roche, Steel→Acier, Water→Eau). Type 2 propose « Aucun » en premier (valeur par défaut).
- Pastille de la couleur du type à côté du menu (`COULEURS_TYPES`).
- **Images de type (optionnel)** : si `assets/types/<type anglais en minuscules>.png` existe (ex. `fire.png`), l'afficher à la place de la pastille avec `CTkImage`, proportions conservées (hauteur ~40 px). Fichier absent ou illisible : pastille colorée, sans erreur. Chemin construit avec `os.path.join`, existence vérifiée avec `os.path.exists`.
- Règle : Type 2 ≠ Type 1 (aucun cas dans le jeu de données, le modèle ne l'a jamais vu).

### 5.5 Boutons et phrase de résultat
- **Prédire** (bouton principal) et **Réinitialiser** (valeurs par défaut).
- « Ce Pokémon aurait environ **90 PV**. » puis « Erreur moyenne du modèle : ± 15 PV » (MAE lue dans les métadonnées, arrondie). Une régression n'a pas de probabilité : la MAE sert d'indice de confiance.

### 5.6 Graphique 1 — Radar « Profil du Pokémon » (Matplotlib, projection polaire)
6 axes dans cet ordre : PV, Attaque, Défense, Vitesse, Déf. Spé., Att. Spé. Mis à jour quand une saisie change. Le sommet PV n'est tracé qu'après une prédiction (point orange `#D9480F`). Titre, légende (« Saisie » / « PV prédits »).

### 5.7 Graphique 2 — « Où se situe la prédiction ? » (Matplotlib)
Histogramme des PV du jeu de données + ligne verticale à la valeur prédite + bande ± MAE. Titre, axe X « PV », axe Y « Nombre de Pokémon », légende. Les effectifs viennent des métadonnées (pas de relecture du CSV au lancement).

### 5.8 Onglet Historique
- Tableau : date et heure, Attaque, Défense, Att. Spé., Déf. Spé., Vitesse, Type 1, Type 2, Légendaire, PV prédits.
- Relu depuis `historique.csv` à l'ouverture de l'onglet, après chaque prédiction et au clic sur **Actualiser** ; plus récent en premier, tri avec une `lambda` comme clé (outil du ch. 7 à citer dans le README).
- Fichier absent ou vide : « Aucune prédiction pour l'instant. », pas d'erreur.

## 6. États et messages d'erreur

| État | Déclencheur | Ligne PV | Message |
|---|---|---|---|
| Initial | lancement, Réinitialiser | « — », barre vide | aucun |
| Saisie invalide | clic Prédire avec erreur | inchangée | rouge, champ fautif encadré en rouge |
| Prédit | clic Prédire, tout valide | valeur + barre | aucun ; ligne ajoutée à l'historique |
| Périmé | une entrée change après une prédiction | valeur grisée | « Cliquez sur Prédire pour mettre à jour » |

La validation est faite par les classes de variables : l'interface appelle `variable.valider(saisie)` et attrape `DonneeInvalideError`. Toutes les erreurs d'une tentative sont affichées d'un coup, une par ligne.

| Cas | Message affiché |
|---|---|
| Champ vide | « Attaque : entrez une valeur. » |
| Non numérique | « Attaque : "abc" n'est pas un nombre. » |
| Hors intervalle | « Attaque : la valeur doit être entre 5 et 190. » |
| Type inconnu | « Type 1 : "xyz" n'est pas un type valide. » |
| Type 2 = Type 1 | « Le type 2 doit être différent du type 1 (ou "Aucun"). » |
| `Pokemon.csv` ou `predicteur.py` introuvable lors de la première sauvegarde | fenêtre d'erreur claire, puis fermeture propre |
| Historique illisible | l'onglet affiche le message, la prédiction reste possible |

## 7. Modèle sauvegardé et métadonnées (nouveau module `modele.py`)

`modele.py` est le **seul** module qui importe `predicteur`, et il le fait à l'intérieur d'une fonction, jamais en haut du fichier (sinon chaque import relancerait l'entraînement, y compris dans les tests).

- `sauvegarder_modele() -> None` : `import predicteur` ; `joblib.dump(predicteur.model, "modeles/modele.joblib")` ; écrit `modeles/metadonnees.json`. Décorée par un chronomètre maison (décorateur, ch. 7).
- `class Modele` : `charger()` lit les deux fichiers ; s'ils sont absents, appelle `sauvegarder_modele()` une fois. `predire(valeurs: dict) -> float` construit la ligne dans l'ordre de `colonnes_modele` et appelle le modèle.
- Les effectifs de l'histogramme sont calculés avec `np.histogram` et la MAE de référence avec NumPy, sans boucle (calcul vectorisé, ch. 12).

```json
{
  "cible": {"nom": "HP", "libelle": "PV", "min": 1, "max": 255},
  "variables": [
    {"nom": "Attack", "libelle": "Attaque", "type": "numerique", "min": 5, "max": 190, "defaut": 75},
    {"nom": "Defense", "libelle": "Défense", "type": "numerique", "min": 5, "max": 230, "defaut": 70},
    {"nom": "Sp. Atk", "libelle": "Att. Spé.", "type": "numerique", "min": 10, "max": 194, "defaut": 65},
    {"nom": "Sp. Def", "libelle": "Déf. Spé.", "type": "numerique", "min": 20, "max": 230, "defaut": 70},
    {"nom": "Speed", "libelle": "Vitesse", "type": "numerique", "min": 5, "max": 180, "defaut": 65},
    {"nom": "Type 1", "libelle": "Type 1", "type": "categorielle", "valeurs": ["Bug", "Dark", "..."]},
    {"nom": "Type 2", "libelle": "Type 2", "type": "categorielle", "valeurs": ["Aucun", "Bug", "..."], "optionnelle": true},
    {"nom": "Legendary", "libelle": "Légendaire", "type": "categorielle", "valeurs": [false, true]}
  ],
  "colonnes_modele": ["Attack", "Speed", "Defense", "Sp. Atk", "Sp. Def", "Legendary", "<18 types dans l'ordre de model.feature_names_in_>"],
  "metrique": {"nom": "MAE", "valeur": 14.6, "r2": 0.24, "reference_mae": 18.8},
  "distribution_cible": {"bornes": [], "effectifs": []}
}
```

Les nombres ci-dessus sont ceux mesurés aujourd'hui ; le code doit les calculer, pas les recopier. `reference_mae` = erreur d'un modèle qui prédit toujours la moyenne des PV.

## 8. Architecture du code (à plat, à la racine)

```
Projet-2/
├── Pokemon.csv          NE PAS MODIFIER
├── predicteur.py        NE PAS MODIFIER
├── main.py              point d'entrée : crée Application et lance la boucle
├── UI.py                Application + widgets (CustomTkinter)
├── modele.py            sauvegarder_modele(), classe Modele
├── variables.py         Variable (abstraite) → VariableNumerique, VariableCategorielle
├── historique.py        classe Historique : ajouter(), lire()  (CSV, os.path, with)
├── apparence.py         couleur_pour_valeur(), COULEURS_TYPES, NOMS_TYPES_FR
├── exceptions.py        DonneeInvalideError, ModeleIntrouvableError
├── modeles/             modele.joblib + metadonnees.json (générés)
├── assets/types/        images de type (optionnel)
├── docs/maquette/       exports de la maquette
└── tests/               test_variables.py, test_historique.py, test_apparence.py, test_modele.py
```

Classes de `UI.py` :
- `Application(ctk.CTk)` : **composition** → contient un `Modele`, la liste des `Variable`, un `Historique` et les panneaux. Méthodes `_construire()`, `_sur_predire()`, `_sur_changement()`, `_reinitialiser()`.
- `LigneStatistique`, `LigneResultat`, `SelecteurType`, `PanneauRadar`, `PanneauDistribution`, `OngletHistorique`.

`Variable.valider(saisie)` est redéfinie par les deux classes enfants (polymorphisme) ; `__str__` redéfinie (méthode spéciale).

Déroulement de `_sur_predire()` :
1. lire les saisies brutes (chaînes) ;
2. `variable.valider(saisie)` pour chacune, en accumulant les `DonneeInvalideError` ;
3. erreurs → état « Saisie invalide », fin ;
4. `modele.predire(valeurs)` → PV ;
5. mettre à jour ligne PV, phrase, radar, distribution ;
6. `historique.ajouter(...)` puis rafraîchir l'onglet.

## 9. Ordre d'implémentation (un commit par étape)

1. `requirements.txt` (section 10), `exceptions.py`, dossier `tests/` avec un premier test qui passe.
2. `variables.py` + tests (valeur valide, vide, non numérique, hors bornes, type inconnu).
3. `apparence.py` + tests (`couleur_pour_valeur` aux bornes).
4. `historique.py` + tests (fichier absent, ajout, relecture, tri).
5. `modele.py` : sauvegarde, chargement, `predire()` + tests (ordre des colonnes respecté, Type 2 « Aucun », même prédiction que `predicteur.model` sur une ligne du CSV avec `pytest.approx`).
6. `UI.py` : fenêtre, onglets, deux colonnes ; `main.py`.
7. Lignes de statistiques depuis les métadonnées, synchronisation, couleurs ; interrupteur ; types.
8. Bouton Prédire : validation, messages, ligne PV, phrase de résultat.
9. Radar, puis graphique de distribution.
10. Onglet Historique, état « périmé », Réinitialiser.
11. README (lancement : `python main.py`, lien doc CustomTkinter, outil ch. 7), workflow GitHub Actions qui lance `pytest`.

Tests : ne jamais importer `UI.py` dans les tests (la CI n'a pas d'écran). Seul `test_modele.py` déclenche l'import de `predicteur` (≈ 1,5 s).

## 10. Maquette de référence et librairies

**Maquette** : deux écrans, `docs/maquette/maquette_prediction.html` (état après un clic sur Prédire) et `docs/maquette/maquette_historique.html`. Ce sont des pages HTML statiques : lire leur code source pour la disposition, les libellés et les couleurs exacts.

Couleurs : fond `#F3F4F7`, cartes `#FFFFFF`, texte `#1D2030`, texte secondaire `#4A5060`, bouton principal `#1F6F8B`, pastille de type `#3A3D56`, radar `#2E9DB8` (contour `#14506A`), marqueur de prédiction `#D9480F`, erreur `#B3261E`.

**`requirements.txt`** (le fichier actuel contient `pandas`, `scikit-learn`, `matplotlib`) :

```
pandas
numpy
scikit-learn
matplotlib
customtkinter
pytest
coverage
```

- `joblib` est installé avec scikit-learn.
- `tkinter`, `os`, `json`, `csv`, `datetime`, `abc` font partie de Python. Sur Mac avec Python de Homebrew : `brew install python-tk`.

## 11. Vérification finale

- [ ] `git diff --stat` ne montre aucun changement dans `Pokemon.csv` ni `predicteur.py`
- [ ] Un champ par variable, adapté à son type, construit depuis les métadonnées
- [ ] Saisie vide / non numérique / hors intervalle → message clair, jamais de traceback
- [ ] Bouton « Prédire », résultat en langage courant + erreur moyenne
- [ ] Au moins un graphique Matplotlib dans la fenêtre, avec titre, axes, légende
- [ ] Chaque prédiction écrite dans `historique.csv` et consultable dans l'onglet Historique
- [ ] Deuxième lancement : le modèle est chargé depuis `modeles/`, pas ré-entraîné
- [ ] Clone neuf : `pip install -r requirements.txt` puis `python main.py`
- [ ] Démo : un cas normal, une saisie invalide (« abc » dans Attaque), le graphique
