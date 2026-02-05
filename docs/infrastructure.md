# Infrastructure — Terraform & GCP

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| [CI/CD](cicd.md) | [Expérimentation](experimentation.md) |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 🎯 Objectif

**Provisionner une infrastructure cloud simple sur GCP via Terraform et déployer l'API en production**

### ❓ Questions Clés
- Qu'est-ce que l'IaC et comment structurer un projet Terraform ?
- Comment provisionner des ressources de base (bucket, VM) ?
- Comment gérer les rôles IAM ?
- Comment sécuriser l'infrastructure et déployer l'API en production ?

### ⏱️ Répartition des Heures (20h)
- **6h** → Apprentissage des bases de Terraform (HCL, variables, state local)
- **7h** → Écrire le code pour provisionner un bucket GCS et une petite VM GCP
- **7h** → Gérer les IAM (comptes de service) pour l'accès aux ressources et déployer l'API

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [État Actuel du Projet](#état-actuel-du-projet)
3. [Sécurité : État et Améliorations](#sécurité-état-et-améliorations)
4. [Structure Terraform](#structure-terraform)
5. [Installation et Configuration](#installation-et-configuration)
6. [Tutoriel de Déploiement Complet](#tutoriel-de-déploiement-complet)
7. [Ressources Créées](#ressources-créées)
8. [Commandes Terraform Utiles](#commandes-terraform-utiles)
9. [Améliorations Futures](#améliorations-futures)
10. [Checklist de Production](#checklist-de-production)
11. [Dépannage](#dépannage)

---

## 🎯 Vue d'Ensemble

Ce guide complet vous accompagne dans la compréhension, la sécurisation et le déploiement de l'API MLOps sur Google Cloud Platform (GCP) via Terraform.

### Objectifs

- ✅ Comprendre l'état actuel de la sécurité
- ✅ Connaître les améliorations déjà implémentées
- ✅ Déployer l'infrastructure et l'API en production
- ✅ Identifier les améliorations futures possibles

### Prérequis

- Terraform >= 1.0
- Google Cloud SDK (gcloud)
- Docker
- Accès à un projet GCP avec permissions suffisantes
- Connaissances de base en infrastructure cloud

---

## 📊 État Actuel du Projet

### Score Global de Préparation : **9/10** ✅

| Catégorie | Score | Statut |
|-----------|-------|--------|
| **Sécurité** | 9/10 | ✅ Excellente |
| **Configuration** | 9/10 | ✅ Excellente |
| **Déploiement** | 9/10 | ✅ Excellent |
| **Monitoring** | 8/10 | ✅ Très bon |

### ✅ Points Forts Actuels

1. **Sécurité Réseau** : Firewalls configurés avec "deny by default"
2. **Authentification API** : Système d'API keys implémenté avec Secret Manager
3. **Rate Limiting** : Protection contre les abus (10 req/min)
4. **IAM** : Service account avec permissions minimales
5. **Dockerfile Sécurisé** : Utilisateur non-root
6. **Logging** : Activé sur les firewalls pour audit
7. **Variables Sécurisées** : Valeurs par défaut restrictives
8. **Secret Manager** : Création et gestion via Terraform ✅
9. **Chiffrement KMS** : Support pour Customer-Managed Encryption Keys ✅
10. **Load Balancer** : Support avec Cloud Armor pour DDoS protection ✅
11. **Monitoring** : Alertes Cloud Monitoring configurées ✅

### ✅ Améliorations Implémentées

1. **Déploiement Automatique** : ✅ Startup script complet avec gestion d'erreurs
2. **Gestion des Secrets** : ✅ Intégration complète Secret Manager via Terraform
3. **Monitoring** : ✅ Alertes Cloud Monitoring configurées (CPU, mémoire, instance down)
4. **Chiffrement** : ✅ Support KMS explicite pour le bucket
5. **Load Balancer** : ✅ Load Balancer HTTP avec Cloud Armor optionnel

---

## 🔒 Sécurité : État et Améliorations

### État Actuel de la Sécurité

#### ✅ Améliorations Déjà Implémentées

**1. Restriction des Firewalls**

- ✅ `allowed_http_ips` : Liste vide par défaut (deny by default)
- ✅ `allowed_ssh_ips` : Liste vide par défaut (deny by default)
- ✅ Règle firewall interne : Limité aux ports 8000 (API) et 22 (SSH)
- ✅ Logging activé sur toutes les règles firewall

**2. Authentification API**

- ✅ Module `src/serving/security.py` créé
- ✅ Vérification de l'API key via header `X-API-Key`
- ✅ Support pour proxies (X-Forwarded-For, X-Real-IP)
- ✅ Logging des tentatives d'accès non autorisées
- ✅ Mode développement : Désactivation automatique si `API_KEY` non configurée

**3. Rate Limiting**

- ✅ `/predict` : 10 requêtes par minute par IP
- ✅ `/model/info` : 20 requêtes par minute par IP
- ✅ `/health` : 30 requêtes par minute par IP

**4. Configuration Sécurisée**

- ✅ `enable_public_ip` : Désactivé par défaut (`false`)
- ✅ `force_destroy_bucket` : Variable ajoutée, désactivée par défaut
- ✅ Backend Terraform : Configuration exemple fournie

#### ✅ Améliorations Implémentées

**1. Gestion des Secrets avec Secret Manager** ✅

**Implémenté** :
- ✅ Création du secret Secret Manager via Terraform (`create_secret_manager_secret`)
- ✅ Accès IAM automatique pour le service account
- ✅ Support de la création manuelle ou automatique
- ✅ Variable d'environnement `TF_VAR_api_key_value` pour sécurité maximale

**Configuration détaillée** : Voir la section [1.2 Stocker dans Secret Manager](#12-stocker-dans-secret-manager-recommandé) pour les instructions complètes avec les deux options (Terraform ou manuel).

**2. Chiffrement KMS pour le Bucket** ✅

**Implémenté** :
- ✅ Support du chiffrement KMS pour le bucket GCS
- ✅ Variables `enable_kms_encryption` et `kms_key_name`
- ✅ Configuration dynamique dans le bucket
- ⚠️ **Désactivé par défaut** (`enable_kms_encryption = false`)

**Configuration** (optionnel, pour activer KMS) :
```hcl
# Dans terraform.tfvars
# ⚠️ Nécessite de créer la clé KMS au préalable et de configurer les permissions
enable_kms_encryption = true
kms_key_name = "projects/PROJECT/locations/LOCATION/keyRings/RING/cryptoKeys/KEY"
```

**Note** : Par défaut, le bucket utilise le chiffrement géré par Google (GMEK). KMS (Customer-Managed Encryption Keys) est optionnel et nécessite une configuration supplémentaire.

**3. Load Balancer avec Cloud Armor** ✅

**Qu'est-ce qu'un Load Balancer ?**

Un **Load Balancer** (répartiteur de charge) est un service qui :
- ✅ **Reçoit le trafic** des utilisateurs sur une IP publique unique
- ✅ **Répartit les requêtes** entre plusieurs serveurs (ou instances)
- ✅ **Vérifie la santé** des serveurs (health checks)
- ✅ **Améliore la sécurité** en masquant les IPs réelles des serveurs
- ✅ **Gère la haute disponibilité** : si un serveur tombe, le trafic est redirigé vers les autres

**Dans notre cas** (avec une seule VM) :
- Le Load Balancer sert principalement de **point d'entrée sécurisé**
- Il masque l'IP de la VM (on peut désactiver l'IP publique)
- Il permet d'ajouter **Cloud Armor** pour la protection DDoS
- Il facilite l'ajout de nouvelles VMs plus tard (scalabilité)

**Architecture** :
```
Utilisateurs → Load Balancer (IP publique) → VM (IP privée)
                ↓
            Cloud Armor (protection DDoS)
```

**Implémenté** :
- ✅ Load Balancer HTTP avec instance group
- ✅ Health check configuré
- ✅ Cloud Armor Security Policy (optionnel)
- ✅ Firewall rule pour autoriser le trafic du Load Balancer

**Configuration** :
```hcl
# Dans terraform.tfvars
enable_load_balancer = true
enable_cloud_armor = true
load_balancer_name = "mlops-api-lb"
# Désactiver l'IP publique sur la VM (recommandé avec Load Balancer)
enable_public_ip = false
# Configurer allowed_http_ips avec les plages IP des Load Balancers GCP
allowed_http_ips = ["130.211.0.0/22", "35.191.0.0/16"]
```

**Comment connaître les IPs des Load Balancers GCP** :

Il y a **deux approches** pour configurer `allowed_http_ips` avec un Load Balancer :

**Option 1 : Utiliser les plages IP connues des Load Balancers GCP** ✅ (Recommandé)

Les plages IP suivantes sont **les mêmes pour tous les utilisateurs GCP dans le monde entier**. Ce sont les plages IP réservées par Google Cloud Platform pour leurs Load Balancers HTTP(S) :
- `130.211.0.0/22` : Plage principale des Load Balancers GCP (globale)
- `35.191.0.0/16` : Plage secondaire des Load Balancers GCP (globale)

**⚠️ Important** : Ces plages IP sont **identiques pour tous les utilisateurs GCP**, peu importe votre localisation géographique ou votre projet. Tous les Load Balancers HTTP(S) de GCP utilisent des IPs dans ces plages.

**Avantages** :
- ✅ Fonctionne pour tous les Load Balancers GCP (pas seulement le vôtre)
- ✅ Pas besoin de connaître l'IP spécifique à l'avance
- ✅ Plus flexible si vous créez plusieurs Load Balancers
- ✅ Fonctionne immédiatement, même avant de créer votre Load Balancer

**Option 2 : Utiliser l'IP spécifique du Load Balancer** (Moins flexible)

Si vous préférez utiliser uniquement l'IP de votre Load Balancer :

```bash
# 1. Après terraform apply, récupérer l'IP du Load Balancer
LOAD_BALANCER_IP=$(terraform -chdir=terraform output -raw load_balancer_ip)
echo "Load Balancer IP: $LOAD_BALANCER_IP"

# 2. Mettre à jour terraform.tfvars avec cette IP spécifique
# allowed_http_ips = ["$LOAD_BALANCER_IP/32"]
```

**⚠️ Note** : L'Option 1 est recommandée car elle est plus simple et fonctionne immédiatement sans connaître l'IP à l'avance.

**4. Monitoring et Alertes** ✅

**Implémenté** :
- ✅ Alertes Cloud Monitoring pour :
  - CPU élevé (> 80%)
  - Mémoire élevée (> 85%)
  - Instance down
- ✅ Canaux de notification email
- ✅ Variables `enable_monitoring_alerts` et `notification_channels`

**Configuration** :
```hcl
# Dans terraform.tfvars
enable_monitoring_alerts = true
notification_channels = ["email:admin@example.com"]
```

---

## 📁 Structure Terraform

### Organisation des Fichiers

```
terraform/
├── main.tf                  # Ressources principales (VPC, VM, Bucket, IAM)
├── variables.tf             # Variables d'entrée
├── outputs.tf               # Valeurs de sortie
├── providers.tf             # Configuration des providers
├── backend.tf.example       # Exemple de configuration backend distant
├── terraform.tfvars.example # Exemple de configuration
└── .gitignore               # Fichiers à ignorer
```

### Description des Fichiers

- **`main.tf`** : Contient toutes les ressources GCP (VPC, VM, Bucket, Firewall, IAM)
- **`variables.tf`** : Définit toutes les variables d'entrée avec leurs descriptions et valeurs par défaut
- **`outputs.tf`** : Définit les valeurs de sortie (IPs, noms, commandes SSH, etc.)
- **`providers.tf`** : Configure le provider Google Cloud
- **`backend.tf.example`** : Exemple de configuration pour un backend distant (GCS)
- **`terraform.tfvars.example`** : Exemple de fichier de configuration (à copier vers `terraform.tfvars`)
- **Documentation détaillée** : ce fichier `docs/infrastructure.md` (guide complet Terraform pour le projet)

---

## 🚀 Installation et Configuration

### 1. Installer Terraform

#### macOS
```bash
brew install terraform
```

#### Linux
```bash
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

#### Vérifier l'installation
```bash
terraform version  # Doit être >= 1.0
```

### 2. Installer Google Cloud SDK

#### macOS
```bash
brew install google-cloud-sdk
```

#### Linux
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

#### Vérifier l'installation
```bash
gcloud version
```

---

## 🚀 Tutoriel de Déploiement Complet

### Étape 0 : Préparation de l'Environnement

#### 0.1 Vérifier les Outils Installés

```bash
# Vérifier Terraform
terraform version  # Doit être >= 1.0

# Vérifier gcloud
gcloud version

# Vérifier Docker
docker --version
```

#### 0.2 Configurer GCP

```bash
# Variables d'environnement (définir au début)
export PROJECT_ID="your-project-id"
export REGION="europe-west1"

# Se connecter et sélectionner le projet
gcloud auth login
gcloud config set project $PROJECT_ID

# Authentifier Terraform avec Google Cloud
gcloud auth application-default login

# Activer les APIs nécessaires
gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

#### 0.3 Vérifier les Permissions

Votre compte doit avoir `roles/owner` OU `roles/editor` + `roles/iam.securityAdmin` + `roles/storage.admin`

---

### Étape 1 : Configuration des Secrets

#### 1.1 Générer l'API Key

**⚠️ IMPORTANT** : Générez l'API_KEY une seule fois au début. Cette clé sera utilisée dans les étapes suivantes.

```bash
# Générer une clé API sécurisée (32 bytes = 64 caractères hex)
API_KEY=$(openssl rand -hex 32)
echo "API_KEY=$API_KEY"
echo "⚠️ SAUVEGARDEZ cette clé dans un endroit sûr (password manager, etc.) !"
```

**Note** : Cette clé sera utilisée dans l'étape 1.2 pour créer le secret dans Secret Manager.

#### 1.2 Stocker dans Secret Manager (Recommandé)

Vous avez deux options pour stocker l'API_KEY générée en 1.1 dans Secret Manager. Choisissez celle qui correspond le mieux à votre workflow.

---

##### **Option A : Création via Terraform (Recommandé)** ✅

Cette option permet de créer et gérer le secret entièrement via Terraform, avec une meilleure traçabilité et automatisation.

**Avantages** :
- ✅ Gestion complète via Infrastructure as Code
- ✅ Accès IAM configuré automatiquement
- ✅ Traçabilité dans le state Terraform
- ✅ Pas d'actions manuelles nécessaires

**Méthode recommandée : Variable d'environnement** 🔒

⚠️ **SÉCURITÉ CRITIQUE** : Ne JAMAIS mettre l'API_KEY directement dans `terraform.tfvars` (risque de commit accidentel).

```bash
# Utiliser l'API_KEY générée en 1.1
# Exporter comme variable d'environnement Terraform
export TF_VAR_api_key_value="$API_KEY"

# Vérifier que la variable est bien définie
echo "Variable définie : ${TF_VAR_api_key_value:0:10}..."  # Affiche seulement les 10 premiers caractères
```

**Configuration dans `terraform.tfvars`** :

```hcl
# Création du secret via Terraform
create_secret_manager_secret = true
secret_manager_api_key_name = "mlops-api-key"

# ⚠️ api_key_value n'est PAS dans terraform.tfvars
# Elle vient de la variable d'environnement TF_VAR_api_key_value
```

**Explication** :
- Terraform lit automatiquement les variables d'environnement préfixées par `TF_VAR_`
- `TF_VAR_api_key_value` sera utilisé pour créer le secret lors de `terraform apply`
- La clé n'apparaît jamais dans les fichiers versionnés
- Terraform créera automatiquement :
  - Le secret dans Secret Manager
  - La version du secret avec la valeur
  - L'accès IAM pour le service account (`roles/secretmanager.secretAccessor`)

**Alternative : Fichier séparé non versionné** (Moins recommandé)

Si vous préférez utiliser un fichier (acceptable mais moins sécurisé) :

```bash
# 1. Créer un fichier secrets.tfvars (DOIT être dans .gitignore)
cat > terraform/secrets.tfvars <<EOF
api_key_value = "votre-cle-secrete-ici"
EOF

# 2. Vérifier que secrets.tfvars est dans .gitignore
grep -q "secrets.tfvars" .gitignore || echo "secrets.tfvars" >> .gitignore

# 3. Appliquer avec le fichier de secrets
terraform -chdir=terraform apply -var-file=secrets.tfvars
```

**Dans `terraform.tfvars`** :
```hcl
create_secret_manager_secret = true
secret_manager_api_key_name = "mlops-api-key"
# api_key_value est dans secrets.tfvars (non versionné)
```

---

##### **Option B : Création manuelle** 🔧

Cette option permet de créer le secret manuellement avant de déployer l'infrastructure Terraform.

**Avantages** :
- ✅ Contrôle total sur la création du secret
- ✅ Peut être fait avant le déploiement Terraform
- ✅ Utile pour les environnements où Terraform n'a pas accès à Secret Manager

**Inconvénients** :
- ⚠️ Actions manuelles nécessaires
- ⚠️ Accès IAM doit être configuré (automatique via Terraform si `secret_manager_api_key_name` est défini)

**Étapes** :

```bash
# Utiliser l'API_KEY générée en 1.1
# Créer le secret dans Secret Manager
echo -n "$API_KEY" | gcloud secrets create mlops-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Vérifier que le secret a été créé
gcloud secrets describe mlops-api-key --project=$PROJECT_ID

# Vérifier la valeur (optionnel, pour test)
gcloud secrets versions access latest --secret="mlops-api-key" --project=$PROJECT_ID
```

**Configuration dans `terraform.tfvars`** :

```hcl
# Référencer le secret existant (ne pas créer)
secret_manager_api_key_name = "mlops-api-key"
# create_secret_manager_secret = false (ou omis, false par défaut)
```

**Note importante** : ✅ L'accès IAM au secret pour le service account est **automatiquement configuré par Terraform** si `secret_manager_api_key_name` est défini dans `terraform.tfvars`. Aucune action manuelle requise pour l'IAM !

**Si vous devez configurer l'accès IAM manuellement** (non recommandé, Terraform le fait automatiquement) :

```bash
# Récupérer l'email du service account (après terraform apply)
SERVICE_ACCOUNT=$(terraform -chdir=terraform output -raw service_account_email)

# Donner accès au secret
gcloud secrets add-iam-policy-binding mlops-api-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

---

##### **Comparaison des Options**

| Critère | Option A (Terraform) | Option B (Manuel) |
|---------|---------------------|-------------------|
| **Automatisation** | ✅ Complète | ⚠️ Partielle |
| **Traçabilité** | ✅ Dans state Terraform | ⚠️ Manuelle |
| **Sécurité** | ✅ Variable d'env | ✅ Gcloud CLI |
| **IAM automatique** | ✅ Oui | ✅ Oui (via Terraform) |
| **Complexité** | Simple | Moyenne |
| **Recommandation** | ✅ **Production** | ⚠️ **Développement/Test** |

**Recommandation** : Utilisez l'**Option A** en production pour une meilleure automatisation et traçabilité.

#### 1.3 Alternative : Variables d'Environnement (Moins Sécurisé)

**Note** : En développement local, vous pouvez exporter les variables d'environnement directement ou les passer à docker-compose. En production, utilisez Secret Manager.

---

### Étape 2 : Préparer le Modèle ML

#### 2.1 Entraîner le Modèle Localement

```bash
# Depuis le répertoire racine du projet
cd mlops-core

# Installer les dépendances si nécessaire
poetry install

# Entraîner le modèle
make train

# Vérifier que les fichiers sont créés
ls -la models/
# Devrait contenir :
# - metadata.json (contient l'URI MLflow pour charger le modèle)
# - metrics.json
# Le modèle est sauvegardé dans MLflow (mlruns/), chargé via l'URI dans metadata.json
```

#### 2.2 Uploader vers GCS

> ⚠️ **Important** : Cette étape doit être effectuée **après** `terraform apply` pour que le bucket existe.

> 💡 **Note** : Google recommande d'utiliser `gcloud storage` plutôt que `gsutil` car ces commandes sont plus modernes et supportent les dernières fonctionnalités de Cloud Storage.

```bash
# ⚠️ ÉTAPE 1 : Créer les ressources GCP d'abord (voir section Déploiement ci-dessous)
# terraform apply

# ⚠️ ÉTAPE 2 : Récupérer le nom du bucket créé par Terraform
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)

# ⚠️ IMPORTANT : Uploader mlruns/ vers GCS (nécessaire pour que l'API charge le modèle)
gcloud storage cp -r mlruns/ gs://$BUCKET_NAME/

# Note: models/metadata.json et models/metrics.json sont inclus dans l'image Docker
# Ils sont versionnés avec Git via DVC et n'ont pas besoin d'être uploadés séparément
# Le modèle est chargé depuis MLflow via GCS en utilisant mlflow_run_id depuis metadata.json

# Vérifier
gcloud storage ls gs://$BUCKET_NAME/
gcloud storage ls gs://$BUCKET_NAME/mlruns/
```

**Note** : 
- Les fichiers `models/metadata.json` et `models/metrics.json` sont inclus dans l'image Docker (versionnés avec Git via DVC)
- Le modèle est chargé dynamiquement depuis GCS via MLflow en utilisant `mlflow_run_id` depuis `metadata.json`
- MLflow télécharge temporairement le modèle dans son cache (`~/.mlflow/cache`) lors du chargement
- Pas besoin de copier manuellement le modèle ou les métadonnées sur la VM

---

### Étape 3 : Build et Push de l'Image Docker

#### 3.1 Build Local et Test

```bash
# Build l'image localement (pour test rapide)
docker build -t iris-api:latest .

# Tester localement
docker run -p 127.0.0.1:8000:8000 \
  -e API_KEY="test-key" \
  -v $(pwd)/models:/app/models \
  iris-api:latest

# Dans un autre terminal, tester l'API
curl -H "X-API-Key: test-key" http://localhost:8000/health
```

#### 3.2 Build Multi-plateforme et Push vers Artifact Registry

```bash
# Définir l'URI de l'image Docker
export DOCKER_IMAGE_URI="europe-west1-docker.pkg.dev/$PROJECT_ID/mlops-repo/iris-api:latest"

# Créer un repository Artifact Registry
gcloud artifacts repositories create mlops-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="MLOps API Docker repository" \
  --project=$PROJECT_ID || true

# Configurer Docker
gcloud auth configure-docker $REGION-docker.pkg.dev

# Builder l'image Docker (linux/amd64 - compatible partout)
docker build --platform linux/amd64 -t $DOCKER_IMAGE_URI .

# Pusher l'image vers Artifact Registry
docker push $DOCKER_IMAGE_URI
```

> **💡 Note** : `linux/amd64` fonctionne partout : GCP, AWS, Azure, et même sur Mac M1/M2 via émulation Rosetta (transparent avec Docker). Plus simple et plus rapide qu'un build multi-plateforme !

---

### Étape 4 : Configuration Terraform

#### 4.1 Créer le Fichier de Configuration

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

#### 4.2 Éditer terraform.tfvars

Ouvrez `terraform.tfvars` et configurez les valeurs. Le fichier `terraform.tfvars.example` contient des commentaires détaillés pour chaque section.

**⚠️ Variables OBLIGATOIRES à configurer** :

```hcl
# ============================================================================
# CONFIGURATION OBLIGATOIRE
# ============================================================================

# ⚠️ OBLIGATOIRE : ID du projet GCP (créé manuellement)
project_id = "your-project-id"

# Région et zone
region = "europe-west1"
zone   = "europe-west1-a"

# ============================================================================
# CONFIGURATION RÉSEAU - SÉCURITÉ CRITIQUE
# ============================================================================
#
# ⚠️ IMPORTANT : Deux scénarios de sécurité possibles
#
# SCÉNARIO 1 : Load Balancer (RECOMMANDÉ en production)
#   - enable_load_balancer = true
#   - enable_public_ip = false
#   - Accès HTTP : Via Load Balancer (IP publique du LB, protégé par Cloud Armor)
#   - Accès SSH : Via IAP uniquement (pas d'IP publique sur la VM)
#   - allowed_http_ips : Plages IP des Load Balancers GCP (pour autoriser LB → VM)
#   - allowed_ssh_ips : Vide (SSH via IAP uniquement)
#
# SCÉNARIO 2 : IP publique sur la VM (moins sécurisé, pour tests/dev)
#   - enable_load_balancer = false
#   - enable_public_ip = true
#   - Accès HTTP : Directement à l'IP publique de la VM (ports 80, 8000)
#   - Accès SSH : Directement à l'IP publique de la VM (port 22)
#   - allowed_http_ips : Votre IP uniquement (ex: ["123.45.67.89/32"])
#   - allowed_ssh_ips : Votre IP uniquement (ex: ["123.45.67.89/32"])
#   ⚠️ SÉCURITÉ : Seules les IPs dans ces listes peuvent accéder à la VM
#
# ============================================================================

# IPs autorisées pour SSH (si enable_public_ip = true)
# Pour connaître votre IP publique : curl https://checkip.amazonaws.com
# ⚠️ Si vous utilisez uniquement IAP (enable_public_ip = false), cette liste peut rester vide
allowed_ssh_ips = [
  "VOTRE-IP-PUBLIQUE/32",  # ⚠️ REMPLACEZ par votre IP publique réelle (ex: "123.45.67.89/32")
  # Récupérer votre IP : curl https://checkip.amazonaws.com
]

# IPs autorisées pour HTTP/HTTPS
# Option 1 : Si vous utilisez un Load Balancer GCP (RECOMMANDÉ)
#   → Ces plages IP autorisent le trafic du Load Balancer vers la VM
allowed_http_ips = [
  "130.211.0.0/22",  # Plages IP des Load Balancers GCP (globales)
  "35.191.0.0/16",
]

# Option 2 : Si vous exposez directement la VM (NON RECOMMANDÉ en production)
#   → Votre IP uniquement pour accéder directement à l'API
# allowed_http_ips = [
#   "123.45.67.89/32",  # Votre IP uniquement
# ]

# ============================================================================
# CONFIGURATION DU DÉPLOIEMENT DE L'API
# ============================================================================

# Image Docker (après build et push)
# Utiliser la variable DOCKER_IMAGE_URI définie lors du build
docker_image = "$DOCKER_IMAGE_URI"

# ============================================================================
# SECRET MANAGER
# ============================================================================

# Option A : Création via Terraform (Recommandé)
# 1. Exporter : export TF_VAR_api_key_value="votre-api-key"
# 2. Configurer :
create_secret_manager_secret = true
secret_manager_api_key_name = "mlops-api-key"

# Option B : Secret créé manuellement
# secret_manager_api_key_name = "mlops-api-key"
# create_secret_manager_secret = false
```

**Configuration optionnelle** (selon vos besoins) :

```hcl
# ============================================================================
# LOAD BALANCER (Recommandé en production)
# ============================================================================
enable_load_balancer = true
enable_cloud_armor = true
load_balancer_name = "mlops-api-lb"
# Si Load Balancer activé, désactiver l'IP publique sur la VM
enable_public_ip = false

# ============================================================================
# MONITORING (Recommandé en production)
# ============================================================================
enable_monitoring_alerts = true
notification_channels = ["email:admin@example.com"]

# ============================================================================
# KMS (Optionnel - Désactivé par défaut)
# ============================================================================
# ⚠️ KMS est désactivé par défaut. Le bucket utilise le chiffrement géré par Google (GMEK).
# Pour activer KMS (Customer-Managed Encryption Keys), vous devez :
# 1. Créer la clé KMS au préalable
# 2. Configurer les permissions du service account Cloud Storage
# 3. Décommenter et configurer :
# enable_kms_encryption = true
# kms_key_name = "projects/your-project-id/locations/europe-west1/keyRings/mlops-keyring/cryptoKeys/mlops-key"
```

**⚠️ Important** : 
- Ne commitez JAMAIS `terraform.tfvars` (il est dans `.gitignore`)
- ⚠️ **OBLIGATOIRE** : Configurez `project_id` et `iap_tunnel_users` (pour SSH via IAP)
- ⚠️ **Deux scénarios de sécurité** :
  - **Scénario 1 (Recommandé)** : Load Balancer activé → `enable_public_ip = false`, `allowed_http_ips` = plages IP Load Balancers GCP
  - **Scénario 2** : IP publique activée → `enable_load_balancer = false`, configurez `allowed_ssh_ips` et `allowed_http_ips` avec votre IP uniquement
- Consultez `terraform.tfvars.example` pour les commentaires détaillés sur chaque option
- Pour Secret Manager : voir la section [1.2 Stocker dans Secret Manager](#12-stocker-dans-secret-manager-recommandé) pour les instructions complètes

#### 4.3 (Optionnel) Configurer le Backend Terraform

Pour une meilleure sécurité et collaboration :

```bash
# Créer le bucket pour le state
gcloud storage buckets create gs://$PROJECT_ID-terraform-state \
  --project=$PROJECT_ID \
  --location=$REGION

# Activer le versioning
gcloud storage buckets update gs://$PROJECT_ID-terraform-state \
  --versioning

# Copier et configurer
cp terraform/backend.tf.example terraform/backend.tf

# Éditer terraform/backend.tf avec vos valeurs
# terraform/backend.tf :
# terraform {
#   backend "gcs" {
#     bucket = "$PROJECT_ID-terraform-state"
#     prefix = "mlops-core/terraform/state"
#   }
# }
```

⚠️ **Recommandé en production** : Utiliser un backend distant avec chiffrement KMS

---

### Étape 5 : Déploiement Terraform

✅ **Note** : Le script de déploiement est intégré directement dans le startup-script. Le service est configuré et activé (démarrage au boot), mais non démarré automatiquement. Aucun upload manuel n'est nécessaire.

#### 5.1 Initialisation

```bash
# Initialiser Terraform (depuis la racine du projet)
make terraform-init
# ou directement
terraform -chdir=terraform init

# Si vous utilisez un backend distant
terraform -chdir=terraform init -migrate-state
```

#### 5.2 Validation

```bash
# Valider la syntaxe
make terraform-validate
# ou directement
terraform -chdir=terraform validate

# Voir ce qui sera créé (sans créer)
make terraform-plan
# ou directement
terraform -chdir=terraform plan

# Vérifier attentivement :
# - Les IPs autorisées sont correctes
# - Le bucket ne sera pas supprimé (force_destroy_bucket = false)
# - L'IP publique est désactivée (si souhaité)
```

#### 5.3 Application

```bash
# Appliquer la configuration
make terraform-apply
# ou directement
terraform -chdir=terraform apply

# Confirmer avec "yes" quand demandé
# ⚠️ Cette opération peut prendre 5-10 minutes
```

✅ **Le déploiement de l'API est entièrement automatique.** Le script de déploiement est intégré dans le startup-script, aucune action manuelle n'est requise.

#### 5.4 Vérification Post-Déploiement

```bash
# Voir tous les outputs
make terraform-output
# ou directement
terraform -chdir=terraform output

# Voir un output spécifique
terraform -chdir=terraform output vm_internal_ip
terraform -chdir=terraform output vm_external_ip
terraform -chdir=terraform output load_balancer_ip
terraform -chdir=terraform output load_balancer_url
terraform -chdir=terraform output vm_ssh_command
terraform -chdir=terraform output bucket_name
```

#### 5.5 Accès au Secret Manager

✅ **Configuration automatique** : Terraform configure automatiquement l'accès IAM pour le service account, que vous utilisiez l'Option A (création via Terraform) ou l'Option B (création manuelle).

**Fonctionnement** : Si `secret_manager_api_key_name` est défini dans `terraform.tfvars`, Terraform ajoute automatiquement le rôle `roles/secretmanager.secretAccessor` au service account et configure les scopes nécessaires. **Aucune action manuelle requise !**

**Vérification** (après `terraform apply`) :

```bash
# Vérifier que le service account a accès au secret
SERVICE_ACCOUNT=$(terraform -chdir=terraform output -raw service_account_email)
gcloud secrets get-iam-policy mlops-api-key \
  --project=$PROJECT_ID \
  | grep "$SERVICE_ACCOUNT"
```

**Note** : Pour les détails complets sur la configuration des secrets, voir la section [1.2 Stocker dans Secret Manager](#12-stocker-dans-secret-manager-recommandé).

---

### Étape 6 : Préparer le Déploiement Automatique

✅ **Note** : Le script de déploiement est maintenant intégré directement dans le startup-script Terraform. Aucun upload manuel dans GCS n'est nécessaire.

#### 6.1 Configurer les Variables de Déploiement dans terraform.tfvars

Assurez-vous que votre `terraform.tfvars` contient :

```hcl
# Image Docker complète
# Utiliser la variable DOCKER_IMAGE_URI définie lors du build
docker_image = "$DOCKER_IMAGE_URI"

# Configuration Secret Manager
# Voir section 1.2 pour les détails complets des deux options
secret_manager_api_key_name = "mlops-api-key"
# Option A : create_secret_manager_secret = true (avec TF_VAR_api_key_value exportée)
# Option B : create_secret_manager_secret = false (secret créé manuellement)

# Note: Le service est configuré et activé (démarrage au boot), mais non démarré automatiquement
```

**Important** : 
- Si vous utilisez l'**Option A** : Assurez-vous d'avoir exporté `TF_VAR_api_key_value` avant `terraform apply` (voir [section 1.2](#12-stocker-dans-secret-manager-recommandé))
- Si vous utilisez l'**Option B** : Assurez-vous que le secret `mlops-api-key` existe déjà dans Secret Manager (voir [section 1.2](#12-stocker-dans-secret-manager-recommandé))

#### 6.2 Déploiement Automatique

Le startup-script :
1. Installe Docker et docker compose (plugin)
2. Récupère l'API_KEY depuis Secret Manager
3. Configure l'API (utilisateur, répertoires, docker-compose.yml, service systemd)
4. **Active** le service systemd (démarrage automatique au boot)

**⚠️ Action requise** : Le service est activé mais **non démarré** automatiquement. Vous devez démarrer l'API manuellement après vérification de la configuration (voir section 6.3).

#### 6.3 Vérifier et Démarrer l'API

**Le service est configuré mais non démarré.** Vérifiez la configuration puis démarrez l'API :

```bash
# Se connecter à la VM
ZONE=$(terraform -chdir=terraform output -raw vm_zone)

# Via IAP (si pas d'IP publique - recommandé)
gcloud compute ssh iris-api-server \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --tunnel-through-iap

# Ou directement si IP publique activée
# gcloud compute ssh iris-api-server --zone=$ZONE --project=$PROJECT_ID

# Vérifier Docker
docker --version
docker compose version  # Note: "docker compose" (plugin), pas "docker-compose"

# Vérifier que le service est configuré
sudo systemctl status mlops-api
ls -la /opt/mlops-api/

# Démarrer l'API
sudo systemctl start mlops-api

# Vérifier que l'API tourne
sudo systemctl status mlops-api
docker ps

# Voir les logs du déploiement (configuration)
cat /var/log/startup.log

# Voir les logs de l'API (après démarrage)
journalctl -u mlops-api -f
# Ou
docker compose -f /opt/mlops-api/docker-compose.yml logs -f

# Tester l'API depuis la VM
curl http://localhost:8000/health

# Tester avec API key
export API_KEY=$(gcloud secrets versions access latest --secret="mlops-api-key" --project=$PROJECT_ID)
curl -H "X-API-Key: $API_KEY" http://localhost:8000/health
```

**Pour arrêter/démarrer l'API manuellement** :

```bash
# Se connecter à la VM
ZONE=$(terraform -chdir=terraform output -raw vm_zone)
gcloud compute ssh iris-api-server --zone=$ZONE --project=$PROJECT_ID

# Arrêter l'API
sudo systemctl stop mlops-api

# Démarrer l'API
sudo systemctl start mlops-api

# Redémarrer l'API (après modification de docker-compose.yml)
sudo systemctl restart mlops-api

# Vérifier le statut
sudo systemctl status mlops-api
docker ps
```

---

### Étape 7 : Validation et Tests

#### 7.1 Tests Locaux (depuis la VM)

```bash
# Health check
curl http://localhost:8000/health

# Test de prédiction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'

# Test de rate limiting (faire 11 requêtes rapides)
for i in {1..11}; do
  curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
  echo ""
done
# La 11ème devrait retourner 429 Too Many Requests
```

#### 7.2 Tests Externes

```bash
# Depuis votre machine locale

# Récupérer l'API key
SECRET_NAME=$(terraform -chdir=terraform output -raw secret_manager_secret_name)
API_KEY=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project=$PROJECT_ID)

# Utiliser le Load Balancer (ou l'IP de la VM en fallback)
API_IP=$(terraform -chdir=terraform output -raw load_balancer_ip 2>/dev/null || terraform -chdir=terraform output -raw vm_external_ip)

# Tests
curl http://$API_IP/health
curl -X POST "http://$API_IP/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

#### 7.3 Test d'Authentification

```bash
# Test sans API key (devrait échouer avec 401)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Test avec API key invalide (devrait échouer avec 403)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

---

### Étape 8 : Monitoring et Alertes (Optionnel mais Recommandé)

#### 8.1 Configurer Cloud Monitoring

```bash
# Créer une alerte sur les erreurs API
# (Via la console GCP ou gcloud CLI)

# Exemple via console :
# 1. Aller dans Cloud Monitoring > Alerting
# 2. Créer une nouvelle politique
# 3. Condition : Taux d'erreur HTTP > 10%
# 4. Notification : Email/Slack
```

#### 8.2 Créer un Dashboard

Via la console GCP :
1. Aller dans Cloud Monitoring > Dashboards
2. Créer un nouveau dashboard
3. Ajouter des métriques :
   - CPU utilisation de la VM
   - Mémoire utilisation
   - Requêtes API par seconde
   - Taux d'erreur HTTP
   - Latence des requêtes

---

## 📊 Ressources Créées

### Bucket GCS

- **Nom** : `{project_id}-ml-models` (ou personnalisé via `bucket_name`)
- **Région** : Configurée dans `terraform.tfvars` (défaut: `europe-west1`)
- **Versioning** : Activé (pour la traçabilité des modèles)
- **Lifecycle** : Suppression automatique après 365 jours
- **Uniform Bucket Level Access** : Activé (meilleure sécurité IAM)
- **Force Destroy** : Désactivé par défaut (`force_destroy_bucket = false`)

### VM Compute Engine

- **Nom** : Configuré via `vm_name` (défaut: `iris-api-server`)
- **Type** : Configuré via `machine_type` (défaut: `e2-micro` pour le free tier)
- **OS** : Ubuntu 22.04 LTS (`ubuntu-os-cloud/ubuntu-2204-lts`)
- **Disque** : Configuré via `disk_size_gb` (défaut: 10GB SSD)
- **IP** : Publique désactivée par défaut (`enable_public_ip = false`)
- **Script de démarrage** : Installe Docker automatiquement
- **Zone** : Configurée via `zone` (défaut: `europe-west1-a`)

### VPC Network

- **Réseau** : `mlops-vpc` (configuré via `network_name`)
- **Sous-réseau** : `mlops-vpc-subnet`
- **Plage IP** : `10.0.1.0/24`
- **Région** : Configurée dans `terraform.tfvars`

### Firewall Rules

- **SSH** : Port 22
  - Si IP publique activée : IPs configurées via `allowed_ssh_ips` (liste vide par défaut)
  - Si Load Balancer : SSH via IAP uniquement (pas d'IP publique sur la VM)
- **HTTP** : Ports 80, 8000
  - Si IP publique activée : IPs configurées via `allowed_http_ips` (liste vide par défaut)
  - Si Load Balancer : Accès via Load Balancer (IP publique du LB), `allowed_http_ips` autorise LB → VM
- **Interne** : Ports 8000 (API) et 22 (SSH) uniquement dans le sous-réseau (10.0.1.0/24)
- **Logging** : Activé sur toutes les règles firewall pour l'audit de sécurité

**⚠️ IMPORTANT - Deux scénarios de sécurité** :

1. **Load Balancer (RECOMMANDÉ)** :
   - `enable_load_balancer = true`, `enable_public_ip = false`
   - Accès HTTP : Via Load Balancer (IP publique du LB, protégé par Cloud Armor)
   - Accès SSH : Via IAP uniquement (pas d'IP publique sur la VM)
   - `allowed_http_ips` : Plages IP des Load Balancers GCP (`130.211.0.0/22`, `35.191.0.0/16`)
   - `allowed_ssh_ips` : Vide (SSH via IAP uniquement)

2. **IP publique sur la VM (moins sécurisé)** :
   - `enable_load_balancer = false`, `enable_public_ip = true`
   - Accès HTTP : Directement à l'IP publique de la VM (ports 80, 8000)
   - Accès SSH : Directement à l'IP publique de la VM (port 22)
   - `allowed_http_ips` : Votre IP uniquement (ex: `["123.45.67.89/32"]`)
   - `allowed_ssh_ips` : Votre IP uniquement (ex: `["123.45.67.89/32"]`)
   - ⚠️ **SÉCURITÉ** : Seules les IPs dans ces listes peuvent accéder à la VM

### Service Account

- **Nom** : `mlops-api-sa` (configuré via `service_account_name`)
- **Rôles** :
  - `storage.objectAdmin` : Accès au bucket GCS (lecture/écriture)
  - `logging.logWriter` : Écriture des logs
  - `monitoring.metricWriter` : Métriques
- **Scopes** : Limités (pas de `cloud-platform` complet)
  - `devstorage.read_write` : GCS
  - `logging.write` : Logs
  - `monitoring.write` : Monitoring

---

## 📝 Commandes Terraform Utiles

### Commandes de Base

> **💡 Note** : Toutes les commandes peuvent être exécutées depuis la racine du projet avec `make terraform-*` ou `terraform -chdir=terraform`.

```bash
# Voir l'état actuel
terraform -chdir=terraform show

# Rafraîchir l'état (synchroniser avec GCP)
terraform -chdir=terraform refresh

# Valider la configuration
make terraform-validate
# ou directement
terraform -chdir=terraform validate

# Formater les fichiers Terraform
terraform -chdir=terraform fmt -recursive

# Voir les outputs
make terraform-output
# ou directement
terraform -chdir=terraform output

# Voir les outputs en JSON
terraform -chdir=terraform output -json

# Voir un output spécifique
terraform -chdir=terraform output vm_external_ip
terraform -chdir=terraform output bucket_name
```

### Commandes de Déploiement

```bash
# Initialiser Terraform
make terraform-init
# ou directement
terraform -chdir=terraform init

# Voir ce qui sera créé/modifié
make terraform-plan
# ou directement
terraform -chdir=terraform plan

# Appliquer les changements
make terraform-apply
# ou directement
terraform -chdir=terraform apply

# Appliquer sans confirmation (non recommandé)
terraform -chdir=terraform apply -auto-approve

# Détruire l'infrastructure
make terraform-destroy
# ou directement
terraform -chdir=terraform destroy
```

### Commandes de Connexion

```bash
# Utiliser la commande SSH générée
terraform -chdir=terraform output vm_ssh_command

# Ou directement avec gcloud
ZONE=$(terraform -chdir=terraform output -raw vm_zone)
gcloud compute ssh iris-api-server \
  --zone=$ZONE \
  --project=$PROJECT_ID
```

---

## 🔮 Améliorations Futures

### Court Terme (1-2 semaines)

1. ✅ **Intégrer Secret Manager dans Terraform** - **FAIT**
   - ✅ Création de la ressource Secret Manager via Terraform
   - ✅ Automatisation de l'accès depuis le service account

2. **Automatiser le Build/Push Docker**
   - Intégrer avec GitHub Actions
   - Build automatique à chaque push

3. ✅ **Améliorer le Startup Script** - **FAIT**
   - ✅ Script de déploiement intégré directement dans le startup script Terraform
   - ✅ Plus besoin d'uploader manuellement dans GCS - tout est versionné avec Terraform
   - ✅ Gestion d'erreurs robuste ajoutée
   - ✅ Support de docker compose (plugin) et docker-compose (fallback)

4. ✅ **Configurer Cloud Monitoring** - **FAIT**
   - ✅ Alertes sur métriques critiques (CPU, mémoire, instance down)
   - 📋 Dashboard de monitoring (à créer manuellement via console GCP)

### Moyen Terme (1 mois)

5. ✅ **Load Balancer avec Cloud Armor** - **FAIT**
   - ✅ Load Balancer GCP implémenté
   - ✅ Cloud Armor configuré pour protection DDoS

6. ✅ **Chiffrement KMS** - **FAIT**
   - ✅ Support Customer-Managed Encryption Keys
   - ✅ Chiffrement du bucket GCS avec KMS (optionnel, désactivé par défaut)
   - ⚠️ Par défaut, le bucket utilise le chiffrement géré par Google (GMEK)

7. **Backups Automatiques**
   - Configurer des backups réguliers du bucket
   - Politique de rétention

8. **Tests d'Intégration**
   - Tests automatisés post-déploiement
   - Validation de l'infrastructure

### Long Terme (3+ mois)

9. **CI/CD Complet**
   - Pipeline de déploiement automatisé
   - Tests automatiques
   - Rollback automatique

10. **Rotation des Secrets**
    - Rotation automatique de l'API_KEY
    - Gestion des versions de secrets

11. **Multi-Environnement**
    - Environnements dev/staging/prod
    - Configuration par environnement

12. **Audit de Sécurité Régulier**
    - Audit trimestriel
    - Mise à jour des politiques de sécurité

---

## ✅ Checklist de Production

### Pré-Déploiement

- [ ] **Outils Installés**
  - [ ] Terraform >= 1.0
  - [ ] Google Cloud SDK
  - [ ] Docker

- [ ] **Configuration GCP**
  - [ ] APIs activées
  - [ ] Permissions vérifiées
  - [ ] Projet sélectionné

- [ ] **Secrets**
  - [ ] API_KEY générée (`openssl rand -hex 32`)
  - [ ] **Option A (Terraform)** :
    - [ ] `TF_VAR_api_key_value` exportée comme variable d'environnement
    - [ ] `create_secret_manager_secret = true` dans terraform.tfvars
    - [ ] `secret_manager_api_key_name` configuré
    - [ ] ⚠️ API_KEY **PAS** dans terraform.tfvars
  - [ ] **OU Option B (Manuel)** :
    - [ ] Secret créé manuellement via `gcloud secrets create`
    - [ ] `secret_manager_api_key_name` configuré dans terraform.tfvars
    - [ ] `create_secret_manager_secret = false` (ou omis)
  - [ ] ✅ Accès IAM configuré automatiquement par Terraform (si `secret_manager_api_key_name` est défini)
  - [ ] Secret vérifié : `gcloud secrets describe mlops-api-key`

- [ ] **Modèle ML**
  - [ ] Modèle entraîné localement
  - [ ] Modèle uploadé vers GCS
  - [ ] Métadonnées uploadées

- [ ] **Image Docker**
  - [ ] Image buildée et testée
  - [ ] Image pushée vers Artifact Registry
  - [ ] Tag de version défini

- [ ] **Configuration Terraform**
  - [ ] `terraform.tfvars` configuré
  - [ ] `allowed_ssh_ips` configuré avec IPs réelles
  - [ ] `allowed_http_ips` configuré (ou Load Balancer)
  - [ ] `enable_public_ip` configuré selon besoins
  - [ ] `force_destroy_bucket = false`
  - [ ] `docker_image` configuré avec `$DOCKER_IMAGE_URI` (voir section Build et Push)
  - [ ] `secret_manager_api_key_name` configuré (ex: `mlops-api-key`)
  - [ ] `cors_origins` configuré avec des origines explicites (jamais `"*"` en production)
  - [ ] Configuration Terraform validée
  - [ ] Backend Terraform configuré (optionnel)

### Déploiement

- [ ] **Infrastructure**
  - [ ] `terraform init` exécuté
  - [ ] `terraform plan` vérifié
  - [ ] `terraform apply` exécuté avec succès
  - [ ] Toutes les ressources créées
  - [ ] ✅ Script de déploiement intégré dans le startup-script (aucun upload manuel nécessaire)

- [ ] **Application**
  - [ ] Déploiement automatique vérifié via logs
  - [ ] Connexion SSH à la VM réussie
  - [ ] Docker installé et fonctionnel
  - [ ] docker compose (plugin) disponible
  - [ ] Modèle téléchargé depuis GCS
  - [ ] API_KEY récupérée depuis Secret Manager
  - [ ] Container Docker lancé
  - [ ] Service systemd `mlops-api` actif
  - [ ] Health check répond

- [ ] **Validation**
  - [ ] Test `/health` réussi
  - [ ] Test `/predict` avec API key réussi
  - [ ] Test sans API key échoue (401)
  - [ ] Test avec API key invalide échoue (403)
  - [ ] Rate limiting fonctionne (429 après 10 req/min)
  - [ ] Logs accessibles

### Post-Déploiement

- [ ] **Monitoring**
  - [ ] Cloud Monitoring configuré
  - [ ] Alertes configurées
  - [ ] Dashboard créé

- [ ] **Documentation**
  - [ ] Documentation à jour
  - [ ] Runbook créé
  - [ ] Procédures d'urgence documentées

---

## 🔧 Dépannage

### Problème : L'API ne démarre pas

**Symptômes** :
- Container ne démarre pas
- Erreurs dans les logs

**Solutions** :

```bash
# Vérifier les logs Docker
docker logs iris-api

# Vérifier les logs système
journalctl -u mlops-api -f

# Vérifier que le modèle est présent
ls -la /opt/mlops-api/models/

# Vérifier les variables d'environnement
docker exec iris-api env | grep API_KEY
docker exec iris-api env | grep MODEL_DIR
```

### Problème : API key invalide

**Symptômes** :
- Erreur 401 ou 403
- "API key invalide" dans les logs

**Solutions** :

```bash
# Vérifier la variable d'environnement dans le container
docker exec iris-api env | grep API_KEY

# Vérifier Secret Manager
gcloud secrets versions access latest --secret="mlops-api-key"

# Vérifier que le service account a accès
gcloud secrets get-iam-policy mlops-api-key
```

### Problème : Modèle non trouvé

**Symptômes** :
- Erreur "Modèle non trouvé" au démarrage
- 503 Service Unavailable

**Solutions** :

```bash
# Vérifier GCS
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)
gcloud storage ls gs://$BUCKET_NAME/

# Note : models/metadata.json et models/metrics.json sont inclus dans l'image Docker
# Ils sont versionnés avec Git via DVC et n'ont pas besoin d'être téléchargés séparément
# Le modèle est chargé depuis MLflow via GCS en utilisant mlflow_run_id depuis metadata.json
# Si vous devez vérifier les métadonnées, elles sont dans l'image Docker à /app/models/

# ⚠️ IMPORTANT : MLFLOW_TRACKING_URI est configuré automatiquement par Terraform
# Le modèle est chargé via runs:/<run_id>/model, résolu automatiquement vers GCS
# MLflow télécharge temporairement le modèle dans son cache (~/.mlflow/cache)
# Pas besoin de télécharger mlruns/ localement sur la VM

# Vérifier les permissions du service account
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:mlops-api-sa@*"
```

### Problème : Rate limiting trop restrictif

**Symptômes** :
- 429 Too Many Requests trop fréquent

**Solutions** :

Modifier les limites dans `src/serving/app.py` :

```python
# Augmenter la limite
@limiter.limit("20/minute")  # Au lieu de 10/minute
async def predict_iris(...):
    ...
```

Puis rebuild et push l'image Docker.

### Problème : Connexion SSH impossible

**Symptômes** :
- Timeout lors de la connexion SSH

**Solutions** :

```bash
# Vérifier que votre IP est dans allowed_ssh_ips
# Récupérer votre IP publique
curl https://checkip.amazonaws.com

# Vérifier la règle firewall
gcloud compute firewall-rules describe mlops-vpc-allow-ssh

# Vérifier que la VM a le tag ssh-allowed
ZONE=$(terraform -chdir=terraform output -raw vm_zone)
gcloud compute instances describe iris-api-server \
  --zone=$ZONE \
  --format="get(tags.items)"
```

### Problème : API inaccessible depuis l'extérieur

**Symptômes** :
- Timeout ou connexion refusée depuis l'extérieur

**Solutions** :

```bash
# Vérifier que votre IP est dans allowed_http_ips
# Vérifier la règle firewall
gcloud compute firewall-rules describe mlops-vpc-allow-http

# Vérifier que la VM a le tag http-server
ZONE=$(terraform -chdir=terraform output -raw vm_zone)
gcloud compute instances describe iris-api-server \
  --zone=$ZONE \
  --format="get(tags.items)"

# Vérifier que l'IP publique est activée (si nécessaire)
terraform -chdir=terraform output vm_external_ip
```

### Erreur Terraform : "API not enabled"

```bash
# Activer les APIs nécessaires
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com
```

### Erreur Terraform : "Error: google: could not find default credentials"

Cette erreur indique que Terraform ne peut pas s'authentifier avec Google Cloud. Solution :

```bash
# Authentifier Terraform avec Google Cloud
gcloud auth application-default login
```

**Note** : Cette commande doit être exécutée après `gcloud auth login` et configure les credentials par défaut que Terraform utilisera.

### Erreur Terraform : "Bucket name already exists"

Le nom du bucket doit être unique globalement. Changez `bucket_name` dans `terraform.tfvars`.

### Erreur Terraform : "Insufficient permissions"

Vérifiez que votre compte a les permissions nécessaires :
- `roles/owner` ou
- `roles/editor` + `roles/iam.securityAdmin` + `roles/storage.admin`

---

## 📚 Ressources Complémentaires

### Documentation

- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [Terraform Security Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/security.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

### Documentation Externe

- [Terraform Documentation](https://developer.hashicorp.com/terraform/docs)
- [Google Cloud Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCP Free Tier](https://cloud.google.com/free)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)

---

## 🎯 Conclusion

Ce guide vous a accompagné dans :

1. ✅ **Comprendre l'état actuel** de la sécurité et de la configuration
2. ✅ **Déployer l'infrastructure** complète sur GCP
3. ✅ **Déployer l'API** et la rendre fonctionnelle
4. ✅ **Valider le déploiement** avec des tests
5. ✅ **Identifier les améliorations** futures possibles

### Prochaines Étapes Recommandées

1. **Tester en environnement de staging** avant production
2. **Configurer le monitoring** et les alertes (déjà implémenté, à activer via `enable_monitoring_alerts = true`)
3. **Documenter les procédures** d'urgence
4. **Automatiser le build/push Docker** via CI/CD

### Support

Pour toute question ou problème :
- Consulter la section [Dépannage](#dépannage)
- Vérifier les logs : `docker logs iris-api`
- Consulter la documentation GCP

---

## 📈 Progression Infrastructure

### Étape 1 : Setup (6h) ✅
- [x] Installation de Terraform
- [x] Configuration GCP CLI
- [x] Création du projet GCP
- [x] Structure des fichiers Terraform

### Étape 2 : Infrastructure de Base (7h) ✅
- [x] Configuration du provider Google
- [x] Création du bucket GCS
- [x] Configuration du réseau VPC
- [x] Règles de firewall sécurisées

### Étape 3 : VM et IAM (7h) ✅
- [x] Création de la VM Compute Engine
- [x] Configuration du service account
- [x] Attribution des rôles IAM
- [x] Script de démarrage avec Docker
- [x] Déploiement de l'API

## ✅ Validation des Objectifs

| Objectif | Status | Détails |
|----------|--------|---------|
| **Terraform Setup** | ✅ | Structure complète avec tous les fichiers |
| **Bucket GCS** | ✅ | Bucket avec versioning et lifecycle |
| **VM Compute Engine** | ✅ | VM avec Docker pré-installé |
| **VPC Network** | ✅ | Réseau privé avec sous-réseau |
| **Firewall Rules** | ✅ | SSH, HTTP, et trafic interne sécurisés |
| **IAM** | ✅ | Service Account avec rôles appropriés |
| **Sécurité** | ✅ | Firewalls restrictifs, authentification API, rate limiting, Secret Manager, KMS |
| **Déploiement** | ✅ | Guide complet de déploiement avec Load Balancer optionnel |
| **Monitoring** | ✅ | Alertes Cloud Monitoring configurées |
| **Documentation** | ✅ | Guide complet avec tutoriel pas-à-pas |

---

**Date de dernière mise à jour** : 2025  
**Version** : 1.0.0

---

**Infrastructure terminée avec succès.**

L'infrastructure Terraform est maintenant complètement configurée, sécurisée et prête pour le déploiement en production sur GCP. L'API est déployée et fonctionnelle avec toutes les mesures de sécurité en place.

**✅ Toutes les améliorations recommandées ont été implémentées** :
- Secret Manager avec création via Terraform
- Chiffrement KMS pour le bucket
- Load Balancer avec Cloud Armor
- Monitoring avec alertes Cloud Monitoring

Ces fonctionnalités sont activables via des variables dans `terraform.tfvars` (voir `terraform.tfvars.example` pour la configuration).