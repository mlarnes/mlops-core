"""
Module d'entraînement du modèle ML
Modèle de classification sur le dataset Iris
Intégration MLflow pour le tracking des expériences (Phase 4)
Lit les paramètres depuis params.yaml avec validation Pydantic
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import joblib
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.config import get_config
from src.evaluation.evaluate import evaluate_model

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_data(
    test_size: float, random_state: int
) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Charge les données depuis CSV (DVC pipeline) ou scikit-learn

    Returns:
        Tuple[train_df, test_df, iris_metadata]
    """
    train_path = Path("data/processed/train.csv")
    test_path = Path("data/processed/test.csv")

    # Charger les métadonnées Iris une seule fois (utilisées dans les deux cas)
    iris = load_iris()
    iris_metadata = {
        "feature_names": list(iris.feature_names),
        "target_names": list(iris.target_names),
    }

    if train_path.exists() and test_path.exists():
        logger.info("   📂 Chargement depuis les fichiers CSV (DVC pipeline)...")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        return train_df, test_df, iris_metadata
    else:
        logger.info("   📦 Chargement depuis scikit-learn...")
        df = pd.DataFrame(iris.data, columns=iris.feature_names)
        df["target"] = iris.target

        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df["target"],
        )

        return train_df, test_df, iris_metadata

def _configure_hyperparameters(
    n_estimators: Optional[int],
    max_depth: Optional[int],
    random_state: Optional[int],
    test_size: Optional[float],
) -> tuple[int, Optional[int], int, float]:
    """Lit la configuration applicative et applique les éventuels overrides CLI.

    Cette fonction est surtout là pour clarifier `train_model` et raconter
    explicitement la logique de fallback (params.yaml → arguments optionnels).
    """
    config = get_config()
    resolved_n_estimators = n_estimators or config.train.n_estimators
    resolved_max_depth = max_depth or config.train.max_depth
    resolved_random_state = random_state or config.train.random_state
    resolved_test_size = test_size or config.data.test_size

    return (
        resolved_n_estimators,
        resolved_max_depth,
        resolved_random_state,
        resolved_test_size,
    )


def _configure_mlflow(experiment_name: str) -> None:
    """Configure MLflow pour le tracking (local ou serveur HTTP).

    Cette fonction encapsule simplement la logique de :
    - lecture de `MLFLOW_TRACKING_URI`,
    - configuration du backend,
    - création (ou récupération) de l'expérience.
    """
    # Configuration MLflow (toujours activé)
    # Support de backends distants via variable d'environnement
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        logger.info(f"📊 MLflow Tracking URI: {mlflow_tracking_uri}")
    else:
        logger.info("📊 MLflow Tracking URI: local (mlruns/)")

    # Configurer l'expérience (doit être fait même sans tracking URI personnalisé)
    mlflow.set_experiment(experiment_name)


def _prepare_features(
    train_df: pd.DataFrame, test_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, list[str]]:
    """Prépare les features/targets dans un seul endroit.

    Cela évite de disperser les sélections de colonnes dans `train_model` et
    rend explicite la structure du dataset Iris.
    """
    feature_cols = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    X_train = train_df[feature_cols].values
    y_train = train_df["target"].values
    X_test = test_df[feature_cols].values
    y_test = test_df["target"].values
    return X_train, X_test, y_train, y_test, feature_cols


def _save_local_artifacts(
    models_dir: Path,
    model: RandomForestClassifier,
    metadata: dict,
    metrics: dict,
) -> None:
    """Sauvegarde la copie "runtime" du modèle pour l'API.

    Dans ce projet de portfolio :
    - MLflow reste la source de vérité analytique (UI, runs, registry),
    - mais l'API charge le modèle depuis une copie maîtrisée dans `models/`
      (PVC partagé avec le job d'entraînement en mode Kubernetes).
    """
    models_dir.mkdir(exist_ok=True)

    # Sauvegarder le modèle au format joblib pour l'API
    joblib.dump(model, models_dir / "model.joblib")

    # Sauvegarder metadata.json et metrics.json (consommés par l'API au startup)
    for filename, data in [("metadata.json", metadata), ("metrics.json", metrics)]:
        path = models_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def train_model(
    n_estimators: Optional[int] = None,
    max_depth: Optional[int] = None,
    random_state: Optional[int] = None,
    test_size: Optional[float] = None,
    experiment_name: str = "iris-classification",
    run_name: Optional[str] = None,
    tags: Optional[dict] = None,
) -> Tuple[RandomForestClassifier, dict]:
    """
    Entraîne un modèle RandomForest sur le dataset Iris avec tracking MLflow
    Les paramètres sont lus depuis params.yaml avec validation Pydantic si non fournis

    Args:
        n_estimators: Nombre d'arbres dans la forêt (surcharge params.yaml si fourni)
        max_depth: Profondeur maximale des arbres (surcharge params.yaml si fourni)
        random_state: Graine aléatoire pour la reproductibilité (surcharge params.yaml si fourni)
        test_size: Proportion du dataset pour le test (surcharge params.yaml si fourni)
        experiment_name: Nom de l'experiment MLflow (par défaut: "iris-classification")
        run_name: Nom du run MLflow (auto-généré si None)
        tags: Tags MLflow (ex: {"experiment_type": "baseline", "status": "testing"})

    Returns:
        Tuple[RandomForestClassifier, dict]: Modèle entraîné et métadonnées
    """
    (
        n_estimators,
        max_depth,
        random_state,
        test_size,
    ) = _configure_hyperparameters(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        test_size=test_size,
    )

    # Configuration MLflow (toujours activé)
    _configure_mlflow(experiment_name=experiment_name)

    # Générer le nom du run si non fourni
    if run_name is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_name = f"n_est-{n_estimators}_maxd-{max_depth or 'None'}_{timestamp}"

    # Utiliser context manager pour garantir le nettoyage même en cas d'erreur
    with mlflow.start_run(run_name=run_name):
        logger.info("🌱 Chargement du dataset Iris...")
        train_df, test_df, iris_metadata = load_data(test_size, random_state)

        # Séparer features et target (centralisé pour plus de lisibilité)
        X_train, X_test, y_train, y_test, feature_cols = _prepare_features(
            train_df, test_df
        )

        # Hyperparamètres et dimensions
        hyperparams = {
            "n_estimators": n_estimators,
            "max_depth": max_depth or "None",
            "random_state": random_state,
        }
        n_features = X_train.shape[1]
        n_samples = len(X_train) + len(X_test)

        # Logging MLflow
        mlflow.log_params(hyperparams)
        mlflow.log_params(
            {
                "algorithm": "RandomForestClassifier",
                "dataset": "Iris",
                "n_features": n_features,
                "n_samples": n_samples,
                "n_classes": len(iris_metadata["target_names"]),
                "data.test_size": test_size,
            }
        )
        if tags:
            for key, value in tags.items():
                mlflow.set_tag(key, str(value))
        mlflow.set_tags(
            {
                "model_type": "RandomForestClassifier",
                "experiment_name": experiment_name,
            }
        )

        logger.info(f"🤖 Entraînement RandomForest: {hyperparams}")
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
        )
        model.fit(X_train, y_train)

        # Évaluation
        metrics, metadata = evaluate_model(model, X_test, y_test, iris_metadata)

        # Sauvegarde dans MLflow (source de vérité, avec Model Registry)
        mlflow_model_name = "IrisClassifier"
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name=mlflow_model_name,
            input_example=X_test[0:1],
        )
        # Capturer l'URI du run MLflow pour référence
        mlflow_run_uri = mlflow.get_artifact_uri("model")
        logger.info(f"📊 Modèle enregistré dans MLflow: {mlflow_run_uri}")

        # Récupérer les informations du run MLflow actif
        active_run = mlflow.active_run()
        mlflow_run_id = active_run.info.run_id if active_run else None
        mlflow_experiment_id = active_run.info.experiment_id if active_run else None
        mlflow_relative_path = (
            f"mlruns/{mlflow_experiment_id}/{mlflow_run_id}" if active_run else None
        )

        # Récupérer la version associée dans le Model Registry
        mlflow_model_version: Optional[str] = None
        if mlflow_run_id:
            client = MlflowClient()
            latest_versions = client.get_latest_versions(mlflow_model_name)
            for mv in latest_versions:
                if mv.run_id == mlflow_run_id:
                    mlflow_model_version = mv.version
                    break

        # Enrichir et sauvegarder les métadonnées (toutes les infos en une seule fois)
        metadata.update(
            {
                "model_type": "RandomForestClassifier",
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": random_state,
                "n_features": n_features,
                "n_samples": n_samples,
                # Informations MLflow (run)
                "mlflow_run_uri": mlflow_run_uri,
                "mlflow_experiment_name": experiment_name,
                "mlflow_run_name": run_name,
                "mlflow_run_id": mlflow_run_id,
                "mlflow_relative_path": mlflow_relative_path,
                # Informations Model Registry
                "mlflow_model_name": mlflow_model_name,
                "mlflow_model_version": mlflow_model_version,
                # Local model path (copie runtime pour l'API, montée sur PVC en K8s)
                "local_model_path": str(Path("models") / "model.joblib"),
            }
        )

        # Créer/mettre à jour la copie "runtime" du modèle pour l'API
        _save_local_artifacts(
            models_dir=Path("models"),
            model=model,
            metadata=metadata,
            metrics=metrics,
        )

        mlflow.log_dict(metadata, "metadata.json")
        logger.info("🔗 MLflow UI: mlflow ui")

        logger.info("✅ Entraînement terminé avec succès !")
        return model, metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Entraîner le modèle avec MLflow")
    parser.add_argument(
        "--experiment-name", default="iris-classification", help="Nom experiment MLflow"
    )
    parser.add_argument("--run-name", help="Nom du run MLflow")
    parser.add_argument("--n-estimators", type=int, help="Nombre d'arbres")
    parser.add_argument("--max-depth", type=int, help="Profondeur maximale")
    parser.add_argument("--test-size", type=float, help="Proportion test (0-1)")
    parser.add_argument("--random-state", type=int, help="Graine aléatoire")
    parser.add_argument(
        "--tag", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Tags MLflow"
    )

    args = parser.parse_args()

    # Validation
    if args.test_size is not None and not 0 < args.test_size < 1:
        parser.error("--test-size doit être entre 0 et 1")
    if args.n_estimators is not None and args.n_estimators <= 0:
        parser.error("--n-estimators doit être > 0")
    if args.max_depth is not None and args.max_depth <= 0:
        parser.error("--max-depth doit être > 0")

    tags = dict(args.tag) if args.tag else {}
    train_model(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
        test_size=args.test_size,
        experiment_name=args.experiment_name,
        run_name=args.run_name,
        tags=tags,
    )
