import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression

csv_path = Path(__file__).with_name('Pokemon.csv')
data = pd.read_csv(csv_path)

X = data[["Attack", "Speed", "Defense","Sp. Atk","Sp. Def", "Legendary" ,"Type 1", "Type 2"]]
y = data["HP"]

types = list(set(X["Type 1"].unique()).union(set(X["Type 2"].unique())))
types.remove(np.nan)
print(types)
for t in types:
    X[t] = X["Type 1"].eq(t).astype(int) + X["Type 2"].eq(t).astype(int)

X = X.drop(columns=["Type 1", "Type 2"])
X["Legendary"] = X["Legendary"].astype(int)
print(X.head())

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=123)

model = LinearRegression()

r2_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
mae_scores = -cross_val_score(model, X, y, cv=5, scoring="neg_mean_absolute_error")

print("R² par pli :", r2_scores)
print("R² moyen :", r2_scores.mean(), "+/-", r2_scores.std())
print("Erreur moyenne (MAE) :", mae_scores.mean(), "+/-", mae_scores.std())

model.fit(X, y)

# nouveau_pokemon = pd.DataFrame({
#     "Attack": [49],
#     "Speed": [45],
#     "Defense": [49]
#     ""
# })

# prediction = model.predict(nouveau_pokemon)
# print("HP prévus :", prediction[0])