"""
Spatial Binary Classification + Kriging with Mean Variogram (by year)
--------------------------------------------------------------------

Pipeline:
- train ML model (RF, XGBoost, Logistic, SVM)
- compute raw probabilities
- compute variogram per training year
- average variogram parameters (range, sill, nugget)
- fit per-year Kriging models using the mean variogram
- apply spatial correction on TEST (year by year)
"""

import numpy as np
import pandas as pd

# --------- Machine Learning -----------
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    confusion_matrix,
    classification_report,
    RocCurveDisplay
)

# --------- Optional: XGBoost -----------
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except:
    XGB_AVAILABLE = False

# --------- Spatial Kriging ------------
from pykrige.ok import OrdinaryKriging
import matplotlib.pyplot as plt
from pykrige import variogram_models
from scipy.spatial.distance import pdist
from scipy.optimize import minimize

# =======================================================================
# 1. MODEL SELECTION
# =======================================================================

def get_model(model_name):
    if model_name == "RandomForest":
        return RandomForestClassifier(
            n_estimators=3000,
            max_depth=None,
            min_samples_leaf=10,
            n_jobs=-1,
            random_state=42
        )

    elif model_name == "Logistic":
        return LogisticRegression(max_iter=5000, solver="lbfgs")

    elif model_name == "SVM":
        return SVC(C=1.0, gamma="scale", probability=True)

    elif model_name == "XGBoost":
        if not XGB_AVAILABLE:
            raise ValueError("XGBoost not installed")
        return XGBClassifier(
            n_estimators=3000,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss"
        )

    else:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose among: "
            "['RandomForest','Logistic','SVM','XGBoost']"
        )


# =======================================================================
# 2. VARIOGRAM AVERAGING
# =======================================================================

def compute_mean_variogram(df_train, prob_col, year_col="ANNEE",variogram_model="gaussian"):
    """
    Pour chaque année du TRAIN :
    - ajuste un variogramme gaussien via OrdinaryKriging
    - extrait (sill, range, nugget)

    Retourne la moyenne de ces paramètres.
    """

    ranges = []
    sills = []
    nuggets = []

    for year, df_y in df_train.groupby(year_col):
        df_y = df_y.dropna(subset=[prob_col, "x", "y"])

        if len(df_y) < 15:
            print(f"[Variogram] Year {year}: skipped (too few points).")
            continue

        print(f"[Variogram] Fitting variogram for year {year}...")

        ok = OrdinaryKriging(
            df_y["x"].values,
            df_y["y"].values,
            df_y[prob_col].values,
            variogram_model=variogram_model,
            verbose=False,
            enable_plotting=False
        )

        params = ok.variogram_model_parameters  # [sill, range, nugget]
        sill, var_range, nugget = params

        ranges.append(var_range)
        sills.append(sill)
        nuggets.append(nugget)

    mean_range = np.mean(ranges)
    mean_sill = np.mean(sills)
    mean_nugget = np.mean(nuggets)

    print("\n=== MEAN VARIOGRAM PARAMETERS ===")
    print(f"Mean range  = {mean_range:.4f}")
    print(f"Mean sill   = {mean_sill:.4f}")
    print(f"Mean nugget = {mean_nugget:.4f}")

    return mean_sill, mean_range, mean_nugget


# =======================================================================
# 3. KRIGING PAR ANNÉE AVEC VARIOGRAMME MOYEN
# =======================================================================

def fit_kriging_with_mean_variogram(df_train, prob_col, mean_params, year_col="ANNEE",variogram_model="gaussian"):
    """
    Ajuste un modèle de Kriging PAR ANNÉE,
    mais en imposant le même variogramme (paramètres moyens).

    Retourne un dict: {année: modèle OrdinaryKriging}
    """
    sill, var_range, nugget = mean_params
    kriging_models = {}

    for year, df_y in df_train.groupby(year_col):
        df_y = df_y.dropna(subset=[prob_col, "x", "y"])
        if len(df_y) < 10:
            print(f"[Kriging] Year {year}: not enough points. Skipped.")
            continue

        print(f"[Kriging] Fitting Kriging for year {year} with mean variogram.")

        ok = OrdinaryKriging(
            df_y["x"].values,
            df_y["y"].values,
            df_y[prob_col].values,
            variogram_model=variogram_model,
            variogram_parameters=[sill, var_range, nugget],
            verbose=False,
            enable_plotting=False
        )

        kriging_models[year] = ok

    return kriging_models


def apply_kriging_by_year(df, base_prob_col, kriging_models, year_col="ANNEE"):
    """
    Applique la correction spatiale année par année :

    - si un modèle existe pour l'année -> utilise le Kriging
    - sinon -> garde la probabilité brute (p_raw)
    """
    df = df.copy()
    corrected = np.zeros(len(df))

    for year, df_y in df.groupby(year_col):
        idx = df_y.index
        base = df_y[base_prob_col].values

        if year not in kriging_models:
            # Pas de modèle pour cette année -> pas de correction
            corrected[df.index.get_indexer(idx)] = base
            continue

        ok = kriging_models[year]

        z, _ = ok.execute("points", df_y["x"].values, df_y["y"].values)
        z = np.clip(np.array(z), 1e-6, 1 - 1e-6)

        corrected[df.index.get_indexer(idx)] = z

    df["p_corr"] = corrected
    return df


# =======================================================================
# 4. DIAGNOSTIC DES VARIOGRAMMES : UN SOUS-GRAPHE PAR ANNÉE
# =======================================================================

def plot_variograms_grid(df_train, prob_col="p_raw", year_col="ANNEE",
                         n_bins=40, variogram_model="gaussian", max_points=3000):
    """
    Variogrammes annuels en grille + WLS metric (Cressie, 1985)
    - barres verticales : nombre de paires
    - points bleus     : variogramme empirique binned
    - courbe verte     : variogramme ajusté
    - WLS              : critère de qualité d'ajustement
    """

    years = sorted(df_train[year_col].unique())
    n_years = len(years)

    n_cols = int(np.ceil(np.sqrt(n_years)))
    n_rows = int(np.ceil(n_years / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(5 * n_cols, 4 * n_rows),
                             squeeze=False)

    # mapping PyKrige
    variogram_functions = {
        "gaussian": variogram_models.gaussian_variogram_model,
        "spherical": variogram_models.spherical_variogram_model,
        "exponential": variogram_models.exponential_variogram_model,
        "power": variogram_models.power_variogram_model,
        "hole-effect": variogram_models.hole_effect_variogram_model
    }

    if variogram_model not in variogram_functions:
        raise ValueError(f"Unsupported variogram model '{variogram_model}'. "
                         f"Choose among: {list(variogram_functions.keys())}")

    # 👉 dictionnaire pour stocker les WLS
    wls_scores = {}

    for i, year in enumerate(years):
        ax = axes[i // n_cols, i % n_cols]

        df_y = df_train[df_train[year_col] == year].dropna(subset=["x", "y", prob_col])
        if len(df_y) < 50:
            ax.text(0.5, 0.5, f"Year {year}\nNot enough data",
                    ha="center", va="center")
            ax.set_axis_off()
            continue

        # Sous-échantillonnage
        df_sample = df_y.sample(min(max_points, len(df_y)), random_state=42)
        coords = df_sample[["x", "y"]].values
        values = df_sample[prob_col].values

        # Variogramme empirique
        dists = pdist(coords)
        diffs = pdist(values.reshape(-1, 1))
        gamma = 0.5 * diffs**2

        # Bins
        bins = np.linspace(0, np.max(dists), n_bins + 1)
        bin_centers = 0.5 * (bins[1:] + bins[:-1])

        gamma_binned = []
        counts = []

        for j in range(n_bins):
            mask = (dists >= bins[j]) & (dists < bins[j + 1])
            counts.append(mask.sum())
            gamma_binned.append(np.mean(gamma[mask]) if mask.sum() > 0 else np.nan)

        gamma_binned = np.array(gamma_binned)
        counts = np.array(counts)

        # Ajustement variogramme
        ok = OrdinaryKriging(
            df_sample["x"].values,
            df_sample["y"].values,
            df_sample[prob_col].values,
            variogram_model=variogram_model,
            verbose=False,
            enable_plotting=False
        )

        sill, var_range, nugget = ok.variogram_model_parameters

        # Forme théorique
        h = np.linspace(0, np.max(dists), 300)
        gamma_fit = variogram_functions[variogram_model](
            [sill, var_range, nugget], h
        )

        # WLS metric (Cressie)
        gamma_model_bins = variogram_functions[variogram_model](
            [sill, var_range, nugget], bin_centers
        )

        mask_valid = ~np.isnan(gamma_binned) & (counts > 0)
        w = counts[mask_valid]  # poids
        residuals = gamma_binned[mask_valid] - gamma_model_bins[mask_valid]

        WLS = np.sum(w * (residuals ** 2))
        wls_scores[year] = WLS  # save score

        # Barres verticales
        bar_max = np.nanmax(gamma_binned)
        if bar_max == 0 or np.isnan(bar_max):
            bar_max = 1e-6

        bar_heights = (counts / counts.max()) * (bar_max * 0.9)
        ax.vlines(bin_centers, 0, bar_heights, color="red", linewidth=2, alpha=0.5)

        # Points + courbe
        ax.plot(bin_centers, gamma_binned, "o", color="blue", markersize=5)
        ax.plot(h, gamma_fit, color="green", linewidth=2)

        ax.set_title(f"Year {year} — model: {variogram_model}\nWLS = {WLS:.4f}",
                     fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_ylabel("γ(h)")
        if i // n_cols == n_rows - 1:
            ax.set_xlabel("Lag distance h")

    # Cases vides
    for k in range(i + 1, n_rows * n_cols):
        axes[k // n_cols, k % n_cols].set_axis_off()

    plt.tight_layout()
    plt.show()

    return wls_scores



def compare_variogram_models_with_mean(
    df_train,
    prob_col="p_raw",
    year_col="ANNEE",
    n_bins=40,
    max_points=3000,
    models=("gaussian", "spherical", "exponential", "hole-effect", "power")
):
    """
    1. Compute variograms for each year
    2. Compute mean empirical variogram
    3. Fit models (Gaussian, Spherical, Exponential, Hole-effect, Power)
       using appropriate parameterization for each
    4. Compare models via WLS
    5. Plot and return comparison table
    """

    # Mapping vers les fonctions PyKrige
    vfunc = {
        "gaussian": variogram_models.gaussian_variogram_model,
        "spherical": variogram_models.spherical_variogram_model,
        "exponential": variogram_models.exponential_variogram_model,
        "hole-effect": variogram_models.hole_effect_variogram_model,
        "power": variogram_models.power_variogram_model,
    }

    years = sorted(df_train[year_col].unique())
    print(f"\nDetected years: {years}")

    # ------------------------------------------
    # ÉTAPE 1 — Variogrammes annuels
    # ------------------------------------------
    annual_binned = []
    bin_centers = None

    print("\n=== STEP 1: Annual variograms ===\n")

    for year in years:
        df_y = df_train[df_train[year_col] == year].dropna(subset=["x", "y", prob_col])
        if len(df_y) < 50:
            print(f"[Year {year}] Not enough points, skipped.")
            continue

        df_sample = df_y.sample(min(max_points, len(df_y)), random_state=42)
        coords = df_sample[["x", "y"]].values
        values = df_sample[prob_col].values

        # Empirical variogram
        dists = pdist(coords)
        diffs = pdist(values.reshape(-1, 1))
        gamma = 0.5 * (diffs ** 2)

        # Binning
        bins = np.linspace(0, np.max(dists), n_bins + 1)
        centers = 0.5 * (bins[1:] + bins[:-1])
        if bin_centers is None:
            bin_centers = centers

        g_binned = []
        for j in range(n_bins):
            mask = (dists >= bins[j]) & (dists < bins[j + 1])
            g_binned.append(np.mean(gamma[mask]) if mask.sum() > 0 else np.nan)

        annual_binned.append(np.array(g_binned))

    annual_binned = np.array(annual_binned)
    gamma_mean = np.nanmean(annual_binned, axis=0)

    print("\n=== Mean variogram computed ===\n")

    # ------------------------------------------
    # ÉTAPE 2 — Ajustement des modèles
    # ------------------------------------------
    model_curves = {}
    wls_scores = {}

    print("\n=== STEP 2: Fitting models to mean variogram ===\n")

    for model in models:

        if model == "power":
            # Paramètres power = [scale, exponent, nugget]
            def objective(theta):
                scale, exponent, nugget = theta
                g_fit = variogram_models.power_variogram_model(
                    [scale, exponent, nugget], bin_centers
                )
                return np.nansum((gamma_mean - g_fit) ** 2)

            init = np.array([np.nanmax(gamma_mean), 1.0, 0.01])
            bounds = [
                (0, None),   # scale >= 0
                (0, 2),      # exponent in [0, 2]
                (0, None),   # nugget >= 0
            ]

        else:
            # Paramètres std = [sill, range, nugget]
            def objective(theta):
                sill, rng, nugget = theta
                g_fit = vfunc[model]([sill, rng, nugget], bin_centers)
                return np.nansum((gamma_mean - g_fit) ** 2)

            init = np.array([
                np.nanmax(gamma_mean),        # sill init
                np.max(bin_centers) / 3,      # range init
                0.01                           # nugget init
            ])

            bounds = [
                (0, None),      # sill
                (1e-6, None),   # range > 0
                (0, None)       # nugget
            ]

        # Optimization safer
        res = minimize(objective, init, bounds=bounds, method="L-BFGS-B")
        params = res.x

        # Build fitted curve
        if model == "power":
            scale, exponent, nugget = params
            curve = variogram_models.power_variogram_model(
                [scale, exponent, nugget], bin_centers
            )
        else:
            sill, rng, nugget = params
            curve = vfunc[model]([sill, rng, nugget], bin_centers)

        model_curves[model] = curve
        wls_scores[model] = np.sum((gamma_mean - curve) ** 2)

        print(f"Model {model}: params={params} → WLS={wls_scores[model]:.6f}")

    # ------------------------------------------
    # ÉTAPE 3 — PLOT COMPARATIF
    # ------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.plot(bin_centers, gamma_mean, "o", label="Mean empirical variogram", color="blue")

    for model in models:
        plt.plot(bin_centers, model_curves[model], label=f"{model} (WLS={wls_scores[model]:.4f})")

    plt.title("Mean Variogram — Model Comparison")
    plt.xlabel("Lag h")
    plt.ylabel("γ(h)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.show()

    # ------------------------------------------
    # ÉTAPE 4 — TABLEAU FINAL
    # ------------------------------------------
    df_scores = pd.DataFrame.from_dict(wls_scores, orient="index", columns=["WLS"])
    df_scores["Rank"] = df_scores["WLS"].rank(method="min")
    df_scores = df_scores.sort_values("WLS")

    print("\n=== FINAL MODEL COMPARISON ===\n")
    print(df_scores)

    return gamma_mean, df_scores


def compare_variogram_models(df_train, prob_col="p_raw", year_col="ANNEE",
                             n_bins=40, max_points=3000,
                             models=("gaussian","spherical","exponential","power","hole-effect")):
    """
    Compare plusieurs modèles de variogramme :
    - génère tous les graphiques pour chaque modèle
    - calcule la métrique WLS pour chaque année et modèle
    - retourne un tableau comparatif
    """

    # Mapping des fonctions PyKrige
    variogram_functions = {
        "gaussian": variogram_models.gaussian_variogram_model,
        "spherical": variogram_models.spherical_variogram_model,
        "exponential": variogram_models.exponential_variogram_model,
        "power": variogram_models.power_variogram_model,
        "hole-effect": variogram_models.hole_effect_variogram_model,
    }

    # Tableau final des scores
    years = sorted(df_train[year_col].unique())
    wls_table = pd.DataFrame(index=years, columns=models)

    # ==== BOUCLE SUR LES MODÈLES ====
    for variogram_model in models:
        print(f"\n==============================")
        print(f"   MODEL: {variogram_model}")
        print(f"==============================\n")

        # Utilise ta fonction modifiée
        wls_scores = plot_variograms_grid(
            df_train,
            prob_col=prob_col,
            year_col=year_col,
            n_bins=n_bins,
            max_points=max_points,
            variogram_model=variogram_model
        )

        # Sauvegarde dans tableau
        for year, score in wls_scores.items():
            wls_table.loc[year, variogram_model] = score

    # Ajoute colonne Best
    wls_table["Best Model"] = wls_table.astype(float).idxmin(axis=1)

    print("\n================ WLS METRIC TABLE ================\n")
    print(wls_table)

    return wls_table



# =======================================================================
# 5. METRICS
# =======================================================================

def print_metrics(y_true, y_pred_proba, threshold=0.5):
    y_pred = (y_pred_proba > threshold).astype(int)

    print("\n---------------- Metrics ----------------")
    print("AUC :", roc_auc_score(y_true, y_pred_proba))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred))

def plot_roc_curve(y_true, y_proba, model_name):
    plt.figure(figsize=(6, 5))
    RocCurveDisplay.from_predictions(y_true, y_proba, name=model_name)
    plt.title(f"ROC Curve - {model_name}")
    plt.grid(True)
    plt.show()
# =======================================================================
# 6. MASTER PIPELINE
# =======================================================================

def run_pipeline(df, features, target, model_name,
                 year_col="ANNEE", test_years=[2023, 2024]):

    # 0. Model selection
    model = get_model(model_name)
    print(f"\n======== SELECTED MODEL: {model_name} ========")

    # 1. Split by year
    df_train = df.loc[~df[year_col].isin(test_years)].copy()
    df_test = df.loc[df[year_col].isin(test_years)].copy()

    print(f"\nTrain years = {df_train[year_col].unique()}")
    print(f"Test years  = {df_test[year_col].unique()}")
    print(f"Train size  = {len(df_train)}")
    print(f"Test size   = {len(df_test)}")

    # 2. Train ML
    print("\n--- TRAINING MODEL ---")
    model.fit(df_train[features], df_train[target])

    # 3. Predict raw probabilities
    df_train["p_raw"] = model.predict_proba(df_train[features])[:, 1]
    df_test["p_raw"] = model.predict_proba(df_test[features])[:, 1]

    print("\n--- DIAGNOSTIC: VARIOGRAMS BY YEAR (TRAIN) ---")
    plot_variograms_grid(df_train, prob_col="p_raw", year_col=year_col)

    print("\n--- RAW PROBABILITY METRICS (TEST) ---")
    print_metrics(df_test[target], df_test["p_raw"])
    plot_roc_curve(df_test[target], df_test["p_raw"], model_name + " (raw)")


    # 4. Mean variogram (sur TRAIN)
    print("\n--- COMPUTING MEAN VARIOGRAM ---")
    mean_params = compute_mean_variogram(df_train, "p_raw", year_col)

    # 5. Kriging par année avec variogramme moyen (sur TRAIN)
    print("\n--- FITTING PER-YEAR KRIGING MODELS (MEAN VARIOGRAM) ---")
    kriging_models = fit_kriging_with_mean_variogram(
        df_train, "p_raw", mean_params, year_col
    )

    # 6. Application de la correction spatiale sur le TEST
    print("\n--- APPLYING SPATIAL CORRECTION (TEST) ---")
    df_test_corr = apply_kriging_by_year(
        df_test, "p_raw", kriging_models, year_col
    )

    print("\n--- CORRECTED PROBABILITY METRICS (TEST) ---")
    print_metrics(df_test[target], df_test_corr["p_corr"])
    plot_roc_curve(df_test[target], df_test_corr["p_corr"], model_name + " (raw)")


    return df_test_corr


# =======================================================================
# 7. USAGE EXAMPLE
# =======================================================================

if __name__ == "__main__":
    print("This module is intended to be imported, not run directly.")
