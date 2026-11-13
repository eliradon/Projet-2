"""Interface graphique (CustomTkinter).

Ce module ne contient que de l'affichage. Il ne valide rien, ne calcule
rien et ne lit aucun fichier : il appelle les classes de variables.py,
modele.py et historique.py.
"""

import tkinter
from tkinter import messagebox

import customtkinter as ctk

import apparence
from historique import Historique
from modele import Modele
from variables import Variable, creer_variable

TITRE = "Prédicteur de PV — Pokémon"
ONGLET_PREDICTION = "Prédiction"
ONGLET_HISTORIQUE = "Historique"
MARGE = 20


def afficher_erreur_fatale(message: str) -> None:
    """Reçoit un message et l'affiche dans une fenêtre d'erreur, quand
    l'application ne peut pas démarrer. Ne renvoie rien, n'échoue pas."""
    racine = tkinter.Tk()
    racine.withdraw()  # on cache la fenêtre vide créée par tkinter
    messagebox.showerror(TITRE, message)
    racine.destroy()


def creer_carte(parent, titre: str) -> ctk.CTkFrame:
    """Reçoit un widget parent et un titre ; renvoie un cadre blanc aux
    coins arrondis (une « carte » de la maquette) avec ce titre en haut."""
    carte = ctk.CTkFrame(parent, fg_color=apparence.COULEUR_CARTE,
                         corner_radius=14)
    etiquette = ctk.CTkLabel(carte, text=titre, anchor="w",
                             text_color=apparence.COULEUR_TEXTE,
                             font=ctk.CTkFont(size=16, weight="bold"))
    etiquette.pack(fill="x", padx=24, pady=(20, 8))
    return carte


class Application(ctk.CTk):
    """Fenêtre principale. Elle CONTIENT (composition) le modèle, la liste
    des variables et l'historique, ainsi que les panneaux de l'écran."""

    def __init__(self, modele: Modele) -> None:
        """Reçoit un modèle déjà chargé et construit la fenêtre.
        Ne renvoie rien. Échoue avec ModeleIntrouvableError si le modèle
        n'a pas été chargé."""
        super().__init__(fg_color=apparence.COULEUR_FOND)
        self._modele = modele
        metadonnees = modele.metadonnees
        # Les variables viennent des métadonnées : rien n'est codé en dur.
        self._variables: list[Variable] = [
            creer_variable(description)
            for description in metadonnees["variables"]]
        colonnes = [variable.nom for variable in self._variables]
        self._historique = Historique(colonnes + [metadonnees["cible"]["nom"]])

        self.title(TITRE)
        self.geometry("1280x860")
        self.minsize(1000, 700)
        self._construire()

    def _construire(self) -> None:
        """Crée les onglets et la disposition générale de la fenêtre."""
        self._onglets = ctk.CTkTabview(
            self, anchor="ne",
            fg_color=apparence.COULEUR_FOND,
            segmented_button_fg_color=apparence.COULEUR_FOND_ONGLETS,
            segmented_button_selected_color=apparence.COULEUR_CARTE,
            segmented_button_selected_hover_color=apparence.COULEUR_CARTE,
            segmented_button_unselected_color=apparence.COULEUR_FOND_ONGLETS,
            segmented_button_unselected_hover_color=apparence.COULEUR_SEPARATEUR,
            segmented_button_font=ctk.CTkFont(size=15),
            text_color=apparence.COULEUR_TEXTE)
        self._onglets.pack(fill="both", expand=True, padx=MARGE, pady=(8, MARGE))
        self._onglets.add(ONGLET_PREDICTION)
        self._onglets.add(ONGLET_HISTORIQUE)

        # Le titre est posé en haut à gauche, sur la même ligne que les onglets.
        titre = ctk.CTkLabel(self, text=TITRE,
                             text_color=apparence.COULEUR_TEXTE,
                             font=ctk.CTkFont(size=22, weight="bold"))
        titre.place(x=MARGE + 8, y=14)

        self._construire_onglet_prediction(self._onglets.tab(ONGLET_PREDICTION))
        self._construire_onglet_historique(self._onglets.tab(ONGLET_HISTORIQUE))

    def _construire_onglet_prediction(self, onglet: ctk.CTkFrame) -> None:
        """Reçoit le cadre de l'onglet Prédiction et y place deux colonnes :
        la saisie à gauche, les deux graphiques à droite."""
        # La colonne de gauche est un peu plus large (5 parts contre 4).
        onglet.grid_columnconfigure(0, weight=5, uniform="colonnes")
        onglet.grid_columnconfigure(1, weight=4, uniform="colonnes")
        onglet.grid_rowconfigure(0, weight=1)
        onglet.grid_rowconfigure(1, weight=1)

        self._carte_saisie = creer_carte(onglet, "Caractéristiques du Pokémon")
        self._carte_saisie.grid(row=0, column=0, rowspan=2, sticky="nsew",
                                padx=(0, MARGE // 2))
        self._carte_radar = creer_carte(onglet, "Profil du Pokémon")
        self._carte_radar.grid(row=0, column=1, sticky="nsew",
                               padx=(MARGE // 2, 0), pady=(0, MARGE // 2))
        self._carte_distribution = creer_carte(onglet,
                                               "Où se situe la prédiction ?")
        self._carte_distribution.grid(row=1, column=1, sticky="nsew",
                                      padx=(MARGE // 2, 0), pady=(MARGE // 2, 0))

    def _construire_onglet_historique(self, onglet: ctk.CTkFrame) -> None:
        """Reçoit le cadre de l'onglet Historique et y place sa carte."""
        self._carte_historique = creer_carte(onglet, "Prédictions enregistrées")
        self._carte_historique.pack(fill="both", expand=True)
