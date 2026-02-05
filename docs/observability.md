# Observabilité — Prometheus, Grafana, AlertManager

## 🧭 Navigation

| ← Précédent | Suivant → |
|-------------|-----------|
| [Orchestration](orchestration.md) | - |
| [Retour au README](../README.md) | [Documentation](README.md) |

## 📋 Table des Matières

1. [Objectif](#-objectif)
2. [Tâches à Accomplir](#-tâches-à-accomplir)
3. [Livrables Créés](#-livrables-créés)
4. [Fonctionnalités Implémentées](#-fonctionnalités-implémentées)
5. [Concepts d'Observabilité](#-concepts-dobservabilité)
6. [Architecture du Monitoring](#-architecture-du-monitoring)
7. [Installation et Configuration](#-installation-et-configuration)
8. [Guide de Déploiement](#-guide-de-déploiement)
9. [Métriques Collectées](#-métriques-collectées)
10. [Dashboards Grafana](#-dashboards-grafana)
11. [Règles d'Alerte](#-règles-dalerte)
12. [Tests et Validation](#-tests-et-validation)
13. [Commandes Utiles](#-commandes-utiles)
14. [Sécurité](#-sécurité)
15. [Dépannage](#-dépannage)
16. [Validation des Objectifs](#-validation-des-objectifs)
17. [Ressources](#-ressources)

---

## 🎯 Objectif

**Mettre en place une stack complète d'observabilité pour monitorer l'API ML en production avec collecte de métriques, visualisation et alertes**

### ❓ Questions Clés
- Comment collecter et stocker les métriques d'une application ML en production ?
- Comment visualiser les métriques pour comprendre le comportement du système ?
- Comment détecter et alerter sur les problèmes avant qu'ils n'impactent les utilisateurs ?
- Quelles métriques sont critiques pour une API ML en production ?

### ⏱️ Répartition des Heures (20h)
- **10h** → Configuration Prometheus pour scraper les métriques
- **7h** → Création de dashboards Grafana pour visualisation
- **3h** → Configuration d'AlertManager avec règles d'alerte

---

## 📋 Tâches à Accomplir

### 1. 🎓 Comprendre les Concepts d'Observabilité
- Comprendre les 3 piliers : métriques, logs, traces
- Maîtriser Prometheus (collecte, stockage, requêtes PromQL)
- Comprendre Grafana (visualisation, dashboards)
- Apprendre AlertManager (gestion des alertes, notifications)

### 2. 📊 Configuration Prometheus
- Déployer Prometheus sur Kubernetes
- Configurer le scraping des métriques de l'API
- Définir les règles d'alerte (PromQL)
- Configurer la rétention des données

### 3. 📈 Création de Dashboards Grafana
- Configurer Grafana avec Prometheus comme datasource
- Créer des dashboards pour les métriques API
- Créer des dashboards pour les métriques infrastructure
- Configurer les alertes visuelles

### 4. 🚨 Configuration AlertManager
- Déployer AlertManager
- Configurer le routage des alertes
- Définir les receivers (notifications)
- Tester les alertes

---

## 📦 Livrables Créés

### Structure des Fichiers Monitoring

```
k8s/monitoring/
├── prometheus-rbac.yaml              # RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)
├── prometheus-configmap.yaml         # Configuration Prometheus (scraping targets)
├── prometheus-rules.yaml             # Règles d'alerte Prometheus
├── prometheus-deployment.yaml       # Deployment + Service Prometheus
├── servicemonitor-iris-api.yaml     # ServiceMonitor pour l'API Iris
├── alertmanager-configmap.yaml      # Configuration AlertManager
├── alertmanager-deployment.yaml    # Deployment + Service AlertManager
├── grafana-configmap.yaml           # Configuration Grafana (datasources)
├── grafana-dashboards-configmap.yaml # Dashboards JSON
├── grafana-deployment.yaml          # Deployment + Service Grafana
├── deploy.sh                        # Script de déploiement
└── README.md                        # Guide de déploiement
```

### Fichiers Principaux

- **`prometheus-rbac.yaml`** : Permissions Kubernetes pour Prometheus
- **`prometheus-configmap.yaml`** : Configuration scraping, rétention, AlertManager
- **`prometheus-rules.yaml`** : Règles d'alerte (API down, erreurs, latence, modèle)
- **`prometheus-deployment.yaml`** : Déploiement Prometheus avec volumes
- **`servicemonitor-iris-api.yaml`** : Découverte automatique des métriques API
- **`alertmanager-configmap.yaml`** : Routage alertes, receivers, inhibitions
- **`alertmanager-deployment.yaml`** : Déploiement AlertManager
- **`grafana-configmap.yaml`** : Datasources, configuration dashboards
- **`grafana-dashboards-configmap.yaml`** : Dashboards JSON (API + Infrastructure)
- **`grafana-deployment.yaml`** : Déploiement Grafana avec secrets

---

## ✨ Fonctionnalités Implémentées

### ✅ Collecte de Métriques (Prometheus)
- Scraping automatique des métriques API via endpoint `/metrics`
- Découverte automatique des services Kubernetes
- Stockage avec rétention configurable (15 jours)
- Requêtes PromQL pour analyse

### ✅ Visualisation (Grafana)
- 2 dashboards pré-configurés :
  - **Iris API - Overview** : Métriques API (prédictions, confiance, erreurs, modèle)
  - **Kubernetes - Infrastructure** : Métriques infrastructure (CPU, mémoire, pods)
- Datasource Prometheus automatiquement configuré
- Authentification configurable

### ✅ Alertes (AlertManager)
- 6 règles d'alerte actives (7ème désactivée - nécessite métrique HTTP latency) :
  - API down (critical)
  - Taux d'erreur élevé (warning)
  - Latence élevée (warning)
  - Modèle non chargé (critical)
  - Taux de prédictions bas (info)
  - Pod en crash loop (warning)
  - Utilisation CPU/mémoire élevée (warning)
- Routage par sévérité
- Groupement et inhibition des alertes

### ✅ Intégration Kubernetes
- RBAC configuré pour Prometheus
- ServiceMonitor pour découverte automatique
- Déploiement dans le namespace `mlops`
- Health checks configurés

---

## 🎓 Concepts d'Observabilité

### Les 3 Piliers de l'Observabilité

1. **Métriques** : Mesures numériques agrégées dans le temps
   - Exemple : nombre de requêtes/seconde, latence p95, taux d'erreur
   - Avantage : léger, efficace, historique
   - Outil : Prometheus

2. **Logs** : Événements textuels avec timestamp
   - Exemple : erreurs, warnings, traces d'exécution
   - Avantage : contexte détaillé, débogage
   - Outil : ELK, Loki, Cloud Logging

3. **Traces** : Suivi d'une requête à travers plusieurs services
   - Exemple : durée de chaque étape d'une requête
   - Avantage : compréhension du flux complet
   - Outil : Jaeger, Zipkin, OpenTelemetry

**L’observabilité se concentre sur les métriques** (Prometheus/Grafana).

### Prometheus

**Prometheus** est un système de monitoring et d'alerte open-source qui :
- **Collecte** les métriques via scraping (pull model)
- **Stocke** les métriques dans une base de données temporelle
- **Interroge** les métriques via PromQL (langage de requête)
- **Alerte** via AlertManager

**Architecture** :
```
Application → /metrics endpoint → Prometheus (scraping) → Time Series DB
                                                              ↓
                                                         PromQL queries
                                                              ↓
                                                         Grafana / AlertManager
```

**Métriques Prometheus** :
- **Counter** : Valeur qui ne peut qu'augmenter (ex: `model_predictions_total`)
- **Gauge** : Valeur qui peut augmenter ou diminuer (ex: `model_loaded`)
- **Histogram** : Distribution de valeurs (ex: `model_confidence`)
- **Summary** : Similaire à Histogram mais avec quantiles calculés côté client

### Grafana

**Grafana** est une plateforme de visualisation qui :
- Se connecte à Prometheus (et autres datasources)
- Crée des dashboards interactifs
- Configure des alertes visuelles
- Partage des dashboards

**Dashboards** : Collections de panneaux (graphs, stats, tables) affichant des métriques.

### AlertManager

**AlertManager** gère les alertes Prometheus :
- **Routage** : Envoie les alertes aux bons receivers selon les labels
- **Groupement** : Regroupe les alertes similaires
- **Inhibition** : Supprime certaines alertes si d'autres sont actives
- **Notifications** : Envoie via Slack, email, PagerDuty, etc.

---

## 🏗️ Architecture du Monitoring

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  Iris API     │         │  Prometheus   │                 │
│  │  (FastAPI)    │◄────────┤  (Scraper)    │                 │
│  │  /metrics     │  scrape │  (Storage)    │                 │
│  └──────────────┘         └───────┬────────┘                 │
│                                   │                           │
│                                   │ PromQL                    │
│                                   │                           │
│  ┌──────────────┐         ┌───────▼────────┐                 │
│  │   Grafana    │◄────────┤  Prometheus   │                 │
│  │ (Dashboards) │  query   │    (Query)     │                 │
│  └──────────────┘         └───────┬────────┘                 │
│                                   │                           │
│                                   │ Alerts                    │
│                                   │                           │
│                          ┌────────▼────────┐                 │
│                          │  AlertManager   │                 │
│                          │  (Notifications)│                 │
│                          └─────────────────┘                 │
│                                   │                           │
│                                   │ Notifications             │
│                                   │ (Slack, Email, etc.)     │
│                          ┌────────▼────────┐                 │
│                          │   Receivers      │                 │
│                          └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### Composants

#### 1. Prometheus
- **Rôle** : Collecte, stocke et interroge les métriques
- **Port** : 9090
- **Storage** : Time Series Database (TSDB)
- **Rétention** : 15 jours (configurable)

#### 2. Grafana
- **Rôle** : Visualisation des métriques via dashboards
- **Port** : 3000
- **Datasource** : Prometheus (automatiquement configuré)
- **Authentification** : Admin/admin par défaut (à changer en production)

#### 3. AlertManager
- **Rôle** : Gestion des alertes et notifications
- **Port** : 9093
- **Configuration** : Routage, groupement, inhibition

### Flux de Données

1. **Collecte** :
   - L'API Iris expose `/metrics` avec les métriques Prometheus
   - Prometheus scrape cet endpoint toutes les 15 secondes
   - Les métriques sont stockées dans la TSDB

2. **Visualisation** :
   - Grafana interroge Prometheus via PromQL
   - Les dashboards affichent les métriques en temps réel
   - Mise à jour automatique (rafraîchissement configurable)

3. **Alertes** :
   - Prometheus évalue les règles d'alerte toutes les 15 secondes
   - Si une condition est remplie, une alerte est envoyée à AlertManager
   - AlertManager route l'alerte selon la sévérité
   - Notification envoyée (Slack, email, etc.)

---

## 🔧 Installation et Configuration

### Prérequis

- Cluster Kubernetes fonctionnel (minikube, kind, ou GKE)
- Namespace `mlops` créé
- API Iris déployée et fonctionnelle
- `kubectl` installé et configuré

### Installation

#### Option 1 : Via Makefile (Recommandé)

```bash
# Déployer la stack de monitoring
make k8s-monitoring-deploy

# Vérifier le statut
make k8s-monitoring-status

# Port-forward pour accéder aux interfaces
make k8s-monitoring-port-forward
```

#### Option 2 : Via Script

```bash
cd k8s/monitoring
./deploy.sh
```

#### Option 3 : Manuellement

```bash
# Déployer tous les manifests
kubectl apply -f k8s/monitoring/

# Vérifier les pods
kubectl get pods -n mlops -l component=monitoring
```

### Configuration

#### Prometheus

La configuration Prometheus est dans `prometheus-configmap.yaml` :

```yaml
global:
  scrape_interval: 15s          # Fréquence de scraping
  evaluation_interval: 15s     # Fréquence d'évaluation des règles
  external_labels:
    cluster: 'mlops-local'
    environment: 'production'

scrape_configs:
  - job_name: 'iris-api'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - mlops
    metrics_path: /metrics
    scheme: http
```

**Modifier la configuration** :
```bash
# Éditer le ConfigMap
kubectl edit configmap prometheus-config -n mlops

# Recharger Prometheus (via API)
curl -X POST http://localhost:9090/-/reload
```

#### Grafana

La configuration Grafana est dans `grafana-configmap.yaml` :

- **Datasource** : Prometheus (automatiquement configuré)
- **Dashboards** : Chargés depuis ConfigMap
- **Authentification** : Anonyme activée (à désactiver en production)

**Changer le mot de passe admin** :
```bash
# Éditer le Secret
kubectl edit secret grafana-secrets -n mlops

# Redémarrer Grafana
kubectl rollout restart deployment/grafana -n mlops
```

#### AlertManager

La configuration AlertManager est dans `alertmanager-configmap.yaml` :

- **Routage** : Par sévérité (critical, warning, info)
- **Groupement** : Par `alertname`, `severity`, `component`
- **Receivers** : Par défaut (logs), critical, warning

**Configurer les notifications** (ex: Slack) :
```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#mlops-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## 🚀 Guide de Déploiement

### Étape 1 : Vérifier les Prérequis

```bash
# Vérifier que l'API est déployée
kubectl get deployment iris-api -n mlops

# Vérifier que l'endpoint /metrics répond
kubectl port-forward -n mlops svc/iris-api-service 8000:8000
curl http://localhost:8000/metrics
```

### Étape 2 : Déployer Prometheus

```bash
# RBAC
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml

# Configuration
kubectl apply -f k8s/monitoring/prometheus-configmap.yaml
kubectl apply -f k8s/monitoring/prometheus-rules.yaml

# Deployment
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# ServiceMonitor
kubectl apply -f k8s/monitoring/servicemonitor-iris-api.yaml
```

### Étape 3 : Déployer AlertManager

```bash
# Configuration
kubectl apply -f k8s/monitoring/alertmanager-configmap.yaml

# Deployment
kubectl apply -f k8s/monitoring/alertmanager-deployment.yaml
```

### Étape 4 : Déployer Grafana

```bash
# Configuration
kubectl apply -f k8s/monitoring/grafana-configmap.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards-configmap.yaml

# Deployment
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

### Étape 5 : Vérifier le Déploiement

```bash
# Vérifier les pods
kubectl get pods -n mlops -l component=monitoring

# Vérifier les services
kubectl get svc -n mlops -l component=monitoring

# Vérifier les logs
kubectl logs -n mlops -l app=prometheus --tail=50
```

### Étape 6 : Accéder aux Interfaces

```bash
# Prometheus
kubectl port-forward -n mlops svc/prometheus-service 9090:9090
# http://localhost:9090

# Grafana
kubectl port-forward -n mlops svc/grafana-service 3000:3000
# http://localhost:3000 (admin/admin)

# AlertManager
kubectl port-forward -n mlops svc/alertmanager-service 9093:9093
# http://localhost:9093
```

---

## 📊 Métriques Collectées

### Métriques API Iris

L'API Iris expose les métriques suivantes via `/metrics` :

#### 1. `model_predictions_total` (Counter)
- **Description** : Nombre total de prédictions par classe
- **Labels** : `predicted_class` (setosa, versicolor, virginica)
- **Usage** : Taux de prédictions, distribution des classes

**Exemple PromQL** :
```promql
# Taux de prédictions par seconde
rate(model_predictions_total[5m])

# Total de prédictions par classe
sum by (predicted_class) (model_predictions_total)
```

#### 2. `model_confidence` (Histogram)
- **Description** : Distribution de la confiance des prédictions
- **Labels** : `predicted_class`
- **Buckets** : [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
- **Usage** : Confiance moyenne, p95, p99

**Exemple PromQL** :
```promql
# Confiance moyenne
avg(model_confidence)

# Confiance p95
histogram_quantile(0.95, rate(model_confidence_bucket[5m]))
```

#### 3. `model_loaded` (Gauge)
- **Description** : Statut du chargement du modèle (1 = chargé, 0 = non chargé)
- **Usage** : Vérifier que le modèle est disponible

**Exemple PromQL** :
```promql
# Modèle chargé ?
model_loaded == 1
```

#### 4. `api_errors_total` (Counter)
- **Description** : Nombre total d'erreurs par type et endpoint
- **Labels** : `error_type`, `endpoint`
- **Usage** : Taux d'erreur, types d'erreurs les plus fréquents

**Exemple PromQL** :
```promql
# Taux d'erreur par type
rate(api_errors_total[5m])

# Taux d'erreur total
sum(rate(api_errors_total[5m]))
```

### Métriques Kubernetes

Prometheus collecte également les métriques Kubernetes standard :

- `container_cpu_usage_seconds_total` : Utilisation CPU
- `container_memory_usage_bytes` : Utilisation mémoire
- `kube_pod_status_phase` : Statut des pods
- `kube_pod_container_status_restarts_total` : Nombre de redémarrages

---

## 📈 Dashboards Grafana

### Dashboard 1 : Iris API - Overview

**Objectif** : Vue d'ensemble des métriques de l'API

**Panneaux** :
1. **Model Predictions Rate** : Taux de prédictions par classe (graph)
2. **Model Confidence Distribution** : Distribution de confiance p50/p95 (graph)
3. **API Errors Rate** : Taux d'erreurs par type (graph)
4. **Model Loaded Status** : Statut du modèle (stat, vert/rouge)
5. **Total Predictions** : Total cumulé de prédictions (stat)

**Accès** :
- Grafana → Dashboards → Browse → "Iris API - Overview"

### Dashboard 2 : Kubernetes - Infrastructure

**Objectif** : Métriques infrastructure (CPU, mémoire, pods)

**Panneaux** :
1. **CPU Usage** : Utilisation CPU par pod (graph)
2. **Memory Usage** : Utilisation mémoire par pod (graph)
3. **Pod Status** : Statut des pods (table)

**Accès** :
- Grafana → Dashboards → Browse → "Kubernetes - Infrastructure"

### Créer un Nouveau Dashboard

1. Grafana → Dashboards → New Dashboard
2. Add Panel → Choose Visualization
3. Sélectionner "Prometheus" comme datasource
4. Entrer une requête PromQL (ex: `rate(model_predictions_total[5m])`)
5. Configurer le graphique (titre, axes, légende)
6. Save Dashboard

---

## 🚨 Règles d'Alerte

### Alertes API

#### 1. IrisAPIDown (Critical)
- **Condition** : `up{job="iris-api"} == 0`
- **Durée** : 1 minute
- **Sévérité** : Critical
- **Description** : L'API Iris n'expose plus de métriques depuis 1 minute

#### 2. HighErrorRate (Warning)
- **Condition** : `rate(api_errors_total[5m]) > 0.05`
- **Durée** : 5 minutes
- **Sévérité** : Warning
- **Description** : Taux d'erreur > 5% sur 5 minutes

#### 3. HighLatency (Warning)
- **Condition** : `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1`
- **Durée** : 5 minutes
- **Sévérité** : Warning
- **Description** : Latence p95 > 1 seconde
- **⚠️ Note** : Cette alerte nécessite l'ajout d'une métrique de latence HTTP dans l'API (non implémentée actuellement)

#### 4. ModelNotLoaded (Critical)
- **Condition** : `model_loaded == 0`
- **Durée** : 2 minutes
- **Sévérité** : Critical
- **Description** : Le modèle ML n'est pas chargé

#### 5. LowPredictionRate (Info)
- **Condition** : `rate(model_predictions_total[10m]) < 0.1`
- **Durée** : 10 minutes
- **Sévérité** : Info
- **Description** : Taux de prédictions très bas (< 0.1/min)

### Alertes Infrastructure

#### 6. PodCrashLooping (Warning)
- **Condition** : `kube_pod_container_status_restarts_total > 3`
- **Durée** : 5 minutes
- **Sévérité** : Warning
- **Description** : Pod redémarre en boucle

#### 7. HighCPUUsage (Warning)
- **Condition** : `(rate(container_cpu_usage_seconds_total[5m]) * 100) > 80`
- **Durée** : 5 minutes
- **Sévérité** : Warning
- **Description** : Utilisation CPU > 80%

#### 8. HighMemoryUsage (Warning)
- **Condition** : `(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 90`
- **Durée** : 5 minutes
- **Sévérité** : Warning
- **Description** : Utilisation mémoire > 90%

### Vérifier les Alertes

```bash
# Dans Prometheus UI
# http://localhost:9090/alerts

# Dans AlertManager UI
# http://localhost:9093
```

---

## 🧪 Tests et Validation

### Test 1 : Vérifier que Prometheus Scrape les Métriques

```bash
# Port-forward Prometheus
kubectl port-forward -n mlops svc/prometheus-service 9090:9090

# Dans le navigateur : http://localhost:9090
# Aller dans Status → Targets
# Vérifier que "iris-api" est "UP"
```

### Test 2 : Vérifier les Métriques dans Prometheus

```bash
# Dans Prometheus UI : http://localhost:9090
# Aller dans Graph
# Tester des requêtes PromQL :
#   - model_predictions_total
#   - rate(model_predictions_total[5m])
#   - model_loaded
```

### Test 3 : Vérifier les Dashboards Grafana

```bash
# Port-forward Grafana
kubectl port-forward -n mlops svc/grafana-service 3000:3000

# Dans le navigateur : http://localhost:3000
# Se connecter (admin/admin)
# Aller dans Dashboards → Browse
# Ouvrir "Iris API - Overview"
# Vérifier que les graphiques s'affichent
```

### Test 4 : Tester les Alertes

```bash
# Simuler une alerte (arrêter l'API)
kubectl scale deployment iris-api -n mlops --replicas=0

# Attendre 1-2 minutes
# Vérifier dans Prometheus : http://localhost:9090/alerts
# Vérifier dans AlertManager : http://localhost:9093

# Redémarrer l'API
kubectl scale deployment iris-api -n mlops --replicas=2
```

### Test 5 : Générer du Trafic pour les Métriques

```bash
# Port-forward l'API
kubectl port-forward -n mlops svc/iris-api-service 8000:8000

# Générer des requêtes
for i in {1..100}; do
  curl -X POST http://localhost:8000/predict \
    -H "X-API-Key: your-api-key" \
    -H "Content-Type: application/json" \
    -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
  sleep 0.5
done

# Vérifier les métriques dans Grafana
```

---

## 🛠️ Commandes Utiles

### Prometheus

```bash
# Vérifier les targets
kubectl port-forward -n mlops svc/prometheus-service 9090:9090
# http://localhost:9090/targets

# Requête PromQL via API
curl 'http://localhost:9090/api/v1/query?query=model_predictions_total'

# Recharger la configuration
curl -X POST http://localhost:9090/-/reload
```

### Grafana

```bash
# Logs Grafana
kubectl logs -n mlops -l app=grafana --tail=100

# Redémarrer Grafana
kubectl rollout restart deployment/grafana -n mlops

# Exporter un dashboard
# Grafana UI → Dashboard → Share → Export → Save to file
```

### AlertManager

```bash
# Logs AlertManager
kubectl logs -n mlops -l app=alertmanager --tail=100

# Vérifier la configuration
kubectl get configmap alertmanager-config -n mlops -o yaml

# Recharger AlertManager
kubectl exec -n mlops -it deployment/alertmanager -- kill -HUP 1
```

### Makefile

```bash
# Déployer la stack
make k8s-monitoring-deploy

# Vérifier le statut
make k8s-monitoring-status

# Logs
make k8s-monitoring-logs
make k8s-monitoring-logs-grafana

# Port-forward
make k8s-monitoring-port-forward

# Supprimer
make k8s-monitoring-delete
```

---

## 🔒 Sécurité

### Bonnes Pratiques

1. **Authentification Grafana** :
   - ⚠️ Désactiver l'authentification anonyme en production
   - Configurer OAuth, LDAP, ou authentification externe
   - Utiliser des secrets Kubernetes pour les mots de passe

2. **RBAC Prometheus** :
   - Permissions minimales (seulement ce qui est nécessaire)
   - ServiceAccount dédié (pas de permissions excessives)

3. **Secrets** :
   - Utiliser Secret Manager (GCP) ou Vault
   - Ne jamais commiter les secrets
   - Rotation régulière des mots de passe

4. **Network Policies** :
   - Restreindre l'accès réseau aux composants de monitoring
   - Seuls Prometheus peut scraper les métriques

5. **TLS** :
   - Activer HTTPS pour Grafana et Prometheus en production
   - Utiliser cert-manager pour les certificats automatiques

### Configuration Production

```yaml
# Grafana : Désactiver l'anonyme
[auth.anonymous]
enabled = false

# Prometheus : Activer l'authentification
# Utiliser un reverse proxy (nginx) avec authentification
```

---

## 🔧 Dépannage

### Prometheus ne Scrape pas les Métriques

**Symptôme** : Les métriques n'apparaissent pas dans Prometheus

**Solutions** :
1. Vérifier que l'API est accessible :
   ```bash
   kubectl get pods -n mlops -l app=iris-api
   kubectl logs -n mlops -l app=iris-api --tail=50
   ```

2. Vérifier que l'endpoint `/metrics` répond :
   ```bash
   kubectl port-forward -n mlops svc/iris-api-service 8000:8000
   curl http://localhost:8000/metrics
   ```

3. Vérifier la configuration Prometheus :
   ```bash
   kubectl get configmap prometheus-config -n mlops -o yaml
   ```

4. Vérifier les targets dans Prometheus UI :
   - http://localhost:9090/targets
   - Vérifier que "iris-api" est "UP"

### Grafana ne Charge pas les Dashboards

**Symptôme** : Les dashboards ne s'affichent pas

**Solutions** :
1. Vérifier les logs Grafana :
   ```bash
   kubectl logs -n mlops -l app=grafana --tail=100
   ```

2. Vérifier que les ConfigMaps sont montés :
   ```bash
   kubectl exec -n mlops -it deployment/grafana -- ls -la /var/lib/grafana/dashboards
   ```

3. Vérifier la configuration du datasource :
   - Grafana UI → Configuration → Data Sources
   - Vérifier que "Prometheus" est configuré et testé

### Alertes ne se Déclenchent pas

**Symptôme** : Les alertes ne sont pas envoyées

**Solutions** :
1. Vérifier que les règles sont chargées :
   ```bash
   kubectl exec -n mlops -it deployment/prometheus -- cat /etc/prometheus/rules/api-alerts.yml
   ```

2. Vérifier les alertes dans Prometheus UI :
   - http://localhost:9090/alerts
   - Vérifier que les règles sont actives

3. Vérifier la connexion Prometheus → AlertManager :
   ```bash
   kubectl logs -n mlops -l app=prometheus | grep alertmanager
   ```

4. Vérifier la configuration AlertManager :
   ```bash
   kubectl get configmap alertmanager-config -n mlops -o yaml
   ```

### Métriques Manquantes

**Symptôme** : Certaines métriques n'apparaissent pas

**Solutions** :
1. Vérifier que l'API expose les métriques :
   ```bash
   curl http://localhost:8000/metrics | grep model_predictions_total
   ```

2. Vérifier les labels dans Prometheus :
   - http://localhost:9090
   - Graph → `model_predictions_total`

3. Vérifier la configuration de scraping :
   - Les labels doivent matcher ceux de l'API

---

## ✅ Validation des Objectifs

### Objectifs Atteints

- ✅ **Prometheus déployé** : Collecte et stocke les métriques
- ✅ **Grafana déployé** : Visualisation via dashboards
- ✅ **AlertManager déployé** : Gestion des alertes
- ✅ **Métriques API collectées** : Prédictions, confiance, erreurs, modèle
- ✅ **Dashboards créés** : API Overview + Infrastructure
- ✅ **Alertes configurées** : 6 règles d'alerte actives (7ème désactivée - nécessite métrique HTTP latency)
- ✅ **Documentation complète** : Guide de déploiement et dépannage

### Métriques de Succès

- **Disponibilité** : Prometheus, Grafana, AlertManager opérationnels
- **Couverture** : Toutes les métriques API collectées
- **Visualisation** : 2 dashboards fonctionnels
- **Alertes** : 6 règles d'alerte configurées et testées (7ème désactivée - nécessite métrique HTTP latency)

---

## 📚 Ressources

### Documentation

- [k8s/monitoring/README.md](../k8s/monitoring/README.md) — Stack Prometheus / Grafana / AlertManager
- [Prometheus Documentation](https://prometheus.io/docs/) - Documentation officielle
- [Grafana Documentation](https://grafana.com/docs/) - Documentation officielle
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/) - Documentation officielle

### Ressources Externes

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/)

### Articles et Tutoriels

- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator) - Alternative pour déploiement avancé
- [Observability in Kubernetes](https://kubernetes.io/docs/tasks/debug-application-cluster/monitoring-application-health/)
- [MLOps Monitoring Best Practices](https://www.mlops.community/mlops-monitoring)

---

**Observabilité terminée avec succès.**

La stack de monitoring est maintenant opérationnelle avec :
- ✅ Prometheus collectant les métriques
- ✅ Grafana visualisant les métriques via dashboards
- ✅ AlertManager gérant les alertes
- ✅ 6 règles d'alerte configurées (7ème désactivée - nécessite métrique HTTP latency)
- ✅ Documentation complète

Le projet MLOps est maintenant **production-ready** avec observabilité complète ! 🚀
