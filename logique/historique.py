"""Historique des prédictions, enregistré dans un fichier CSV.

Chaque prédiction ajoute une ligne au fichier. L'onglet Historique relit
ce fichier pour afficher le tableau, les plus récentes en premier.
"""

import csv
import os
from datetime import datetime

from logique.exceptions import HistoriqueInaccessibleError

# Le fichier est placé à la racine du dépôt (le dossier parent de
# « logique/ »), quel que soit le dossier depuis lequel on lance l'application.
DOSSIER_PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEMIN_PAR_DEFAUT = os.path.join(DOSSIER_PROJET, "historique.csv")
COLONNE_DATE = "date"
FORMAT_DATE = "%Y-%m-%d %H:%M:%S"


class Historique:
    """Lit et écrit le fichier CSV des prédictions."""

    def __init__(self, colonnes: list[str],
                 chemin: str = CHEMIN_PAR_DEFAUT) -> None:
        """Reçoit les noms des colonnes à enregistrer (les variables puis la
        cible) et le chemin du fichier. Ne renvoie rien, n'échoue pas :
        le fichier n'est ni ouvert ni créé ici."""
        self._colonnes = [COLONNE_DATE] + list(colonnes)
        self._chemin = chemin

    @property
    def chemin(self) -> str:
        """Renvoie le chemin du fichier CSV (lecture seule)."""
        return self._chemin

    def _fichier_absent_ou_vide(self) -> bool:
        """Renvoie True si le fichier n'existe pas ou ne contient rien."""
        return (not os.path.exists(self._chemin)
                or os.path.getsize(self._chemin) == 0)

    def ajouter(self, valeurs: dict, moment: datetime | None = None) -> None:
        """Reçoit un dictionnaire {colonne: valeur} et l'ajoute au fichier,
        avec la date et l'heure (« moment », par défaut maintenant).

        Ne renvoie rien. Échoue avec HistoriqueInaccessibleError si le
        fichier ne peut pas être écrit, et avec KeyError s'il manque une
        colonne dans « valeurs ».
        """
        if moment is None:
            moment = datetime.now()
        ligne = {COLONNE_DATE: moment.strftime(FORMAT_DATE)}
        for colonne in self._colonnes[1:]:
            ligne[colonne] = valeurs[colonne]

        ecrire_entete = self._fichier_absent_ou_vide()
        try:
            # Mode « a » (append) : on ajoute à la fin sans effacer le reste.
            with open(self._chemin, "a", newline="", encoding="utf-8") as fichier:
                redacteur = csv.DictWriter(fichier, fieldnames=self._colonnes)
                if ecrire_entete:
                    redacteur.writeheader()
                redacteur.writerow(ligne)
        except OSError:
            raise HistoriqueInaccessibleError(
                "Impossible d'enregistrer la prédiction dans l'historique."
            ) from None

    def lire(self) -> list[dict]:
        """Renvoie la liste des prédictions, la plus récente en premier.

        Chaque prédiction est un dictionnaire {colonne: texte} : un CSV ne
        contient que du texte. Renvoie une liste vide si le fichier est
        absent ou vide. Échoue avec HistoriqueInaccessibleError si le
        fichier est illisible ou n'a pas les colonnes attendues.
        """
        if self._fichier_absent_ou_vide():
            return []
        try:
            with open(self._chemin, "r", newline="", encoding="utf-8") as fichier:
                lecteur = csv.DictReader(fichier)
                entete = lecteur.fieldnames
                lignes = list(lecteur)
        except (OSError, UnicodeDecodeError, csv.Error):
            raise HistoriqueInaccessibleError(
                "Le fichier d'historique est illisible.") from None
        if entete != self._colonnes:
            raise HistoriqueInaccessibleError(
                "Le fichier d'historique n'a pas les colonnes attendues.")

        # On inverse d'abord l'ordre du fichier : si deux prédictions ont
        # exactement la même date, la dernière écrite reste ainsi devant.
        lignes.reverse()
        # La date est écrite « année-mois-jour heure » : trier ce texte par
        # ordre alphabétique revient à trier par ordre chronologique.
        return sorted(lignes, key=lambda ligne: ligne[COLONNE_DATE], reverse=True)
