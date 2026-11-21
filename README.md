# Prédicteur de PV — Pokémon

Projet 2 du cours INF1007. L'application prédit les PV (HP) d'un Pokémon à
partir de ses autres statistiques, de ses types et de son caractère
légendaire, son poids, sa taille et son stade d'évolution. Le modèle est une
régression linéaire entraînée sur `pokemon_utf8.csv` (The Complete Pokédex
Dataset, 1025 Pokémon).

## Lancer l'application

```
pip install -r requirements.txt
python main.py
```

Au premier lancement, le modèle est entraîné puis enregistré dans le dossier
`modeles/` (quelques secondes). Aux lancements suivants, il est simplement
relu : rien n'est ré-entraîné.

Sur Mac avec le Python de Homebrew, tkinter s'installe à part :
`brew install python-tk`.

## Utiliser l'application

- **Onglet Prédiction** : réglez les statistiques, le poids, la taille et le
  stade d'évolution (curseur ou champ), choisissez les types et les
  interrupteurs (Légendaire, Sous-légendaire, Fabuleux, Forme finale), puis
  cliquez sur **Prédire**. Les PV estimés s'affichent avec l'erreur moyenne du modèle,
  et les deux graphiques se mettent à jour.
- **Onglet Historique** : le tableau des prédictions enregistrées dans
  `historique.csv`, les plus récentes en premier.
- Une saisie vide, non numérique ou hors intervalle affiche un message en
  rouge ; l'application ne plante pas.

## Organisation des fichiers

```
Projet-2/
├── main.py              point d'entrée : charge le modèle, ouvre la fenêtre
├── predicteur.py        préparation des données et entraînement du modèle
├── test_donnees.py      tests du modèle (stade d'évolution, forme finale)
├── pokemon_utf8.csv     jeu de données d'origine
├── pokemon_propre.csv   colonnes préparées (écrit par predicteur.py)
├── logique/             tout ce qui ne dépend pas de l'écran
│   ├── exceptions.py    exceptions personnalisées
│   ├── variables.py     classes de variables et validation des saisies
│   ├── historique.py    lecture et écriture de historique.csv
│   └── modele.py        sauvegarde, chargement et prédiction du modèle
├── interface/           tout ce qui concerne l'affichage
│   ├── UI.py            la fenêtre et ses widgets (CustomTkinter)
│   └── apparence.py     couleurs, noms français des types, mise en forme
├── tests/               tests pytest de la logique
├── docs/                plan de l'interface et maquettes
├── modeles/             modèle et métadonnées (générés au premier lancement)
└── historique.csv       prédictions enregistrées (généré)
```

L'interface ne valide rien, ne calcule rien et ne lit aucun fichier : elle
appelle les classes du dossier `logique/`. Les champs, leurs bornes, la liste
des types et l'erreur moyenne viennent de `modeles/metadonnees.json`.

`predicteur.py` et les CSV restent à la racine, car `predicteur.py` cherche
`pokemon_utf8.csv` à côté de lui.

## Tests

```
pytest
```

`pytest` lance nos tests du dossier `tests/` et ceux du modèle
(`test_donnees.py`). Ils couvrent cas usuels, cas limites et cas d'erreur. Aucun
test n'importe `interface/UI.py`, car l'intégration continue n'a pas d'écran.
Le workflow `.github/workflows/tests.yml` lance `pytest` à chaque push.

Pour mesurer la couverture :

```
coverage run -m pytest
coverage report
```

## Outils du chapitre 7

- **Décorateur** : `chronometre`, dans `logique/modele.py`, mesure la durée
  de `sauvegarder_modele()`.
- **Fonction `lambda`** : clé de tri de l'historique dans
  `logique/historique.py` (`sorted(..., key=lambda ligne: ligne["date"])`).

## Calcul vectorisé (NumPy)

Dans `construire_metadonnees()` (`logique/modele.py`) : l'histogramme des PV
avec `np.histogram` et l'erreur de référence avec `np.mean(np.abs(...))`,
sans boucle sur les Pokémon.

## Documentation consultée

- CustomTkinter, fenêtre `CTk` :
  https://customtkinter.tomschimansky.com/documentation/windows/window/
- CustomTkinter, `CTkTabview` :
  https://customtkinter.tomschimansky.com/documentation/widgets/tabview/
- CustomTkinter, `CTkSlider` :
  https://customtkinter.tomschimansky.com/documentation/widgets/slider/
- CustomTkinter, `CTkSwitch` :
  https://customtkinter.tomschimansky.com/documentation/widgets/switch/
- CustomTkinter, `CTkOptionMenu` :
  https://customtkinter.tomschimansky.com/documentation/widgets/optionmenu/
- Matplotlib, intégration dans tkinter (« Embed in Tk ») :
  https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html

## Images de type (facultatif)

Si un fichier `assets/types/<type en anglais, en minuscules>.png` existe
(par exemple `assets/types/fire.png`), il remplace la pastille colorée à
côté de la liste des types. Sans image, la pastille colorée est affichée.
