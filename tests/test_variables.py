"""Tests de la validation des saisies (variables.py)."""

import pytest

from logique.exceptions import DonneeInvalideError
from logique.variables import (AUCUN_TYPE, Variable, VariableCategorielle,
                       VariableNumerique, creer_variable,
                       verifier_types_differents)


@pytest.fixture
def attaque() -> VariableNumerique:
    """Une variable numérique d'exemple, réutilisée par plusieurs tests."""
    return VariableNumerique("Attack", "Attack", 5, 190, 75)


@pytest.fixture
def type_1() -> VariableCategorielle:
    """Une variable catégorielle d'exemple, réutilisée par plusieurs tests."""
    return VariableCategorielle("Type 1", "Type 1", ["Fire", "Water", "Grass"])


# --- VariableNumerique : cas usuels ---

def test_numerique_valeur_valide(attaque: VariableNumerique) -> None:
    assert attaque.valider("50") == pytest.approx(50.0)


def test_numerique_ignore_les_espaces(attaque: VariableNumerique) -> None:
    assert attaque.valider("  50 ") == pytest.approx(50.0)


# --- VariableNumerique : cas limites ---

def test_numerique_accepte_les_deux_bornes(attaque: VariableNumerique) -> None:
    assert attaque.valider("5") == pytest.approx(5.0)
    assert attaque.valider("190") == pytest.approx(190.0)


@pytest.mark.parametrize("saisie", ["4", "191", "-10", "nan", "inf"])
def test_numerique_hors_bornes(attaque: VariableNumerique, saisie: str) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        attaque.valider(saisie)
    assert str(info.value) == "Attack: the value must be between 5 and 190."


# --- VariableNumerique : cas d'erreur ---

@pytest.mark.parametrize("saisie", ["", "   "])
def test_numerique_vide(attaque: VariableNumerique, saisie: str) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        attaque.valider(saisie)
    assert str(info.value) == "Attack: enter a value."


def test_numerique_non_numerique(attaque: VariableNumerique) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        attaque.valider("abc")
    assert str(info.value) == 'Attack: "abc" is not a number.'


# --- VariableCategorielle ---

def test_categorielle_valeur_valide(type_1: VariableCategorielle) -> None:
    assert type_1.valider("Fire") == "Fire"


def test_categorielle_type_inconnu(type_1: VariableCategorielle) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        type_1.valider("xyz")
    assert str(info.value) == 'Type 1: "xyz" is not a valid choice.'


def test_categorielle_booleenne() -> None:
    legendaire = VariableCategorielle("Legendary", "Legendary", [False, True])
    assert legendaire.valider(True) is True
    assert legendaire.defaut is False


# --- Règle Type 2 différent de Type 1 ---

def test_types_differents_acceptes() -> None:
    verifier_types_differents("Fire", "Flying")
    verifier_types_differents("Fire", AUCUN_TYPE)


def test_types_identiques_refuses() -> None:
    with pytest.raises(DonneeInvalideError) as info:
        verifier_types_differents("Fire", "Fire")
    assert str(info.value) == (
        'Type 2 must be different from Type 1 (or "None").')


# --- Classe abstraite, __str__ et création depuis les métadonnées ---

def test_variable_est_abstraite() -> None:
    with pytest.raises(TypeError):
        Variable("Attack", "Attack")


def test_str(attaque: VariableNumerique, type_1: VariableCategorielle) -> None:
    assert str(attaque) == "Attack (5 to 190)"
    assert str(type_1) == "Type 1 (3 choices)"


def test_creer_variable_numerique() -> None:
    variable = creer_variable({"nom": "Attack", "libelle": "Attack",
                               "type": "numerique", "min": 5, "max": 190,
                               "defaut": 75})
    assert isinstance(variable, VariableNumerique)
    assert (variable.minimum, variable.maximum, variable.defaut) == (5, 190, 75)


def test_creer_variable_categorielle() -> None:
    variable = creer_variable({"nom": "Type 1", "libelle": "Type 1",
                               "type": "categorielle",
                               "valeurs": ["Fire", "Water"]})
    assert isinstance(variable, VariableCategorielle)
    assert variable.valeurs == ["Fire", "Water"]


def test_creer_variable_type_inconnu() -> None:
    with pytest.raises(ValueError):
        creer_variable({"nom": "x", "libelle": "x", "type": "date"})


# --- Variable décimale (poids, taille) ---

def test_numerique_decimale() -> None:
    taille = VariableNumerique("height_m", "Height (m)", 0.1, 20.0, 1.0,
                               pas=0.1, statistique=False)
    assert taille.valider("1.5") == pytest.approx(1.5)
    assert taille.formater(1.5) == "1.5"
    assert taille.statistique is False


def test_numerique_entiere_formatee_sans_decimale(attaque: VariableNumerique) -> None:
    assert attaque.formater(50.4) == "50"
    assert attaque.pas == 1


def test_creer_variable_avec_pas() -> None:
    variable = creer_variable({"nom": "weight_kg", "libelle": "Weight (kg)",
                               "type": "numerique", "min": 0.1, "max": 999.9,
                               "defaut": 28.0, "pas": 0.1,
                               "statistique": False})
    assert variable.pas == pytest.approx(0.1)
    assert variable.statistique is False
