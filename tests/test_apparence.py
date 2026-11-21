"""Tests des couleurs et des libellés (apparence.py)."""

import os

import pytest

from interface.apparence import (COULEUR_MENU_TYPE, COULEURS_TYPES, NOMS_TYPES_FR,
                       chemin_image_type, couleur_pour_valeur, couleur_type,
                       formater_cellule, nom_type_fr)


# Chaque ligne teste les deux côtés d'un seuil : la couleur doit changer
# exactement à 30, 60, 90, 120 et 150.
@pytest.mark.parametrize("valeur, couleur", [
    (29, "#F34444"), (30, "#FF7F0F"),
    (59, "#FF7F0F"), (60, "#FFDD57"),
    (89, "#FFDD57"), (90, "#A0E515"),
    (119, "#A0E515"), (120, "#23CD5E"),
    (149, "#23CD5E"), (150, "#00C2B8"),
])
def test_couleur_aux_bornes(valeur: float, couleur: str) -> None:
    assert couleur_pour_valeur(valeur) == couleur


def test_couleur_valeurs_extremes() -> None:
    assert couleur_pour_valeur(-5) == "#F34444"
    assert couleur_pour_valeur(0) == "#F34444"
    assert couleur_pour_valeur(255) == "#00C2B8"


def test_couleur_valeur_decimale() -> None:
    assert couleur_pour_valeur(29.9) == "#F34444"


def test_nom_type_fr() -> None:
    assert nom_type_fr("Fire") == "Feu"
    assert nom_type_fr("Electric") == "Électrik"


def test_nom_type_inconnu_renvoye_tel_quel() -> None:
    assert nom_type_fr("Aucun") == "Aucun"


def test_couleur_type() -> None:
    assert couleur_type("Fire") == "#E62829"
    assert couleur_type("Aucun") == COULEUR_MENU_TYPE


def test_dictionnaires_couvrent_les_memes_18_types() -> None:
    assert len(NOMS_TYPES_FR) == 18
    assert set(NOMS_TYPES_FR) == set(COULEURS_TYPES)


def test_image_de_type_absente(tmp_path) -> None:
    assert chemin_image_type("Fire", str(tmp_path)) is None


def test_image_de_type_presente(tmp_path) -> None:
    chemin = os.path.join(tmp_path, "fire.png")
    with open(chemin, "wb") as fichier:
        fichier.write(b"image")
    assert chemin_image_type("Fire", str(tmp_path)) == chemin


@pytest.mark.parametrize("texte, attendu", [
    ("True", "Oui"), ("False", "Non"),
    ("Fire", "Feu"), ("Aucun", "Aucun"),
    ("50.0", "50"), ("78", "78"), ("12.5", "12.5"),
    ("2026-11-12 18:04:00", "2026-11-12 18:04:00"), ("", ""),
])
def test_formater_cellule(texte: str, attendu: str) -> None:
    assert formater_cellule(texte) == attendu


def test_types_en_minuscules() -> None:
    """Le nouveau jeu de données écrit les types en minuscules (« fire »)."""
    assert nom_type_fr("fire") == "Feu"
    assert couleur_type("fire") == "#E62829"
    assert formater_cellule("water") == "Eau"
