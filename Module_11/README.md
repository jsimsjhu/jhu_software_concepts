## 1. Module 11 – MLOps Tracking with MLflow

This module adds MLflow tracking to the KMeans clustering pipeline from Module 9. The pipeline loads Grad Café program data, vectorizes program names using TF-IDF, reduces dimensionality with PCA, and trains a KMeans model. MLflow tracks the parameters, inertia metric, and saves the model as a registered artifact.

## 2. Setup

2.1 Create a virtual environment
python -m venv venv
source venv/bin/activate      # On macOS/Linux
venv\Scripts\activate         # On Windows

2.2 Install dependencies
bash
pip install -r requirements.txt

2.3 Start MLflow server
bash
mlflow server --host 127.0.0.1 --port 8080

2.4 Run the pipeline
bash
python kmeans_mlops_pipeline.py

## 3. What Gets Logged
Type	Items
Parameters	max_iter, n_clusters, n_init, random_state
Metrics	inertia
Model	KMeans model saved as a registered MLflow model

## 4. Where to Find Results
After running the pipeline:
Open your browser and go to http://127.0.0.1:8080
Click on the latest run to view parameters and inertia

The saved model is visible in the MLflow Model Registry under "Clustering"

## 5. Screenshots
5.1 cluster_run.png
MLflow UI showing the run

5.2 cluster_details.png
Run details with parameters and inertia metric

5.3 model_details.png
Registered model in MLflow Model Registry

## 6. Dataset
This pipeline uses the Grad Café dataset. The script first checks for `applicant_data.json` in the local folder. If not found, it falls back to `../Module_9/cleaned_gradcafe.json` or the raw data from Module 6.

## 7. Optional wandb Extension
To run with wandb tracking instead, set USE_WANDB = True in the script:

USE_WANDB = True   # Set to False for MLflow only
wandb screenshots:

wandb_run.png – wandb UI showing the run

wandb_details.png – wandb run with parameters and inertia metric

wandb_artifact.png – wandb saved model artifact


---

## ✅ Checklist

| Requirement | Status |
|-------------|--------|
| Purpose of script described | ✅ |
| How to install and run | ✅ |
| MLflow server setup | ✅ |
| What gets logged | ✅ |
| Where to find results | ✅ |
| Dataset mentioned | ✅ |
| Screenshots listed | ✅ |

---