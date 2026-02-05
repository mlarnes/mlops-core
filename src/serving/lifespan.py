"""
Gestion du cycle de vie de l'application (startup/shutdown).

Priorité de chargement du modèle au démarrage (portfolio-friendly) :

1. **Copie locale contrôlée** dans `MODEL_DIR` (par défaut `models/`), typiquement
   montée depuis un PVC `/app/models` mis à jour par un Job d'entraînement K8s.
2. **Model Registry MLflow** via `models:/name/version` ou `models:/name/stage`,
   quand les informations sont présentes dans `metadata.json`.
3. **Fallback** vers un run MLflow (`runs:/<run_id>/model` ou chemin `mlruns/...`)
   pour les scénarios purement locaux.

Ce design reflète le choix d'architecture du projet :
- MLflow = source de vérité analytique (UI, runs, registry),
- PVC `/app/models` = source de vérité opérationnelle pour le runtime de l'API.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import joblib
import mlflow
import mlflow.sklearn
from fastapi import FastAPI

from .metrics import model_loaded

logger = logging.getLogger("iris_api")


def _configure_mlflow_tracking() -> tuple[str, Optional[str]]:
    """Configure MLflow tracking et retourne:

    - tracking_uri: URI du tracking backend (ou chaîne vide si non utilisée)
    - artifact_base_uri: base URI pour les artefacts (ex: gs://bucket/mlruns) si applicable

    Cas gérés:
    - MLFLOW_TRACKING_URI commence par 'gs://': utilisé comme base GCS pour les artefacts,
      sans être configuré comme tracking URI (MLflow ne supporte pas gs:// pour le registry).
    - MLFLOW_TRACKING_URI est une URI supportée (file://, http(s)://, postgres://, ...):
      configurée comme tracking URI classique.
    - MLFLOW_TRACKING_URI non défini: tracking local file://mlruns.
    """
    raw_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()

    # Cas 1 : URI GCS → artifact store uniquement
    if raw_uri.startswith("gs://"):
        artifact_base_uri = raw_uri.rstrip("/")
        logger.info(f"MLflow artifact base (GCS): {artifact_base_uri}")
        # On ne configure PAS mlflow.set_tracking_uri avec gs:// (non supporté pour le registry)
        return "", artifact_base_uri

    # Cas 2 : URI explicite supportée (registry MLflow classique)
    if raw_uri:
        mlflow.set_tracking_uri(raw_uri)
        logger.info(f"MLflow Tracking URI configuré: {raw_uri}")
        return raw_uri, None

    # Cas 3 : défaut local - utiliser mlruns/ relatif (fonctionne avec/sans Docker)
    mlruns_path = Path("mlruns").absolute()
    local_uri = f"file://{mlruns_path}"
    mlflow.set_tracking_uri(local_uri)
    logger.info(f"MLflow Tracking URI (local): {local_uri}")
    return local_uri, None


def _build_model_uri(
    mlflow_run_id: str,
    mlflow_tracking_uri: str,
    metadata: dict,
    artifact_base_uri: Optional[str] = None,
) -> str:
    """Construit l'URI du modèle MLflow.

    - Si artifact_base_uri est fourni (ex: gs://bucket/mlruns), construit une URI artefact GCS.
    - Sinon, reproduit le comportement historique:
      - si tracking URI défini ou pas de chemin relatif → runs:/<run_id>/model
      - sinon, chemin de fichier local sous mlruns/.
    """
    mlflow_relative_path = metadata.get("mlflow_relative_path", "")

    # Cas 1 : on a une base d'artefacts explicite (ex: GCS)
    if artifact_base_uri:
        # Si on dispose d'un chemin relatif MLflow, on le réutilise
        if mlflow_relative_path:
            if mlflow_relative_path.startswith("mlruns/"):
                relative_path = mlflow_relative_path[7:]  # Retirer "mlruns/"
            else:
                relative_path = mlflow_relative_path
            return f"{artifact_base_uri.rstrip('/')}/{relative_path}/artifacts/model"

        # Fallback : chemin standard à partir du run_id
        return f"{artifact_base_uri.rstrip('/')}/{mlflow_run_id}/artifacts/model"

    # Cas 2 : comportement historique avec tracking URI (registry MLflow)
    if mlflow_tracking_uri or not mlflow_relative_path:
        return f"runs:/{mlflow_run_id}/model"

    # Cas 3 : en local avec chemin relatif, construire le chemin direct
    mlruns_path = Path("mlruns").absolute()

    # Extraire la partie après "mlruns/" si présent
    if mlflow_relative_path.startswith("mlruns/"):
        relative_path = mlflow_relative_path[7:]  # Retirer "mlruns/"
    else:
        relative_path = mlflow_relative_path

    model_path = mlruns_path / relative_path / "artifacts" / "model"
    return str(model_path)


def _load_metadata(model_dir: Path) -> dict:
    """Charge et valide les métadonnées du modèle."""
    metadata_path = model_dir / "metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Métadonnées non trouvées : {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    if not metadata.get("mlflow_run_id"):
        raise ValueError(
            "mlflow_run_id non trouvé dans metadata.json. "
            "Le modèle doit être entraîné avec MLflow."
        )

    return metadata


def _load_metrics(model_dir: Path) -> Optional[dict]:
    """Charge les métriques du modèle si disponibles."""
    metrics_path = model_dir / "metrics.json"

    if not metrics_path.exists():
        logger.warning("Metrics not found", extra={"path": str(metrics_path)})
        return None

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    logger.info("Metrics loaded", extra={"path": str(metrics_path)})
    return metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application.

    Rappel de la stratégie de chargement du modèle :

    - Si un fichier local `model.joblib` est présent dans `MODEL_DIR` (copie
      produite par le job d'entraînement et montée via PVC), il est chargé en
      priorité. C'est le chemin "runtime" principal de ce portfolio.
    - Sinon, on tente de charger le modèle via MLflow :
        * d'abord via le Model Registry (si `mlflow_model_name` + version/stage),
        * sinon via le run MLflow historique (URI construite par `_build_model_uri`).
    - En cas d'erreur, l'application démarre sans modèle mais expose un état
      cohérent (`model_loaded = 0`) et des logs détaillés.
    """
    model_dir = Path(os.getenv("MODEL_DIR", "models"))

    # Initialiser l'état de l'application
    app.state.model = None
    app.state.metadata = None
    app.state.metrics = None

    try:
        # Charger et valider les métadonnées
        metadata = _load_metadata(model_dir)
        app.state.metadata = metadata

        # 1) Tentative de chargement direct du modèle local (copie déposée par le job)
        local_model_path = metadata.get("local_model_path")
        local_model_file = model_dir / "model.joblib"

        if local_model_path and local_model_file.exists():
            logger.info(f"Loading model from local file: {local_model_file}")
            app.state.model = joblib.load(local_model_file)
            model_loaded.set(1)
            app.state.metrics = _load_metrics(model_dir)
            logger.info(
                "Model loaded successfully from local file",
                extra={"local_model_path": str(local_model_file)},
            )
            yield
            model_loaded.set(0)
            return

        # Configurer MLflow (tracking + éventuelle base d'artefacts GCS)
        mlflow_tracking_uri, artifact_base_uri = _configure_mlflow_tracking()

        # Construire l'URI du modèle
        mlflow_run_id = metadata["mlflow_run_id"]

        # Préférence : charger depuis le Model Registry si disponible
        mlflow_model_name = metadata.get("mlflow_model_name")
        mlflow_model_version = metadata.get("mlflow_model_version")
        mlflow_model_stage = metadata.get("mlflow_model_stage")

        if mlflow_model_name and (mlflow_model_version or mlflow_model_stage):
            if mlflow_model_version:
                model_uri = f"models:/{mlflow_model_name}/{mlflow_model_version}"
            else:
                model_uri = f"models:/{mlflow_model_name}/{mlflow_model_stage}"
        else:
            # Fallback : comportement historique (runs:/... ou chemin fichier)
            model_uri = _build_model_uri(
                mlflow_run_id,
                mlflow_tracking_uri,
                metadata,
                artifact_base_uri=artifact_base_uri,
            )

        logger.info(f"Loading model from: {model_uri}")

        # Charger le modèle
        app.state.model = mlflow.sklearn.load_model(model_uri)
        model_loaded.set(1)

        logger.info(
            "Model loaded successfully",
            extra={
                "run_id": mlflow_run_id,
                "tracking_uri": mlflow_tracking_uri or "local (mlruns/)",
                "model_uri": model_uri,
            },
        )

        # Charger les métriques (non bloquant)
        app.state.metrics = _load_metrics(model_dir)

    except FileNotFoundError as exc:
        model_loaded.set(0)
        logger.error(f"File not found: {exc}")
        # L'application démarre quand même mais sans modèle
    except ValueError as exc:
        model_loaded.set(0)
        logger.error(f"Invalid configuration: {exc}")
    except Exception as exc:
        model_loaded.set(0)
        logger.exception(
            "Failed to load model",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )

    yield  # l'app est maintenant prête

    # Cleanup au shutdown
    model_loaded.set(0)
