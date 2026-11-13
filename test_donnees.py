import numpy as np
import pandas as pd
import pytest

# À adapter : le module où se trouvent tes fonctions (ex. src/donnees.py)
from predicteur import cols, nettoyer_texte, trouver_stade, is_final_stage


def faire_ligne(nom, chaine):
    """Construit une ligne comme dans le CSV : english_name + 4 colonnes evochain."""
    valeurs = list(chaine) + [np.nan] * (len(cols) - len(chaine))
    ligne = {"english_name": nom}
    ligne.update(dict(zip(cols, valeurs)))
    return pd.Series(ligne)


# --- nettoyer_texte ---------------------------------------------------------

def test_nettoyer_texte_nan_donne_chaine_vide():
    assert nettoyer_texte(np.nan) == ""


def test_nettoyer_texte_enleve_espaces_et_majuscules():
    assert nettoyer_texte("  Eevee ") == "eevee"


# --- trouver_stade ----------------------------------------------------------

@pytest.mark.parametrize("nom, chaine, attendu", [
    ("Bulbasaur", ["Bulbasaur", "Ivysaur", "Venusaur"], 1),
    ("Ivysaur", ["Bulbasaur", "Ivysaur", "Venusaur"], 2),
    ("Charizard", ["Charmander", "Charmeleon", "Charizard"], 3),
])
def test_trouver_stade_lignee_complete(nom, chaine, attendu):
    assert trouver_stade(faire_ligne(nom, chaine)) == attendu


# --- is_final_stage : cas usuels (lignées de la capture) --------------------

@pytest.mark.parametrize("nom, chaine, attendu", [
    ("Bulbasaur", ["Bulbasaur", "Ivysaur", "Venusaur"], False),
    ("Ivysaur", ["Bulbasaur", "Ivysaur", "Venusaur"], False),
    ("Venusaur", ["Bulbasaur", "Ivysaur", "Venusaur"], True),
    ("Charmander", ["Charmander", "Charmeleon", "Charizard"], False),
    ("Charmeleon", ["Charmander", "Charmeleon", "Charizard"], False),
    ("Charizard", ["Charmander", "Charmeleon", "Charizard"], True),
    ("Squirtle", ["Squirtle", "Wartortle", "Blastoise"], False),
    ("Blastoise", ["Squirtle", "Wartortle", "Blastoise"], True),
    ("Caterpie", ["Caterpie", "Metapod", "Butterfree"], False),
    ("Butterfree", ["Caterpie", "Metapod", "Butterfree"], True),
])
def test_is_final_stage_lignees_a_trois_stades(nom, chaine, attendu):
    assert is_final_stage(faire_ligne(nom, chaine)) is attendu


# --- is_final_stage : lignées à deux stades ---------------------------------

def test_is_final_stage_base_de_deux_stades():
    # Yanma (chaîne supposée identique à celle de Yanmega)
    assert is_final_stage(faire_ligne("Yanma", ["Yanma", "Yanmega"])) is False


def test_is_final_stage_forme_finale_de_deux_stades():
    assert is_final_stage(faire_ligne("Yanmega", ["Yanma", "Yanmega"])) is True


def test_is_final_stage_quatre_colonnes_pleines():
    # Cas limite : le Pokémon est dans la dernière colonne (pas de colonne suivante)
    chaine = ["A", "B", "C", "D"]
    assert is_final_stage(faire_ligne("D", chaine)) is True


# --- is_final_stage : Évoli et ses évolutions -------------------------------

def test_is_final_stage_eevee_nest_pas_final():
    assert is_final_stage(faire_ligne("Eevee", ["Eevee"])) is False


@pytest.mark.parametrize("nom", ["Leafeon", "Glaceon"])
def test_is_final_stage_evolutions_deevee_sont_finales(nom):
    assert is_final_stage(faire_ligne(nom, ["Eevee"])) is True


# --- is_final_stage : sans évolution et anomalie ----------------------------

def test_is_final_stage_sans_evolution():
    assert is_final_stage(faire_ligne("Ditto", ["Ditto"])) is True


def test_is_final_stage_anomalie_nom_absent_de_la_chaine():
    # Cas observé dans le CSV : la chaîne de Mamoswine s'arrête à Piloswine.
    # Le comportement actuel renvoie False (anomalie documentée, pas un vrai résultat).
    assert is_final_stage(faire_ligne("Mamoswine", ["Swinub", "Piloswine"])) is False
