"""Sauvegarde, chargement et utilisation du modèle de prédiction.

C'est le SEUL module qui importe « predicteur », et il le fait à
l'intérieur d'une fonction : importer predicteur.py relance tout
l'entraînement. On le fait donc une seule fois, pour enregistrer le
modèle et ses métadonnées dans le dossier « modeles/ ». Ensuite
l'application relit simplement ces deux fichiers.
"""

import functools
import json
import os
import pickle
import time

import joblib
import numpy as np
import pandas as pd

from logique.exceptions import ModeleIntrouvableError
from logique.variables import AUCUN_TYPE

# Racine du dépôt : le dossier parent de « logique/ », là où se trouvent
# pokemon_utf8.csv et predicteur.py.
DOSSIER_PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_MODELES = os.path.join(DOSSIER_PROJET, "modeles")
NOM_FICHIER_MODELE = "modele.joblib"
NOM_FICHIER_METADONNEES = "metadonnees.json"
FICHIERS_NECESSAIRES = ["pokemon_utf8.csv", "predicteur.py"]

# Colonnes numériques du modèle, dans l'ordre d'affichage, avec leur libellé.
LIBELLES_NUMERIQUES = {
    "attack": "Attaque",
    "defense": "Défense",
    "sp_attack": "Att. Spé.",
    "sp_defense": "Déf. Spé.",
    "speed": "Vitesse",
    "weight_kg": "Poids (kg)",
    "height_m": "Taille (m)",
    "evostage": "Stade d'évolution",
}
# Les cinq statistiques de combat : ce sont elles qu'on montre sur le radar
# et dont la barre change de couleur selon la valeur.
STATISTIQUES_DE_COMBAT = ["attack", "defense", "sp_attack", "sp_defense",
                          "speed"]
# Colonnes à valeur décimale : on les règle par pas de 0,1.
COLONNES_DECIMALES = ["weight_kg", "height_m"]
PAS_DECIMAL = 0.1

# Colonnes oui/non du modèle (0 ou 1), avec leur libellé.
LIBELLES_BOOLEENS = {
    "is_legendary": "Légendaire",
    "is_sublegendary": "Sous-légendaire",
    "is_mythical": "Fabuleux",
    "is_final_stage": "Forme finale",
}
COLONNE_CIBLE = "hp"
LARGEUR_CLASSE_HISTOGRAMME = 20

# Erreurs possibles quand un des deux fichiers est abîmé. Un fichier
# .joblib corrompu peut échouer de plusieurs façons selon son contenu ;
# json.JSONDecodeError est une sorte de ValueError.
ERREURS_DE_LECTURE = (OSError, EOFError, ValueError, ImportError,
                      AttributeError, IndexError, KeyError,
                      pickle.UnpicklingError)


def chronometre(fonction):
    """Décorateur : reçoit une fonction et renvoie la même fonction, qui
    affiche en plus sa durée d'exécution dans le terminal."""
    @functools.wraps(fonction)
    def fonction_chronometree(*args, **kwargs):
        debut = time.perf_counter()
        resultat = fonction(*args, **kwargs)
        duree = time.perf_counter() - debut
        print(f"{fonction.__name__} : {duree:.2f} s")
        return resultat
    return fonction_chronometree


def decrire_variable_numerique(entrees: pd.DataFrame, nom: str) -> dict:
    """Reçoit le tableau des entrées du modèle et le nom d'une colonne
    numérique ; renvoie sa description pour les métadonnées (bornes, valeur
    par défaut = médiane, pas du curseur).

    Échoue avec KeyError si la colonne n'existe pas dans le tableau.
    """
    colonne = entrees[nom]
    if nom in COLONNES_DECIMALES:
        pas = PAS_DECIMAL
        minimum, maximum = float(colonne.min()), float(colonne.max())
        defaut = round(float(colonne.median()), 1)
    else:
        pas = 1
        minimum, maximum = int(colonne.min()), int(colonne.max())
        defaut = int(colonne.median())
    return {"nom": nom, "libelle": LIBELLES_NUMERIQUES[nom],
            "type": "numerique", "min": minimum, "max": maximum,
            "defaut": defaut, "pas": pas,
            "statistique": nom in STATISTIQUES_DE_COMBAT}


def construire_metadonnees(entrees: pd.DataFrame, cible: pd.Series,
                           colonnes_modele: list[str], mae: float,
                           r2: float) -> dict:
    """Reçoit le tableau des entrées du modèle, la colonne cible (PV),
    l'ordre des colonnes du modèle et ses deux métriques ; renvoie le
    dictionnaire de métadonnées décrit dans le plan.

    Échoue avec KeyError si une colonne attendue manque dans le tableau.
    """
    variables = [decrire_variable_numerique(entrees, nom)
                 for nom in LIBELLES_NUMERIQUES]

    # Les types sont les colonnes du modèle qui ne sont ni numériques ni
    # oui/non. On les trie pour un affichage stable.
    types = sorted(colonne for colonne in colonnes_modele
                   if colonne not in LIBELLES_NUMERIQUES
                   and colonne not in LIBELLES_BOOLEENS)
    variables.append({"nom": "Type 1", "libelle": "Type 1",
                      "type": "categorielle", "valeurs": types})
    variables.append({"nom": "Type 2", "libelle": "Type 2",
                      "type": "categorielle", "valeurs": [AUCUN_TYPE] + types,
                      "optionnelle": True})
    for nom, libelle in LIBELLES_BOOLEENS.items():
        variables.append({"nom": nom, "libelle": libelle,
                          "type": "categorielle", "valeurs": [False, True]})

    # Calculs vectorisés avec NumPy : aucune boucle sur les Pokémon.
    pv = cible.to_numpy()
    reference_mae = np.mean(np.abs(pv - pv.mean()))
    bornes_classes = np.arange(0, pv.max() + LARGEUR_CLASSE_HISTOGRAMME,
                               LARGEUR_CLASSE_HISTOGRAMME)
    effectifs, bornes = np.histogram(pv, bins=bornes_classes)

    return {
        "cible": {"nom": COLONNE_CIBLE, "libelle": "PV",
                  "min": int(pv.min()), "max": int(pv.max())},
        "variables": variables,
        "colonnes_modele": list(colonnes_modele),
        "metrique": {"nom": "MAE", "valeur": float(mae), "r2": float(r2),
                     "reference_mae": float(reference_mae)},
        "distribution_cible": {"bornes": bornes.tolist(),
                               "effectifs": effectifs.tolist()},
    }


def arrondir_pv(pv: float, minimum: int) -> int:
    """Reçoit les PV prédits et le minimum possible ; renvoie les PV arrondis
    à l'entier, sans jamais descendre sous « minimum ». N'échoue pas.

    Une régression linéaire peut donner une valeur négative pour des
    saisies extrêmes : un Pokémon ne peut pas avoir moins de 1 PV.
    """
    return max(minimum, round(pv))


@chronometre
def sauvegarder_modele(dossier: str = DOSSIER_MODELES) -> None:
    """Entraîne le modèle (en important predicteur) et l'enregistre dans
    « dossier », avec le fichier JSON de métadonnées. Ne renvoie rien.

    Échoue avec ModeleIntrouvableError si pokemon_utf8.csv ou predicteur.py
    est introuvable, si l'import échoue ou si l'écriture est impossible.
    """
    for nom_fichier in FICHIERS_NECESSAIRES:
        if not os.path.exists(os.path.join(DOSSIER_PROJET, nom_fichier)):
            raise ModeleIntrouvableError(
                f"Le fichier « {nom_fichier} » est introuvable.")
    try:
        import predicteur  # exécute tout le script : lecture, entraînement
    except (ImportError, OSError):
        raise ModeleIntrouvableError(
            "Le modèle n'a pas pu être entraîné à partir de predicteur.py."
        ) from None

    # L'ordre des colonnes change à chaque entraînement : on le lit dans le
    # modèle lui-même au lieu de le supposer.
    colonnes_modele = list(predicteur.model.feature_names_in_)
    metadonnees = construire_metadonnees(
        predicteur.X, predicteur.y, colonnes_modele,
        predicteur.mae_scores.mean(), predicteur.r2_scores.mean())
    try:
        os.makedirs(dossier, exist_ok=True)
        joblib.dump(predicteur.model, os.path.join(dossier, NOM_FICHIER_MODELE))
        chemin_json = os.path.join(dossier, NOM_FICHIER_METADONNEES)
        with open(chemin_json, "w", encoding="utf-8") as fichier:
            json.dump(metadonnees, fichier, ensure_ascii=False, indent=2)
    except OSError:
        raise ModeleIntrouvableError(
            "Le modèle n'a pas pu être enregistré sur le disque.") from None


class Modele:
    """Le modèle sauvegardé et ses métadonnées, prêts à prédire."""

    def __init__(self, dossier: str = DOSSIER_MODELES) -> None:
        """Reçoit le dossier des deux fichiers. Ne renvoie rien, n'échoue
        pas : rien n'est lu avant l'appel de charger()."""
        self._dossier = dossier
        self._modele = None
        self._metadonnees = None

    @property
    def metadonnees(self) -> dict:
        """Renvoie le dictionnaire de métadonnées.
        Échoue avec ModeleIntrouvableError si charger() n'a pas été appelée."""
        if self._metadonnees is None:
            raise ModeleIntrouvableError("Le modèle n'est pas chargé.")
        return self._metadonnees

    def charger(self) -> None:
        """Lit le modèle et les métadonnées. Si l'un des deux fichiers est
        absent, appelle d'abord sauvegarder_modele() pour les créer.

        Ne renvoie rien. Échoue avec ModeleIntrouvableError si les fichiers
        ne peuvent être ni créés ni lus.
        """
        chemin_modele = os.path.join(self._dossier, NOM_FICHIER_MODELE)
        chemin_json = os.path.join(self._dossier, NOM_FICHIER_METADONNEES)
        if not (os.path.exists(chemin_modele) and os.path.exists(chemin_json)):
            sauvegarder_modele(self._dossier)
        try:
            self._modele = joblib.load(chemin_modele)
            with open(chemin_json, "r", encoding="utf-8") as fichier:
                self._metadonnees = json.load(fichier)
        except ERREURS_DE_LECTURE:
            raise ModeleIntrouvableError(
                "Les fichiers du modèle sont illisibles. Supprimez le "
                "dossier « modeles » puis relancez l'application.") from None

    def _types_connus(self) -> list[str]:
        """Renvoie la liste des types (en anglais) connus du modèle."""
        for variable in self.metadonnees["variables"]:
            if variable["nom"] == "Type 1":
                return variable["valeurs"]
        return []

    def predire(self, valeurs: dict) -> float:
        """Reçoit les valeurs validées, par nom de colonne du CSV (ex.
        {"Attack": 50, ..., "Type 1": "Fire", "Type 2": "Aucun",
        "Legendary": False}) et renvoie les PV prédits.

        Échoue avec ModeleIntrouvableError si le modèle n'est pas chargé et
        avec KeyError s'il manque une valeur.
        """
        types = self._types_connus()
        ligne = {}
        for colonne in self.metadonnees["colonnes_modele"]:
            if colonne in types:
                # Même encodage que predicteur.py : 1 si le Pokémon a ce
                # type (en type 1 ou en type 2), 0 sinon.
                ligne[colonne] = (int(valeurs["Type 1"] == colonne)
                                  + int(valeurs["Type 2"] == colonne))
            else:
                # Valeur numérique, ou oui/non (True devient 1.0, False 0.0).
                ligne[colonne] = float(valeurs[colonne])
        # Le tableau d'une seule ligne reprend l'ordre exact des colonnes
        # utilisé à l'entraînement.
        tableau = pd.DataFrame([ligne],
                               columns=self.metadonnees["colonnes_modele"])
        return float(self._modele.predict(tableau)[0])
