import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression

csv_path = Path(__file__).with_name('pokemon_utf8.csv')
data = pd.read_csv(csv_path)
data = data.dropna(how="all")
X = data[["attack", "speed", "defense","sp_attack","sp_defense", "weight_kg", "height_m", "is_sublegendary", "is_legendary", "is_mythical"]].copy()
y = data["hp"]

types = list(set(data["primary_type"].dropna().unique()).union(set(data["secondary_type"].dropna().unique())))

print(types)
for t in types:
    X[t] = data["primary_type"].eq(t).astype(int) + data["secondary_type"].eq(t).astype(int)



cols = ["evochain_0", "evochain_2", "evochain_4", "evochain_6"]


def nettoyer_texte(valeur):
    if pd.isna(valeur):
        return ""
    return str(valeur).strip().lower()



def trouver_stade(ligne):
    nom = nettoyer_texte(ligne["english_name"])
    if nettoyer_texte(ligne["evochain_0"]) == "eevee" and nom != "eevee":
        return 2

    for i, col in enumerate(cols, start=1):
        if nettoyer_texte(ligne[col]) == nom:
            return i

    return 1

X["evostage"] = data.apply(trouver_stade, axis=1)

def is_final_stage(ligne: pd.Series) -> bool:
    """True si le Pokémon est la dernière forme de sa lignée, False sinon.

    Les évolutions d'Évoli (chaîne de base 'eevee') sont considérées finales.
    Les cas introuvables (anomalies) renvoient False.
    """
    nom = nettoyer_texte(ligne["english_name"])

    if nettoyer_texte(ligne["evochain_0"]) == "eevee":
        return nom != "eevee"   # Évoli lui-même n'est pas final

    for i, col in enumerate(cols):
        if nettoyer_texte(ligne[col]) == nom:
            if i + 1 == len(cols):          # dernière colonne : rien après
                return True
            return nettoyer_texte(ligne[cols[i + 1]]) == ""

    return False

X["is_final_stage"] = data.apply(is_final_stage, axis=1).astype(int)

print(X.head())
sortie = Path(__file__).with_name("pokemon_propre.csv")
X.to_csv(sortie, index=False, encoding="utf-8")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=2)

model = LinearRegression()

# Validation croisée sur l'ensemble d'entraînement seulement
r2_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
mae_scores = -cross_val_score(model, X_train, y_train, cv=5, scoring="neg_mean_absolute_error")

print("R² moyen :", r2_scores.mean(), "+/-", r2_scores.std())
print("Erreur moyenne (MAE) :", mae_scores.mean(), "+/-", mae_scores.std())

# Score officiel : entraînement sur le train, évaluation une seule fois sur le test
model.fit(X_train, y_train)
y_pred_test = model.predict(X_test)
print("R² (test) :", r2_score(y_test, y_pred_test))
print("MAE (test) :", mean_absolute_error(y_test, y_pred_test))

# Modèle final pour l'application : entraîné sur toutes les données
model.fit(X, y)

#Dummy Regressor
from sklearn.dummy import DummyRegressor

baseline = DummyRegressor(strategy="mean")
baseline.fit(X_train, y_train)
y_pred_base = baseline.predict(X_test)

print("R² baseline :", r2_score(y_test, y_pred_base))
print("MAE baseline :", mean_absolute_error(y_test, y_pred_base))

print("le modèle réduit l'erreur d'un pourcentage de :", (mean_absolute_error(y_test, y_pred_base) - mean_absolute_error(y_test, y_pred_test)) / mean_absolute_error(y_test, y_pred_base) * 100)



# Parti Entierement generee par Claude

from sklearn.tree import DecisionTreeRegressor

# Choix de la profondeur par validation croisée, sur le train seulement
meilleure_profondeur, meilleur_r2 = None, -np.inf
for profondeur in range(2, 11):
    arbre = DecisionTreeRegressor(max_depth=profondeur, random_state=2)
    r2 = cross_val_score(arbre, X_train, y_train, cv=5, scoring="r2").mean()
    print(f"profondeur {profondeur} : R² CV = {r2:.3f}")
    if r2 > meilleur_r2:
        meilleure_profondeur, meilleur_r2 = profondeur, r2

# Score officiel de l'arbre : une seule évaluation sur le test
arbre = DecisionTreeRegressor(max_depth=meilleure_profondeur, random_state=2)
arbre.fit(X_train, y_train)
y_pred_arbre = arbre.predict(X_test)

print("Arbre, profondeur retenue :", meilleure_profondeur)
print("R² arbre (test) :", r2_score(y_test, y_pred_arbre))
print("MAE arbre (test) :", mean_absolute_error(y_test, y_pred_arbre))