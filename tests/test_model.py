"""
Tests unitaires pour le modèle ML
"""

import json
import os
import tempfile

import joblib
import numpy as np
import pytest
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from src.training.train import train_model as train_iris_model


class TestModel:
    """Tests pour le modèle ML"""

    def test_model_training(self, trained_model):
        """Test de l'entraînement du modèle"""
        model, metadata = trained_model

        # Vérifications
        assert model is not None
        assert metadata is not None
        assert metadata["model_type"] == "RandomForestClassifier"
        assert len(metadata["feature_names"]) == 4
        assert len(metadata["target_names"]) == 3

        # Vérifier que metrics.json existe et contient accuracy
        metrics_path = os.path.join(os.getcwd(), "models/metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
            assert "accuracy" in metrics
            assert (
                metrics["accuracy"] > 0.8
            )  # Le modèle devrait avoir une bonne précision

    def test_model_save_load(self, trained_model):
        """Test de sauvegarde et chargement du modèle"""
        model, metadata = trained_model

        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = f.name

        try:
            # Sauvegarder
            joblib.dump(model, temp_path)

            # Vérifier que le fichier existe
            assert os.path.exists(temp_path)

            # Charger
            loaded_model = joblib.load(temp_path)
            assert loaded_model is not None

            # Vérifier que le modèle chargé fonctionne
            iris = load_iris()
            predictions = loaded_model.predict(iris.data[:5])
            assert len(predictions) == 5

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_model_prediction(self, trained_model, iris_dataset):
        """Test des prédictions du modèle"""
        model, metadata = trained_model
        X, y, feature_names, target_names = iris_dataset

        # Test sur quelques échantillons
        test_samples = X[:5]
        predictions = model.predict(test_samples)
        probabilities = model.predict_proba(test_samples)

        # Vérifications
        assert len(predictions) == 5
        assert predictions.shape[0] == test_samples.shape[0]
        assert probabilities.shape[0] == test_samples.shape[0]
        assert probabilities.shape[1] == 3  # 3 classes

        # Vérification que les probabilités somment à 1
        for prob_row in probabilities:
            assert abs(np.sum(prob_row) - 1.0) < 1e-6

        # Vérifier que les prédictions sont dans les classes valides
        assert all(pred in [0, 1, 2] for pred in predictions)

    def test_model_accuracy(self, trained_model, iris_dataset):
        """Test de la précision du modèle"""
        model, metadata = trained_model
        X, y, feature_names, target_names = iris_dataset

        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Prédiction sur le test set
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Vérification que la précision est raisonnable
        assert accuracy > 0.8

        # Vérifier que accuracy est dans metrics.json si disponible
        metrics_path = os.path.join(os.getcwd(), "models/metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
            # La précision peut varier légèrement selon le split, donc on vérifie juste qu'elle existe
            assert "accuracy" in metrics
            assert metrics["accuracy"] > 0

    def test_model_feature_importance(self, trained_model):
        """Test de l'importance des features"""
        model, metadata = trained_model

        # Vérification que le modèle a des feature importances
        assert hasattr(model, "feature_importances_")
        assert len(model.feature_importances_) == 4  # 4 features

        # Vérification que les importances sont positives et somment à 1
        importances = model.feature_importances_
        assert all(imp >= 0 for imp in importances)
        assert abs(np.sum(importances) - 1.0) < 1e-6

    def test_model_metadata_structure(self, trained_model):
        """Test de la structure des métadonnées"""
        model, metadata = trained_model

        # Vérification des clés requises dans metadata.json (sans métriques)
        required_metadata_keys = [
            "model_type",
            "n_estimators",
            "feature_names",
            "target_names",
            "n_features",
            "n_samples",
        ]

        for key in required_metadata_keys:
            assert key in metadata, f"Clé manquante dans metadata : {key}"

        # Vérification des types
        assert isinstance(metadata["model_type"], str)
        assert isinstance(metadata["n_features"], int)
        assert isinstance(metadata["n_samples"], int)
        assert isinstance(metadata["feature_names"], list)
        assert isinstance(metadata["target_names"], list)

        # Vérification des valeurs
        assert metadata["n_features"] == 4
        assert metadata["n_samples"] == 150
        assert len(metadata["feature_names"]) == 4
        assert len(metadata["target_names"]) == 3

        # Vérification de metrics.json (séparé) si disponible
        metrics_path = os.path.join(os.getcwd(), "models/metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as f:
                metrics = json.load(f)

            required_metrics_keys = ["accuracy", "precision", "recall", "f1_score"]
            for key in required_metrics_keys:
                assert key in metrics, f"Clé manquante dans metrics : {key}"
                assert isinstance(metrics[key], float)

            assert metrics["accuracy"] > 0

    def test_model_predict_proba(self, trained_model, iris_dataset):
        """Test que le modèle retourne des probabilités valides"""
        model, metadata = trained_model
        X, y, feature_names, target_names = iris_dataset

        # Test sur un échantillon
        sample = X[0:1]
        proba = model.predict_proba(sample)[0]

        # Vérifications
        assert len(proba) == 3  # 3 classes
        assert all(0 <= p <= 1 for p in proba)  # Probabilités entre 0 et 1
        assert abs(np.sum(proba) - 1.0) < 1e-6  # Somme à 1

    def test_model_consistency(self, trained_model, iris_dataset):
        """Test de cohérence du modèle (même input = même output)"""
        model, metadata = trained_model
        X, y, feature_names, target_names = iris_dataset

        # Test sur le même échantillon deux fois
        sample = X[0:1]
        pred1 = model.predict(sample)
        pred2 = model.predict(sample)

        # Les prédictions doivent être identiques
        assert pred1[0] == pred2[0]

        # Les probabilités doivent être identiques
        proba1 = model.predict_proba(sample)
        proba2 = model.predict_proba(sample)
        np.testing.assert_array_almost_equal(proba1, proba2)
