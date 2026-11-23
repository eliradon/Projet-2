"""Interface graphique (CustomTkinter).

Ce module ne contient que de l'affichage. Il ne valide rien, ne calcule
rien et ne lit aucun fichier : il appelle les classes de variables.py,
modele.py et historique.py.
"""

import math
import os
import tkinter
from collections.abc import Callable
from tkinter import messagebox, ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image

from interface import apparence
from logique.exceptions import DonneeInvalideError, HistoriqueInaccessibleError
from logique.historique import COLONNE_DATE, Historique
from logique.modele import (COLONNE_STADE, NOM_RARETE, Modele, arrondir_pv,
                            forme_finale_imposee)
from logique.variables import (AUCUN_TYPE, Variable, VariableCategorielle,
                       VariableNumerique, creer_variable,
                       verifier_types_differents)

TITRE = "Prédicteur de PV — Pokémon"
ONGLET_PREDICTION = "Prédiction"
ONGLET_HISTORIQUE = "Historique"
MARGE = 20
TEXTE_PV_VIDE = "—"
MESSAGE_PERIME = "Cliquez sur Prédire pour mettre à jour"
MESSAGE_HISTORIQUE_VIDE = "Aucune prédiction pour l'instant."
# Axes du radar après les PV, dans le sens des aiguilles d'une montre.
ORDRE_RADAR = ["attack", "defense", "speed", "sp_defense", "sp_attack"]
LARGEUR_LIBELLE = 150


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

        libelle = ctk.CTkLabel(self, text=variable.libelle,
                               width=LARGEUR_LIBELLE, anchor="e",
                               text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
                               font=ctk.CTkFont(size=15))
        libelle.grid(row=0, column=0, padx=(0, 16), pady=5)

        self._champ = ctk.CTkEntry(
            self, width=84, height=36, corner_radius=8, border_width=1,
            justify="center", fg_color=apparence.COULEUR_CARTE,
            border_color=apparence.COULEUR_BORDURE,
            text_color=apparence.COULEUR_TEXTE,
            font=ctk.CTkFont(size=20, weight="bold"))
        self._champ.grid(row=0, column=1, padx=(0, 16), pady=5)
        # À chaque touche relâchée dans le champ, on met le curseur à jour.
        self._champ.bind("<KeyRelease>", self._sur_saisie)

        self._curseur = ctk.CTkSlider(
            self, from_=variable.minimum, to=variable.maximum,
            # Nombre de crans : 1 par unité, ou 1 par dixième pour un décimal.
            number_of_steps=round((variable.maximum - variable.minimum)
                                  / variable.pas),
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
        self.marquer_erreur(False)
        self._ecrire(self._variable.formater(self._variable.defaut))
        self._placer_curseur(self._variable.defaut)

    def marquer_erreur(self, en_erreur: bool) -> None:
        """Reçoit True pour encadrer le champ en rouge, False pour lui
        rendre sa bordure normale."""
        if en_erreur:
            self._champ.configure(border_width=2,
                                  border_color=apparence.COULEUR_ERREUR)
        else:
            self._champ.configure(border_width=1,
                                  border_color=apparence.COULEUR_BORDURE)

    def _ecrire(self, texte: str) -> None:
        """Remplace le contenu du champ par « texte »."""
        self._champ.delete(0, "end")
        self._champ.insert(0, texte)

    def _placer_curseur(self, valeur: float) -> None:
        """Déplace le curseur sur « valeur » et colore sa barre."""
        self._curseur.set(valeur)
        # Seules les statistiques de combat changent de couleur selon la
        # valeur ; le poids, la taille et le stade gardent une couleur fixe.
        if self._variable.statistique:
            couleur = apparence.couleur_pour_valeur(valeur)
        else:
            couleur = apparence.COULEUR_RADAR
        self._curseur.configure(progress_color=couleur)

    def _sur_curseur(self, valeur: float) -> None:
        """Appelée quand on déplace le curseur : recopie la valeur dans le champ."""
        self._ecrire(self._variable.formater(valeur))
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


class ChampSimple(ctk.CTkFrame):
    """Une case de saisie seule, avec son libellé au-dessus (poids, taille,
    stade d'évolution). Même méthodes que LigneStatistique, sans curseur."""

    def __init__(self, parent, variable: VariableNumerique,
                 sur_changement: Callable[[], None]) -> None:
        """Reçoit le widget parent, la variable à saisir et la fonction à
        appeler quand la saisie change."""
        super().__init__(parent, fg_color="transparent")
        self._variable = variable
        etiquette = ctk.CTkLabel(self, text=variable.libelle, anchor="w",
                                 height=18,
                                 text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
                                 font=ctk.CTkFont(size=13))
        etiquette.pack(fill="x", pady=(0, 6))
        self._champ = ctk.CTkEntry(
            self, width=120, height=40, corner_radius=8, border_width=1,
            justify="center", fg_color=apparence.COULEUR_CARTE,
            border_color=apparence.COULEUR_BORDURE,
            text_color=apparence.COULEUR_TEXTE,
            font=ctk.CTkFont(size=18, weight="bold"))
        self._champ.pack(anchor="w")
        # La lambda ignore l'événement reçu et appelle sur_changement().
        self._champ.bind("<KeyRelease>", lambda evenement: sur_changement())
        self.reinitialiser()

    def lire(self) -> str:
        """Renvoie le texte brut de la case, sans le valider."""
        return self._champ.get()

    def reinitialiser(self) -> None:
        """Remet la valeur par défaut dans la case."""
        self.marquer_erreur(False)
        self._champ.delete(0, "end")
        self._champ.insert(0, self._variable.formater(self._variable.defaut))

    def marquer_erreur(self, en_erreur: bool) -> None:
        """Reçoit True pour encadrer la case en rouge, False sinon."""
        if en_erreur:
            self._champ.configure(border_width=2,
                                  border_color=apparence.COULEUR_ERREUR)
        else:
            self._champ.configure(border_width=1,
                                  border_color=apparence.COULEUR_BORDURE)


class LigneResultat(ctk.CTkFrame):
    """La ligne PV : même gabarit qu'une statistique, mais en lecture seule."""

    def __init__(self, parent, libelle: str, maximum: float) -> None:
        """Reçoit le widget parent, le libellé (« PV ») et la plus grande
        valeur possible, qui correspond à une barre pleine."""
        super().__init__(parent, fg_color=apparence.COULEUR_FOND_ACCENT,
                         corner_radius=0)
        self._maximum = maximum
        self.grid_columnconfigure(2, weight=1)

        etiquette = ctk.CTkLabel(self, text=libelle, width=LARGEUR_LIBELLE,
                                 anchor="e",
                                 text_color=apparence.COULEUR_ACCENT,
                                 font=ctk.CTkFont(size=17, weight="bold"))
        etiquette.grid(row=0, column=0, padx=(0, 16), pady=8)
        self._valeur = ctk.CTkLabel(self, width=76, height=44,
                                    text_color=apparence.COULEUR_ACCENT,
                                    font=ctk.CTkFont(size=30, weight="bold"))
        self._valeur.grid(row=0, column=1, padx=(0, 16), pady=8)
        self._barre = ctk.CTkProgressBar(
            self, height=18, fg_color=apparence.COULEUR_SEPARATEUR)
        self._barre.grid(row=0, column=2, sticky="ew", padx=(0, 12))
        self.vider()

    def afficher(self, pv: int) -> None:
        """Reçoit les PV prédits ; affiche le nombre et remplit la barre."""
        self._valeur.configure(text=str(pv),
                               text_color=apparence.COULEUR_ACCENT)
        # La barre attend une proportion entre 0 (vide) et 1 (pleine).
        self._barre.set(min(1.0, pv / self._maximum))
        self._barre.configure(progress_color=apparence.couleur_pour_valeur(pv))

    def griser(self) -> None:
        """Grise la valeur et la barre : la prédiction n'est plus à jour."""
        self._valeur.configure(text_color=apparence.COULEUR_BORDURE)
        self._barre.configure(progress_color=apparence.COULEUR_BORDURE)

    def vider(self) -> None:
        """Revient à l'état initial : « — » et barre vide."""
        self._valeur.configure(text=TEXTE_PV_VIDE)
        self._barre.set(0)


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


class PanneauRadar:
    """Graphique 1 : le profil du Pokémon sur un radar à six axes."""

    def __init__(self, parent, libelles: list[str], maximum: float) -> None:
        """Reçoit le widget parent, les six libellés (les PV en premier) et
        la valeur qui correspond au bord extérieur du radar."""
        self._libelles = libelles
        self._maximum = maximum
        # Un angle par axe, répartis régulièrement sur le tour complet.
        self._angles = [2 * math.pi * numero / len(libelles)
                        for numero in range(len(libelles))]
        figure = Figure(figsize=(5, 3.4), dpi=100, layout="constrained")
        self._axes = figure.add_subplot(projection="polar")
        # FigureCanvasTkAgg transforme la figure Matplotlib en widget tkinter.
        self._canevas = FigureCanvasTkAgg(figure, master=parent)
        self._canevas.get_tk_widget().pack(fill="both", expand=True,
                                           padx=12, pady=12)

    def tracer(self, statistiques: list[float], pv: int | None) -> None:
        """Reçoit les cinq statistiques (dans l'ordre des axes) et les PV
        prédits, ou None s'il n'y a pas de prédiction à montrer. Redessine."""
        axes = self._axes
        axes.clear()
        axes.set_theta_offset(math.pi / 2)  # premier axe (PV) en haut
        axes.set_theta_direction(-1)        # sens des aiguilles d'une montre
        axes.set_xticks(self._angles)
        axes.set_xticklabels(self._libelles)
        axes.set_ylim(0, self._maximum)
        axes.set_yticklabels([])
        axes.set_title("Profil du Pokémon", fontweight="bold")

        if pv is None:
            # Sans prédiction, le sommet PV n'est pas tracé : ligne ouverte.
            axes.plot(self._angles[1:], statistiques, linewidth=2.5,
                      color=apparence.COULEUR_ACCENT, label="Saisie")
        else:
            # On revient au premier point pour fermer le polygone.
            angles = self._angles + [self._angles[0]]
            rayons = [pv] + statistiques + [pv]
            axes.plot(angles, rayons, linewidth=2.5,
                      color=apparence.COULEUR_ACCENT, label="Saisie")
            axes.fill(angles, rayons, color=apparence.COULEUR_RADAR, alpha=0.35)
            axes.plot([self._angles[0]], [pv], "o", markersize=9,
                      color=apparence.COULEUR_PREDICTION, label="PV prédits")
        axes.legend(loc="upper left", bbox_to_anchor=(1.15, 1.0))
        self._canevas.draw_idle()


class PanneauDistribution:
    """Graphique 2 : où se situe la prédiction parmi les PV du jeu de données."""

    def __init__(self, parent, bornes: list[float], effectifs: list[int],
                 erreur_moyenne: float) -> None:
        """Reçoit le widget parent, les bornes et les effectifs de
        l'histogramme (lus dans les métadonnées) et l'erreur moyenne."""
        self._bornes = bornes
        self._effectifs = effectifs
        self._erreur_moyenne = erreur_moyenne
        figure = Figure(figsize=(5, 3.4), dpi=100, layout="constrained")
        self._axes = figure.add_subplot()
        self._canevas = FigureCanvasTkAgg(figure, master=parent)
        self._canevas.get_tk_widget().pack(fill="both", expand=True,
                                           padx=12, pady=12)

    def tracer(self, pv: int | None) -> None:
        """Reçoit les PV prédits, ou None avant toute prédiction. Redessine
        l'histogramme, puis la ligne et la bande d'erreur s'il y a des PV."""
        axes = self._axes
        axes.clear()
        largeur = self._bornes[1] - self._bornes[0]
        # Chaque barre commence à sa borne gauche (align="edge").
        axes.bar(self._bornes[:-1], self._effectifs, width=largeur * 0.92,
                 align="edge", color=apparence.COULEUR_HISTOGRAMME,
                 label="Jeu de données")
        if pv is not None:
            axes.axvspan(pv - self._erreur_moyenne, pv + self._erreur_moyenne,
                         color=apparence.COULEUR_PREDICTION, alpha=0.12,
                         label="± erreur moyenne")
            axes.axvline(pv, linewidth=2.5, color=apparence.COULEUR_PREDICTION,
                         label=f"PV prédits ({pv})")
        axes.set_title("Où se situe la prédiction ?", fontweight="bold")
        axes.set_xlabel("PV")
        axes.set_ylabel("Nombre de Pokémon")
        axes.set_xlim(self._bornes[0], self._bornes[-1])
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        axes.legend(loc="upper right")
        self._canevas.draw_idle()


class OngletHistorique(ctk.CTkFrame):
    """Le tableau des prédictions enregistrées, les plus récentes en premier."""

    def __init__(self, parent, historique: Historique, entetes: dict[str, str],
                 colonnes_numeriques: list[str]) -> None:
        """Reçoit le widget parent, l'historique à afficher, les en-têtes
        {colonne du CSV: libellé affiché} et les colonnes à aligner à droite."""
        super().__init__(parent, fg_color=apparence.COULEUR_CARTE,
                         corner_radius=14)
        self._historique = historique
        self._colonnes = list(entetes)

        haut = ctk.CTkFrame(self, fg_color="transparent")
        haut.pack(fill="x", padx=28, pady=(28, 16))
        bouton = ctk.CTkButton(
            haut, text="Actualiser", height=44, width=120, corner_radius=10,
            border_width=1, fg_color=apparence.COULEUR_CARTE,
            hover_color=apparence.COULEUR_FOND,
            border_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            text_color=apparence.COULEUR_TEXTE, font=ctk.CTkFont(size=15),
            command=self.actualiser)
        bouton.pack(side="right")
        titre = ctk.CTkLabel(haut, text="Prédictions enregistrées", anchor="w",
                             text_color=apparence.COULEUR_TEXTE,
                             font=ctk.CTkFont(size=18, weight="bold"))
        titre.pack(fill="x")
        self._sous_titre = ctk.CTkLabel(
            haut, text="", anchor="w", font=ctk.CTkFont(size=14),
            text_color=apparence.COULEUR_TEXTE_SECONDAIRE)
        self._sous_titre.pack(fill="x")

        # Message affiché à la place du tableau (historique vide ou illisible).
        self._message = ctk.CTkLabel(
            self, text="", anchor="w", font=ctk.CTkFont(size=15),
            text_color=apparence.COULEUR_TEXTE_SECONDAIRE)

        self._appliquer_style()
        self._tableau = ttk.Treeview(self, columns=self._colonnes,
                                     show="headings", selectmode="none")
        for colonne, libelle in entetes.items():
            alignement = "e" if colonne in colonnes_numeriques else "w"
            self._tableau.heading(colonne, text=libelle, anchor=alignement)
            self._tableau.column(colonne, anchor=alignement, width=68)
        self._tableau.column(COLONNE_DATE, width=150)
        self.actualiser()

    def _appliquer_style(self) -> None:
        """Règle les couleurs et les tailles du tableau (widget ttk)."""
        style = ttk.Style()
        style.theme_use("default")  # le thème de macOS ignore les couleurs
        style.configure("Treeview", rowheight=40, font=("", 14), borderwidth=0,
                        background=apparence.COULEUR_CARTE,
                        fieldbackground=apparence.COULEUR_CARTE,
                        foreground=apparence.COULEUR_TEXTE)
        style.configure("Treeview.Heading", font=("", 12, "bold"),
                        relief="flat", padding=8,
                        background=apparence.COULEUR_FOND,
                        foreground=apparence.COULEUR_TEXTE_SECONDAIRE)

    def actualiser(self) -> None:
        """Relit l'historique et remplit le tableau. N'échoue pas : si le
        fichier est illisible, le message d'erreur remplace le tableau."""
        try:
            lignes = self._historique.lire()
        except HistoriqueInaccessibleError as erreur:
            self._afficher_message(str(erreur))
            return
        if len(lignes) == 0:
            self._afficher_message(MESSAGE_HISTORIQUE_VIDE)
            return

        self._tableau.delete(*self._tableau.get_children())
        for ligne in lignes:
            cases = [apparence.formater_cellule(ligne[colonne])
                     for colonne in self._colonnes]
            self._tableau.insert("", "end", values=cases)
        pluriel = "s" if len(lignes) > 1 else ""
        self._sous_titre.configure(
            text=f"{len(lignes)} prédiction{pluriel} · les plus récentes en "
                 f"premier · fichier {os.path.basename(self._historique.chemin)}")
        self._message.pack_forget()
        self._tableau.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _afficher_message(self, texte: str) -> None:
        """Reçoit un texte et l'affiche à la place du tableau."""
        self._sous_titre.configure(text="")
        self._tableau.pack_forget()
        self._message.configure(text=texte)
        self._message.pack(fill="x", padx=28, pady=(0, 28))


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
        self._variables_par_nom = {variable.nom: variable
                                   for variable in self._variables}
        colonnes = [variable.nom for variable in self._variables]
        self._historique = Historique(colonnes + [metadonnees["cible"]["nom"]])

        # True quand des PV prédits sont affichés à l'écran.
        self._prediction_affichee = False

        self.title(TITRE)
        self.geometry("1280x940")  # assez haut pour voir le résultat sans défiler
        # La carte de saisie défile : la fenêtre peut être plus petite.
        self.minsize(1100, 700)
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
            text_color=apparence.COULEUR_TEXTE,
            command=self._sur_onglet)
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

        # La carte de gauche défile si la fenêtre est trop petite pour tout
        # afficher (il y a beaucoup de variables).
        self._carte_saisie = ctk.CTkScrollableFrame(
            onglet, fg_color=apparence.COULEUR_CARTE, corner_radius=14)
        self._carte_saisie.grid(row=0, column=0, rowspan=2, sticky="nsew",
                                padx=(0, MARGE // 2))
        self._construire_saisie(self._carte_saisie)
        # Les titres de ces deux cartes sont dessinés par Matplotlib.
        self._carte_radar = creer_carte(onglet)
        self._carte_radar.grid(row=0, column=1, sticky="nsew",
                               padx=(MARGE // 2, 0), pady=(0, MARGE // 2))
        self._carte_distribution = creer_carte(onglet)
        self._carte_distribution.grid(row=1, column=1, sticky="nsew",
                                      padx=(MARGE // 2, 0), pady=(MARGE // 2, 0))
        self._construire_graphiques()

    def _construire_graphiques(self) -> None:
        """Crée les deux graphiques à partir des métadonnées et les dessine
        dans leur état initial (sans prédiction)."""
        metadonnees = self._modele.metadonnees
        cible = metadonnees["cible"]
        libelles = [cible["libelle"]] + [
            self._variables_par_nom[nom].libelle for nom in ORDRE_RADAR]
        maximum = max([cible["max"]] + [
            self._variables_par_nom[nom].maximum for nom in ORDRE_RADAR])
        self._radar = PanneauRadar(self._carte_radar, libelles, maximum)
        distribution = metadonnees["distribution_cible"]
        self._distribution = PanneauDistribution(
            self._carte_distribution, distribution["bornes"],
            distribution["effectifs"], metadonnees["metrique"]["valeur"])
        self._tracer_radar(None)
        self._distribution.tracer(None)

    def _tracer_radar(self, pv: int | None) -> None:
        """Reçoit les PV à montrer (ou None) et redessine le radar avec les
        saisies actuelles. Si une saisie est invalide, le radar ne change pas."""
        statistiques = []
        for nom in ORDRE_RADAR:
            try:
                statistiques.append(self._variables_par_nom[nom].valider(
                    self._lignes[nom].lire()))
            except DonneeInvalideError:
                return
        self._radar.tracer(statistiques, pv)

    def _construire_saisie(self, carte: ctk.CTkFrame) -> None:
        """Reçoit la carte de gauche et y crée un widget par variable, selon
        son type : curseur, case de saisie, liste déroulante, choix de
        rareté ou case à cocher."""
        zone_statistiques = ctk.CTkFrame(carte, fg_color="transparent")
        zone_statistiques.pack(fill="x", padx=20, pady=(16, 0))
        zone_champs = ctk.CTkFrame(carte, fg_color="transparent")
        zone_champs.pack(fill="x", padx=20, pady=(16, 0))
        zone_types = ctk.CTkFrame(carte, fg_color="transparent")
        zone_types.pack(fill="x", padx=20, pady=(16, 0))
        zone_rarete = ctk.CTkFrame(carte, fg_color="transparent")
        zone_rarete.pack(fill="x", padx=20, pady=(16, 0))

        cible = self._modele.metadonnees["cible"]
        self._ligne_pv = LigneResultat(zone_statistiques, cible["libelle"],
                                       cible["max"])
        self._ligne_pv.pack(fill="x")

        self._lignes: dict[str, LigneStatistique | ChampSimple] = {}
        self._selecteurs: dict[str, SelecteurType] = {}
        for variable in self._variables:
            if isinstance(variable, VariableNumerique) and variable.statistique:
                ligne = LigneStatistique(zone_statistiques, variable,
                                         self._sur_changement)
                ligne.pack(fill="x")
                self._lignes[variable.nom] = ligne
            elif isinstance(variable, VariableNumerique):
                champ = ChampSimple(zone_champs, variable, self._sur_changement)
                champ.pack(side="left", padx=(0, 20))
                self._lignes[variable.nom] = champ
            elif isinstance(variable.defaut, bool):
                self._construire_case_a_cocher(zone_rarete, variable)
            elif variable.nom == NOM_RARETE:
                self._construire_rarete(zone_rarete, variable)
            else:
                selecteur = SelecteurType(zone_types, variable,
                                          self._sur_changement)
                selecteur.pack(side="left", padx=(0, 20))
                self._selecteurs[variable.nom] = selecteur
        self._construire_actions(carte)

    def _construire_rarete(self, zone: ctk.CTkFrame,
                           variable: VariableCategorielle) -> None:
        """Reçoit la zone du bas et la variable de rareté ; y place un bouton
        à plusieurs choix (Aucune, Sous-légendaire, Légendaire, Fabuleux)."""
        self._variable_rarete = variable
        bloc = ctk.CTkFrame(zone, fg_color="transparent")
        bloc.pack(side="left", padx=(0, 24))
        etiquette = ctk.CTkLabel(bloc, text=variable.libelle, anchor="w",
                                 height=18,
                                 text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
                                 font=ctk.CTkFont(size=13))
        etiquette.pack(fill="x", pady=(0, 6))
        self._choix_rarete = ctk.CTkSegmentedButton(
            bloc, values=variable.valeurs, height=40,
            fg_color=apparence.COULEUR_FOND_ONGLETS,
            selected_color=apparence.COULEUR_BOUTON_PRINCIPAL,
            selected_hover_color=apparence.COULEUR_ACCENT,
            unselected_color=apparence.COULEUR_FOND_ONGLETS,
            unselected_hover_color=apparence.COULEUR_SEPARATEUR,
            text_color=apparence.COULEUR_TEXTE, font=ctk.CTkFont(size=14),
            command=lambda choix: self._sur_changement())
        self._choix_rarete.pack(anchor="w")
        self._choix_rarete.set(variable.defaut)

    def _construire_case_a_cocher(self, zone: ctk.CTkFrame,
                                  variable: VariableCategorielle) -> None:
        """Reçoit la zone du bas et la variable oui/non (forme finale) ; y
        place une case à cocher, décochée par défaut."""
        self._variable_forme_finale = variable
        self._case_forme_finale = ctk.CTkCheckBox(
            zone, text=variable.libelle, checkbox_width=26, checkbox_height=26,
            fg_color=apparence.COULEUR_BOUTON_PRINCIPAL,
            hover_color=apparence.COULEUR_ACCENT,
            border_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            text_color=apparence.COULEUR_TEXTE,
            text_color_disabled=apparence.COULEUR_TEXTE_SECONDAIRE,
            font=ctk.CTkFont(size=15), command=self._sur_changement)
        self._case_forme_finale.pack(side="left", pady=(24, 0))

    def _construire_actions(self, carte: ctk.CTkFrame) -> None:
        """Reçoit la carte de gauche et y ajoute, sous la saisie : la zone
        des messages, les deux boutons et l'encadré du résultat."""
        self._message = ctk.CTkLabel(carte, text="", anchor="w", justify="left",
                                     text_color=apparence.COULEUR_ERREUR,
                                     font=ctk.CTkFont(size=14))
        self._message.pack(fill="x", padx=20, pady=(16, 8))

        zone_boutons = ctk.CTkFrame(carte, fg_color="transparent")
        zone_boutons.pack(fill="x", padx=20)
        bouton_predire = ctk.CTkButton(
            zone_boutons, text="Prédire", height=48, width=140,
            corner_radius=10, fg_color=apparence.COULEUR_BOUTON_PRINCIPAL,
            hover_color=apparence.COULEUR_ACCENT,
            text_color=apparence.COULEUR_TEXTE_CLAIR,
            font=ctk.CTkFont(size=17, weight="bold"),
            command=self._sur_predire)
        bouton_predire.pack(side="left", padx=(0, 12))
        bouton_reinitialiser = ctk.CTkButton(
            zone_boutons, text="Réinitialiser", height=48, width=150,
            corner_radius=10, border_width=1,
            fg_color=apparence.COULEUR_CARTE,
            hover_color=apparence.COULEUR_FOND,
            border_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            text_color=apparence.COULEUR_TEXTE,
            font=ctk.CTkFont(size=17), command=self._reinitialiser)
        bouton_reinitialiser.pack(side="left")

        # L'encadré du résultat n'est affiché qu'après une prédiction.
        self._encadre_resultat = ctk.CTkFrame(
            carte, fg_color=apparence.COULEUR_FOND_ACCENT, corner_radius=10)
        self._phrase_resultat = ctk.CTkLabel(
            self._encadre_resultat, text="", anchor="w",
            text_color=apparence.COULEUR_TEXTE,
            font=ctk.CTkFont(size=20, weight="bold"))
        self._phrase_resultat.pack(fill="x", padx=20, pady=(14, 0))
        self._phrase_erreur_moyenne = ctk.CTkLabel(
            self._encadre_resultat, text="", anchor="w",
            text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            font=ctk.CTkFont(size=14))
        self._phrase_erreur_moyenne.pack(fill="x", padx=20)
        self._phrase_r2 = ctk.CTkLabel(
            self._encadre_resultat, text="", anchor="w",
            text_color=apparence.COULEUR_TEXTE_SECONDAIRE,
            font=ctk.CTkFont(size=14))
        self._phrase_r2.pack(fill="x", padx=20, pady=(0, 14))

    def _lire_saisies(self) -> dict:
        """Renvoie les saisies brutes, non validées : {nom de variable: saisie}."""
        saisies = {}
        for nom, ligne in self._lignes.items():
            saisies[nom] = ligne.lire()
        for nom, selecteur in self._selecteurs.items():
            saisies[nom] = selecteur.lire()
        saisies[self._variable_rarete.nom] = self._choix_rarete.get()
        saisies[self._variable_forme_finale.nom] = (
            self._case_forme_finale.get() == 1)
        return saisies

    def _valider_saisies(self, saisies: dict) -> tuple[dict, list[str]]:
        """Reçoit les saisies brutes ; renvoie les valeurs validées et la
        liste des messages d'erreur (vide si tout est valide). Encadre en
        rouge les champs fautifs. N'échoue pas : les erreurs sont accumulées."""
        valeurs = {}
        erreurs = []
        for variable in self._variables:
            try:
                valeurs[variable.nom] = variable.valider(saisies[variable.nom])
            except DonneeInvalideError as erreur:
                erreurs.append(str(erreur))
            if variable.nom in self._lignes:
                self._lignes[variable.nom].marquer_erreur(
                    variable.nom not in valeurs)
        if "Type 1" in valeurs and "Type 2" in valeurs:
            try:
                verifier_types_differents(valeurs["Type 1"], valeurs["Type 2"])
            except DonneeInvalideError as erreur:
                erreurs.append(str(erreur))
        return valeurs, erreurs

    def _sur_predire(self) -> None:
        """Appelée au clic sur Prédire : valide, prédit, affiche, enregistre."""
        valeurs, erreurs = self._valider_saisies(self._lire_saisies())
        if erreurs:
            # État « Saisie invalide » : une erreur par ligne, PV inchangés.
            self._afficher_message("\n".join(erreurs))
            return
        self._afficher_message("")

        metadonnees = self._modele.metadonnees
        pv = arrondir_pv(self._modele.predire(valeurs),
                         metadonnees["cible"]["min"])
        self._afficher_resultat(pv)

        valeurs[metadonnees["cible"]["nom"]] = pv
        try:
            self._historique.ajouter(valeurs)
        except HistoriqueInaccessibleError as erreur:
            # La prédiction reste affichée ; on signale seulement le problème.
            self._afficher_message(str(erreur))
        self._onglet_historique.actualiser()

    def _afficher_resultat(self, pv: int) -> None:
        """Reçoit les PV prédits ; met à jour la ligne PV et la phrase."""
        metrique = self._modele.metadonnees["metrique"]
        erreur_moyenne = round(metrique["valeur"])
        self._prediction_affichee = True
        self._ligne_pv.afficher(pv)
        self._tracer_radar(pv)
        self._distribution.tracer(pv)
        self._phrase_resultat.configure(
            text=f"Ce Pokémon aurait environ {pv} PV.")
        self._phrase_erreur_moyenne.configure(
            text=f"Erreur moyenne du modèle : ± {erreur_moyenne} PV")
        self._phrase_r2.configure(
            text=f"Score R² du modèle : {apparence.formater_r2(metrique['r2'])}"
                 " (1 = parfait, 0 = pas mieux que la moyenne)")
        self._encadre_resultat.pack(fill="x", padx=20, pady=(16, 20))

    def _reinitialiser(self) -> None:
        """Appelée au clic sur Réinitialiser : revient à l'état initial."""
        for ligne in self._lignes.values():
            ligne.reinitialiser()
        for selecteur in self._selecteurs.values():
            selecteur.reinitialiser()
        self._choix_rarete.set(self._variable_rarete.defaut)
        self._case_forme_finale.configure(state="normal")
        self._case_forme_finale.deselect()
        self._ligne_pv.vider()
        self._tracer_radar(None)
        self._distribution.tracer(None)
        self._prediction_affichee = False
        self._afficher_message("")
        self._encadre_resultat.pack_forget()

    def _imposer_forme_finale(self) -> None:
        """Coche et bloque la case « Forme finale » si le stade d'évolution
        saisi est le dernier possible ; sinon la case redevient modifiable.
        La règle elle-même est dans logique/modele.py."""
        variable_stade = self._variables_par_nom.get(COLONNE_STADE)
        if variable_stade is None:
            return
        try:
            stade = variable_stade.valider(self._lignes[COLONNE_STADE].lire())
        except DonneeInvalideError:
            return  # stade mal saisi : l'erreur s'affichera au clic sur Prédire
        if forme_finale_imposee(stade, variable_stade.maximum):
            self._case_forme_finale.select()
            self._case_forme_finale.configure(state="disabled")
        elif self._case_forme_finale.cget("state") == "disabled":
            # On quitte le dernier stade : la case avait été cochée par la
            # règle, on la décoche et on la rend de nouveau modifiable.
            self._case_forme_finale.configure(state="normal")
            self._case_forme_finale.deselect()

    def _sur_changement(self) -> None:
        """Appelée quand une saisie change (curseur, case, type, rareté...).
        Applique la règle du dernier stade, redessine le radar sans le sommet
        PV qui n'est plus à jour, et passe une prédiction affichée à l'état
        « périmé »."""
        self._imposer_forme_finale()
        self._tracer_radar(None)
        if self._prediction_affichee:
            self._ligne_pv.griser()
            self._afficher_message(MESSAGE_PERIME,
                                   apparence.COULEUR_TEXTE_SECONDAIRE)

    def _afficher_message(self, texte: str,
                          couleur: str = apparence.COULEUR_ERREUR) -> None:
        """Reçoit un texte (et sa couleur, rouge par défaut) et l'affiche
        dans la zone des messages. Un texte vide efface la zone."""
        self._message.configure(text=texte, text_color=couleur)

    def _sur_onglet(self) -> None:
        """Appelée quand on change d'onglet : relit l'historique à son ouverture."""
        if self._onglets.get() == ONGLET_HISTORIQUE:
            self._onglet_historique.actualiser()

    def _construire_onglet_historique(self, onglet: ctk.CTkFrame) -> None:
        """Reçoit le cadre de l'onglet Historique et y place le tableau,
        avec une colonne par variable des métadonnées."""
        cible = self._modele.metadonnees["cible"]
        entetes = {COLONNE_DATE: "Date et heure"}
        colonnes_numeriques = [cible["nom"]]
        for variable in self._variables:
            entetes[variable.nom] = variable.libelle
            if isinstance(variable, VariableNumerique):
                colonnes_numeriques.append(variable.nom)
        entetes[cible["nom"]] = cible["libelle"] + " prédits"
        self._onglet_historique = OngletHistorique(
            onglet, self._historique, entetes, colonnes_numeriques)
        self._onglet_historique.pack(fill="both", expand=True)
