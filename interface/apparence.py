"""Couleurs et libellés de l'interface.

Tout ce qui concerne l'apparence est regroupé ici : l'interface n'a ainsi
aucun code hexadécimal écrit directement dans ses widgets, et les règles
de couleur peuvent être testées sans ouvrir de fenêtre.
"""

import os

# Dossier facultatif des images de type : assets/types/fire.png, etc.
# Le dossier « assets » est à la racine du dépôt, à côté de « interface/ ».
DOSSIER_IMAGES_TYPES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "types")

# --- Palette générale (codes repris de la maquette) ---
COULEUR_FOND = "#F3F4F7"
COULEUR_CARTE = "#FFFFFF"
COULEUR_TEXTE = "#1D2030"
COULEUR_TEXTE_SECONDAIRE = "#4A5060"
COULEUR_FOND_ONGLETS = "#E2E4EA"
COULEUR_BORDURE = "#C4C6CC"
COULEUR_SEPARATEUR = "#E6E8EE"
COULEUR_BOUTON_PRINCIPAL = "#1F6F8B"
COULEUR_ACCENT = "#14506A"
COULEUR_FOND_ACCENT = "#F0F8FB"
COULEUR_MENU_TYPE = "#3A3D56"
COULEUR_RADAR = "#2E9DB8"
COULEUR_HISTOGRAMME = "#9CC9D8"
COULEUR_PREDICTION = "#D9480F"
COULEUR_ERREUR = "#B3261E"
COULEUR_INTERRUPTEUR_ACTIF = "#23CD5E"
COULEUR_TEXTE_CLAIR = "#FFFFFF"

# --- Couleur d'une barre de statistique selon sa valeur ---
# Chaque couple donne la valeur à partir de laquelle la couleur s'applique.
# Les seuils sont rangés du plus grand au plus petit.
SEUILS_COULEURS = [
    (150, "#00C2B8"),  # turquoise
    (120, "#23CD5E"),  # vert
    (90, "#A0E515"),   # vert clair
    (60, "#FFDD57"),   # jaune
    (30, "#FF7F0F"),   # orange
]
COULEUR_VALEUR_BASSE = "#F34444"  # rouge : en dessous de 30

# --- Types de Pokémon : nom français et couleur ---
# Les clés sont les noms anglais du CSV : ce sont eux qu'on envoie au modèle.
NOMS_TYPES_FR = {
    "Bug": "Insecte",
    "Dark": "Ténèbres",
    "Dragon": "Dragon",
    "Electric": "Électrik",
    "Fairy": "Fée",
    "Fighting": "Combat",
    "Fire": "Feu",
    "Flying": "Vol",
    "Ghost": "Spectre",
    "Grass": "Plante",
    "Ground": "Sol",
    "Ice": "Glace",
    "Normal": "Normal",
    "Poison": "Poison",
    "Psychic": "Psy",
    "Rock": "Roche",
    "Steel": "Acier",
    "Water": "Eau",
}

COULEURS_TYPES = {
    "Bug": "#91A119",
    "Dark": "#624D4E",
    "Dragon": "#5060E1",
    "Electric": "#FAC000",
    "Fairy": "#EF70EF",
    "Fighting": "#FF8000",
    "Fire": "#E62829",
    "Flying": "#81B9EF",
    "Ghost": "#704170",
    "Grass": "#3FA129",
    "Ground": "#915121",
    "Ice": "#3DCEF3",
    "Normal": "#9FA19F",
    "Poison": "#9141CB",
    "Psychic": "#EF4179",
    "Rock": "#AFA981",
    "Steel": "#60A1B8",
    "Water": "#2980EF",
}


def couleur_pour_valeur(valeur: float) -> str:
    """Reçoit la valeur d'une statistique et renvoie la couleur de sa barre
    (code hexadécimal). N'échoue pas : toute valeur sous 30 donne du rouge."""
    for seuil, couleur in SEUILS_COULEURS:
        if valeur >= seuil:
            return couleur
    return COULEUR_VALEUR_BASSE


def nom_type_fr(type_anglais: str) -> str:
    """Reçoit un type en anglais, en minuscules ou non (ex. « fire »), et
    renvoie son nom français (« Feu »). N'échoue pas : un type inconnu
    (ou « Aucun ») est renvoyé tel quel."""
    # capitalize() met la première lettre en majuscule : « fire » → « Fire ».
    return NOMS_TYPES_FR.get(type_anglais.capitalize(), type_anglais)


def couleur_type(type_anglais: str) -> str:
    """Reçoit un type en anglais, en minuscules ou non, et renvoie la couleur
    de sa pastille. N'échoue pas : un type inconnu (ou « Aucun ») donne la
    couleur neutre du menu."""
    return COULEURS_TYPES.get(type_anglais.capitalize(), COULEUR_MENU_TYPE)


def chemin_image_type(type_anglais: str,
                      dossier: str = DOSSIER_IMAGES_TYPES) -> str | None:
    """Reçoit un type en anglais et renvoie le chemin de son image
    (ex. assets/types/fire.png) si le fichier existe, sinon None.
    N'échoue pas : l'image est facultative."""
    chemin = os.path.join(dossier, type_anglais.lower() + ".png")
    if os.path.exists(chemin):
        return chemin
    return None


def formater_cellule(texte: str) -> str:
    """Reçoit le texte d'une case de l'historique (tel qu'écrit dans le CSV)
    et renvoie le texte à afficher : « True » devient « Oui », « Fire »
    devient « Feu », « 50.0 » devient « 50 ». N'échoue pas : un texte
    non reconnu est renvoyé tel quel."""
    if texte == "True":
        return "Oui"
    if texte == "False":
        return "Non"
    if texte.capitalize() in NOMS_TYPES_FR:
        return NOMS_TYPES_FR[texte.capitalize()]
    try:
        nombre = float(texte)
    except ValueError:
        return texte
    if nombre.is_integer():
        return str(int(nombre))
    return texte


def formater_r2(r2: float) -> str:
    """Reçoit le score R² du modèle et renvoie le texte à afficher, avec
    deux décimales et une virgule à la française (0.4573 → « 0,46 »).
    N'échoue pas."""
    return f"{r2:.2f}".replace(".", ",")
