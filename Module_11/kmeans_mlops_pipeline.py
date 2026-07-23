"""
Module 11: MLOps Tracking for KMeans Clustering with MLflow.

This script loads Grad Café program data, applies TF-IDF vectorization,
reduces dimensionality with PCA, trains a KMeans model, and tracks the
experiment using MLflow. Parameters, inertia metric, and the model itself
are logged to the MLflow server.
"""
import os
import json
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import mlflow
import mlflow.sklearn
import wandb
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Set to True to use Weights & Biases instead of MLflow (extra credit)
USE_WANDB = True

# MLflow server URI (use localhost for local development)
MLFLOW_TRACKING_URI = "http://127.0.0.1:8080"

# KMeans parameters (required by assignment)
PARAMS = {
    "max_iter": 500,
    "n_clusters": 25,
    "n_init": 5,
    "random_state": 42,
}

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_data():
    """Load the Grad Café dataset from the local file or fallback."""
    # Try local dataset first
    local_path = "applicant_data.json"
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data["results"])
        print(f"[OK] Loaded local data: {len(df)} rows")
        return df

    # Try cleaned data from Module 9
    if os.path.exists("../Module_9/cleaned_gradcafe.json"):
        with open("../Module_9/cleaned_gradcafe.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"[OK] Loaded cleaned data from Module_9: {len(df)} rows")
        return df

    raise FileNotFoundError("No data file found!")


def clean_data(df):
    """Clean program names and prepare for vectorization."""
    # Remove rows where program is None
    df_clean = df[df["program"].notna()].copy()

    # Strip whitespace from program names
    df_clean["program"] = df_clean["program"].str.strip()

    print(f"Rows after cleaning: {len(df_clean)}")
    print(f"Unique programs: {df_clean['program'].nunique():,}")

    return df_clean


def vectorize_programs(df):
    """Vectorize program names using TF-IDF."""
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words="english",
        lowercase=True,
    )
    tfidf_matrix = vectorizer.fit_transform(df["program"])
    print(f"TF-IDF Matrix Shape: {tfidf_matrix.shape}")
    return vectorizer, tfidf_matrix


def reduce_dimensions(tfidf_matrix):
    """Reduce TF-IDF matrix to 50 components using PCA."""
    pca = PCA(n_components=50, random_state=42)
    pca_features = pca.fit_transform(tfidf_matrix.toarray())
    print(f"PCA Features Shape: {pca_features.shape}")
    return pca, pca_features


def train_kmeans(pca_features, params):
    """Train a KMeans model with the given parameters."""
    kmeans = KMeans(
        n_clusters=params["n_clusters"],
        max_iter=params["max_iter"],
        n_init=params["n_init"],
        random_state=params["random_state"],
    )
    kmeans.fit(pca_features)
    print(f"KMeans inertia: {kmeans.inertia_:.2f}")
    return kmeans


def run_mlflow_tracking(kmeans, params):
    """Run MLflow tracking for the KMeans model."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    with mlflow.start_run(run_name="Clustering v1") as run:
        # Log parameters
        mlflow.log_params(params)

        # Log metric (inertia)
        mlflow.log_metric("inertia", kmeans.inertia_)

        # Log the model
        mlflow.sklearn.log_model(
            sk_model=kmeans,
            artifact_path="kmeans_model",
            registered_model_name="Clustering",
        )

        print(f"\n[OK] MLflow Run ID: {run.info.run_id}")
        print("[OK] MLflow Tracking URI:", MLFLOW_TRACKING_URI)
        print("[OK] Model registered as: Clustering")

        # Return run ID for screenshot reference
        return run.info.run_id


def run_wandb_tracking(kmeans, params):
    """Run wandb tracking for the KMeans model."""
    wandb.init(
        project="kmeans-clustering",
        name="Clustering-v1-wandb",
        config=params
    )

    # Log inertia metric
    wandb.log({"inertia": kmeans.inertia_})

    # Save and log model artifact
    with open("kmeans_model.pkl", "wb") as f:
        pickle.dump(kmeans, f)

    artifact = wandb.Artifact("kmeans_model", type="model")
    artifact.add_file("kmeans_model.pkl")
    wandb.log_artifact(artifact)

    print("[OK] wandb run completed!")
    print("[OK] Check wandb.ai for results")

    wandb.finish()


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def main():
    """Execute the full KMeans clustering pipeline with MLOps tracking."""
    print("=" * 60)
    print("Module 11: KMeans Clustering with MLOps Tracking")
    print("=" * 60)

    # 1. Load and clean data
    df = load_data()
    df_clean = clean_data(df)

    # 2. Vectorize
    _, tfidf_matrix = vectorize_programs(df_clean)

    # 3. PCA
    _, pca_features = reduce_dimensions(tfidf_matrix)

    # 4. Train KMeans
    kmeans = train_kmeans(pca_features, PARAMS)

    # 5. Track with MLflow or wandb
    if USE_WANDB:
        run_wandb_tracking(kmeans, PARAMS)
    else:
        _ = run_mlflow_tracking(kmeans, PARAMS)

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("Open your browser to http://127.0.0.1:8080 to view MLflow UI.")
    print("=" * 60)


if __name__ == "__main__":
    main()
