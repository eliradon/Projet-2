"""Tests des exceptions personnalisées (exceptions.py)."""

import pytest

from logique.exceptions import DonneeInvalideError, ModeleIntrouvableError


def test_donnee_invalide_conserve_son_message() -> None:
    """Le message donné à l'exception est celui qu'on retrouve en l'affichant."""
    erreur = DonneeInvalideError("Attaque : entrez une valeur.")
    assert str(erreur) == "Attaque : entrez une valeur."


def test_donnee_invalide_se_leve_avec_raise() -> None:
    """On peut lever l'exception avec raise et l'attraper précisément."""
    with pytest.raises(DonneeInvalideError):
        raise DonneeInvalideError("Attaque : entrez une valeur.")


def test_donnee_invalide_est_une_value_error() -> None:
    """DonneeInvalideError hérite de ValueError (une saisie est une mauvaise valeur)."""
    assert issubclass(DonneeInvalideError, ValueError)


def test_modele_introuvable_n_est_pas_une_donnee_invalide() -> None:
    """Les deux exceptions sont distinctes : on ne les confond pas dans un except."""
    assert not issubclass(ModeleIntrouvableError, DonneeInvalideError)
