"""Tests de l'historique des prédictions (historique.py).

« tmp_path » est un dossier temporaire fourni par pytest : les tests
n'écrivent donc jamais dans le vrai historique.csv.
"""

import os
from datetime import datetime

import pytest

from logique.exceptions import HistoriqueInaccessibleError
from logique.historique import Historique

COLONNES = ["Attack", "Type 1", "HP"]


@pytest.fixture
def historique(tmp_path) -> Historique:
    """Un historique vide dans un dossier temporaire."""
    return Historique(COLONNES, os.path.join(tmp_path, "historique.csv"))


# --- Cas limites : fichier absent ou vide ---

def test_fichier_absent_donne_liste_vide(historique: Historique) -> None:
    assert historique.lire() == []


def test_fichier_vide_donne_liste_vide(historique: Historique) -> None:
    with open(historique.chemin, "w", encoding="utf-8"):
        pass  # crée un fichier de 0 octet
    assert historique.lire() == []


# --- Cas usuels : ajout, relecture, tri ---

def test_ajout_puis_relecture(historique: Historique) -> None:
    historique.ajouter({"Attack": 50, "Type 1": "Fire", "HP": 78},
                       datetime(2026, 11, 12, 18, 4, 0))
    assert historique.lire() == [{"date": "2026-11-12 18:04:00",
                                  "Attack": "50", "Type 1": "Fire", "HP": "78"}]


def test_ajout_cree_le_fichier(historique: Historique) -> None:
    assert not os.path.exists(historique.chemin)
    historique.ajouter({"Attack": 50, "Type 1": "Fire", "HP": 78})
    assert os.path.exists(historique.chemin)


def test_entete_ecrit_une_seule_fois(historique: Historique) -> None:
    historique.ajouter({"Attack": 50, "Type 1": "Fire", "HP": 78})
    historique.ajouter({"Attack": 60, "Type 1": "Water", "HP": 80})
    with open(historique.chemin, "r", encoding="utf-8") as fichier:
        lignes = fichier.read().splitlines()
    assert lignes[0] == "date,Attack,Type 1,HP"
    assert len(lignes) == 3


def test_plus_recent_en_premier(historique: Historique) -> None:
    # Les lignes sont volontairement ajoutées dans le désordre.
    historique.ajouter({"Attack": 2, "Type 1": "Fire", "HP": 0},
                       datetime(2026, 11, 12, 17, 0, 0))
    historique.ajouter({"Attack": 1, "Type 1": "Fire", "HP": 0},
                       datetime(2026, 11, 11, 21, 30, 0))
    historique.ajouter({"Attack": 3, "Type 1": "Fire", "HP": 0},
                       datetime(2026, 11, 12, 18, 4, 0))
    assert [ligne["Attack"] for ligne in historique.lire()] == ["3", "2", "1"]


def test_meme_date_dernier_ajout_en_premier(historique: Historique) -> None:
    moment = datetime(2026, 11, 12, 18, 4, 0)
    historique.ajouter({"Attack": 1, "Type 1": "Fire", "HP": 0}, moment)
    historique.ajouter({"Attack": 2, "Type 1": "Fire", "HP": 0}, moment)
    assert [ligne["Attack"] for ligne in historique.lire()] == ["2", "1"]


# --- Cas d'erreur ---

def test_colonne_manquante_a_l_ajout(historique: Historique) -> None:
    with pytest.raises(KeyError):
        historique.ajouter({"Attack": 50})


def test_colonnes_inattendues(historique: Historique) -> None:
    with open(historique.chemin, "w", encoding="utf-8") as fichier:
        fichier.write("nom,age\nPikachu,3\n")
    with pytest.raises(HistoriqueInaccessibleError):
        historique.lire()


def test_fichier_illisible(historique: Historique) -> None:
    with open(historique.chemin, "wb") as fichier:
        fichier.write(b"\xff\xfe\x00illisible")  # octets qui ne sont pas du texte UTF-8
    with pytest.raises(HistoriqueInaccessibleError):
        historique.lire()


def test_ecriture_impossible(tmp_path) -> None:
    # Le dossier « absent » n'existe pas : l'ouverture du fichier échoue.
    chemin = os.path.join(tmp_path, "absent", "historique.csv")
    with pytest.raises(HistoriqueInaccessibleError):
        Historique(COLONNES, chemin).ajouter(
            {"Attack": 50, "Type 1": "Fire", "HP": 78})
