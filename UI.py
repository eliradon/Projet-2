"""Interface graphique (CustomTkinter).

Ce module ne contient que de l'affichage. Il ne valide rien, ne calcule
rien et ne lit aucun fichier : il appelle les classes de variables.py,
modele.py et historique.py.
"""

import tkinter
from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

import apparence
from exceptions import DonneeInvalideError
from historique import Historique
from modele import Modele
from variables import (AUCUN_TYPE, Variable, VariableCategorielle,
                       VariableNumerique, creer_variable)

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


def creer_carte(parent, titre: str | None = None) -> ctk.CTkFrame:
    """Reçoit un widget parent et un titre facultatif ; renvoie un cadre
    blanc aux coins arrondis (une « carte » de la maquette)."""
    carte = ctk.CTkFrame(parent, fg_color=apparence.COULEUR_CARTE,
                         corner_radius=14)
    if titre is None:
        return carte
    etiquette = ctk.CTkLabel(carte, text=titre, anchor="w",
                             text_color=apparence.COULEUR_TEXTE,
                             font=ctk.CTkFont(size=16, weight="bold"))
    etiquette.pack(fill="x", padx=24, pady=(20, 8))
    return carte


class LigneStatistique(ctk.CTkFrame):
    """Une ligne de saisie : libellé, champ éditable et curseur synchronisés."""

    def __init__(self, parent, variable: VariableNumerique,
                 sur_changement: Callable[[], None]) -> None:
        """Reçoit le widget parent, la variable à saisir (bornes, valeur par
        défaut) et la fonction à appeler quand la saisie change."""
        super().__init__(parent, fg_color="transparent")
        self._variable = variable
        self._sur_changement = sur_changement
        self.grid_columnconfigure(2, weight=1)  # le curseur prend la place libre

        libelle = ctk.CTkLabel(self, text=variable.libelle, width=96, anchor="e",
                               text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
                               font=ctk.CTkFont(size=17))
        libelle.grid(row=0, column=0, padx=(0, 16), pady=8)

        self._champ = ctk.CTkEntry(
            self, width=76, height=44, corner_radius=8, border_width=1,
            justify="center", fg_color=apparence.COULEUR_CARTE,
            border_color=apparence.COULEUR_BORDURE,
            text_color=apparence.COULEUR_TEXTE,
            font=ctk.CTkFont(size=24, weight="bold"))
        self._champ.grid(row=0, column=1, padx=(0, 16), pady=8)
        # À chaque touche relâchée dans le champ, on met le curseur à jour.
        self._champ.bind("<KeyRelease>", self._sur_saisie)

        self._curseur = ctk.CTkSlider(
            self, from_=variable.minimum, to=variable.maximum,
            number_of_steps=int(variable.maximum - variable.minimum),
            height=18, fg_color=apparence.COULEUR_SEPARATEUR,
            button_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            button_hover_color=apparence.COULEUR_TEXTE,
            command=self._sur_curseur)
        self._curseur.grid(row=0, column=2, sticky="ew")

        separateur = ctk.CTkFrame(self, height=1, corner_radius=0,
                                  fg_color=apparence.COULEUR_SEPARATEUR)
        separateur.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.reinitialiser()

    def lire(self) -> str:
        """Renvoie le texte brut du champ, sans le valider."""
        return self._champ.get()

    def reinitialiser(self) -> None:
        """Remet le champ et le curseur à la valeur par défaut."""
        self._ecrire(str(self._variable.defaut))
        self._placer_curseur(self._variable.defaut)

    def _ecrire(self, texte: str) -> None:
        """Remplace le contenu du champ par « texte »."""
        self._champ.delete(0, "end")
        self._champ.insert(0, texte)

    def _placer_curseur(self, valeur: float) -> None:
        """Déplace le curseur sur « valeur » et colore sa barre."""
        self._curseur.set(valeur)
        self._curseur.configure(
            progress_color=apparence.couleur_pour_valeur(valeur))

    def _sur_curseur(self, valeur: float) -> None:
        """Appelée quand on déplace le curseur : recopie la valeur dans le champ."""
        self._ecrire(str(round(valeur)))
        self._placer_curseur(valeur)
        self._sur_changement()

    def _sur_saisie(self, evenement: tkinter.Event) -> None:
        """Appelée quand on tape dans le champ : si le texte est une valeur
        valide, déplace le curseur ; sinon le curseur ne bouge pas."""
        try:
            valeur = self._variable.valider(self._champ.get())
        except DonneeInvalideError:
            pass  # le message d'erreur sera affiché au clic sur Prédire
        else:
            self._placer_curseur(valeur)
        self._sur_changement()


class SelecteurType(ctk.CTkFrame):
    """Une liste déroulante de types, avec la pastille (ou l'image) du type."""

    def __init__(self, parent, variable: VariableCategorielle,
                 sur_changement: Callable[[], None]) -> None:
        """Reçoit le widget parent, la variable (liste des types en anglais)
        et la fonction à appeler quand le choix change."""
        super().__init__(parent, fg_color="transparent")
        self._variable = variable
        self._sur_changement = sur_changement
        # Le menu affiche le nom français en majuscules ; ce dictionnaire
        # permet de retrouver le nom anglais attendu par le modèle.
        self._types_par_libelle = {
            apparence.nom_type_fr(type_anglais).upper(): type_anglais
            for type_anglais in variable.valeurs}

        titre = variable.libelle
        if AUCUN_TYPE in variable.valeurs:
            titre = titre + " (optionnel)"
        etiquette = ctk.CTkLabel(self, text=titre, anchor="w", height=18,
                                 text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
                                 font=ctk.CTkFont(size=13))
        etiquette.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self._pastille = None
        self._menu = ctk.CTkOptionMenu(
            self, values=list(self._types_par_libelle), width=150, height=44,
            corner_radius=8, anchor="center",
            fg_color=apparence.COULEUR_MENU_TYPE,
            button_color=apparence.COULEUR_MENU_TYPE,
            button_hover_color=apparence.COULEUR_TEXTE,
            text_color=apparence.COULEUR_TEXTE_CLAIR,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._sur_choix)
        self._menu.grid(row=1, column=1)
        self.reinitialiser()

    def lire(self) -> str:
        """Renvoie le type choisi, en anglais (ou « Aucun »)."""
        return self._types_par_libelle[self._menu.get()]

    def reinitialiser(self) -> None:
        """Revient au premier choix de la liste."""
        self._menu.set(list(self._types_par_libelle)[0])
        self._afficher_pastille()

    def _sur_choix(self, libelle: str) -> None:
        """Appelée quand on choisit un type dans le menu."""
        self._afficher_pastille()
        self._sur_changement()

    def _afficher_pastille(self) -> None:
        """Affiche l'image du type si elle existe, sinon un carré de sa couleur."""
        if self._pastille is not None:
            self._pastille.destroy()
        type_anglais = self.lire()
        self._pastille = ctk.CTkLabel(
            self, text="", width=44, height=44, corner_radius=8,
            fg_color=apparence.couleur_type(type_anglais))
        chemin = apparence.chemin_image_type(type_anglais)
        if chemin is not None:
            try:
                image = Image.open(chemin)
                largeur = round(40 * image.width / image.height)
                self._pastille.configure(
                    fg_color="transparent",
                    image=ctk.CTkImage(light_image=image, size=(largeur, 40)))
            except OSError:
                pass  # image illisible : on garde la pastille colorée
        self._pastille.grid(row=1, column=0, padx=(0, 6))


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

        self._carte_saisie = creer_carte(onglet)
        self._carte_saisie.grid(row=0, column=0, rowspan=2, sticky="nsew",
                                padx=(0, MARGE // 2))
        self._construire_saisie(self._carte_saisie)
        self._carte_radar = creer_carte(onglet, "Profil du Pokémon")
        self._carte_radar.grid(row=0, column=1, sticky="nsew",
                               padx=(MARGE // 2, 0), pady=(0, MARGE // 2))
        self._carte_distribution = creer_carte(onglet,
                                               "Où se situe la prédiction ?")
        self._carte_distribution.grid(row=1, column=1, sticky="nsew",
                                      padx=(MARGE // 2, 0), pady=(MARGE // 2, 0))

    def _construire_saisie(self, carte: ctk.CTkFrame) -> None:
        """Reçoit la carte de gauche et y crée un widget par variable, selon
        son type : curseur, interrupteur ou liste déroulante."""
        zone_legendaire = ctk.CTkFrame(carte, fg_color="transparent")
        zone_legendaire.pack(fill="x", padx=28, pady=(28, 12))
        zone_statistiques = ctk.CTkFrame(carte, fg_color="transparent")
        zone_statistiques.pack(fill="x", padx=28)
        zone_types = ctk.CTkFrame(carte, fg_color="transparent")
        zone_types.pack(fill="x", padx=28, pady=(20, 0))

        self._lignes: dict[str, LigneStatistique] = {}
        self._selecteurs: dict[str, SelecteurType] = {}
        for variable in self._variables:
            if isinstance(variable, VariableNumerique):
                ligne = LigneStatistique(zone_statistiques, variable,
                                         self._sur_changement)
                ligne.pack(fill="x")
                self._lignes[variable.nom] = ligne
            elif isinstance(variable.defaut, bool):
                self._variable_legendaire = variable
                self._construire_interrupteur(zone_legendaire, variable)
            else:
                selecteur = SelecteurType(zone_types, variable,
                                          self._sur_changement)
                selecteur.pack(side="left", padx=(0, 20))
                self._selecteurs[variable.nom] = selecteur

    def _construire_interrupteur(self, zone: ctk.CTkFrame,
                                 variable: VariableCategorielle) -> None:
        """Reçoit la zone du haut et la variable oui/non ; y place la question
        et l'interrupteur, désactivé par défaut."""
        question = ctk.CTkLabel(zone, text=variable.libelle + " ?",
                                text_color=apparence.COULEUR_TEXTE,
                                font=ctk.CTkFont(size=26, weight="bold"))
        question.pack(side="left", padx=(0, 20))
        self._interrupteur = ctk.CTkSwitch(
            zone, text="Non", switch_width=84, switch_height=44,
            fg_color=apparence.COULEUR_BORDURE,
            progress_color=apparence.COULEUR_INTERRUPTEUR_ACTIF,
            button_color=apparence.COULEUR_CARTE,
            button_hover_color=apparence.COULEUR_SEPARATEUR,
            text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            font=ctk.CTkFont(size=15), command=self._sur_interrupteur)
        self._interrupteur.pack(side="left")

    def _sur_interrupteur(self) -> None:
        """Appelée quand on bascule l'interrupteur : met à jour « Oui » / « Non »."""
        if self._interrupteur.get() == 1:
            self._interrupteur.configure(text="Oui")
        else:
            self._interrupteur.configure(text="Non")
        self._sur_changement()

    def _sur_changement(self) -> None:
        """Appelée quand une saisie change (curseur, champ, type, interrupteur).
        Ne fait rien pour l'instant : le radar et l'état « périmé » viendront
        aux étapes 9 et 10."""

    def _construire_onglet_historique(self, onglet: ctk.CTkFrame) -> None:
        """Reçoit le cadre de l'onglet Historique et y place sa carte."""
        self._carte_historique = creer_carte(onglet, "Prédictions enregistrées")
        self._carte_historique.pack(fill="both", expand=True)
