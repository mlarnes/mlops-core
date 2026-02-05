# Déploiement Kubernetes

Manifests pour déployer l’API MLOps et le serveur MLflow sur un cluster Kubernetes. Deux workflows possibles : **avec MLflow dans le cluster** (recommandé) ou **API seule** (MLflow local / hostPath).

> Guide détaillé et concepts : [docs/orchestration.md](../docs/orchestration.md)

---

## Vue d’ensemble

- **API FastAPI** : 2 replicas, health checks, HPA
- **MLflow** (optionnel) : 1 replica, PVC dédié
- **Services** : ClusterIP ; NodePort pour dev/test
- **Monitoring** : Prometheus, Grafana, AlertManager — voir [monitoring/](monitoring/README.md)

## Structure des manifests

```
k8s/
├── namespace.yaml              # Namespace mlops
├── deployment.yaml             # Deployment API (2 replicas)
├── mlflow-deployment.yaml      # Serveur MLflow
├── mlflow-pvc.yaml             # PVC runs MLflow (/app/mlruns)
├── models-pvc.yaml             # PVC modèles (/app/models)
├── train-job.yaml              # Job d’entraînement in-cluster
├── service.yaml / mlflow-service.yaml
├── service-nodeport.yaml       # Dev/test
├── configmap.yaml / secret.yaml.example
├── ingress.yaml / hpa.yaml
└── monitoring/                 # Prometheus, Grafana, AlertManager
```

## Prérequis

- `kubectl` configuré, cluster accessible (minikube, kind ou cloud)
- Image `iris-api:latest` disponible (voir workflows)

---

## Workflow 1 — Avec MLflow (recommandé)

Objectif : cluster local (minikube), API + MLflow, entraînement dans le cluster, stockage persistant (PVC).

### 1. Démarrer le cluster

```bash
minikube delete   # optionnel
minikube start
kubectl get nodes
```

### 2. Builder l’image dans l’environnement Docker de minikube

```bash
cd mlops-core
eval "$(minikube docker-env)"
make build
docker images | grep iris-api
```

### 3. Préparer le Secret

```bash
cp k8s/secret.yaml.example k8s/secret.yaml
```

Dans `k8s/secret.yaml`, au minimum :

```yaml
stringData:
  API_KEY: "votre-api-key"   # ex: openssl rand -hex 32
  MLFLOW_TRACKING_URI: "http://mlflow-server-service:5000"
```

### 4. Déployer API + MLflow

```bash
make k8s-deploy-mlflow
make k8s-status
```

Attendu : pods `iris-api-...` et `mlflow-server-...` en `Running`.

### 5. Accéder à l’API et à MLflow UI

```bash
# Terminal 1
make k8s-port-forward   # API → http://localhost:8000

# Terminal 2
make k8s-mlflow-ui      # MLflow → http://localhost:5000
```

### 6. Entraîner le modèle dans le cluster (Job)

Le PVC `models-pvc` est déjà déployé par `make k8s-deploy-mlflow`. Lancer le job d’entraînement :

```bash
kubectl delete job iris-train-job -n mlops --ignore-not-found
kubectl apply -f k8s/train-job.yaml
kubectl logs job/iris-train-job -n mlops -f
```

Puis recharger l’API pour qu’elle relise `/app/models` :

```bash
kubectl rollout restart deployment/iris-api -n mlops
```

Le job écrit `model.joblib`, `metadata.json` et `metrics.json` dans le PVC `models-pvc`, utilisés par l’API au démarrage.

### 7. Vérifier

```bash
make k8s-status
curl http://localhost:8000/health   # avec port-forward actif
```

Réponse attendue : `"model_loaded": true`.

### 8. Nettoyage

```bash
make k8s-clean
# ou
minikube delete
```

---

## Workflow 2 — API seule (MLflow local)

Pour du dev avec MLflow sur la machine hôte :

```bash
# Terminal 1 : monter mlruns vers minikube
minikube mount $(pwd)/mlruns:/tmp/mlruns

# Terminal 2
make k8s-deploy
make k8s-port-forward
```

Dans `k8s/secret.yaml`, utiliser `MLFLOW_TRACKING_URI: ""` ou un chemin local selon votre setup.

---

## Déploiement rapide (résumé des commandes)

| Action | Commande |
|--------|----------|
| Cluster | `make k8s-setup` ou `make k8s-setup-kind` |
| Déployer API + MLflow | `make k8s-deploy-mlflow` |
| Déployer API seule | `make k8s-deploy` |
| Statut | `make k8s-status` |
| Logs | `make k8s-logs` |
| Port-forward API | `make k8s-port-forward` |
| Port-forward MLflow | `make k8s-mlflow-ui` |
| Test API | `make k8s-test` |
| Nettoyage | `make k8s-clean` |

Déploiement manuel (sans make) : appliquer dans l’ordre `namespace` → `configmap` → `secret` → `mlflow-pvc` → `models-pvc` → `mlflow-deployment` + `mlflow-service` → `deployment` → `service`.

---

## Configuration

**ConfigMap** : `ENVIRONMENT`, `MODEL_DIR`, `LOG_LEVEL`.

**Secret** : `API_KEY`, `MLFLOW_TRACKING_URI`.

| Mode | `MLFLOW_TRACKING_URI` | Usage |
|------|------------------------|--------|
| K8s Server | `http://mlflow-server-service:5000` | Recommandé, avec PVC |
| Local | `""` + hostPath / mount | Dev |
| GCS | `gs://bucket/mlruns/` | Production cloud |

Pour le mode GCS (Workflow 3), configurer le secret avec `MLFLOW_TRACKING_URI: "gs://bucket-name/mlruns/"` puis **`make k8s-deploy`** (les PVC sont inclus).

---

## Architecture du modèle en production

- **MLflow** : source de vérité analytique (runs, paramètres, métriques, registry).
- **Runtime API** : lit `/app/models` (PVC `models-pvc`) — `model.joblib`, `metadata.json` (contient `mlflow_run_id`), `metrics.json` — écrits par le Job d’entraînement. L'API charge le modèle depuis `model.joblib` local (priorité), ou depuis MLflow via `runs:/<run_id>/model` si le fichier local est absent. Pas de dépendance directe aux artifacts MLflow côté serveur HTTP pour le chargement.

---

## Tests

```bash
make k8s-port-forward
curl http://localhost:8000/health
```

Prédiction (récupérer la clé depuis le secret) :

```bash
export API_KEY=$(kubectl get secret iris-api-secrets -n mlops -o jsonpath='{.data.API_KEY}' | base64 -d)
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

---

## Auto-scaling (HPA)

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl apply -f k8s/hpa.yaml
kubectl get hpa -n mlops
```

HPA : 2–10 replicas selon CPU (70 %) et mémoire (80 %).

---

## Exposition

- **NodePort** : `kubectl apply -f k8s/service-nodeport.yaml` puis `http://<NODE_IP>:30080`
- **Ingress** : installer un Ingress Controller, appliquer `k8s/ingress.yaml` (adapter le domaine).

---

## Monitoring

Stack Prometheus / Grafana / AlertManager dans [monitoring/](monitoring/README.md).

```bash
make k8s-monitoring-deploy
make k8s-monitoring-port-forward
```

---

## Dépannage

| Problème | Vérification |
|----------|---------------|
| Pods ne démarrent pas | `kubectl describe pod <name> -n mlops` ; `kubectl get events -n mlops --sort-by='.lastTimestamp'` |
| API ne répond pas | `kubectl logs -f deployment/iris-api -n mlops` ; `kubectl get svc iris-api-service -n mlops` |
| Secrets | `kubectl get secret iris-api-secrets -n mlops` |
| Image (minikube) | `eval $(minikube docker-env)` puis `make build` |

---

## Sécurité

- Secrets en Kubernetes (jamais en clair dans Git).
- Containers non-root, capabilities limitées.
- Production : External Secrets, Network Policies, Pod Security Standards, cert-manager, scan d’images.

---

## Documentation

- [Orchestration](../docs/orchestration.md) — concepts, architecture, tutoriel détaillé
- [Monitoring](monitoring/README.md) — Prometheus, Grafana, AlertManager
- [Makefile](../Makefile) — commandes `make k8s-*`
