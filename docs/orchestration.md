# Orchestration — Kubernetes

Ce document explique **comment déployer et faire tourner l’API ML sur un cluster Kubernetes** (local ou cloud). Vous y trouverez : les **concepts K8s** utiles (Pods, Deployments, Services, volumes), l’**architecture** du projet (API, MLflow, Job d’entraînement), un **guide de déploiement** pas à pas, les **trois workflows MLflow** (modèle local, entraînement en cluster, GCS), ainsi que l’**auto-scaling**, les **tests** et le **dépannage**.

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| [Expérimentation](experimentation.md) | [Observabilité](observability.md) |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 📋 Table des Matières

1. [Objectif](#-objectif)
2. [Tâches à Accomplir](#-tâches-à-accomplir)
3. [Livrables Créés](#-livrables-créés)
4. [Fonctionnalités Implémentées](#-fonctionnalités-implémentées)
5. [Concepts Kubernetes](#-concepts-kubernetes)
6. [Architecture du Déploiement](#-architecture-du-déploiement)
7. [Installation et Configuration](#-installation-et-configuration)
8. [Guide de Déploiement](#-guide-de-déploiement)
9. [Workflows MLflow](#-workflows-mlflow)
10. [Auto-Scaling avec HPA](#-auto-scaling-avec-hpa)
11. [Tests et Validation](#-tests-et-validation)
12. [Commandes Utiles](#-commandes-utiles)
13. [Sécurité](#-sécurité)
14. [Dépannage](#-dépannage)
15. [Métriques](#-métriques)
16. [Validation des Objectifs](#-validation-des-objectifs)
17. [Prochaines étapes](#-prochaines-étapes-observabilité)
18. [Ressources](#-ressources)

---

## 🎯 Objectif

**Orchestrer l’application ML containerisée sur Kubernetes avec haute disponibilité et auto-scaling.**

À la fin de ce parcours, vous saurez déployer l’API FastAPI et le serveur MLflow sur un cluster (minikube/kind ou cloud), gérer la configuration et les secrets, et faire évoluer le nombre de pods selon la charge.

### ❓ Questions auxquelles ce document répond

- Qu’est-ce qu’un Pod, un Deployment et un Service dans Kubernetes ?
- Comment exposer une application dockerisée dans un cluster K8s ?
- Comment gérer les configurations et secrets dans Kubernetes ?
- Comment mettre en place le scaling automatique basé sur les métriques ?

### ⏱️ Répartition indicative (20 h)

| Phase | Durée | Contenu |
|-------|--------|---------|
| Concepts K8s | 8 h | Pods, Deployments, Services, ConfigMaps, Secrets, Namespaces |
| Installation | 8 h | kubectl, minikube ou kind, cluster local |
| Déploiement | 4 h | Manifests, API + MLflow, health checks, exposition |

---

## 📋 Tâches à Accomplir

Les tâches ci-dessous correspondent au parcours type : de l’apprentissage des concepts à la mise en production sur le cluster.

### 1. 🎓 Apprendre les Concepts Kubernetes
- Comprendre l'architecture d'un cluster Kubernetes
- Maîtriser les concepts de base : Pods, Deployments, Services
- Gérer les configurations avec ConfigMaps et Secrets
- Comprendre les Namespaces pour l'isolation

### 2. 🛠️ Installation et Configuration
- Installer kubectl (client Kubernetes)
- Configurer un cluster local (minikube ou kind)
- Vérifier la connectivité au cluster

### 3. 🚀 Déploiement de l'Application
- Créer les manifests Kubernetes (Deployment, Service, ConfigMap, Secret)
- Déployer l'API FastAPI sur le cluster
- Configurer les health checks (liveness et readiness probes)
- Exposer l'API via Service et Ingress

### 4. 📊 Intégration MLflow
- Déployer un serveur MLflow dans le cluster
- Configurer le partage de volumes pour les données MLflow
- Connecter l'API au serveur MLflow

### 5. ⚖️ Auto-Scaling
- Configurer le Horizontal Pod Autoscaler (HPA)
- Définir les métriques de scaling (CPU, mémoire)
- Tester le scaling automatique

---

## 📦 Livrables Créés

Cette section liste les **fichiers et ressources Kubernetes** produits par le projet. Ils permettent de déployer l’API, le serveur MLflow, le job d’entraînement et l’auto-scaling.

### Structure des Fichiers Kubernetes

```
k8s/
├── namespace.yaml              # Namespace mlops pour isolation
├── deployment.yaml             # Deployment API (2 replicas)
├── mlflow-deployment.yaml      # Deployment MLflow server (1 replica)
├── mlflow-pvc.yaml             # PVC pour les runs MLflow (/app/mlruns)
├── models-pvc.yaml             # PVC pour les modèles et métadonnées (/app/models)
├── train-job.yaml              # Job Kubernetes pour entraîner le modèle et mettre à jour /app/models
├── service.yaml                # Service ClusterIP pour l'API
├── mlflow-service.yaml         # Service ClusterIP pour MLflow
├── service-nodeport.yaml       # Service NodePort (dev/test)
├── configmap.yaml              # Configuration non sensible
├── secret.yaml.example         # Template pour secrets
├── ingress.yaml                # Ingress pour exposition externe
├── hpa.yaml                    # Horizontal Pod Autoscaler
└── README.md                   # Guide rapide de déploiement
```

### Fichiers Principaux

#### `k8s/deployment.yaml` - Déploiement de l'API
- **Replicas** : 2 pods pour haute disponibilité
- **Strategy** : RollingUpdate (zero-downtime)
- **Health Checks** : Liveness et readiness probes sur `/health`
- **Ressources** : Requests et limits CPU/mémoire
- **Sécurité** : Containers non-root, capabilities limitées
- **Volumes** :
  - `mlruns-volume` (hostPath) pour le mode MLflow local (développement)
  - `models-volume` (PVC `models-pvc`) pour les fichiers de modèle (`/app/models`)

#### `k8s/mlflow-deployment.yaml` - Serveur MLflow
- **Replicas** : 1 (singleton)
- **Strategy** : Recreate (serveur avec état)
- **Image** : `ghcr.io/mlflow/mlflow:v2.9.2`
- **Backend Store** : Fichier local (`file:///app/mlruns`)
- **Volume** : PVC dédié `mlflow-pvc` pour les runs MLflow (params, metrics, tags). Avec artifact root `file://`, les artifacts ne sont pas enregistrés sur le serveur depuis un client distant ; pour le serving, le job écrit `model.joblib` dans le PVC `models-pvc`.

#### `k8s/train-job.yaml` - Job d'Entraînement dans le Cluster
- **Kind** : `Job` (Batch)
- **Image** : `iris-api:latest` (réutilise le code d'entraînement existant)
- **Rôle** :
  - Entraîne le modèle dans le cluster
  - Loggue le run dans MLflow (`MLFLOW_TRACKING_URI` = `mlflow-server-service`)
  - Écrit `model.joblib`, `metadata.json` et `metrics.json` dans `/app/models` (PVC `models-pvc`)

#### `k8s/service.yaml` - Service ClusterIP
- **Type** : ClusterIP (accès interne uniquement)
- **Port** : 8000
- **Selector** : `app: iris-api`
- **Load Balancing** : Round-robin entre les pods

#### `k8s/configmap.yaml` - Configuration
- Variables d'environnement non sensibles :
  - `ENVIRONMENT`: production
  - `MODEL_DIR`: /app/models
  - `LOG_LEVEL`: INFO

#### `k8s/secret.yaml.example` - Template Secrets
- `API_KEY`: Clé API pour authentification
- `MLFLOW_TRACKING_URI`: URI du serveur MLflow ou GCS

#### `k8s/hpa.yaml` - Auto-Scaling
- **Min replicas** : 2
- **Max replicas** : 10
- **Métriques** : CPU (70%) et mémoire (80%)
- **Comportement** : Scaling up réactif, scaling down prudent

#### `k8s/ingress.yaml` - Exposition Externe
- **Controller** : nginx-ingress
- **TLS** : Support HTTPS (cert-manager)
- **Annotations** : Rate limiting, CORS, timeouts

**En résumé** : L’API et MLflow sont déployés via des Deployments ; le **Job** `iris-train-job` entraîne le modèle et écrit dans le PVC `models-pvc` ; l’API charge le modèle depuis `/app/models`. Les ConfigMaps et Secrets fournissent la configuration et les clés.

---

## ✅ Fonctionnalités Implémentées

Cette section récapitule **ce qui est déjà en place** dans le projet : déploiement, services, configuration, MLflow, HPA et commandes Makefile.

### Déploiement Kubernetes
- ✅ Namespace `mlops` pour isolation
- ✅ Deployment avec 2 replicas pour haute disponibilité
- ✅ Rolling update sans interruption de service
- ✅ Health checks (liveness et readiness probes)
- ✅ Gestion des ressources (requests et limits)
- ✅ Sécurité renforcée (non-root, capabilities limitées)

### Services et Exposition
- ✅ Service ClusterIP pour accès interne
- ✅ Service NodePort pour développement/test
- ✅ Ingress pour exposition externe avec TLS
- ✅ Load balancing automatique entre pods

### Configuration et Secrets
- ✅ ConfigMap pour variables d'environnement non sensibles
- ✅ Secrets Kubernetes pour données sensibles (API keys)
- ✅ Injection via `envFrom` et `env`
- ✅ Template de secret avec instructions

### MLflow Integration
- ✅ Serveur MLflow déployé dans le cluster
- ✅ Partage de volumes entre API et MLflow
- ✅ Service ClusterIP pour accès interne
- ✅ Support de trois modes :
  - Serveur MLflow dans K8s (recommandé)
  - Local avec hostPath (développement)
  - GCS (production cloud)

> 🔍 **Note d’architecture**  
> Dans ce projet, MLflow est utilisé comme **source de vérité analytique** (UI, runs, Model Registry),
> tandis que le **runtime de l’API** consomme une copie contrôlée du modèle via un PVC (`/app/models`).
> Cela évite de dépendre d’implémentations parfois ambiguës de `mlruns/.../artifacts` avec un backend
> `file:///` et un serveur HTTP, tout en restant très proche d’un setup réel (Job d’entraînement → PVC
> → API). En contexte entreprise, la v2 naturelle serait : **backend SQL + object store (S3/MinIO/GCS) +
> chargement `models:/name/stage` côté API**.

### Auto-scaling
- ✅ Horizontal Pod Autoscaler (HPA) configuré
- ✅ Scaling basé sur CPU et mémoire
- ✅ Comportement configurable (stabilisation, politiques)
- ✅ Métriques via metrics-server

### Commandes Makefile
- ✅ `make k8s-setup` : Installation minikube/kind
- ✅ `make k8s-deploy` : Déploiement API (avec PVC, sans serveur MLflow)
- ✅ `make k8s-deploy-mlflow` : Déploiement API + MLflow server (avec PVC)
- ✅ `make k8s-status` : Vérification du statut
- ✅ `make k8s-logs` : Visualisation des logs
- ✅ `make k8s-port-forward` : Accès à l'API
- ✅ `make k8s-mlflow-ui` : Accès à MLflow UI
- ✅ `make k8s-test` : Tests automatisés
- ✅ `make k8s-clean` : Nettoyage complet

---

## 🎓 Concepts Kubernetes

Avant de déployer, il est utile de comprendre les **concepts de base** utilisés dans ce projet. Chaque concept est illustré par son usage concret (API, MLflow, Job).

### Pod

**Plus petite unité déployable** dans Kubernetes. Un Pod contient un ou plusieurs containers qui partagent :
- Le même réseau (même IP)
- Le même stockage (volumes)
- Le même namespace

**Exemple** : Un Pod contient l'API FastAPI.

### Deployment
**Orchestrateur qui gère un ensemble de Pods identiques** (replicas). Assure :
- ✅ Création et mise à jour des Pods
- ✅ Rolling update (déploiement sans interruption)
- ✅ Rollback en cas de problème
- ✅ Scaling (augmentation/réduction)

**Dans notre cas** : 2 Pods identiques pour la haute disponibilité.

### Service
**Expose un ensemble de Pods comme un service réseau**. Fournit :
- ✅ IP stable (ClusterIP)
- ✅ Équilibrage de charge entre les Pods
- ✅ DNS interne (`service-name.namespace.svc.cluster.local`)

**Types** :
- **ClusterIP** : Accès interne uniquement
- **NodePort** : Accès externe via port sur chaque node
- **LoadBalancer** : IP publique externe (cloud)
- **Ingress** : Routage HTTP/HTTPS basé sur domaine

### ConfigMap
**Stocke des données de configuration non sensibles** (clé-valeur).

**Dans notre cas** : `ENVIRONMENT`, `MODEL_DIR`, `LOG_LEVEL`.

### Secret
**Stocke des données sensibles** (clés API, mots de passe). Similaire à ConfigMap mais :
- ✅ Encodé en base64
- ✅ Plus sécurisé (ne pas exposer dans les logs)

**Dans notre cas** : `API_KEY`, `MLFLOW_TRACKING_URI`.

### Namespace
**Isole des ressources dans un cluster**. Utile pour :
- ✅ Séparer les environnements (dev, staging, prod)
- ✅ Limiter les permissions (RBAC)
- ✅ Organiser les ressources

**Dans notre cas** : Namespace `mlops` pour toutes les ressources.

### Volume
**Permet aux pods de partager des données**. Types :
- **hostPath** : Monte un répertoire de la machine hôte (surtout pour le dev local)
- **PersistentVolume / PersistentVolumeClaim (PVC)** : Stockage persistant géré par Kubernetes
- **ConfigMap/Secret** : Montés comme volumes

**Dans notre cas** :
- Un **PVC dédié** (`mlflow-pvc`) pour stocker les runs MLflow dans `/app/mlruns` (mode serveur K8s)
- Un **hostPath + minikube mount** uniquement pour le mode local (développement)

### HPA (Horizontal Pod Autoscaler)

**Ajuste automatiquement le nombre de replicas** selon les métriques (CPU, mémoire). Kubernetes compare l’utilisation actuelle aux seuils définis et ajoute ou retire des pods.

**Dans notre cas** : Scale entre 2 et 10 pods selon CPU (70 %) et mémoire (80 %).

**À retenir** : Pod = unité de base ; Deployment = orchestrateur de Pods identiques ; Service = point d’accès réseau stable ; ConfigMap/Secret = configuration ; Namespace = isolation ; Volume/PVC = stockage partagé ; HPA = scaling automatique.

---

## 🏗️ Architecture du Déploiement

Cette section décrit **comment les composants sont organisés** dans le cluster et comment ils communiquent (réseau, volumes, DNS).

### Vue d’ensemble

Le cluster héberge **deux applications métier** dans le namespace `mlops` (API et MLflow), et **optionnellement** un Ingress Controller dans un autre namespace pour exposer l’API vers l’extérieur.

| Application | Namespace | Rôle |
|-------------|-----------|------|
| **iris-api** (FastAPI) | `mlops` | API ML pour prédictions (2 replicas) |
| **mlflow-server** (MLflow) | `mlops` | Tracking des runs (params, metrics, tags) |
| **nginx** (Ingress Controller) | `ingress-nginx` | Optionnel : reverse proxy, routage HTTP/HTTPS |

### Namespaces

Le projet utilise le namespace **`mlops`** pour l’API et MLflow ; un namespace **`ingress-nginx`** (ou équivalent) est optionnel pour l’Ingress Controller.

#### Namespace `ingress-nginx`

**Rôle** : Héberge l'Ingress Controller nginx (optionnel, pour exposition externe)

**Ressources** :
- Deployment `ingress-nginx-controller`
- Service `ingress-nginx-controller` (LoadBalancer ou NodePort)
- ConfigMaps, Secrets pour la configuration nginx

**Installation** :
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

**Vérification** :
```bash
kubectl get pods -n ingress-nginx
kubectl get service -n ingress-nginx
```

#### Namespace `mlops`

**Rôle** : Héberge les applications métier (API et MLflow)

**Ressources** :
- Deployment `iris-api` (2 replicas)
- Deployment `mlflow-server` (1 replica)
- Services `iris-api-service` et `mlflow-server-service`
- ConfigMap `iris-api-config`
- Secret `iris-api-secrets`
- Ingress `iris-api-ingress` (optionnel)
- HPA `iris-api-hpa` (optionnel)

**Création** :
```bash
kubectl apply -f k8s/namespace.yaml
```

**Vérification** :
```bash
kubectl get all -n mlops
```

### Applications et pods

Chaque application est déployée via un **Deployment** (ou équivalent) et exposée via un **Service**.

#### 1. Nginx Ingress Controller (optionnel)

**Namespace** : `ingress-nginx` (ou `kube-system`)

**Deployment** : `ingress-nginx-controller`

**Container** :
- **Image** : `registry.k8s.io/ingress-nginx/controller`
- **Application** : nginx (reverse proxy)
- **Ports** : 80 (HTTP), 443 (HTTPS)

**Rôle** :
- ✅ Lit les règles Ingress de tous les namespaces
- ✅ Route le trafic HTTP/HTTPS vers les Services appropriés
- ✅ Gère TLS/HTTPS (terminaison SSL)
- ✅ Rate limiting (protection DDoS)
- ✅ CORS (Cross-Origin Resource Sharing)
- ✅ Load balancing au niveau HTTP

**Service** :
- **Type** : `LoadBalancer` (production cloud) ou `NodePort` (local)
- **Accès** : Production via IP publique du LoadBalancer, Local via `http://<node-ip>:<nodePort>`

#### 2. Iris API (FastAPI)

**Namespace** : `mlops`

**Deployment** : `iris-api`

**Pods** : `iris-api-<hash>-1`, `iris-api-<hash>-2` (2 replicas)

**Container** :
- **Image** : `iris-api:latest` (ou depuis Artifact Registry)
- **Application** : FastAPI (serveur web Python)
- **Port** : 8000

**Rôle** :
- ✅ API REST pour prédictions ML
- ✅ Endpoints : `/predict`, `/health`, `/metrics`
- ✅ Authentification via API Key
- ✅ Charge les modèles depuis MLflow
- ✅ Métriques Prometheus

**Service** :
- **Type** : `ClusterIP` (accès interne uniquement)
- **DNS** : `iris-api-service.mlops.svc.cluster.local`
- **Port** : 8000

**Accès** :
- Depuis nginx : `http://iris-api-service:8000`
- Depuis mlflow-server : `http://iris-api-service:8000`
- Depuis l'extérieur : Via port-forward ou Ingress

#### 3. MLflow Server

**Namespace** : `mlops`

**Deployment** : `mlflow-server`

**Pod** : `mlflow-server-<hash>` (1 replica)

**Container** :
- **Image** : `ghcr.io/mlflow/mlflow:v2.9.2`
- **Application** : MLflow (serveur de tracking ML)
- **Port** : 5000

**Rôle** :
- ✅ Stocke les runs ML (expériences, paramètres, métriques, tags)
- ✅ UI MLflow (interface web) et API REST
- ✅ Avec backend `file://`, les artifacts ne sont pas stockés sur le serveur depuis un client distant ; le serving du modèle repose sur le PVC `models-pvc` (voir [Workflows MLflow](#-workflows-mlflow))

**Service** :
- **Type** : `ClusterIP` (accès interne uniquement)
- **DNS** : `mlflow-server-service.mlops.svc.cluster.local`
- **Port** : 5000

**Accès** :
- Depuis iris-api : `http://mlflow-server-service:5000`
- Depuis l'extérieur : Via port-forward (`make k8s-mlflow-ui`)

### Services

Chaque application est exposée via un **Service** (ClusterIP dans ce projet) pour un accès réseau stable et un load balancing entre les pods.

#### Service iris-api

**Namespace** : `mlops`

**Nom** : `iris-api-service`

**Type** : `ClusterIP` (interne uniquement)

**Port** : 8000 → 8000

**Sélecteur** : `app: iris-api`

**DNS** : `iris-api-service.mlops.svc.cluster.local`

**Rôle** :
- ✅ Load balancing entre les 2 pods iris-api
- ✅ DNS stable (même si les pods redémarrent)
- ✅ Point d'accès unique pour nginx

**Accès depuis nginx** :
```yaml
# Dans ingress.yaml
backend:
  service:
    name: iris-api-service  # Service dans namespace mlops
    port:
      number: 8000
```

#### Service mlflow-server

**Namespace** : `mlops`

**Nom** : `mlflow-server-service`

**Type** : `ClusterIP` (interne uniquement)

**Port** : 5000 → 5000

**Sélecteur** : `app: mlflow-server`

**DNS** : `mlflow-server-service.mlops.svc.cluster.local`

**Rôle** :
- ✅ Point d'accès stable pour mlflow-server
- ✅ Utilisé par iris-api pour charger les modèles

**Accès depuis iris-api** :
```python
# Dans le code Python
MLFLOW_TRACKING_URI = "http://mlflow-server-service:5000"
```

### Communication inter-namespace

Kubernetes permet la communication entre namespaces via le **DNS interne**. Chaque Service a une adresse DNS stable.

#### Format DNS Kubernetes

```
<service-name>.<namespace>.svc.cluster.local
```

#### Exemples dans l'Architecture

**1. Nginx → Iris API** :
```yaml
# Dans ingress.yaml (namespace: mlops)
# Nginx (namespace: ingress-nginx) lit cette règle
backend:
  service:
    name: iris-api-service  # Service dans namespace mlops
    port:
      number: 8000
```

**DNS utilisé** : `iris-api-service.mlops.svc.cluster.local:8000`

**2. Iris API → MLflow Server** :
```python
# Dans secret.yaml (namespace: mlops)
MLFLOW_TRACKING_URI: "http://mlflow-server-service:5000"
# ou explicitement :
# MLFLOW_TRACKING_URI: "http://mlflow-server-service.mlops.svc.cluster.local:5000"
```

**DNS utilisé** : `mlflow-server-service.mlops.svc.cluster.local:5000`

#### Raccourci DNS

Dans le même namespace, vous pouvez utiliser juste le nom du service :

```python
# Dans namespace mlops
MLFLOW_TRACKING_URI: "http://mlflow-server-service:5000"
# Équivalent à :
# MLFLOW_TRACKING_URI: "http://mlflow-server-service.mlops.svc.cluster.local:5000"
```

### Volumes partagés

Les pods ont besoin de **stockage persistant** pour les runs MLflow et pour les fichiers de modèle utilisés par l’API. Cette section décrit les volumes utilisés.

#### Volume `mlruns-volume` (mode serveur K8s)

**Type** : `PersistentVolumeClaim`

**PVC** : `mlflow-pvc`

**Monté dans** :

**1. Pod mlflow-server** :
```yaml
volumeMounts:
- name: mlruns-volume
  mountPath: /app/mlruns  # MLflow stocke tout ici
  readOnly: false
```

**Usage** :
- ✅ Toujours nécessaire en mode serveur K8s (MLflow stocke les runs dans `/app/mlruns`)

**2. Pods iris-api (optionnel)** :

Si l'API devait accéder aux artifacts MLflow (par ex. avec un artifact store partagé ou en mode local avec hostPath), elle pourrait monter le même PVC. Dans le setup actuel, l'API charge le modèle depuis `/app/models` (PVC `models-pvc`) où le job écrit `model.joblib`.

```yaml
volumeMounts:
- name: mlruns-volume
  mountPath: /app/mlruns  # Accès en lecture/écriture aux artifacts MLflow (si partagés)
  readOnly: false
```

#### Mode Local avec `hostPath` (Développement uniquement)

En mode local (sans serveur MLflow dans K8s), on peut continuer à utiliser un `hostPath` + `minikube mount` :

```bash
minikube mount $(pwd)/mlruns:/tmp/mlruns
```

Puis monter `/tmp/mlruns` dans les pods :

```yaml
volumes:
- name: mlruns-volume
  hostPath:
    path: /tmp/mlruns
    type: DirectoryOrCreate

volumeMounts:
- name: mlruns-volume
  mountPath: /app/mlruns
  readOnly: false
```

**Usage** :
- ✅ Utile pour expérimenter rapidement en local
- ❌ À éviter en production (préférer un PVC ou un backend objet type GCS/S3)

#### Partage de données

**Avec serveur MLflow dans K8s** : Le serveur MLflow stocke les runs dans `/app/mlruns` (PVC `mlflow-pvc`). L’API charge le modèle depuis `/app/models` (PVC `models-pvc`), pas depuis les artifacts MLflow lorsque le backend est `file://`. Le volume `mlruns` est donc utilisé par le serveur MLflow ; le volume `models` est utilisé par l’API et le Job d’entraînement.

**Mode local (hostPath)** : Le répertoire `mlruns/` de la machine est monté dans le cluster ; l’API charge le modèle depuis `/app/mlruns` (metadata + run MLflow).

### Flux de trafic

Comment les requêtes circulent entre le client, l’API et MLflow (Ingress, interne, port-forward).

#### Flux 1 : Client → API (via Ingress)

**Étapes** :
1. Client Internet envoie une requête HTTP/HTTPS vers `iris-api.example.com`
2. DNS résout vers l'IP du LoadBalancer (nginx)
3. Service `ingress-nginx-controller` route vers le Pod nginx (namespace: `ingress-nginx`)
4. Nginx lit les règles Ingress (cherche dans TOUS les namespaces)
5. Nginx trouve l'Ingress `iris-api-ingress` (namespace: `mlops`)
6. Nginx route vers le Service `iris-api-service` (namespace: `mlops`)
7. Service load balance vers un Pod iris-api (1 ou 2)
8. FastAPI traite la requête et retourne la réponse

#### Flux 2 : API → chargement du modèle

**Comportement actuel** : L’API charge en priorité le modèle depuis le fichier local `/app/models/model.joblib` (PVC `models-pvc`). Si ce fichier n’existe pas, elle peut interroger le serveur MLflow (`http://mlflow-server-service:5000`) pour récupérer les métadonnées ou le modèle (par ex. avec un backend GCS). Avec un backend `file://` sur MLflow, les artifacts ne sont pas sur le serveur ; le flux de serving repose donc sur le PVC `models-pvc`.

#### Flux 3 : Port-Forward (développement)

**Étapes** :
1. Votre machine locale utilise `kubectl port-forward`
2. Le port-forward se connecte directement au Service `iris-api-service`
3. Service load balance vers un Pod iris-api (1 ou 2)
4. FastAPI traite la requête et retourne la réponse sur `localhost:8000`

**Note** : Le port-forward contourne complètement nginx et l'Ingress.

### Modes MLflow

Selon la valeur de `MLFLOW_TRACKING_URI`, l’API et le Job utilisent un mode différent (serveur K8s, local, GCS).

| Mode | MLFLOW_TRACKING_URI | Volume | Usage |
|------|---------------------|--------|-------|
| **K8s Server** | `http://mlflow-server-service:5000` | PVC `mlflow-pvc` (monté sur `/app/mlruns`) | Portfolio/Production |
| **Local** | `""` | hostPath + `minikube mount` | Développement |
| **GCS** | `gs://bucket/mlruns/` | Aucun | Production cloud |

### Tableau récapitulatif

| Composant | Namespace | Type | Nom | Port | Accès |
|-----------|-----------|------|-----|------|-------|
| **nginx** | `ingress-nginx` | Deployment | `ingress-nginx-controller` | 80, 443 | Internet (LoadBalancer) |
| **iris-api** | `mlops` | Deployment | `iris-api` | 8000 | Interne (ClusterIP) |
| **mlflow-server** | `mlops` | Deployment | `mlflow-server` | 5000 | Interne (ClusterIP) |
| **Ingress** | `mlops` | Ingress | `iris-api-ingress` | - | Règles de routage |
| **Volume** | `mlops` | Volume | `mlruns-volume` / `models-volume` | - | Partagé (MLflow runs / modèles API) |

**En résumé** : L’API (`iris-api`) et MLflow (`mlflow-server`) tournent dans `mlops`. L’API appelle MLflow via le service `mlflow-server-service`. L’API charge le modèle depuis le PVC `models-pvc` (`/app/models`), pas depuis les artifacts MLflow lorsque le backend est `file://`. L’Ingress (optionnel) expose l’API vers l’extérieur.

---

## 🚀 Installation et Configuration

Cette section décrit **comment installer les outils** (kubectl, minikube ou kind) et créer un cluster local utilisable pour le reste du guide.

### Prérequis

| Outil | Version | Description |
|-------|---------|-------------|
| **kubectl** | >= 1.28 | Client Kubernetes |
| **Docker** | >= 20.10 | Pour minikube/kind |
| **minikube** ou **kind** | >= 1.30 / >= 0.20 | Cluster local (un des deux suffit) |

### Installation Automatique (Recommandé)

```bash
# Avec minikube
make k8s-setup

# Avec kind
make k8s-setup-kind

# Ou directement
./scripts/setup-k8s.sh minikube
./scripts/setup-k8s.sh kind
```

### Installation Manuelle

#### 1. Installer kubectl

**macOS** :
```bash
brew install kubectl
```

**Linux** :
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

#### 2. Installer minikube ou kind

**minikube** (macOS) :
```bash
brew install minikube
minikube start --driver=docker --memory=4096 --cpus=2
```

**kind** :
```bash
brew install kind  # macOS
kind create cluster --name mlops-cluster
```

#### 3. Vérifier

```bash
kubectl cluster-info
kubectl get nodes
```

---

## 🚀 Guide de Déploiement

Ce guide décrit **l’ordre recommandé** pour un premier déploiement : image Docker, secrets, application des manifests, vérification et accès à l’API et à MLflow.

### Étape 1 : Préparer l’image Docker

**Option A : Image Locale (minikube)**
```bash
eval $(minikube docker-env)
make build
```

**Option B : Artifact Registry (Production)**
```yaml
# Dans k8s/deployment.yaml
image: europe-west1-docker.pkg.dev/PROJECT_ID/mlops-repo/iris-api:latest
imagePullPolicy: Always
```

### Étape 2 : Préparer les Secrets

```bash
cp k8s/secret.yaml.example k8s/secret.yaml
# Éditer k8s/secret.yaml avec vos valeurs
# ⚠️ Ne jamais commiter secret.yaml dans le dépôt !
```

**Contenu de `k8s/secret.yaml`** :
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: iris-api-secrets
  namespace: mlops
type: Opaque
stringData:
  API_KEY: "votre-api-key-ici"  # openssl rand -hex 32
  MLFLOW_TRACKING_URI: "http://mlflow-server-service:5000"  # Ou "gs://bucket/mlruns/"
```

### Étape 3 : Déployer

**Option A : Avec MLflow Server** (Recommandé)
```bash
make k8s-deploy-mlflow
```

**Option B : MLflow Local**
```bash
# 1. Monter mlruns/ (terminal séparé)
minikube mount $(pwd)/mlruns:/tmp/mlruns

# 2. Déployer
make k8s-deploy
```

**Déploiement manuel (sans make)** : pour reproduire **`make k8s-deploy-mlflow`** (API + MLflow), appliquer dans l’ordre :
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/mlflow-pvc.yaml
kubectl apply -f k8s/models-pvc.yaml
kubectl apply -f k8s/mlflow-deployment.yaml
kubectl apply -f k8s/mlflow-service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Étape 4 : Vérifier le déploiement

```bash
make k8s-status
# ou
kubectl get pods,services -n mlops
```

**Résultat attendu** :
```
NAME                        READY   STATUS    RESTARTS   AGE
iris-api-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
iris-api-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
mlflow-server-xxxxx         1/1     Running   0          30s
```

### Étape 5 : Accéder à l’API et à MLflow

**Port-Forward** (Développement) :
```bash
make k8s-port-forward
# http://localhost:8000
```

**MLflow UI** (si déployé) :
```bash
make k8s-mlflow-ui
# http://localhost:5000
```

**NodePort** (Test) :
```bash
kubectl apply -f k8s/service-nodeport.yaml
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl http://$NODE_IP:30080/health
```

**Ingress** (production) :
```bash
# Installer Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f k8s/ingress.yaml
```

**En résumé** : Image → Secret → `make k8s-deploy-mlflow` (ou `k8s-deploy`) → vérifier les pods → accéder via port-forward, NodePort ou Ingress. Voir [k8s/README.md](../k8s/README.md) pour un guide pas à pas détaillé.

---

## 🔄 Workflows MLflow

**Trois façons** d’utiliser MLflow et l’API sur Kubernetes, selon la **source du modèle** (déjà entraîné en local, entraînement dans le cluster, backend cloud) et l’**environnement** (développement, cluster local, production GCP). Choisir le workflow adapté à votre cas.

---

### Workflow 1 : Utiliser un modèle déjà entraîné (local → cluster)

**Quand l’utiliser** : Vous avez déjà entraîné un modèle en local ; les runs sont dans `mlruns/`. Vous voulez servir ce modèle depuis l’API déployée sur le cluster sans serveur MLflow dans K8s.

**Idée** : Monter le répertoire `mlruns/` de votre machine vers le cluster (minikube), déployer l’API avec un volume hostPath pointant vers ce montage. L’API charge le modèle depuis `/app/mlruns` (metadata + run MLflow).

| Étape | Action |
|-------|--------|
| 1 | Dans un **terminal dédié** (laisser tourner) : `minikube mount $(pwd)/mlruns:/tmp/mlruns` |
| 2 | Dans le secret K8s : `MLFLOW_TRACKING_URI: ""` (ou chemin local). Puis déployer l’API : `make k8s-deploy` |
| 3 | Vérifier : `kubectl exec -it deployment/iris-api -n mlops -- ls -la /app/mlruns` |

**Résultat** : L’API lit les runs depuis le volume monté ; pas de serveur MLflow dans le cluster. Adapté au développement / démo.

---

### Workflow 2 : Entraîner dans le cluster et servir depuis le PVC (recommandé)

**Quand l’utiliser** : Vous voulez entraîner un nouveau modèle **dans le cluster**, tracker les runs dans MLflow, et servir le modèle via l’API. C’est le flux recommandé pour un usage “production” sur un cluster local (minikube/kind).

**Idée** : Un **Job** Kubernetes lance l’entraînement ; il écrit `model.joblib`, `metadata.json` et `metrics.json` dans le PVC `models-pvc` (monté en `/app/models`). Il envoie aussi params, metrics et tags au **serveur MLflow** (tracking uniquement : avec artifact root `file://`, les artifacts ne sont pas stockés sur le serveur). L’API monte le même PVC et charge le modèle depuis `/app/models`. Après chaque nouvel entraînement, on redémarre l’API pour qu’elle relise le PVC.

| Étape | Action |
|-------|--------|
| 1 | Déployer l’infra : namespace, PVC (`mlflow-pvc`, `models-pvc`), MLflow server, configmap, secret (`MLFLOW_TRACKING_URI="http://mlflow-server-service:5000"`), deployment et service de l’API. Ex. : `make k8s-deploy-mlflow` ou appliquer les manifests dans l’ordre. |
| 2 | Lancer le job d’entraînement : `kubectl delete job iris-train-job -n mlops --ignore-not-found` puis `kubectl apply -f k8s/train-job.yaml` ; suivre les logs : `kubectl logs job/iris-train-job -n mlops -f`. |
| 3 | Recharger l’API pour qu’elle relise `/app/models` : `kubectl rollout restart deployment/iris-api -n mlops`. |

**Option — Entraînement en local, tracking vers le serveur MLflow** : Si vous lancez `make train` en local avec `MLFLOW_TRACKING_URI="http://localhost:5000"` (après port-forward du service MLflow), seuls params, metrics et tags sont enregistrés sur le serveur ; les artifacts ne le sont pas. Pour servir ce modèle en cluster, il faut ensuite l’écrire dans le PVC (par ex. via un job ou une copie de `model.joblib` + metadata/metrics vers le volume).

**Résultat** : Modèle servi depuis `/app/models` (PVC partagé) ; MLflow utilisé pour le tracking (params, metrics, tags). Voir [k8s/README.md](../k8s/README.md) pour le détail des commandes.

---

### Workflow 3 : Production avec GCS (backend MLflow dans le cloud)

**Quand l’utiliser** : Environnement de production sur GCP ; le backend MLflow (runs + artifacts) est un bucket GCS. Pas de volume hostPath ni de PVC MLflow dans le cluster pour les runs.

**Idée** : Configurer `MLFLOW_TRACKING_URI` avec l’URI GCS du bucket (ex. `gs://bucket-name/mlruns/`). L’API et les jobs utilisent ce backend pour le tracking et le chargement du modèle ; pas besoin de monter `mlruns` dans les pods.

| Étape | Action |
|-------|--------|
| 1 | Créer un bucket GCS (ou utiliser un existant) et configurer dans le secret : `MLFLOW_TRACKING_URI: "gs://bucket-name/mlruns/"`. |
| 2 | Déployer l’API (namespace, configmap, secret, PVC, deployment, service) : **`make k8s-deploy`**. Les PVC sont inclus ; pas de serveur MLflow dans le cluster. |
| 3 | L’API charge le modèle depuis GCS via les métadonnées (ex. `metadata.json` ou run_id) ; les artifacts sont lus depuis le bucket. |

**Résultat** : Runs et artifacts MLflow dans GCS ; cluster K8s sans dépendance à un volume local pour MLflow.

---

## 📊 Auto-Scaling avec HPA

Le **Horizontal Pod Autoscaler (HPA)** ajuste automatiquement le nombre de replicas de l’API en fonction de l’utilisation CPU et mémoire. Utile en production pour absorber les pics de charge sans surdimensionner le cluster.

### Installation de metrics-server

Le HPA s’appuie sur les métriques fournies par **metrics-server** (utilisation CPU/mémoire des pods). À installer une fois sur le cluster.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Déploiement du HPA

```bash
kubectl apply -f k8s/hpa.yaml
```

### Vérification

```bash
kubectl get hpa -n mlops
kubectl describe hpa iris-api-hpa -n mlops
```

### Test du scaling

```bash
# Générer de la charge
while true; do curl http://localhost:8000/health; done

# Observer le scaling
watch kubectl get pods -n mlops
kubectl get hpa -n mlops
```

Le HPA scale automatiquement entre 2 et 10 pods selon CPU (70 %) et mémoire (80 %).

---

## 🧪 Tests et Validation

Cette section décrit **comment vérifier** que le déploiement fonctionne : health check, prédiction, logs, scaling.

### Test 1 : Health check

```bash
make k8s-port-forward  # Terminal 1
curl http://localhost:8000/health  # Terminal 2
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Test 2 : Prédiction (endpoint `/predict`)

```bash
export API_KEY=$(kubectl get secret iris-api-secrets -n mlops -o jsonpath='{.data.API_KEY}' | base64 -d)

curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'
```

### Test 3 : Logs (débogage)

```bash
make k8s-logs
# ou
kubectl logs -f deployment/iris-api -n mlops
```

### Test 4 : Scaling manuel

```bash
kubectl scale deployment iris-api --replicas=3 -n mlops
kubectl get pods -n mlops
```

### Test 5 : Auto-scaling (HPA)

```bash
# Installer metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Déployer HPA
kubectl apply -f k8s/hpa.yaml

# Générer de la charge
while true; do curl http://localhost:8000/health; done

# Observer le scaling
watch kubectl get pods -n mlops
```

---

## 📝 Commandes utiles

Les commandes ci-dessous couvrent le **cycle de vie** du déploiement : création du cluster, déploiement, statut, logs, accès, tests, nettoyage.

### Commandes Makefile

| Commande | Description |
|----------|-------------|
| `make k8s-setup` | Installer minikube et créer le cluster |
| `make k8s-setup-kind` | Installer kind et créer le cluster |
| `make k8s-deploy` | Déployer l'API (avec PVC, sans serveur MLflow) |
| `make k8s-deploy-mlflow` | Déployer API + serveur MLflow (avec PVC) |
| `make k8s-status` | Vérifier le statut |
| `make k8s-logs` | Voir les logs |
| `make k8s-port-forward` | Port-forward vers l'API |
| `make k8s-mlflow-ui` | Port-forward vers MLflow UI |
| `make k8s-test` | Tester l'API |
| `make k8s-clean` | Nettoyer complètement |

### Commandes kubectl essentielles

```bash
# Voir toutes les ressources
kubectl get all -n mlops

# Décrire un pod
kubectl describe pod <pod-name> -n mlops

# Exécuter une commande dans un pod
kubectl exec -it <pod-name> -n mlops -- /bin/bash

# Voir les événements
kubectl get events -n mlops --sort-by='.lastTimestamp'

# Redémarrer le déploiement
kubectl rollout restart deployment/iris-api -n mlops

# Rollback
kubectl rollout undo deployment/iris-api -n mlops

# Voir les ressources utilisées
kubectl top pods -n mlops
```

---

## 🔒 Sécurité

Cette section résume les **bonnes pratiques** déjà appliquées dans les manifests et les **recommandations** pour aller plus loin en production.

### Bonnes pratiques implémentées

- ✅ **Secrets Kubernetes** : Jamais en clair dans Git
- ✅ **Containers non-root** : `runAsNonRoot: true`, `runAsUser: 1000`
- ✅ **Capabilities limitées** : `drop: [ALL]`
- ✅ **Read-only root filesystem** : Optionnel (désactivé pour logs)
- ✅ **Seccomp profile** : `RuntimeDefault`
- ✅ **TLS via Ingress** : Support HTTPS en production
- ✅ **RBAC** : Permissions limitées par namespace

### Recommandations production

- 🔐 Utiliser External Secrets Operator avec Secret Manager GCP/AWS
- 🔐 Activer Network Policies pour isolation réseau
- 🔐 Configurer Pod Security Standards
- 🔐 Utiliser cert-manager pour TLS automatique
- 🔐 Activer audit logging
- 🔐 Scanner les images pour vulnérabilités (Trivy, Snyk)

---

## 🔍 Dépannage

En cas de problème, utiliser les commandes ci-dessous pour **diagnostiquer** (pods, API, secrets, image, HPA) et corriger les causes courantes.

### Pods ne démarrent pas

**Symptômes** : `Pending` ou `CrashLoopBackOff`

**Solutions** :
```bash
kubectl describe pod <pod-name> -n mlops
kubectl logs <pod-name> -n mlops
kubectl get events -n mlops --sort-by='.lastTimestamp'

# Causes courantes :
# - Image non trouvée : Vérifier deployment.yaml
# - Secrets manquants : Vérifier secret.yaml
# - Ressources insuffisantes : Vérifier le cluster
```

### API ne répond pas

**Solutions** :
```bash
kubectl get pods -n mlops
kubectl logs -f deployment/iris-api -n mlops
kubectl get service iris-api-service -n mlops

# Tester depuis un pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://iris-api-service:8000/health
```

### Secrets non trouvés

**Solutions** :
```bash
kubectl get secret iris-api-secrets -n mlops
kubectl describe secret iris-api-secrets -n mlops

# Recréer si nécessaire
kubectl delete secret iris-api-secrets -n mlops
kubectl apply -f k8s/secret.yaml
```

### Image non trouvée

**Avec minikube** :
```bash
eval $(minikube docker-env)
docker build -t iris-api:latest .
```

**Avec Artifact Registry** :
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
# Modifier deployment.yaml avec l'image complète
```

### HPA ne fonctionne pas

**Solutions** :
```bash
# Vérifier metrics-server
kubectl get deployment metrics-server -n kube-system

# Installer si nécessaire
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Vérifier les métriques
kubectl top pods -n mlops
kubectl describe hpa iris-api-hpa -n mlops
```

---

## 📊 Métriques

Résumé des **ressources et capacités** déployées par ce projet (nombre de manifests, pods, services, commandes).

| Métrique | Valeur |
|----------|--------|
| **Fichiers créés** | 10+ manifests Kubernetes |
| **Pods déployés** | 2 (API) + 1 (MLflow) |
| **Services** | 2 (ClusterIP) |
| **Auto-scaling** | 2-10 pods selon charge |
| **Health checks** | Liveness + Readiness |
| **Commandes Make** | 10+ commandes k8s-* |

---

## ✅ Validation des Objectifs

Tableau de **suivi des objectifs** du parcours : chaque ligne correspond à un objectif à valider.

| Objectif | Status | Détails |
|----------|--------|---------|
| **Concepts K8s** | ✅ | Compris : Pods, Deployments, Services, ConfigMaps, Secrets |
| **Installation** | ✅ | minikube/kind installé et cluster créé |
| **Manifests** | ✅ | Tous les manifests créés |
| **Déploiement** | ✅ | API déployée sur le cluster local |
| **Health Checks** | ✅ | Liveness et readiness probes configurés |
| **MLflow Integration** | ✅ | Serveur MLflow déployé et connecté |
| **Auto-Scaling** | ✅ | HPA configuré et fonctionnel |
| **Tests** | ✅ | API accessible et fonctionnelle |
| **Documentation** | ✅ | Guide complet avec exemples |

---

## 🚀 Prochaines étapes : Observabilité

Une fois l’orchestration en place, la suite logique est l’**observabilité** : métriques, dashboards, alertes.

Voir [Observabilité](observability.md) pour :
- 📊 Observabilité & Monitoring (Prometheus, Grafana, AlertManager)
- 🔍 Métriques avancées
- 📈 Dashboards de monitoring
- 🚨 Alertes et notifications

---

## 📚 Ressources

Liens utiles pour **aller plus loin** : documentation du projet, Kubernetes, minikube/kind, MLflow, HPA.

### Documentation

- [k8s/README.md](../k8s/README.md) — Déploiement et workflows (MLflow / API seule)
- [Kubernetes Documentation](https://kubernetes.io/docs/) - Documentation officielle
- [minikube](https://minikube.sigs.k8s.io/) - Cluster local
- [kind](https://kind.sigs.k8s.io/) - Kubernetes in Docker

### Ressources externes

- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [MLflow Kubernetes](https://mlflow.org/docs/latest/tracking.html#scenario-5-mlflow-on-kubernetes)
- [HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

---

**Orchestration terminée avec succès.**

L’API MLOps est maintenant déployée sur Kubernetes avec :
- ✅ Haute disponibilité (2 replicas)
- ✅ Health checks configurés
- ✅ Configuration et secrets gérés
- ✅ Auto-scaling optionnel (HPA)
- ✅ Serveur MLflow intégré
- ✅ Documentation complète

Le projet est prêt pour l’observabilité (Prometheus, Grafana, AlertManager).
