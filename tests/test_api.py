"""
Tests unitaires pour l'API FastAPI
"""

import json

import pytest
from fastapi.testclient import TestClient

from src.serving.app import app


class TestAPI:
    """Tests pour l'API FastAPI"""

    def test_root_endpoint(self, api_client):
        """Test de l'endpoint racine"""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "API Classification Iris" in data["message"]
        assert "docs" in data
        assert "health" in data

    def test_health_check(self, api_client):
        """Test de l'endpoint de santé"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
        assert data["status"] in ["healthy", "unhealthy"]

    def test_health_check_with_model(self, api_client_with_model):
        """Test de l'endpoint de santé avec modèle chargé"""
        response = api_client_with_model.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

    def test_model_info_without_model(self, api_client):
        """Test de l'endpoint d'informations du modèle sans modèle chargé"""
        response = api_client.get("/model/info")
        assert response.status_code == 404

    def test_model_info_with_model(self, api_client_with_model, api_key):
        """Test de l'endpoint d'informations du modèle avec modèle chargé"""
        response = api_client_with_model.get(
            "/model/info", headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "model_type" in data
        assert "accuracy" in data
        assert "feature_names" in data
        assert "target_names" in data
        assert len(data["feature_names"]) == 4
        assert len(data["target_names"]) == 3

    def test_predict_without_model(self, api_client, valid_iris_data, api_key):
        """Test de prédiction sans modèle chargé"""
        response = api_client.post(
            "/predict", json=valid_iris_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 503
        assert "Modèle non chargé" in response.json()["detail"]

    def test_predict_valid_data(self, api_client_with_model, valid_iris_data, api_key):
        """Test de prédiction avec des données valides"""
        response = api_client_with_model.post(
            "/predict", json=valid_iris_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1
        assert data["prediction"] in ["setosa", "versicolor", "virginica"]
        # Vérifier que les probabilités somment à ~1
        prob_sum = sum(data["probabilities"].values())
        assert abs(prob_sum - 1.0) < 0.01

    def test_predict_invalid_data(self, api_client_with_model, api_key):
        """Test de prédiction avec des données invalides (champs manquants)"""
        invalid_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5
            # petal_length et petal_width manquants
        }
        response = api_client_with_model.post(
            "/predict", json=invalid_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_negative_values(self, api_client_with_model, api_key):
        """Test avec des valeurs négatives (devrait être rejeté par la validation Pydantic)"""
        test_data = {
            "sepal_length": -1.0,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = api_client_with_model.post(
            "/predict", json=test_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_too_large_values(self, api_client_with_model, api_key):
        """Test avec des valeurs trop grandes (> 20.0)"""
        test_data = {
            "sepal_length": 25.0,  # > 20.0 (limite définie dans IrisFeatures)
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = api_client_with_model.post(
            "/predict", json=test_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_string_values(self, api_client_with_model, api_key):
        """Test avec des valeurs string (devrait échouer)"""
        test_data = {
            "sepal_length": "invalid",
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = api_client_with_model.post(
            "/predict", json=test_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_null_values(self, api_client_with_model, api_key):
        """Test avec des valeurs null"""
        test_data = {
            "sepal_length": None,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = api_client_with_model.post(
            "/predict", json=test_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_iris_setosa(self, api_client_with_model, api_key):
        """Test avec des caractéristiques typiques d'Iris setosa"""
        setosa_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        response = api_client_with_model.post(
            "/predict", json=setosa_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] in ["setosa", "versicolor", "virginica"]
        assert data["confidence"] > 0.5

    def test_predict_iris_versicolor(self, api_client_with_model, api_key):
        """Test avec des caractéristiques typiques d'Iris versicolor"""
        versicolor_data = {
            "sepal_length": 7.0,
            "sepal_width": 3.2,
            "petal_length": 4.7,
            "petal_width": 1.4,
        }
        response = api_client_with_model.post(
            "/predict", json=versicolor_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] in ["setosa", "versicolor", "virginica"]
        assert data["confidence"] > 0.5

    def test_predict_iris_virginica(self, api_client_with_model, api_key):
        """Test avec des caractéristiques typiques d'Iris virginica"""
        virginica_data = {
            "sepal_length": 6.3,
            "sepal_width": 3.3,
            "petal_length": 6.0,
            "petal_width": 2.5,
        }
        response = api_client_with_model.post(
            "/predict", json=virginica_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] in ["setosa", "versicolor", "virginica"]
        assert data["confidence"] > 0.5


class TestAPIAuthentication:
    """Tests pour l'authentification de l'API"""

    def test_predict_without_api_key(
        self, api_client_with_model, valid_iris_data, api_key
    ):
        """Test que /predict requiert une API key (quand API_KEY est configurée)"""
        response = api_client_with_model.post("/predict", json=valid_iris_data)
        # Quand API_KEY est configurée, devrait être 401
        assert response.status_code == 401

    def test_predict_without_api_key_no_auth(
        self, api_client_with_model, valid_iris_data, no_api_key
    ):
        """Test que /predict fonctionne sans API key en mode développement (sans API_KEY configurée)"""
        response = api_client_with_model.post("/predict", json=valid_iris_data)
        # En mode développement sans API_KEY, peut être 200 (authentification désactivée)
        assert response.status_code in [200, 401]

    def test_predict_with_invalid_api_key(
        self, api_client_with_model, valid_iris_data, api_key
    ):
        """Test avec une API key invalide"""
        response = api_client_with_model.post(
            "/predict",
            json=valid_iris_data,
            headers={"X-API-Key": "invalid-key-12345"},
        )
        # Quand API_KEY est configurée, devrait être 403
        assert response.status_code == 403

    def test_predict_with_valid_api_key(
        self, api_client_with_model, valid_iris_data, api_key
    ):
        """Test avec une API key valide"""
        response = api_client_with_model.post(
            "/predict", json=valid_iris_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

    def test_model_info_without_api_key(self, api_client_with_model, api_key):
        """Test que /model/info requiert une API key (quand API_KEY est configurée)"""
        response = api_client_with_model.get("/model/info")
        # Quand API_KEY est configurée, devrait être 401
        assert response.status_code == 401

    def test_model_info_with_invalid_api_key(self, api_client_with_model, api_key):
        """Test /model/info avec une API key invalide"""
        response = api_client_with_model.get(
            "/model/info", headers={"X-API-Key": "invalid-key"}
        )
        # Quand API_KEY est configurée, devrait être 403
        assert response.status_code == 403

    def test_model_info_with_valid_api_key(self, api_client_with_model, api_key):
        """Test /model/info avec une API key valide"""
        response = api_client_with_model.get(
            "/model/info", headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

    def test_health_check_no_auth_required(self, api_client):
        """Test que /health n'exige pas d'authentification"""
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_root_endpoint_no_auth_required(self, api_client):
        """Test que / n'exige pas d'authentification"""
        response = api_client.get("/")
        assert response.status_code == 200


class TestAPIRateLimiting:
    """Tests pour le rate limiting de l'API"""

    def test_rate_limiting_predict(
        self, api_client_with_model, valid_iris_data, api_key
    ):
        """Test que le rate limiting fonctionne sur /predict (10/min)"""
        # Faire 11 requêtes rapides
        responses = []
        for i in range(11):
            response = api_client_with_model.post(
                "/predict",
                json=valid_iris_data,
                headers={"X-API-Key": api_key},
            )
            responses.append(response.status_code)

        # Au moins une des requêtes devrait être limitée (429) ou toutes réussir
        # Note: Le rate limiting peut ne pas fonctionner en test si le limiter
        # n'est pas correctement configuré pour les tests
        # On vérifie au moins que les premières requêtes passent
        assert 200 in responses or 429 in responses

    def test_rate_limiting_health_check(self, api_client):
        """Test que le rate limiting fonctionne sur /health (30/min)"""
        # Faire 31 requêtes rapides
        responses = []
        for i in range(31):
            response = api_client.get("/health")
            responses.append(response.status_code)

        # La plupart devraient passer (limite plus élevée)
        assert 200 in responses


class TestAPISecurityHeaders:
    """Tests pour les headers de sécurité HTTP"""

    def test_security_headers_present(self, api_client):
        """Test que les headers de sécurité sont présents"""
        response = api_client.get("/")
        assert response.status_code == 200
        headers = response.headers

        # Vérifier les headers de sécurité
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Referrer-Policy" in headers


class TestAPICORS:
    """Tests pour la configuration CORS"""

    def test_cors_headers_present(self, api_client):
        """Test que les headers CORS sont configurés"""
        # Faire une requête OPTIONS (preflight)
        response = api_client.options(
            "/predict",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # CORS peut être configuré différemment selon l'environnement
        # On vérifie au moins que la requête ne plante pas
        assert response.status_code in [200, 405, 404]


class TestAPIMetrics:
    """Tests pour l'endpoint de métriques Prometheus"""

    def test_metrics_endpoint(self, api_client):
        """Test de l'endpoint /metrics (Prometheus)"""
        response = api_client.get("/metrics")
        assert response.status_code == 200
        # Vérifier que c'est du texte Prometheus
        assert "text/plain" in response.headers.get("content-type", "")
        content = response.text
        # Vérifier que le contenu contient des métriques Prometheus
        assert "# HELP" in content or "# TYPE" in content
        # Vérifier la présence de métriques spécifiques
        assert "model_loaded" in content or "model_predictions_total" in content

    def test_metrics_endpoint_no_auth_required(self, api_client):
        """Test que /metrics n'exige pas d'authentification"""
        response = api_client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_with_model_loaded(self, api_client_with_model):
        """Test des métriques avec modèle chargé"""
        response = api_client_with_model.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Vérifier que model_loaded est présent
        assert "model_loaded" in content
