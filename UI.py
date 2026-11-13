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
from exceptions import DonneeInvalideError, HistoriqueInaccessibleError
from historique import Historique
from modele import Modele, arrondir_pv
from variables import (AUCUN_TYPE, Variable, VariableCategorielle,
                       VariableNumerique, creer_variable,
                       verifier_types_differents)

TITRE = "Prédicteur de PV — Pokémon"
ONGLET_PREDICTION = "Prédiction"
ONGLET_HISTORIQUE = "Historique"
MARGE = 20
TEXTE_PV_VIDE = "—"


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
        self.marquer_erreur(False)
        self._ecrire(str(self._variable.defaut))
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


class LigneResultat(ctk.CTkFrame):
    """La ligne PV : même gabarit qu'une statistique, mais en lecture seule."""

    def __init__(self, parent, libelle: str, maximum: float) -> None:
        """Reçoit le widget parent, le libellé (« PV ») et la plus grande
        valeur possible, qui correspond à une barre pleine."""
        super().__init__(parent, fg_color=apparence.COULEUR_FOND_ACCENT,
                         corner_radius=0)
        self._maximum = maximum
        self.grid_columnconfigure(2, weight=1)

        etiquette = ctk.CTkLabel(self, text=libelle, width=96, anchor="e",
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
        self._valeur.configure(text=str(pv))
        # La barre attend une proportion entre 0 (vide) et 1 (pleine).
        self._barre.set(min(1.0, pv / self._maximum))
        self._barre.configure(progress_color=apparence.couleur_pour_valeur(pv))

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
        # En dessous de cette taille, le bas de la carte de saisie serait coupé.
        self.minsize(1100, 860)
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

        cible = self._modele.metadonnees["cible"]
        self._ligne_pv = LigneResultat(zone_statistiques, cible["libelle"],
                                       cible["max"])
        self._ligne_pv.pack(fill="x")

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
        self._construire_actions(carte)

    def _construire_actions(self, carte: ctk.CTkFrame) -> None:
        """Reçoit la carte de gauche et y ajoute, sous la saisie : la zone
        des messages, les deux boutons et l'encadré du résultat."""
        self._message = ctk.CTkLabel(carte, text="", anchor="w", justify="left",
                                     text_color=apparence.COULEUR_ERREUR,
                                     font=ctk.CTkFont(size=14))
        self._message.pack(fill="x", padx=28, pady=(16, 8))

        zone_boutons = ctk.CTkFrame(carte, fg_color="transparent")
        zone_boutons.pack(fill="x", padx=28)
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
        self._phrase_erreur_moyenne.pack(fill="x", padx=20, pady=(0, 14))

    def _lire_saisies(self) -> dict:
        """Renvoie les saisies brutes, non validées : {nom de variable: saisie}."""
        saisies = {}
        for nom, ligne in self._lignes.items():
            saisies[nom] = ligne.lire()
        for nom, selecteur in self._selecteurs.items():
            saisies[nom] = selecteur.lire()
        saisies[self._variable_legendaire.nom] = self._interrupteur.get() == 1
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
            self._message.configure(text="\n".join(erreurs))
            return
        self._message.configure(text="")

        metadonnees = self._modele.metadonnees
        pv = arrondir_pv(self._modele.predire(valeurs),
                         metadonnees["cible"]["min"])
        self._afficher_resultat(pv)

        valeurs[metadonnees["cible"]["nom"]] = pv
        try:
            self._historique.ajouter(valeurs)
        except HistoriqueInaccessibleError as erreur:
            # La prédiction reste affichée ; on signale seulement le problème.
            self._message.configure(text=str(erreur))

    def _afficher_resultat(self, pv: int) -> None:
        """Reçoit les PV prédits ; met à jour la ligne PV et la phrase."""
        erreur_moyenne = round(self._modele.metadonnees["metrique"]["valeur"])
        self._ligne_pv.afficher(pv)
        self._phrase_resultat.configure(
            text=f"Ce Pokémon aurait environ {pv} PV.")
        self._phrase_erreur_moyenne.configure(
            text=f"Erreur moyenne du modèle : ± {erreur_moyenne} PV")
        self._encadre_resultat.pack(fill="x", padx=28, pady=(16, 0))

    def _reinitialiser(self) -> None:
        """Appelée au clic sur Réinitialiser : revient à l'état initial."""
        for ligne in self._lignes.values():
            ligne.reinitialiser()
        for selecteur in self._selecteurs.values():
            selecteur.reinitialiser()
        self._interrupteur.deselect()
        self._interrupteur.configure(text="Non")
        self._ligne_pv.vider()
        self._message.configure(text="")
        self._encadre_resultat.pack_forget()

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
