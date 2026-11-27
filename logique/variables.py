"""Variables d'entrée du modèle et validation des saisies.

Chaque variable (Attack, Type 1, Rarity...) sait valider ce que
l'utilisateur a saisi. L'interface ne valide rien elle-même : elle appelle
variable.valider(saisie) et affiche le message si une DonneeInvalideError
est levée.
"""

from abc import ABC, abstractmethod

from logique.exceptions import DonneeInvalideError

# Valeur du Type 2 quand le Pokémon n'a pas de second type.
AUCUN_TYPE = "None"


class Variable(ABC):
    """Classe abstraite : ce que toutes les variables ont en commun.

    On ne peut pas créer directement une Variable : il faut passer par une
    classe enfant qui définit la méthode valider().
    """

    def __init__(self, nom: str, libelle: str) -> None:
        """Reçoit le nom de la colonne du CSV (ex. « sp_attack ») et le libellé
        affiché à l'écran (ex. « Sp. Atk »). Ne renvoie rien, n'échoue pas."""
        self._nom = nom
        self._libelle = libelle

    @property
    def nom(self) -> str:
        """Renvoie le nom de la colonne dans le CSV (lecture seule)."""
        return self._nom

    @property
    def libelle(self) -> str:
        """Renvoie le libellé affiché à l'écran (lecture seule)."""
        return self._libelle

    @abstractmethod
    def valider(self, saisie: str | bool) -> float | str | bool:
        """Reçoit la saisie brute, renvoie la valeur propre à donner au modèle.

        Échoue avec DonneeInvalideError si la saisie n'est pas acceptable.
        Chaque classe enfant écrit sa propre version (polymorphisme).
        """

    def __str__(self) -> str:
        """Renvoie le libellé : c'est ce que print(variable) affiche."""
        return self._libelle


class VariableNumerique(Variable):
    """Variable dont la valeur est un nombre compris entre deux bornes."""

    def __init__(self, nom: str, libelle: str, minimum: float, maximum: float,
                 defaut: float, pas: float = 1,
                 statistique: bool = True) -> None:
        """Reçoit le nom, le libellé, les deux bornes (incluses), la valeur
        par défaut, le pas du curseur (1 ou 0.1) et si c'est une statistique
        de combat. Ne renvoie rien, n'échoue pas."""
        super().__init__(nom, libelle)
        self._minimum = minimum
        self._maximum = maximum
        self._defaut = defaut
        self._pas = pas
        self._statistique = statistique

    @property
    def minimum(self) -> float:
        """Renvoie la plus petite valeur acceptée."""
        return self._minimum

    @property
    def maximum(self) -> float:
        """Renvoie la plus grande valeur acceptée."""
        return self._maximum

    @property
    def defaut(self) -> float:
        """Renvoie la valeur affichée au lancement et après Réinitialiser."""
        return self._defaut

    @property
    def pas(self) -> float:
        """Renvoie le pas du curseur : 1 pour un entier, 0.1 pour un décimal."""
        return self._pas

    @property
    def statistique(self) -> bool:
        """Renvoie True pour une statistique de combat (Attack, Speed...)."""
        return self._statistique

    def formater(self, valeur: float) -> str:
        """Reçoit une valeur et renvoie le texte à afficher dans le champ :
        sans décimale pour un pas de 1 (« 50 »), une décimale sinon (« 1.5 »)."""
        if self._pas >= 1:
            return str(round(valeur))
        return f"{valeur:.1f}"

    def valider(self, saisie: str | bool) -> float:
        """Reçoit le texte du champ de saisie, renvoie le nombre correspondant.

        Échoue avec DonneeInvalideError si le texte est vide, n'est pas un
        nombre, ou si le nombre est en dehors des bornes.
        """
        texte = str(saisie).strip()
        if texte == "":
            raise DonneeInvalideError(f"{self._libelle}: enter a value.")
        try:
            valeur = float(texte)
        except ValueError:
            raise DonneeInvalideError(
                f'{self._libelle}: "{texte}" is not a number.') from None
        # Cette comparaison rejette aussi « nan » et « inf », que float() accepte.
        if not (self._minimum <= valeur <= self._maximum):
            raise DonneeInvalideError(
                f"{self._libelle}: the value must be between "
                f"{self._minimum} and {self._maximum}.")
        return valeur

    def __str__(self) -> str:
        """Renvoie le libellé suivi des bornes, ex. « Attack (5 to 190) »."""
        return f"{self._libelle} ({self._minimum} to {self._maximum})"


class VariableCategorielle(Variable):
    """Variable dont la valeur est choisie dans une liste (type, légendaire)."""

    def __init__(self, nom: str, libelle: str, valeurs: list) -> None:
        """Reçoit le nom, le libellé et la liste des valeurs permises.
        Ne renvoie rien, n'échoue pas."""
        super().__init__(nom, libelle)
        self._valeurs = list(valeurs)

    @property
    def valeurs(self) -> list:
        """Renvoie une copie de la liste des valeurs permises."""
        return list(self._valeurs)

    @property
    def defaut(self) -> str | bool:
        """Renvoie la valeur par défaut : la première de la liste."""
        return self._valeurs[0]

    def valider(self, saisie: str | bool) -> str | bool:
        """Reçoit la valeur choisie et la renvoie telle quelle si elle est permise.

        Échoue avec DonneeInvalideError si elle n'est pas dans la liste.
        """
        if saisie not in self._valeurs:
            raise DonneeInvalideError(
                f'{self._libelle}: "{saisie}" is not a valid choice.')
        return saisie

    def __str__(self) -> str:
        """Renvoie le libellé et le nombre de choix, ex. « Type 1 (18 choices) »."""
        return f"{self._libelle} ({len(self._valeurs)} choices)"


def verifier_types_differents(type_1: str, type_2: str) -> None:
    """Reçoit les deux types choisis et vérifie qu'ils sont différents.

    Ne renvoie rien. Échoue avec DonneeInvalideError si le type 2 est égal
    au type 1 (« None » est toujours accepté comme type 2).
    """
    if type_2 != AUCUN_TYPE and type_2 == type_1:
        raise DonneeInvalideError(
            f'Type 2 must be different from Type 1 (or "{AUCUN_TYPE}").')


def creer_variable(description: dict) -> Variable:
    """Reçoit la description d'une variable lue dans le JSON de métadonnées
    et renvoie l'objet VariableNumerique ou VariableCategorielle correspondant.

    Échoue avec ValueError si le champ « type » n'est ni « numerique » ni
    « categorielle », et avec KeyError s'il manque un champ obligatoire.
    """
    nom = description["nom"]
    libelle = description["libelle"]
    if description["type"] == "numerique":
        return VariableNumerique(nom, libelle, description["min"],
                                 description["max"], description["defaut"],
                                 description.get("pas", 1),
                                 description.get("statistique", True))
    if description["type"] == "categorielle":
        return VariableCategorielle(nom, libelle, description["valeurs"])
    raise ValueError(f'Type de variable inconnu : "{description["type"]}".')
