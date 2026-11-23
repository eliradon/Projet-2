# Diagramme de classes

GitHub affiche ce diagramme directement (format Mermaid).

Notation : `+` public, `#` protégé (nom qui commence par `_` en Python),
`<<abstract>>` classe abstraite, méthode en *italique* = abstraite.

Liens :

- flèche à triangle vide : **héritage** (« est un ») ;
- losange plein : **composition** (« contient et crée ») ;
- losange vide : **agrégation** (« contient, mais reçu de l'extérieur ») ;
- flèche simple : **association** (« utilise ») ;
- flèche pointillée : **dépendance** (« lève » une exception).

```mermaid
classDiagram
    direction TB

    %% ---------- logique/exceptions.py ----------
    class ValueError
    class Exception
    class DonneeInvalideError
    class ModeleIntrouvableError
    class HistoriqueInaccessibleError
    ValueError <|-- DonneeInvalideError
    Exception <|-- ModeleIntrouvableError
    Exception <|-- HistoriqueInaccessibleError

    %% ---------- logique/variables.py ----------
    class Variable {
        <<abstract>>
        #str _nom
        #str _libelle
        +nom() str
        +libelle() str
        +valider(saisie)*
        +__str__() str
    }
    class VariableNumerique {
        #float _minimum
        #float _maximum
        #float _defaut
        #float _pas
        #bool _statistique
        +minimum() float
        +maximum() float
        +defaut() float
        +pas() float
        +statistique() bool
        +formater(valeur) str
        +valider(saisie) float
        +__str__() str
    }
    class VariableCategorielle {
        #list _valeurs
        +valeurs() list
        +defaut()
        +valider(saisie)
        +__str__() str
    }
    Variable <|-- VariableNumerique
    Variable <|-- VariableCategorielle
    Variable ..> DonneeInvalideError : lève

    %% ---------- logique/modele.py ----------
    class Modele {
        #str _dossier
        #LinearRegression _modele
        #dict _metadonnees
        +metadonnees() dict
        +charger()
        +predire(valeurs) float
        #_types_connus() list
        #_stade_maximum() float
    }
    Modele ..> ModeleIntrouvableError : lève

    %% ---------- logique/historique.py ----------
    class Historique {
        #list _colonnes
        #str _chemin
        +chemin() str
        +ajouter(valeurs, moment)
        +lire() list
        #_fichier_absent_ou_vide() bool
    }
    Historique ..> HistoriqueInaccessibleError : lève

    %% ---------- interface/UI.py ----------
    class CTk
    class CTkFrame

    class Application {
        #Modele _modele
        #list _variables
        #Historique _historique
        #dict _lignes
        #dict _selecteurs
        #bool _prediction_affichee
        #_construire()
        #_construire_saisie(carte)
        #_lire_saisies() dict
        #_valider_saisies(saisies) tuple
        #_sur_predire()
        #_afficher_resultat(pv)
        #_reinitialiser()
        #_imposer_forme_finale()
        #_sur_changement()
    }
    class LigneStatistique {
        #VariableNumerique _variable
        +lire() str
        +reinitialiser()
        +marquer_erreur(en_erreur)
        #_sur_curseur(valeur)
        #_sur_saisie(evenement)
    }
    class ChampSimple {
        #VariableNumerique _variable
        +lire() str
        +reinitialiser()
        +marquer_erreur(en_erreur)
    }
    class LigneResultat {
        #float _maximum
        +afficher(pv)
        +griser()
        +vider()
    }
    class SelecteurType {
        #VariableCategorielle _variable
        #dict _types_par_libelle
        +lire() str
        +reinitialiser()
        #_afficher_pastille()
    }
    class PanneauRadar {
        #list _libelles
        #float _maximum
        +tracer(statistiques, pv)
    }
    class PanneauDistribution {
        #list _bornes
        #list _effectifs
        #float _erreur_moyenne
        +tracer(pv)
    }
    class OngletHistorique {
        #Historique _historique
        #list _colonnes
        +actualiser()
        #_afficher_message(texte)
    }

    CTk <|-- Application
    CTkFrame <|-- LigneStatistique
    CTkFrame <|-- ChampSimple
    CTkFrame <|-- LigneResultat
    CTkFrame <|-- SelecteurType
    CTkFrame <|-- OngletHistorique

    Application o-- "1" Modele : reçu de main.py
    Application *-- "8..*" Variable
    Application *-- "1" Historique
    Application *-- "5" LigneStatistique
    Application *-- "3" ChampSimple
    Application *-- "1" LigneResultat
    Application *-- "2" SelecteurType
    Application *-- "1" PanneauRadar
    Application *-- "1" PanneauDistribution
    Application *-- "1" OngletHistorique

    LigneStatistique --> VariableNumerique : valide avec
    ChampSimple --> VariableNumerique
    SelecteurType --> VariableCategorielle
    OngletHistorique --> Historique : relit
```

## À retenir pour l'oral

- **Héritage** : `VariableNumerique` et `VariableCategorielle` héritent de la
  classe abstraite `Variable` et redéfinissent chacune `valider()` et
  `__str__()` (polymorphisme). Les widgets héritent de CustomTkinter
  (`CTk` pour la fenêtre, `CTkFrame` pour les blocs).
- **Composition** : `Application` crée et contient ses variables, son
  historique et tous ses widgets. Le `Modele` est une **agrégation** : il est
  chargé dans `main.py` puis donné à `Application`.
- **Exceptions** : chaque classe de la logique lève sa propre exception ;
  l'interface les attrape pour afficher un message au lieu de planter.
- **Hors diagramme** : `main.py`, `predicteur.py` et les fonctions
  (`creer_variable()`, `sauvegarder_modele()`, `chronometre`…) ne sont pas
  des classes.
