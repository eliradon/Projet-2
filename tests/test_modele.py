"""Tests du modèle sauvegardé (modele.py).

C'est le seul fichier de tests qui déclenche l'import de predicteur
(donc l'entraînement, quelques secondes). Il a lieu une seule fois,
grâce à la fixture de portée « module ».
"""

import os

import numpy as np
import pytest

from logique import modele as module_modele
from logique.exceptions import ModeleIntrouvableError
from logique.modele import (COLONNES_RARETE, LIBELLES_BOOLEENS,
                            LIBELLES_NUMERIQUES, NOM_FICHIER_METADONNEES,
                            NOM_FICHIER_MODELE, NOM_RARETE, RARETE_AUCUNE,
                            Modele, arrondir_pv, chronometre,
                            forme_finale_imposee, sauvegarder_modele)
from logique.variables import AUCUN_TYPE


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
    """Transforme une ligne du jeu de données en dictionnaire pour
    Modele.predire(), comme le ferait l'interface."""
    entrees = predicteur.X.iloc[numero]
    ligne = predicteur.data.iloc[numero]
    valeurs = {nom: entrees[nom] for nom in LIBELLES_NUMERIQUES}
    for nom in LIBELLES_BOOLEENS:
        valeurs[nom] = bool(entrees[nom])
    valeurs[NOM_RARETE] = RARETE_AUCUNE
    for rarete, colonne in COLONNES_RARETE.items():
        if entrees[colonne] == 1:
            valeurs[NOM_RARETE] = rarete
    type_2 = ligne["secondary_type"]
    valeurs["Type 1"] = ligne["primary_type"]
    valeurs["Type 2"] = type_2 if isinstance(type_2, str) else AUCUN_TYPE
    return valeurs


def exemple_feu_vol() -> dict:
    """Un Pokémon d'exemple, type Feu / Vol, pour les tests de prédiction."""
    return {"attack": 50, "defense": 110, "sp_attack": 130, "sp_defense": 130,
            "speed": 90, "weight_kg": 30.0, "height_m": 1.5, "evostage": 2,
            "Type 1": "fire", "Type 2": "flying", NOM_RARETE: RARETE_AUCUNE,
            "is_final_stage": False}


# --- Sauvegarde ---

def test_les_deux_fichiers_sont_crees(dossier: str) -> None:
    assert os.path.exists(os.path.join(dossier, NOM_FICHIER_MODELE))
    assert os.path.exists(os.path.join(dossier, NOM_FICHIER_METADONNEES))


def test_ordre_des_colonnes_respecte(modele: Modele, predicteur) -> None:
    assert (modele.metadonnees["colonnes_modele"]
            == list(predicteur.model.feature_names_in_))


def test_bornes_calculees_depuis_les_donnees(modele: Modele, predicteur) -> None:
    attaque = modele.metadonnees["variables"][0]
    assert attaque["nom"] == "attack"
    assert attaque["min"] == predicteur.X["attack"].min()
    assert attaque["max"] == predicteur.X["attack"].max()
    assert attaque["min"] <= attaque["defaut"] <= attaque["max"]


def test_variable_decimale(modele: Modele, predicteur) -> None:
    variables = {v["nom"]: v for v in modele.metadonnees["variables"]}
    taille = variables["height_m"]
    assert taille["pas"] == pytest.approx(0.1)
    assert taille["min"] == pytest.approx(predicteur.X["height_m"].min())
    assert taille["statistique"] is False
    assert variables["speed"]["statistique"] is True


def test_types_dans_les_metadonnees(modele: Modele) -> None:
    variables = {v["nom"]: v for v in modele.metadonnees["variables"]}
    assert len(variables["Type 1"]["valeurs"]) == 18
    assert variables["Type 2"]["valeurs"][0] == AUCUN_TYPE
    assert len(variables["Type 2"]["valeurs"]) == 19
    for nom in LIBELLES_BOOLEENS:
        assert variables[nom]["valeurs"] == [False, True]
    assert variables[NOM_RARETE]["valeurs"] == [
        "Aucune", "Sous-légendaire", "Légendaire", "Fabuleux"]


def test_metriques(modele: Modele, predicteur) -> None:
    metrique = modele.metadonnees["metrique"]
    assert metrique["valeur"] == pytest.approx(predicteur.mae_scores.mean())
    assert metrique["r2"] == pytest.approx(predicteur.r2_scores.mean())
    # Un modèle utile doit faire mieux que « toujours prédire la moyenne ».
    assert metrique["valeur"] < metrique["reference_mae"]


def test_histogramme_compte_tous_les_pokemon(modele: Modele, predicteur) -> None:
    distribution = modele.metadonnees["distribution_cible"]
    assert sum(distribution["effectifs"]) == len(predicteur.y)
    assert len(distribution["bornes"]) == len(distribution["effectifs"]) + 1


# --- Prédiction ---

def numeros_a_tester(predicteur) -> list[int]:
    """Renvoie quelques lignes variées : la première (deux types), une sans
    type 2, un légendaire, un fabuleux et la dernière."""
    donnees = predicteur.data
    return [0,
            int(donnees["secondary_type"].isna().to_numpy().argmax()),
            int(predicteur.X["is_legendary"].to_numpy().argmax()),
            int(predicteur.X["is_mythical"].to_numpy().argmax()),
            len(donnees) - 1]


def test_meme_prediction_que_predicteur(modele: Modele, predicteur) -> None:
    for numero in numeros_a_tester(predicteur):
        verifier_meme_prediction(modele, predicteur, numero)


def verifier_meme_prediction(modele: Modele, predicteur, numero: int) -> None:
    """Compare la prédiction de Modele à celle du modèle d'origine."""
    attendu = predicteur.model.predict(predicteur.X.iloc[[numero]])[0]
    obtenu = modele.predire(valeurs_de_la_ligne(predicteur, numero))
    assert obtenu == pytest.approx(attendu)


def test_type_2_aucun_change_la_prediction(modele: Modele) -> None:
    valeurs = exemple_feu_vol()
    avec_vol = modele.predire(valeurs)
    valeurs["Type 2"] = AUCUN_TYPE
    sans_type_2 = modele.predire(valeurs)
    assert np.isfinite(sans_type_2)
    assert sans_type_2 != pytest.approx(avec_vol)


def test_valeur_manquante(modele: Modele) -> None:
    with pytest.raises(KeyError):
        modele.predire({"attack": 50})


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


# --- Rareté et forme finale ---

def test_rarete_change_la_prediction(modele: Modele) -> None:
    valeurs = exemple_feu_vol()
    sans_rarete = modele.predire(valeurs)
    valeurs[NOM_RARETE] = "Légendaire"
    assert modele.predire(valeurs) != pytest.approx(sans_rarete)


@pytest.mark.parametrize("stade, attendu", [(1, False), (3, False), (4, True)])
def test_forme_finale_imposee(stade: int, attendu: bool) -> None:
    assert forme_finale_imposee(stade, 4) is attendu


def test_stade_4_impose_la_forme_finale(modele: Modele) -> None:
    """Au stade 4, cocher ou non « Forme finale » donne la même prédiction."""
    valeurs = exemple_feu_vol()
    valeurs["evostage"] = 4
    non_cochee = modele.predire(valeurs)
    valeurs["is_final_stage"] = True
    assert modele.predire(valeurs) == pytest.approx(non_cochee)


def test_forme_finale_libre_avant_le_stade_4(modele: Modele) -> None:
    valeurs = exemple_feu_vol()
    non_cochee = modele.predire(valeurs)
    valeurs["is_final_stage"] = True
    assert modele.predire(valeurs) != pytest.approx(non_cochee)
