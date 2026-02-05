# Expérimentation — MLflow & DVC

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| [Infrastructure](infrastructure.md) | [Orchestration](orchestration.md) |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 📋 Table des Matières

1. [Objectif](#-objectif)
2. [Tâches à Accomplir](#-tâches-à-accomplir)
3. [Livrables Créés](#-livrables-créés)
4. [Implémentation Prévue](#-implémentation-prévue)
5. [Outils à Utiliser](#-outils-à-utiliser)
6. [Métriques Attendues](#-métriques-attendues)
7. [Ressources](#-ressources)
8. [Progression](#-progression)
9. [Objectifs de Validation](#-objectifs-de-validation)
10. [Interface MLflow](#-interface-mlflow)
11. [Pipeline DVC](#-pipeline-dvc)
12. [Implémentation Complète](#-implémentation-complète)
13. [Guide d'Utilisation](#-guide-dutilisation)
14. [Exemples d'Expériences MLflow](#-exemples-dexpériences-mlflow)
15. [Versioning des Données (DVC)](#-versioning-des-données-dvc)
16. [Résultats Attendus](#-résultats-attendus)
17. [Workflow Complet : Entraînement → Déploiement](#-workflow-complet-entraînement--déploiement)
18. [Dépannage](#-dépannage)
19. [Validation des Objectifs](#-validation-des-objectifs)

---

## 🎯 Objectif

**Traquer et versionner les expériences ML localement pour la reproductibilité**

### ❓ Questions Clés
- Comment tracer les expériences (MLflow) ?
- Comment versionner le dataset et le pipeline (DVC) ?

### ⏱️ Répartition des Heures (20h)
- **7h** → Intégrer MLflow Tracking pour logguer les hyperparamètres, métriques et le modèle
- **7h** → Implémenter DVC pour versionner le dataset et le pipeline de pré-traitement
- **6h** → Finalisation Projet 1 : documentation + vidéo démo

---

## 📋 Tâches à Accomplir

### 1. 📊 MLflow Tracking
- Intégrer MLflow dans le script d'entraînement (src/training/train.py)
- Logger les hyperparamètres et métriques
- Sauvegarder les modèles et artifacts
- Interface web MLflow UI

### 2. 🔄 DVC (Data Version Control)
- Initialiser DVC dans le projet
- Versionner le dataset Iris
- Créer un pipeline de pré-traitement
- Gérer les dépendances entre étapes

### 3. 📚 Documentation et Démo
- Rédiger un README complet
- Créer des schémas d'architecture
- Enregistrer une vidéo de démonstration
- Finaliser le Projet 1

## 📦 Livrables Créés

### Structure MLflow
```
mlruns/                    # Dossier MLflow (généré)
├── 0/                    # Experiments
│   └── runs/             # Runs individuels
└── models/               # Modèles enregistrés
```

### Structure DVC
```
.dvc/                     # Configuration DVC
├── config               # Configuration
├── cache/               # Cache des données
└── tmp/                 # Fichiers temporaires

data/                    # Données versionnées
├── raw/                 # Données brutes
├── processed/           # Données traitées
└── .gitignore          # Ignorer les gros fichiers

dvc.yaml                 # Pipeline DVC
dvc.lock                 # Verrouillage des versions
```

### Documentation
- **README.md** : Documentation complète du projet (vue d’ensemble, architecture, schémas)
- **Vidéo de démonstration** (optionnel) : 3–5 min (Loom, OBS Studio) — à enregistrer selon besoins

## 🚀 Implémentation Prévue

### MLflow Integration
```python
# src/training/train.py avec MLflow
import mlflow
import mlflow.sklearn

def train_model():
    with mlflow.start_run():
        # Log des paramètres
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        
        # Entraînement du modèle
        model = RandomForestClassifier(n_estimators=100, max_depth=10)
        model.fit(X_train, y_train)
        
        # Évaluation
        accuracy = model.score(X_test, y_test)
        mlflow.log_metric("accuracy", accuracy)
        
        # Sauvegarde du modèle
        mlflow.sklearn.log_model(model, "model")
        
        return model
```

### DVC Pipeline
```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python -m src.data.prepare
    deps:
    - data/raw/iris.csv
    outs:
    - data/processed/train.csv
    - data/processed/test.csv
    
  train:
    cmd: python -m src.training.train
    deps:
    - data/processed/train.csv
    - data/processed/test.csv
    - src/training/train.py
    - src/evaluation/evaluate.py
    outs:
    - models/metadata.json
    metrics:
    - models/metrics.json
    # Note : Le modèle ML est sauvegardé dans MLflow (mlruns/), pas dans models/
```

## 🛠️ Outils à Utiliser

### MLflow
- **Tracking** : Logging des expériences
- **Models** : Gestion des modèles
- **UI** : Interface web pour visualisation
- **Storage** : Fichier local (puis cloud)

### DVC
- **Data Versioning** : Git-like pour les données
- **Pipeline** : Orchestration des étapes
- **Cache** : Stockage efficace
- **Remote** : Stockage distant (optionnel)

### Visualisation
- **MLflow UI** : Interface web des expériences
- **DVC Plots** : Visualisation des métriques
- **Draw.io** : Schémas d'architecture

## 📊 Métriques Attendues

| Composant | Objectif |
|-----------|----------|
| **MLflow Runs** | 5+ expériences loggées |
| **DVC Pipeline** | 2+ étapes (prepare, train) |
| **Data Versioning** | Dataset et modèles versionnés |
| **Reproductibilité** | Pipeline reproductible |

## 🔗 Ressources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [DVC Documentation](https://dvc.org/doc)
- [MLflow Quickstart](https://mlflow.org/docs/latest/getting-started/index.html)
- [DVC Tutorial](https://dvc.org/doc/start)

## 📈 Progression

### Étape 1 : MLflow (7h) ✅
- [x] Installation et configuration MLflow
- [x] Intégration dans src/training/train.py
- [x] Logging des paramètres et métriques
- [x] Sauvegarde des modèles
- [x] Interface web MLflow UI

### Étape 2 : DVC (7h) ✅
- [x] Installation et initialisation DVC
- [x] Versioning du dataset
- [x] Création du pipeline dvc.yaml
- [x] Gestion des dépendances
- [x] Tests de reproductibilité

### Étape 3 : Finalisation (6h) ✅
- [x] Documentation complète
- [x] Schémas d'architecture
- [x] Vidéo de démonstration (à faire selon besoins)
- [x] Validation du Projet 1

## 🎯 Objectifs de Validation

- [x] MLflow UI accessible et fonctionnel
- [x] Expériences loggées avec paramètres/métriques
- [x] DVC pipeline reproductible
- [x] Dataset et modèles versionnés
- [x] Documentation complète
- [ ] Vidéo de démonstration enregistrée (optionnel)

## 📊 Interface MLflow

### Fonctionnalités à Implémenter
- **Experiments** : Organisation des runs
- **Runs** : Détails de chaque expérience
- **Models** : Gestion des modèles
- **Artifacts** : Fichiers associés
- **Metrics** : Graphiques des métriques

### Métriques à Logger
- **Accuracy** : Précision du modèle
- **Precision** : Précision par classe
- **Recall** : Rappel par classe
- **F1-Score** : Score F1 par classe
- **Confusion Matrix** : Matrice de confusion

## 🔄 Pipeline DVC

### Étapes du Pipeline
1. **Prepare** : Préparation des données
2. **Train** : Entraînement du modèle
3. **Evaluate** : Évaluation et métriques
4. **Deploy** : Préparation du déploiement

### Gestion des Dépendances
- **Data** : Dataset → Train/Test
- **Model** : Train → Model + Metadata
- **Metrics** : Evaluate → Metrics JSON

## 📚 Documentation à Créer

### README Principal
- Vue d'ensemble du projet
- Instructions d'installation
- Guide d'utilisation
- Architecture et schémas (voir README et docs/)

### Documentation Technique
- Configuration MLflow
- Pipeline DVC
- Procédures de déploiement
- Troubleshooting

### Vidéo de Démonstration (optionnel)
- **Durée** : 3–5 minutes
- **Contenu** : Installation, utilisation, résultats
- **Format** : Loom ou OBS Studio
- **Objectif** : Démonstration complète du parcours

---

## ✅ Implémentation Complète

### Étape 1 : MLflow Tracking ✅

#### Installation
MLflow a été ajouté aux dépendances dans `pyproject.toml` :
```toml
mlflow = "^2.9.2"
```

#### Intégration dans training/train.py
Le script `src/training/train.py` a été modifié pour intégrer MLflow :

**Fonctionnalités implémentées** :
- ✅ Tracking des hyperparamètres (n_estimators, max_depth, random_state, test_size)
- ✅ Logging des métriques globales (accuracy, precision, recall, f1-score)
- ✅ Logging des métriques par classe (precision, recall, f1-score pour chaque classe)
- ✅ Sauvegarde de la confusion matrix comme artifact
- ✅ Enregistrement du modèle via `mlflow.sklearn.log_model()`
- ✅ Sauvegarde des métadonnées comme artifact JSON

**Utilisation** :
```python
from src.training.train import train_model

# MLflow est toujours activé
model, metadata = train_model(n_estimators=100, max_depth=10)

# Le modèle est sauvegardé dans MLflow (mlruns/)
# Les métadonnées (metadata.json) contiennent l'URI MLflow pour charger le modèle
```

#### Interface MLflow UI
Lancer l'interface web :
```bash
make mlflow-ui
# Ou directement
poetry run mlflow ui --host 127.0.0.1 --port 5000
```

Accès : http://localhost:5000

**Fonctionnalités disponibles** :
- Visualisation des expériences
- Comparaison des runs
- Graphiques des métriques
- Téléchargement des modèles
- Visualisation des artifacts

### Étape 2 : DVC Pipeline ✅

#### Installation
DVC a été ajouté aux dépendances dans `pyproject.toml` :
```toml
dvc = {extras = ["gs", "s3", "azure", "oss", "ssh", "hdfs", "webdav", "gdrive"], version = "^3.41.0"}
```

#### Structure des données
```
data/
├── raw/              # Dataset brut (versionné avec DVC)
│   └── iris.csv
└── processed/        # Données traitées (générées)
    ├── train.csv
    └── test.csv
```

#### Script de préparation
Le script `src/data/prepare.py` :
- Charge le dataset Iris depuis scikit-learn
- Crée un DataFrame pandas
- Lit les paramètres depuis `params.yaml` via `src/config.py` (validation Pydantic)
- Divise en train/test avec les paramètres configurés
- Sauvegarde dans `data/raw/` et `data/processed/`

#### Configuration centralisée
Le module `src/config.py` :
- Lit et valide les paramètres depuis `params.yaml` avec Pydantic
- Validation type-safe des hyperparamètres et paramètres de données
- Valeurs par défaut si `params.yaml` est absent
- Pattern singleton pour éviter les rechargements multiples

#### Pipeline DVC
Le fichier `dvc.yaml` définit le pipeline :

**1. Prepare**
- Commande : `poetry run python -m src.data.prepare`
- Dépendances : `src/data/prepare.py`, `src/config.py`
- Paramètres : `data.test_size`, `data.random_state` (depuis `params.yaml`)
- Sorties : `data/raw/iris.csv`, `data/processed/train.csv`, `data/processed/test.csv`

**2. Train**
- Commande : `poetry run python -m src.training.train`
- Dépendances : `data/processed/train.csv`, `data/processed/test.csv`, `src/training/train.py`, `src/evaluation/evaluate.py`, `src/config.py`
- Paramètres : `train.n_estimators`, `train.max_depth`, `train.random_state`, `train.test_size` (depuis `params.yaml`)
- Sorties : `models/metadata.json` (contient l'URI MLflow pour charger le modèle)
- Métriques : `models/metrics.json`
- **Modèle ML** : Sauvegardé dans MLflow (`mlruns/`), chargé via l'URI dans `metadata.json`

#### Commandes DVC

**Initialisation** :
```bash
make dvc-init
# Ou directement
poetry run dvc init
```

**Exécution du pipeline** :
```bash
make dvc-repro
# Ou directement
poetry run dvc repro
```

**Expérimenter avec des paramètres personnalisés** :
```bash
# Tester différents paramètres sans modifier params.yaml
poetry run dvc exp run -S train.n_estimators=200 -S train.max_depth=10

# Comparer les résultats dans MLflow
make mlflow-ui
```

> **💡 Note** : `dvc repro` réexécute le pipeline avec les paramètres de `params.yaml`. Pour tester différents paramètres sans modifier le fichier, utilisez `dvc exp run -S`.

**Vérifier l'état** :
```bash
make dvc-status
# Ou directement
poetry run dvc status
```

**Visualiser le pipeline** :
```bash
make dvc-pipeline
# Ou directement
poetry run dvc dag
```

#### Workflow Standard DVC avec Git

**Principe** : DVC utilise un seul fichier `params.yaml` versionné dans Git. Les différentes configurations sont gérées via des branches Git.

**Workflow recommandé** :

1. **Créer une branche pour une nouvelle expérience** :
```bash
git checkout -b experiment/high-n-estimators
```

2. **Modifier params.yaml directement** :
```yaml
# params.yaml
data:
  test_size: 0.2
  random_state: 42

train:
  n_estimators: 200  # Modifié pour l'expérience
  max_depth: 10
```

3. **Exécuter le pipeline** :
```bash
make dvc-repro
# ou directement: dvc repro
```

4. **MLflow track automatiquement les métriques** :
```bash
# Comparer dans MLflow UI
make mlflow-ui
# Ouvrir http://localhost:5000
```

5. **Commit si résultats intéressants** :
```bash
git add params.yaml dvc.lock
git commit -m "Experiment: n_estimators=200, max_depth=10"
git push origin experiment/high-n-estimators
```

6. **Revenir à main pour une autre expérience** :
```bash
git checkout main
```

**Tests rapides sans modifier params.yaml** :

Pour des tests rapides sans créer de branche :
```bash
# Surcharger des paramètres spécifiques avec 'dvc exp run'
# Note : 'dvc repro' ne supporte pas l'option -S, utilisez 'dvc exp run' à la place
poetry run dvc exp run -S train.n_estimators=200 -S train.max_depth=10
```

> **💡 Différence entre `dvc repro` et `dvc exp run`** :
> - `dvc repro` : Réexécute le pipeline avec les paramètres actuels de `params.yaml` (pas d'option `-S`)
> - `dvc exp run` : Permet de tester différents paramètres avec `-S` sans modifier `params.yaml` (expérimentations)

**Versioning des configurations** :

- Chaque commit de `params.yaml` représente une version de configuration
- Utiliser `git log params.yaml` pour voir l'historique des expériences
- DVC suit automatiquement les changements de `params.yaml` via `dvc.lock`

**Pourquoi un seul params.yaml ?**

- ✅ Standard DVC : DVC lit toujours `params.yaml` par défaut
- ✅ Versioning clair : Git gère l'historique des configurations
- ✅ Reproductibilité : Chaque commit = configuration reproductible
- ✅ Pas de duplication : Évite la désynchronisation entre fichiers

**Alternative (non recommandée)** :

Utiliser des branches Git est la pratique recommandée pour gérer différentes configurations de paramètres.

### Étape 3 : Intégration Complète ✅

#### Configuration centralisée avec Pydantic ✅
Le module `src/config.py` a été créé pour :
- ✅ Lire et valider les paramètres depuis `params.yaml`
- ✅ Validation type-safe avec Pydantic (contraintes, types)
- ✅ Gestion d'erreurs robuste avec valeurs par défaut
- ✅ Pattern singleton pour performance
- ✅ Factorisation des paramètres communs (DRY)

#### Scripts améliorés
Les scripts `prepare.py` et `train.py` :
- ✅ Utilisent `get_config()` pour lire les paramètres depuis `params.yaml`
- ✅ Paramètres surchargeables en arguments si nécessaire
- ✅ Logging structuré pour traçabilité
- ✅ Compatible avec MLflow et DVC simultanément

#### Commandes Makefile
Nouvelles commandes ajoutées :

**MLflow** :
- `make mlflow-ui` : Lancer l'interface MLflow
- `make mlflow-experiments` : Lister les expériences

**DVC** :
- `make dvc-init` : Initialiser DVC
- `make dvc-repro` : Réexécuter le pipeline
- `make dvc-status` : Vérifier l'état
- `make dvc-push` : Pousser les données (si remote configuré)
- `make dvc-pull` : Télécharger les données
- `make dvc-pipeline` : Afficher le pipeline

## 🚀 Guide d'Utilisation

### Workflow Complet

#### 1. Installation
```bash
# Installer les dépendances (inclut MLflow et DVC)
make install
```

#### 2. Préparer les données (DVC)
```bash
# Exécuter l'étape prepare du pipeline
poetry run dvc repro prepare

# Ou exécuter directement
poetry run python -m src.data.prepare
```

#### 3. Entraîner le modèle avec MLflow
```bash
# Entraîner avec tracking MLflow
make train

# Ou avec des hyperparamètres personnalisés
poetry run python -c "
from src.training.train import train_model
train_model(n_estimators=150, max_depth=15)
"
```

#### 4. Visualiser les résultats
```bash
# Lancer MLflow UI
make mlflow-ui

# Ouvrir http://localhost:5000 dans le navigateur
```

#### 5. Exécuter le pipeline complet (DVC)
```bash
# Exécuter toutes les étapes
make dvc-repro

# Vérifier l'état
make dvc-status
```

### Exemples d'Expériences MLflow

#### Expérience 1 : Modèle de base
```bash
poetry run python -c "
from src.training.train import train_model
train_model(n_estimators=100, max_depth=None)
"
```

#### Expérience 2 : Modèle avec profondeur limitée
```bash
poetry run python -c "
from src.training.train import train_model
train_model(n_estimators=100, max_depth=5)
"
```

#### Expérience 3 : Plus d'arbres
```bash
poetry run python -c "
from src.training.train import train_model
train_model(n_estimators=200, max_depth=10)
"
```

### Versioning des Données (DVC)

#### Ajouter des données au tracking
```bash
# Ajouter le dataset brut
poetry run dvc add data/raw/iris.csv

# Commit dans Git
git add data/raw/iris.csv.dvc .gitignore
git commit -m "Add iris dataset"
```

#### Changer de version de données
```bash
# Modifier les données
# ...

# Mettre à jour DVC
poetry run dvc add data/raw/iris.csv

# Commit
git add data/raw/iris.csv.dvc
git commit -m "Update dataset version"
```

## 📊 Résultats Attendus

### MLflow
- ✅ Expériences loggées dans `mlruns/`
- ✅ Modèles enregistrés et versionnés
- ✅ Métriques tracées et comparables
- ✅ Interface web fonctionnelle

### DVC
- ✅ Pipeline reproductible
- ✅ Données versionnées
- ✅ Dépendances gérées automatiquement
- ✅ Cache pour accélérer les réexécutions

## 🚀 Workflow Complet : Entraînement → Déploiement

### 1. Entraînement Local

```bash
# 1. Entraîner le modèle localement
make train

# 2. Vérifier les fichiers générés
ls -la models/
# - metadata.json (contient mlflow_run_id, mlflow_run_uri, etc.)
# - metrics.json

# 3. Vérifier MLflow local
ls -la mlruns/
# Structure : mlruns/<experiment_id>/<run_id>/artifacts/model/
```

### 2. Créer les Ressources GCP

> ⚠️ **Important** : Créer d'abord les ressources GCP (bucket, VM, etc.) avant d'uploader les fichiers.

```bash
# 1. Configurer Terraform (voir docs/infrastructure.md pour les détails)
make terraform-init
# ou directement
terraform -chdir=terraform init

make terraform-plan
# ou directement
terraform -chdir=terraform plan

make terraform-apply
# ou directement
terraform -chdir=terraform apply

# 2. Récupérer le nom du bucket créé
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)
```

### 3. Uploader les Fichiers vers GCS

```bash
# 1. Identifier le run_id à déployer
cat models/metadata.json | grep mlflow_run_id

# 2. Uploader mlruns/ vers GCS (⚠️ IMPORTANT : inclure le run spécifique)
# Utiliser gcloud storage (recommandé par Google, plus moderne que gsutil)
gcloud storage cp -r mlruns/ gs://$BUCKET_NAME/

# 3. Note: models/metadata.json et models/metrics.json sont inclus dans l'image Docker
#    Ils sont versionnés avec Git via DVC et n'ont pas besoin d'être uploadés séparément
#    Le modèle est chargé depuis MLflow via GCS en utilisant mlflow_run_id depuis metadata.json

# 4. Vérifier
gcloud storage ls gs://$BUCKET_NAME/
gcloud storage ls gs://$BUCKET_NAME/mlruns/
```

### 4. Déploiement sur la VM

```bash
# 1. Note: models/metadata.json et models/metrics.json sont inclus dans l'image Docker
#    Ils sont versionnés avec Git via DVC et n'ont pas besoin d'être téléchargés
#    Le modèle est chargé depuis MLflow via GCS en utilisant mlflow_run_id depuis metadata.json

# 2. MLFLOW_TRACKING_URI est configuré automatiquement par Terraform
# (variable d'environnement passée au conteneur Docker)

# 3. L'API charge automatiquement le modèle via runs:/<run_id>/model
# MLflow télécharge temporairement depuis GCS dans son cache (~/.mlflow/cache)
```

**Comment ça fonctionne** :
- `metadata.json` contient `mlflow_run_id`
- L'API construit `runs:/<run_id>/model`
- MLflow résout automatiquement vers GCS grâce à `MLFLOW_TRACKING_URI`
- Le modèle est téléchargé temporairement dans le cache MLflow
- Pas besoin de copier manuellement le modèle sur la VM

## 🔍 Dépannage

### MLflow UI ne démarre pas
```bash
# Vérifier que MLflow est installé
poetry run mlflow --version

# Vérifier le port 5000
lsof -i :5000

# Utiliser un autre port
poetry run mlflow ui --port 5001
```

### Configuration MLflow pour développement local

**Sans Docker** :
```bash
make train  # MLflow utilise mlruns/ local
```

**Avec Docker Compose** :
```bash
make train           # Entraîner sur l'hôte
docker compose up    # Conteneur accède à mlruns/ via volume monté
```

**Production avec GCS** :
```bash
# ⚠️ ÉTAPE 1 : Créer les ressources GCP d'abord (Terraform)
# terraform apply

# ⚠️ ÉTAPE 2 : Uploader mlruns/ vers GCS (après création du bucket)
# Utiliser gcloud storage (recommandé par Google, plus moderne que gsutil)
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)
gcloud storage cp -r mlruns/ gs://$BUCKET_NAME/

# ⚠️ ÉTAPE 3 : MLFLOW_TRACKING_URI est configuré automatiquement par Terraform
# L'API chargera automatiquement depuis GCS via run_id dans metadata.json
# MLflow télécharge temporairement le modèle dans son cache (~/.mlflow/cache)
# Format utilisé : runs:/<run_id>/model (résolu automatiquement vers GCS)
```

**Comment ça fonctionne** :
- L'API utilise `runs:/<run_id>/model` depuis `metadata.json`
- MLflow résout automatiquement vers GCS grâce à `MLFLOW_TRACKING_URI`
- Le modèle est téléchargé temporairement dans le cache MLflow (`~/.mlflow/cache`)
- Pas besoin de copier manuellement le modèle sur la VM

**Alternative : MLflow Tracking Server** :
```bash
# Déployer un serveur MLflow (Cloud Run, VM, etc.)
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)
mlflow server --backend-store-uri gs://$BUCKET_NAME/mlruns/ --default-artifact-root gs://$BUCKET_NAME/mlruns/

# Configurer l'URI
export MLFLOW_TRACKING_URI="http://mlflow-server:5000"
```

### Le modèle n'est pas trouvé dans Docker

```bash
# Vérifier que le modèle existe
ls -la mlruns/

# Redémarrer le conteneur
docker compose down && docker compose up
```

### DVC pipeline échoue
```bash
# Vérifier que les dépendances existent
poetry run dvc status

# Nettoyer et réexécuter
poetry run dvc repro --force
```

### Données non trouvées
```bash
# Vérifier que prepare a été exécuté
ls -la data/processed/

# Réexécuter prepare
poetry run dvc repro prepare
```

## ✅ Validation des Objectifs

| Objectif | Status | Détails |
|----------|--------|---------|
| **MLflow Tracking** | ✅ | Intégration complète avec logging paramètres/métriques |
| **MLflow UI** | ✅ | Interface web fonctionnelle |
| **DVC Pipeline** | ✅ | Pipeline à 2 étapes (prepare, train) |
| **Versioning Données** | ✅ | Dataset versionné avec DVC |
| **Reproductibilité** | ✅ | Pipeline reproductible |
| **Documentation** | ✅ | Guide complet dans ce fichier |

---

**Expérimentation terminée avec succès.**

Le projet dispose maintenant de :
- ✅ Tracking complet des expériences ML avec MLflow
- ✅ Versioning des données et pipeline reproductible avec DVC
- ✅ Documentation complète et guide d'utilisation

Le Projet 1 est maintenant finalisé et prêt pour la démonstration !
