"""Exceptions personnalisées de l'application.

Avoir nos propres exceptions permet à l'interface d'attraper précisément
les erreurs prévues (saisie invalide, modèle introuvable) et d'afficher un
message clair, sans jamais utiliser un « except » nu.
"""


class DonneeInvalideError(ValueError):
    """Erreur levée quand une saisie de l'utilisateur n'est pas valide.

    Le message de l'exception est déjà une phrase en français, prête à être
    affichée dans la fenêtre (ex. : « Attaque : entrez une valeur. »).
    Elle hérite de ValueError, car une saisie invalide est une « mauvaise valeur ».
    """


class ModeleIntrouvableError(Exception):
    """Erreur levée quand le modèle ne peut être ni chargé ni recréé.

    Exemple : « Pokemon.csv » ou « predicteur.py » est introuvable au moment
    de la première sauvegarde du modèle.
    """
