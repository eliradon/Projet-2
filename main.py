"""Point d'entrée de l'application : python main.py"""

import customtkinter as ctk

from interface.UI import Application, afficher_erreur_fatale
from logique.exceptions import ModeleIntrouvableError
from logique.modele import Modele


def main() -> None:
    """Charge le modèle, puis ouvre la fenêtre. Ne reçoit et ne renvoie rien.
    N'échoue pas : si le modèle est introuvable, une fenêtre d'erreur
    s'affiche et le programme se termine proprement."""
    ctk.set_appearance_mode("light")  # la maquette est en thème clair
    modele = Modele()
    try:
        # Premier lancement : entraîne et enregistre le modèle (quelques
        # secondes). Lancements suivants : relit simplement les fichiers.
        modele.charger()
    except ModeleIntrouvableError as erreur:
        afficher_erreur_fatale(str(erreur))
        return
    application = Application(modele)
    application.mainloop()


if __name__ == "__main__":
    main()
