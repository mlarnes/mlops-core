# Serving & Containerisation — API FastAPI + Docker

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| - | [CI/CD](cicd.md) |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 📋 Table des Matières

1. [Objectif](#-objectif)
2. [Tâches à Accomplir](#-tâches-à-accomplir)
3. [Livrables Créés](#-livrables-créés)
4. [Fonctionnalités Implémentées](#-fonctionnalités-implémentées)
5. [Compétences Développées](#-compétences-développées)
6. [Instructions de Démarrage](#-instructions-de-démarrage)
7. [Métriques](#-métriques)
8. [Liens Utiles](#-liens-utiles)
9. [Validation des Objectifs](#-validation-des-objectifs)
10. [Prochaines étapes](#-prochaines-étapes-cicd)

---

## 🎯 Objectif

**Conteneuriser et exposer un modèle ML localement via API + premiers tests unitaires**

### ❓ Questions Clés
- Comment dockeriser l'application ML ?
- Comment exposer l'inférence via une API performante ?
- Comment mettre en place les premiers tests de validation ?

### ⏱️ Répartition des Heures (20h)
- **7h** → Docker (concepts, commandes) + création Dockerfile
- **7h** → Implémentation d'une API FastAPI (modèle ML)
- **6h** → Écrire et exécuter les premiers tests unitaires avec pytest

---

## 📋 Tâches à Accomplir

### 1. 🤖 Entraînement du Modèle ML
- Choisir un algorithme de classification
- Utiliser le dataset Iris (scikit-learn)
- Entraîner et évaluer le modèle
- Sauvegarder le modèle et ses métadonnées

### 2. 🚀 API FastAPI
- Créer une API REST avec FastAPI
- Implémenter les endpoints nécessaires
- Ajouter la validation des données (Pydantic)
- Configurer la documentation automatique

### 3. 🐳 Docker
- Créer un Dockerfile optimisé
- Configurer docker-compose pour le développement
- Implémenter les health checks
- Optimiser la taille de l'image

### 4. 🧪 Tests
- Écrire des tests unitaires pour l'API
- Écrire des tests pour le modèle ML
- Configurer pytest
- Intégrer les tests dans le workflow de développement

---

## 📦 Livrables Créés

### Structure du Projet
```
mlops-core/
├── src/
│   ├── config.py             # Configuration centralisée
│   ├── data/
│   │   └── prepare.py        # Préparation des données
│   ├── training/
│   │   └── train.py          # Entraînement du modèle
│   ├── evaluation/
│   │   └── evaluate.py       # Évaluation du modèle
│   └── serving/
│       ├── app.py            # Application principale
│       ├── lifespan.py       # Chargement/déchargement du modèle
│       ├── routes.py         # Endpoints API
│       ├── models.py         # Modèles Pydantic
│       ├── metrics.py        # Métriques Prometheus
│       ├── middleware.py     # Rate limiting, etc.
│       └── security.py       # Authentification API
├── pyproject.toml            # Configuration Poetry
├── Dockerfile                # Image Docker optimisée
├── docker-compose.yml        # Orchestration Docker
├── .dockerignore            # Optimisation des builds
│
├── tests/                    # Tests unitaires
│   ├── __init__.py
│   ├── test_api.py          # Tests de l'API
│   └── test_model.py        # Tests du modèle
│
├── scripts/                  # Scripts utilitaires
│   ├── setup.sh             # Installation Poetry
│   └── validate_project.sh  # Validation du projet
│
└── models/                   # Métadonnées du modèle (générées)
    ├── metadata.json         # Contient l'URI MLflow pour charger le modèle
    └── metrics.json          # Métriques de performance
# Note : Le modèle ML est sauvegardé dans MLflow (mlruns/), chargé via l'URI dans metadata.json
```

### Fichiers Principaux

#### `src/serving/app.py` - API FastAPI
- **Endpoints** : 4 endpoints métier + `/metrics` (Prometheus) et `/docs` (Swagger)
  - `GET /` : Informations générales
  - `GET /health` : État de santé de l'API
  - `POST /predict` : Prédiction de la classe d'iris
  - `GET /model/info` : Informations sur le modèle
  - `GET /metrics` : Métriques Prometheus
  - `GET /docs` : Documentation Swagger interactive
- **Validation** : Modèles Pydantic pour les données d'entrée
- **Documentation** : Swagger UI (`/docs`) et ReDoc (`/redoc`)
- **Gestion d'erreurs** : Codes HTTP appropriés (400, 503, etc.)

#### `src/training/train.py` - Script d'Entraînement
- **Algorithme** : RandomForestClassifier (paramétrable via `params.yaml`)
- **Hyperparamètres par défaut** : `n_estimators=200`, `max_depth=10` (alignés avec `params.yaml` et le `README`)
- **Dataset** : Iris (scikit-learn)
- **Métriques** : Précision, classification report
- **Sauvegarde** : Modèle dans MLflow + métadonnées (metadata.json) + métriques (metrics.json)
- **Précision typique** : ~95%

#### `Dockerfile` - Image Docker
- **Base** : Python 3.11-slim
- **Gestionnaire** : Poetry 1.7.1
- **Optimisations** :
  - Installation des dépendances système minimales
  - Cache des dépendances Poetry
  - Multi-stage build (concepts)
  - Variables d'environnement optimisées
- **Health check** : Vérification automatique de l'API
- **Port** : 8000 exposé

#### `docker-compose.yml` - Orchestration
- **Service** : iris-api
- **Ports** : 127.0.0.1:8000:8000
- **Note** : models/metadata.json et models/metrics.json sont inclus dans l'image Docker (pas de volume nécessaire)
- **Health check** : Vérification toutes les 30s
- **Restart** : unless-stopped

### Tests

#### `tests/test_api.py` - Tests API
- Tests de tous les endpoints
- Tests de validation des données
- Tests de gestion d'erreurs
- Tests avec données limites

#### `tests/test_model.py` - Tests Modèle
- Test d'entraînement du modèle
- Test de prédiction
- Test de métadonnées
- Vérification de la précision

### Automatisation

#### `Makefile` - Commandes Automatisées
- **Installation** : `make install`, `make dev-setup`
- **Modèle** : `make train`
- **Tests** : `make test`
- **API** : `make run`, `make run-prod`
- **Docker** : `make build`, `make run-docker`, `make stop-docker`
- **Qualité** : `make format`, `make lint`
- **Nettoyage** : `make clean`, `make clean-models`

#### Scripts Utilitaires
- **`scripts/setup.sh`** : Installation automatique de Poetry
- **`scripts/validate_project.sh`** : Validation complète du projet

---

## ✅ Fonctionnalités Implémentées

### API FastAPI
- ✅ Endpoint racine avec informations générales
- ✅ Endpoint de santé (`/health`) avec vérification du modèle
- ✅ Endpoint de prédiction (`/predict`) avec validation Pydantic
- ✅ Endpoint d'informations modèle (`/model/info`)
- ✅ Documentation interactive (Swagger UI + ReDoc)
- ✅ Validation des données d'entrée
- ✅ Gestion d'erreurs robuste avec codes HTTP appropriés
- ✅ Lifespan events pour chargement/déchargement du modèle

### Modèle ML
- ✅ RandomForestClassifier sur dataset Iris
- ✅ Division train/test (80/20) avec stratification
- ✅ Évaluation avec métriques complètes
- ✅ Sauvegarde du modèle dans MLflow
- ✅ Sauvegarde des métadonnées (JSON)
- ✅ Précision typique ~95%

### Docker
- ✅ Dockerfile optimisé avec Python 3.11-slim
- ✅ Installation automatique de Poetry
- ✅ Gestion des dépendances avec cache
- ✅ Variables d'environnement configurées
- ✅ Health check intégré
- ✅ docker-compose pour développement
- ✅ .dockerignore pour optimiser les builds

### Tests
- ✅ Tests unitaires pour l'API (pytest + TestClient)
- ✅ Tests unitaires pour le modèle ML
- ✅ Tests de validation des données
- ✅ Tests de gestion d'erreurs
- ✅ Configuration pytest dans pyproject.toml
- ✅ Couverture : API + Modèle ML

---

## 🎓 Compétences Développées

### Docker
- ✅ Création de Dockerfile optimisé
- ✅ Gestion des dépendances système
- ✅ Variables d'environnement
- ✅ Health checks
- ✅ Multi-stage builds (concepts)
- ✅ Optimisation de la taille d'image

### FastAPI
- ✅ API REST moderne avec FastAPI
- ✅ Validation Pydantic des données
- ✅ Documentation automatique (OpenAPI)
- ✅ Gestion d'erreurs HTTP
- ✅ Lifespan events (startup/shutdown)
- ✅ Modèles de réponse structurés

### Tests
- ✅ Tests unitaires avec pytest
- ✅ Tests d'intégration API
- ✅ Utilisation de TestClient FastAPI
- ✅ Tests de validation
- ✅ Configuration pytest

### Poetry
- ✅ Gestion des dépendances avec Poetry
- ✅ Environnements virtuels
- ✅ Configuration pyproject.toml
- ✅ Groupes de dépendances (dev)
- ✅ Scripts personnalisés

---

## 🚀 Instructions de Démarrage

### Prérequis
- Python 3.11+
- Docker (optionnel)
- Git

### Installation Rapide

```bash
# 1. Cloner le projet
git clone <votre-repo>
cd mlops-core

# 2. Installation automatique (Poetry + dépendances)
make install

# 3. Entraîner le modèle
make train

# 4. Lancer l'API en mode développement
make run
```

### Avec Docker

```bash
# Build de l'image
make build
# ou
docker build -t iris-api:latest .

# Pour production (linux/amd64 - compatible partout)
docker build --platform linux/amd64 -t iris-api:latest .

# Lancer avec Docker
make run-docker
# ou
docker run -p 127.0.0.1:8000:8000 iris-api:latest

# Avec Docker Compose
docker compose up --build
```

### Vérification

```bash
# Tests
make test

# Validation complète
./scripts/validate_project.sh

# Vérifier la santé de l'API
make health
# ou
curl http://localhost:8000/health
```

### Accès à l'API

Une fois l'API lancée, accédez à :
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/docs
- **Documentation ReDoc** : http://localhost:8000/redoc
- **Health Check** : http://localhost:8000/health

### Exemple d'Utilisation

```bash
# Test de prédiction
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "sepal_length": 5.1,
       "sepal_width": 3.5,
       "petal_length": 1.4,
       "petal_width": 0.2
     }'
```

---

## 📊 Métriques

| Métrique | Valeur |
|----------|--------|
| **Fichiers créés** | 20+ |
| **Lignes de code** | ~1000+ |
| **Tests unitaires** | 15+ |
| **Endpoints API** | 4 |
| **Commandes Make** | 20+ |
| **Scripts utilitaires** | 2 |
| **Précision modèle** | ~95% |

---

## 🔗 Liens Utiles

- **API Documentation** : http://localhost:8000/docs
- **Health Check** : http://localhost:8000/health
- **ReDoc** : http://localhost:8000/redoc

### Ressources Externes
- [FastAPI Documentation](https://fastapi.tiangolo.com/fr/)
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [pytest Documentation](https://docs.pytest.org/)
- [scikit-learn Iris Dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_iris.html)
- [Poetry Documentation](https://python-poetry.org/docs/)

---

## ✅ Validation des Objectifs

| Objectif | Status | Détails |
|----------|--------|---------|
| **Docker** | ✅ | Dockerfile optimisé + docker-compose + health checks |
| **FastAPI** | ✅ | API complète avec 4 endpoints, validation et documentation |
| **Tests** | ✅ | Suite de tests robuste avec pytest (API + Modèle) |
| **Documentation** | ✅ | README complet + documentation API interactive |
| **Automatisation** | ✅ | Makefile avec 20+ commandes + scripts utilitaires |
| **Modèle ML** | ✅ | RandomForestClassifier avec ~95% précision |

---

## 🚀 Prochaines étapes : CI/CD

- 🔄 CI/CD avec GitHub Actions
- 🔧 Intégration des tests dans le pipeline
- 📦 Build et push automatique des images Docker
- 🏷️ Tagging et versioning automatique
- 🔍 Linting automatique (flake8, black, isort)

---

**Serving & Containerisation terminé avec succès.**

Tous les objectifs sont atteints et le projet est prêt pour la suite (CI/CD).
