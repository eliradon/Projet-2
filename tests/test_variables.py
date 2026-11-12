"""Tests de la validation des saisies (variables.py)."""

import pytest

from exceptions import DonneeInvalideError
from variables import (AUCUN_TYPE, Variable, VariableCategorielle,
                       VariableNumerique, creer_variable,
                       verifier_types_differents)


@pytest.fixture
def attaque() -> VariableNumerique:
    """Une variable numérique d'exemple, réutilisée par plusieurs tests."""
    return VariableNumerique("Attack", "Attaque", 5, 190, 75)


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
    assert str(info.value) == "Attaque : la valeur doit être entre 5 et 190."


# --- VariableNumerique : cas d'erreur ---

@pytest.mark.parametrize("saisie", ["", "   "])
def test_numerique_vide(attaque: VariableNumerique, saisie: str) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        attaque.valider(saisie)
    assert str(info.value) == "Attaque : entrez une valeur."


def test_numerique_non_numerique(attaque: VariableNumerique) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        attaque.valider("abc")
    assert str(info.value) == 'Attaque : "abc" n\'est pas un nombre.'


# --- VariableCategorielle ---

def test_categorielle_valeur_valide(type_1: VariableCategorielle) -> None:
    assert type_1.valider("Fire") == "Fire"


def test_categorielle_type_inconnu(type_1: VariableCategorielle) -> None:
    with pytest.raises(DonneeInvalideError) as info:
        type_1.valider("xyz")
    assert str(info.value) == 'Type 1 : "xyz" n\'est pas un type valide.'


def test_categorielle_booleenne() -> None:
    legendaire = VariableCategorielle("Legendary", "Légendaire", [False, True])
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
        'Le type 2 doit être différent du type 1 (ou "Aucun").')


# --- Classe abstraite, __str__ et création depuis les métadonnées ---

def test_variable_est_abstraite() -> None:
    with pytest.raises(TypeError):
        Variable("Attack", "Attaque")


def test_str(attaque: VariableNumerique, type_1: VariableCategorielle) -> None:
    assert str(attaque) == "Attaque (5 à 190)"
    assert str(type_1) == "Type 1 (3 choix)"


def test_creer_variable_numerique() -> None:
    variable = creer_variable({"nom": "Attack", "libelle": "Attaque",
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
