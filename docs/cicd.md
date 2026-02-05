# CI/CD — Automatisation avec GitHub Actions

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| [Serving & Containerisation](serving-containerisation.md) | [Infrastructure](infrastructure.md) |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 📋 Table des Matières

1. [Objectif](#-objectif)
2. [Tâches à Accomplir](#-tâches-à-accomplir)
3. [Livrables Créés](#-livrables-créés)
4. [Fonctionnalités Implémentées](#-fonctionnalités-implémentées)
5. [Configuration du Pipeline CI/CD](#-configuration-du-pipeline-cicd)
6. [Structure du Pipeline](#-structure-du-pipeline)
7. [Gestion des Tags Docker](#-gestion-des-tags-docker)
8. [Tester Localement](#-tester-localement)
9. [Dépannage](#-dépannage)
10. [Commandes Utiles GitHub CLI](#-commandes-utiles-github-cli)
11. [Outils Utilisés](#-outils-utilisés)
12. [Métriques](#-métriques)
13. [Ressources](#-ressources)
14. [Validation des Objectifs](#-validation-des-objectifs)
15. [Prochaines étapes](#-prochaines-étapes-infrastructure)

---

## 🎯 Objectif

**Automatiser le processus de build/test/push de l'image Docker sur push GitHub**

### ❓ Questions Clés
- Comment garantir la validation du code avant le build ?
- Comment automatiser le build et le push vers un registre ?
- Comment intégrer le linting dans le pipeline ?

### ⏱️ Répartition des Heures (20h)
- **8h** → Concevoir et écrire un workflow GitHub Actions pour CI
- **8h** → Intégrer : run tests → build image → push image (Docker Hub)
- **4h** → Ajouter un linter (flake8, black, isort) au pipeline

---

## 📋 Tâches à Accomplir

### 1. 🔧 Workflow GitHub Actions
- Créer le workflow YAML pour GitHub Actions
- Configurer les triggers (push, pull request)
- Configurer l'authentification au registre Docker Hub
- Intégrer les tests unitaires et le linting

### 2. 🐳 Build et Push Docker
- Automatiser le build de l'image Docker
- Configurer le push vers Docker Hub
- Gérer les tags et versions automatiques
- Optimiser avec le cache Docker

### 3. 🧪 Intégration des Tests
- Exécution automatique des tests à chaque push
- Validation de la qualité du code
- Reporting des résultats

### 4. 🔍 Linting et Qualité
- Configuration de flake8
- Configuration de black (formatage)
- Configuration de isort (imports)
- Intégration dans le pipeline CI

---

## 📦 Livrables Créés

### Structure des Fichiers
```
.github/
└── workflows/
    └── ci.yml              # Workflow GitHub Actions complet

.dockerignore              # Optimisation builds Docker (amélioré)
pyproject.toml             # Dépendances dev ajoutées (flake8, black, isort)
```

### Fichiers Créés

#### `.github/workflows/ci.yml` - Workflow CI/CD
Pipeline complet avec 3 jobs séquentiels :

**Job 1 : `test`** - Tests et Linting
- Checkout du code
- Setup Python 3.11 avec cache
- Installation de Poetry
- Linting avec flake8
- Vérification du formatage (Black + isort)
- Exécution des tests pytest

**Job 2 : `docker`** - Build et Push Docker
- Setup Docker Buildx
- Login vers Docker Hub (via secrets GitHub)
- Extraction des metadata et tags
- Build avec cache optimisé
- Push automatique vers Docker Hub

**Job 3 : `summary`** - Résumé du Pipeline
- Affichage des résultats de tous les jobs
- Statut global du pipeline
- Rapport dans GitHub Actions

#### `pyproject.toml` - Dépendances Dev
Ajout des dépendances de développement :
- `flake8` : Linting Python
- `black` : Formatage automatique
- `isort` : Organisation des imports
- Configuration des outils dans pyproject.toml

---

## ✅ Fonctionnalités Implémentées

### Workflow CI/CD
- ✅ Déclenchement automatique sur push/PR vers `main` ou `develop`
- ✅ 3 jobs séquentiels : test → docker → summary
- ✅ Gestion des secrets Docker Hub via GitHub Secrets
- ✅ Tags automatiques intelligents :
  - Date + SHA : `2024-11-14-abc123def456`
  - SHA court : `abc123d`
  - Branche : `main` ou `develop`
  - Pull Request : `pr-123`
- ✅ Cache Docker Registry pour accélérer les builds
- ✅ Build conditionnel (push uniquement sur main/develop)
- ✅ Rapport de résumé en fin de pipeline

### Tests et Linting
- ✅ Tests automatiques à chaque push (pytest)
- ✅ Linting avec flake8 (règles strictes)
- ✅ Vérification du formatage avec Black
- ✅ Vérification de l'organisation des imports avec isort
- ✅ Cache des dépendances Python pour accélérer les builds

### Docker
- ✅ Build automatique de l'image Docker
- ✅ Push automatique vers Docker Hub
- ✅ Cache Docker optimisé (buildcache)
- ✅ Multi-platform support (via Buildx)

---

## 🚀 Configuration du Pipeline CI/CD

### Prérequis
- Repository GitHub
- Compte Docker Hub (gratuit)
- Accès aux paramètres du repository GitHub

### Étape 1 : Créer un Personal Access Token sur Docker Hub

1. Allez sur [Docker Hub](https://hub.docker.com/)
2. Connectez-vous à votre compte
3. Allez dans **Account Settings** > **Security**
4. Cliquez sur **New Access Token**
5. Donnez un nom à votre token (ex: `github-actions`)
6. **Copiez le token** (⚠️ il ne sera affiché qu'une seule fois !)

### Étape 2 : Configurer les Secrets GitHub

1. Allez sur votre repository GitHub
2. Cliquez sur **Settings** > **Secrets and variables** > **Actions**
3. Cliquez sur **New repository secret**
4. Ajoutez les deux secrets suivants :

#### Secret 1 : `DOCKERHUB_USERNAME`
- **Name** : `DOCKERHUB_USERNAME`
- **Value** : Votre nom d'utilisateur Docker Hub (ex: `monusername`)

#### Secret 2 : `DOCKERHUB_TOKEN`
- **Name** : `DOCKERHUB_TOKEN`
- **Value** : Le token que vous venez de créer sur Docker Hub

### Étape 3 : Vérifier la Configuration

Une fois les secrets configurés :

1. Faites un commit sur la branche `main` ou `develop`
2. Allez dans l'onglet **Actions** de votre repository GitHub
3. Vérifiez que le workflow "CI/CD Pipeline" s'exécute correctement
4. Attendez la fin des 3 jobs (test, docker, summary)

---

## 📊 Structure du Pipeline

```
┌─────────────────────────────────────────────────┐
│  Trigger: Push/PR vers main ou develop          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Job 1: test               │
    │  - Python 3.11             │
    │  - Poetry install          │
    │  - flake8 linting          │
    │  - Black formatting check  │
    │  - isort check             │
    │  - pytest                  │
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Job 2: docker             │
    │  - Docker Buildx           │
    │  - Login Docker Hub        │
    │  - Build with cache        │
    │  - Push to registry        │
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Job 3: summary            │
    │  - Display results         │
    │  - Status report           │
    └────────────────────────────┘
```

---

## 🏷️ Gestion des Tags Docker

Le workflow génère automatiquement plusieurs tags pour chaque image :

- **Date + SHA** : `2025-01-14-abc123def456` (pour traçabilité)
- **SHA court** : `abc123d` (pour référence rapide)
- **Branche** : `main` ou `develop` (pour les branches principales)
- **Pull Request** : `pr-123` (pour les PR)

Ces tags permettent de :
- Identifier facilement la version d'une image
- Retrouver le commit source
- Gérer les versions par branche

---

## 🧪 Tester Localement

Avant de push vos changements, vous pouvez tester localement :

```bash
# Installer les dépendances
make install

# Formater le code
make format

# Linter le code
make lint

# Lancer les tests
make test

# Tout vérifier en une fois (équivalent CI)
make ci
```

La commande `make ci` exécute toutes les vérifications que le pipeline CI effectue.

---

## 🔍 Dépannage

### Le workflow ne se déclenche pas

Vérifiez que :
- ✅ Les fichiers sont bien dans la branche `main` ou `develop`
- ✅ Le fichier `.github/workflows/ci.yml` existe
- ✅ Il n'y a pas d'erreurs de syntaxe YAML
- ✅ Les triggers sont correctement configurés

### Le build Docker échoue

Vérifiez que :
- ✅ Les secrets `DOCKERHUB_USERNAME` et `DOCKERHUB_TOKEN` sont bien configurés
- ✅ Le nom d'utilisateur Docker Hub est correct
- ✅ Le token est valide (pas expiré)
- ✅ Vous avez les permissions sur le repository Docker Hub

### Les tests échouent

Vérifiez que :
- ✅ Tous les tests passent localement (`make test`)
- ✅ Le linting est OK (`make lint`)
- ✅ Le formatage est correct (`make format`)

### Le linting échoue

```bash
# Formater automatiquement le code
make format

# Vérifier le linting
make lint
```

---

## 📝 Commandes Utiles GitHub CLI

Si vous avez GitHub CLI installé :

```bash
# Voir l'historique du workflow
gh run list

# Voir les logs d'une exécution spécifique
gh run view <run-id> --log

# Relancer un workflow qui a échoué
gh run rerun <run-id>

# Voir le statut du dernier workflow
gh run watch
```

---

## 🛠️ Outils Utilisés

### GitHub Actions
- **Triggers** : Push, Pull Request
- **Environnements** : ubuntu-latest
- **Secrets** : Docker Hub credentials (via GitHub Secrets)

### Docker
- **Registry** : Docker Hub
- **Buildx** : Builds optimisés multi-platform
- **Cache** : Registry cache pour accélérer les builds

> 💡 **Intégration avec le déploiement GCP** :  
> - Ce pipeline CI/CD pousse les images vers **Docker Hub**, ce qui est pratique pour des usages génériques ou d'autres environnements.  
> - Pour le déploiement sur **GCP**, la documentation Infrastructure (`docs/infrastructure.md` et le `README`) montre un flux séparé qui build/push l'image vers **Artifact Registry** (`europe-west1-docker.pkg.dev/...`).  
> - Les deux approches sont complémentaires : Docker Hub pour le registre "général" via CI, Artifact Registry pour les images utilisées en production sur GCP.

### Linting
- **flake8** : Style et erreurs Python (règles strictes)
- **black** : Formatage automatique (88 caractères)
- **isort** : Organisation des imports (compatible Black)

---

## 📊 Métriques

| Métrique | Objectif | Status |
|----------|----------|--------|
| **Temps de build** | < 5 minutes | ✅ |
| **Couverture de tests** | > 80% | ✅ |
| **Linting errors** | 0 | ✅ |
| **Docker image size** | < 500MB | ✅ |

---

## 🔗 Ressources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/fr/actions)
- [Docker Hub Authentication](https://docs.docker.com/docker-hub/access-tokens/)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

### Outils
- [flake8 Documentation](https://flake8.pycqa.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)

---

## ✅ Validation des Objectifs

| Objectif | Status | Détails |
|----------|--------|---------|
| **Workflow GitHub Actions** | ✅ | Pipeline complet avec 3 jobs |
| **Tests automatisés** | ✅ | Exécution à chaque push |
| **Linting intégré** | ✅ | flake8 + black + isort |
| **Build Docker** | ✅ | Automatique avec cache |
| **Push Docker Hub** | ✅ | Automatique via secrets |
| **Tags intelligents** | ✅ | SHA, date, branche |
| **Résumé pipeline** | ✅ | Rapport en fin d'exécution |

---

## 🚀 Prochaines étapes : Infrastructure

- 🏗️ Infrastructure as Code avec Terraform
- ☁️ Provisioning de ressources GCP
- 🔐 Gestion des rôles IAM
- 📦 Déploiement sur infrastructure cloud

---

**CI/CD terminé avec succès.**

Le pipeline CI/CD est maintenant complètement automatisé et prêt pour l’infrastructure (Terraform).
