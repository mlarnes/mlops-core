"""
Routes/Endpoints de l'API
"""

import logging
from typing import Dict

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request

from .metrics import (
    api_errors,
    get_metrics_response,
    model_confidence,
    model_predictions,
)
from .middleware import limiter
from .models import HealthResponse, IrisFeatures, PredictionResponse
from .security import verify_api_key

logger = logging.getLogger("iris_api")


def register_routes(app: FastAPI):
    """Enregistre toutes les routes de l'API"""

    @app.get("/", response_model=Dict[str, str])
    async def root():
        """
        Endpoint racine de l'API.
        ⚠️ Note : Cet endpoint n'exige pas d'authentification (information publique).
        """
        return {
            "message": "API Classification Iris",
            "docs": "/docs",
            "health": "/health",
            "security": "Cette API utilise l'authentification par API key. Fournissez votre clé via le header X-API-Key",
        }

    @app.get("/metrics")
    async def metrics():
        """Endpoint Prometheus pour les métriques"""
        return get_metrics_response()

    @app.get("/health", response_model=HealthResponse)
    @limiter.limit("30/minute")  # Rate limiting plus permissif pour le health check
    async def health_check(request: Request):
        """
        Vérifie si le modèle est chargé (via app.state).
        ⚠️ Note : Cet endpoint n'exige pas d'authentification pour permettre le monitoring.
        """
        is_model_loaded = getattr(request.app.state, "model", None) is not None
        return HealthResponse(
            status="healthy" if is_model_loaded else "unhealthy",
            model_loaded=is_model_loaded,
            version=request.app.version,
        )

    @app.post("/predict", response_model=PredictionResponse)
    @limiter.limit("10/minute")  # ⚠️ SÉCURITÉ : 10 requêtes par minute par IP
    async def predict_iris(
        features: IrisFeatures,
        request: Request,
        api_key: str = Depends(
            verify_api_key
        ),  # ⚠️ SÉCURITÉ : Authentification requise
    ):
        """
        Prédiction de la classe d'une fleur d'iris.
        Récupère le modèle depuis request.app.state (évite globals).

        ⚠️ SÉCURITÉ :
        - Authentification : Requiert une API key via le header X-API-Key
        - Rate limiting : 10 requêtes par minute par adresse IP
        - Validation : Les entrées sont validées par Pydantic (IrisFeatures)
        """
        model = getattr(request.app.state, "model", None)
        metadata = getattr(request.app.state, "metadata", None)

        if model is None:
            # 503 Service Unavailable — le modèle n'est pas présent
            raise HTTPException(status_code=503, detail="Modèle non chargé")

        # Préparer l'array
        features_array = np.array(
            [
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width,
            ],
            dtype=float,
        ).reshape(1, -1)

        try:
            # Vérifier si le modèle supporte predict_proba
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(features_array)[0]
            else:
                # fallback : one-hot sur la prédiction simple (confiance = 1.0)
                pred_idx = int(model.predict(features_array)[0])
                proba = np.zeros(len(getattr(model, "classes_", [0])))
                if pred_idx < proba.shape[0]:
                    proba[pred_idx] = 1.0
                else:
                    # Incohérence : on reconstruira un vecteur minimal
                    proba = np.array([1.0])

            # Récupérer noms des classes depuis metadata si fourni, sinon depuis model.classes_
            if metadata and "target_names" in metadata:
                class_names = metadata["target_names"]
            elif hasattr(model, "classes_"):
                # si model.classes_ est un array de labels (ex: [0,1,2]) on convertit en str
                class_names = [str(c) for c in model.classes_]
            else:
                class_names = ["setosa", "versicolor", "virginica"]

            # S'assurer que la longueur correspond
            if len(class_names) != len(proba):
                # si mismatch, on aligne en prenant min des deux longueurs
                n = min(len(class_names), len(proba))
                class_names = class_names[:n]
                proba = proba[:n]

            probabilities = {
                class_names[i]: float(proba[i]) for i in range(len(class_names))
            }
            # prédiction (classe la plus probable)
            pred_index = int(np.argmax(proba))
            predicted_class = class_names[pred_index]
            confidence = float(max(proba)) if proba.size > 0 else 0.0

            # Tracker les métriques
            model_predictions.labels(predicted_class=predicted_class).inc()
            model_confidence.labels(predicted_class=predicted_class).observe(confidence)

            logger.info(
                "Prediction made",
                extra={
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "status": "success",
                },
            )

            return PredictionResponse(
                prediction=predicted_class,
                confidence=confidence,
                probabilities=probabilities,
            )

        except Exception as exc:
            api_errors.labels(error_type=type(exc).__name__, endpoint="/predict").inc()
            logger.exception(
                "Error in prediction",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "status": "error",
                },
            )
            # ⚠️ SÉCURITÉ : Ne pas exposer les détails de l'exception à l'utilisateur
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la prédiction. Veuillez vérifier vos données d'entrée.",
            )

    @app.get("/model/info")
    @limiter.limit(
        "20/minute"
    )  # ⚠️ SÉCURITÉ : 20 requêtes par minute par IP (endpoint moins coûteux)
    async def model_info(
        request: Request,
        api_key: str = Depends(
            verify_api_key
        ),  # ⚠️ SÉCURITÉ : Authentification requise
    ):
        """Renvoie les métadonnées et métriques du modèle si disponibles"""
        metadata = getattr(request.app.state, "metadata", None)
        metrics = getattr(request.app.state, "metrics", None)
        model = getattr(request.app.state, "model", None)

        if metadata is None and model is None:
            raise HTTPException(
                status_code=404, detail="Modèle et métadonnées non disponibles"
            )

        # Construction d'une réponse
        # Séparation claire : metrics.json = métriques, metadata.json = métadonnées
        return {
            # Métadonnées du modèle (depuis metadata.json)
            "model_type": metadata.get("model_type")
            if metadata
            else getattr(model, "__class__", "Unknown").__name__,
            "n_features": metadata.get("n_features") if metadata else "Unknown",
            "n_samples": metadata.get("n_samples") if metadata else "Unknown",
            "feature_names": metadata.get("feature_names", []) if metadata else [],
            "target_names": metadata.get("target_names", [])
            if metadata
            else getattr(model, "classes_", []),
            # Métriques de performance (depuis metrics.json uniquement)
            "accuracy": metrics.get("accuracy") if metrics else "Unknown",
            "precision": metrics.get("precision") if metrics else "Unknown",
            "recall": metrics.get("recall") if metrics else "Unknown",
            "f1_score": metrics.get("f1_score") if metrics else "Unknown",
        }
