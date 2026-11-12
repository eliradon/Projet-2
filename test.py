import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression

csv_path = Path(__file__).with_name('Pokemon.csv')
data = pd.read_csv(csv_path)

X = data[["Attack", "Speed", "Defense", "Type 1", "Type 2"]]
y = data["HP"]

types = list(set(X["Type 1"].unique()).union(set(X["Type 2"].unique())))
types.remove(np.nan)
print(types)
for t in types:
    X[t] = X["Type 1"].eq(t).astype(int) + X["Type 2"].eq(t).astype(int)

X = X.drop(columns=["Type 1", "Type 2"])
print(X.head())
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("Erreur moyenne :", mean_absolute_error(y_test, y_pred))
print("Score R² :", r2_score(y_test, y_pred))

# nouveau_pokemon = pd.DataFrame({
#     "Attack": [49],
#     "Speed": [45],
#     "Defense": [49]
#     ""
# })

# prediction = model.predict(nouveau_pokemon)
# print("HP prévus :", prediction[0])