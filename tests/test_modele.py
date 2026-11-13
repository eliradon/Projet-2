"""Tests du modèle sauvegardé (modele.py).

C'est le seul fichier de tests qui déclenche l'import de predicteur
(donc l'entraînement, quelques secondes). Il a lieu une seule fois,
grâce à la fixture de portée « module ».
"""

import os

import numpy as np
import pytest

import modele as module_modele
from exceptions import ModeleIntrouvableError
from modele import (NOM_FICHIER_METADONNEES, NOM_FICHIER_MODELE, Modele,
                    arrondir_pv, chronometre, sauvegarder_modele)
from variables import AUCUN_TYPE


@pytest.fixture(scope="module")
def dossier(tmp_path_factory) -> str:
    """Sauvegarde le modèle une fois dans un dossier temporaire."""
    chemin = str(tmp_path_factory.mktemp("modeles"))
    sauvegarder_modele(chemin)
    return chemin


@pytest.fixture(scope="module")
def modele(dossier: str) -> Modele:
    """Un modèle chargé depuis le dossier temporaire."""
    modele_charge = Modele(dossier)
    modele_charge.charger()
    return modele_charge


@pytest.fixture(scope="module")
def predicteur(dossier: str):
    """Le module de mon coéquipier, déjà importé par sauvegarder_modele()."""
    import predicteur
    return predicteur


def valeurs_de_la_ligne(predicteur, numero: int) -> dict:
    """Transforme une ligne du CSV en dictionnaire pour Modele.predire()."""
    ligne = predicteur.data.iloc[numero]
    type_2 = ligne["Type 2"]
    return {
        "Attack": ligne["Attack"], "Defense": ligne["Defense"],
        "Sp. Atk": ligne["Sp. Atk"], "Sp. Def": ligne["Sp. Def"],
        "Speed": ligne["Speed"], "Type 1": ligne["Type 1"],
        "Type 2": type_2 if isinstance(type_2, str) else AUCUN_TYPE,
        "Legendary": bool(ligne["Legendary"]),
    }


# --- Sauvegarde ---

def test_les_deux_fichiers_sont_crees(dossier: str) -> None:
    assert os.path.exists(os.path.join(dossier, NOM_FICHIER_MODELE))
    assert os.path.exists(os.path.join(dossier, NOM_FICHIER_METADONNEES))


def test_ordre_des_colonnes_respecte(modele: Modele, predicteur) -> None:
    assert (modele.metadonnees["colonnes_modele"]
            == list(predicteur.model.feature_names_in_))


def test_bornes_calculees_depuis_les_donnees(modele: Modele, predicteur) -> None:
    attaque = modele.metadonnees["variables"][0]
    assert attaque["nom"] == "Attack"
    assert attaque["min"] == predicteur.data["Attack"].min()
    assert attaque["max"] == predicteur.data["Attack"].max()
    assert attaque["min"] <= attaque["defaut"] <= attaque["max"]


def test_types_dans_les_metadonnees(modele: Modele) -> None:
    variables = {v["nom"]: v for v in modele.metadonnees["variables"]}
    assert len(variables["Type 1"]["valeurs"]) == 18
    assert variables["Type 2"]["valeurs"][0] == AUCUN_TYPE
    assert len(variables["Type 2"]["valeurs"]) == 19
    assert variables["Legendary"]["valeurs"] == [False, True]


def test_metriques(modele: Modele, predicteur) -> None:
    metrique = modele.metadonnees["metrique"]
    assert metrique["valeur"] == pytest.approx(predicteur.mae_scores.mean())
    assert metrique["r2"] == pytest.approx(predicteur.r2_scores.mean())
    # Un modèle utile doit faire mieux que « toujours prédire la moyenne ».
    assert metrique["valeur"] < metrique["reference_mae"]


def test_histogramme_compte_tous_les_pokemon(modele: Modele, predicteur) -> None:
    distribution = modele.metadonnees["distribution_cible"]
    assert sum(distribution["effectifs"]) == len(predicteur.data)
    assert len(distribution["bornes"]) == len(distribution["effectifs"]) + 1


# --- Prédiction ---

# Lignes du CSV : 0 = deux types, 4 = pas de type 2, 162 = légendaire.
@pytest.mark.parametrize("numero", [0, 4, 162, 799])
def test_meme_prediction_que_predicteur(modele: Modele, predicteur,
                                        numero: int) -> None:
    attendu = predicteur.model.predict(predicteur.X.iloc[[numero]])[0]
    obtenu = modele.predire(valeurs_de_la_ligne(predicteur, numero))
    assert obtenu == pytest.approx(attendu)


def test_type_2_aucun_change_la_prediction(modele: Modele) -> None:
    valeurs = {"Attack": 50, "Defense": 110, "Sp. Atk": 130, "Sp. Def": 130,
               "Speed": 90, "Type 1": "Fire", "Type 2": "Flying",
               "Legendary": False}
    avec_vol = modele.predire(valeurs)
    valeurs["Type 2"] = AUCUN_TYPE
    sans_type_2 = modele.predire(valeurs)
    assert np.isfinite(sans_type_2)
    assert sans_type_2 != pytest.approx(avec_vol)


def test_valeur_manquante(modele: Modele) -> None:
    with pytest.raises(KeyError):
        modele.predire({"Attack": 50})


# --- Chargement ---

def test_modele_non_charge() -> None:
    with pytest.raises(ModeleIntrouvableError):
        Modele().predire({})


def test_second_chargement_sans_reentrainement(dossier: str,
                                               monkeypatch) -> None:
    """Quand les fichiers existent, charger() ne doit pas ré-entraîner."""
    def interdit(dossier_recu: str) -> None:
        raise AssertionError("sauvegarder_modele() ne devait pas être appelée")
    # monkeypatch remplace la fonction le temps de ce test seulement.
    monkeypatch.setattr(module_modele, "sauvegarder_modele", interdit)
    Modele(dossier).charger()


def test_fichiers_illisibles(tmp_path) -> None:
    for nom in [NOM_FICHIER_MODELE, NOM_FICHIER_METADONNEES]:
        with open(os.path.join(tmp_path, nom), "w", encoding="utf-8") as fichier:
            fichier.write("ceci n'est pas un modèle")
    with pytest.raises(ModeleIntrouvableError):
        Modele(str(tmp_path)).charger()


# --- Décorateur ---

def test_chronometre_renvoie_le_resultat(capsys) -> None:
    @chronometre
    def addition(a: int, b: int) -> int:
        return a + b
    assert addition(2, 3) == 5
    # capsys capture ce que print() a affiché.
    assert "addition" in capsys.readouterr().out


# --- Arrondi des PV ---

def test_arrondir_pv_cas_usuel() -> None:
    assert arrondir_pv(77.6, 1) == 78
    assert arrondir_pv(77.4, 1) == 77


def test_arrondir_pv_jamais_sous_le_minimum() -> None:
    assert arrondir_pv(-12.3, 1) == 1
    assert arrondir_pv(0.2, 1) == 1
