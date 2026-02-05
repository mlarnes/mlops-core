# Monitoring — Prometheus, Grafana, AlertManager

Stack de monitoring pour l’API MLOps sur Kubernetes : collecte (Prometheus), visualisation (Grafana), alertes (AlertManager). Documentation détaillée : [docs/observability.md](../../docs/observability.md).

## Vue d'ensemble

Cette stack de monitoring comprend :
- **Prometheus** : Collecte et stocke les métriques
- **Grafana** : Visualisation des métriques via dashboards
- **AlertManager** : Gestion des alertes et notifications

## Structure des manifests

```
k8s/monitoring/
├── prometheus-rbac.yaml          # RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)
├── prometheus-configmap.yaml     # Configuration Prometheus (scraping targets)
├── prometheus-rules.yaml          # Règles d'alerte Prometheus
├── prometheus-deployment.yaml    # Deployment + Service Prometheus
├── servicemonitor-iris-api.yaml   # ServiceMonitor pour l'API Iris
├── alertmanager-configmap.yaml   # Configuration AlertManager
├── alertmanager-deployment.yaml  # Deployment + Service AlertManager
├── grafana-configmap.yaml        # Configuration Grafana (datasources, dashboards)
├── grafana-dashboards-configmap.yaml  # Dashboards JSON
├── grafana-deployment.yaml       # Deployment + Service Grafana
└── README.md                     # Ce fichier
```

## Déploiement rapide

### Prérequis
- Cluster Kubernetes fonctionnel (minikube, kind, ou GKE)
- Namespace `mlops` créé
- API Iris déployée et fonctionnelle

### Déploiement Complet

```bash
# Depuis la racine du projet
cd k8s/monitoring

# Déployer dans l'ordre (dépendances)
kubectl apply -f prometheus-rbac.yaml
kubectl apply -f prometheus-configmap.yaml
kubectl apply -f prometheus-rules.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f servicemonitor-iris-api.yaml
kubectl apply -f alertmanager-configmap.yaml
kubectl apply -f alertmanager-deployment.yaml
kubectl apply -f grafana-configmap.yaml
kubectl apply -f grafana-dashboards-configmap.yaml
kubectl apply -f grafana-deployment.yaml

# Ou déployer tout d'un coup
kubectl apply -f .
```

### Vérification

```bash
# Vérifier que tous les pods sont en cours d'exécution
kubectl get pods -n mlops -l component=monitoring

# Vérifier les services
kubectl get svc -n mlops -l component=monitoring

# Vérifier les logs Prometheus
kubectl logs -n mlops -l app=prometheus --tail=50

# Vérifier les logs Grafana
kubectl logs -n mlops -l app=grafana --tail=50
```

## Accès aux interfaces

### Port-Forward (Accès Local)

```bash
# Prometheus UI (port 9090)
kubectl port-forward -n mlops svc/prometheus-service 9090:9090
# Accès : http://localhost:9090

# Grafana UI (port 3000)
kubectl port-forward -n mlops svc/grafana-service 3000:3000
# Accès : http://localhost:3000
# Identifiants par défaut : admin / admin

# AlertManager UI (port 9093)
kubectl port-forward -n mlops svc/alertmanager-service 9093:9093
# Accès : http://localhost:9093
```

### Via Ingress (Si configuré)

Si vous avez configuré un Ingress, les services sont accessibles via :
- Prometheus : `http://prometheus.mlops.local`
- Grafana : `http://grafana.mlops.local`
- AlertManager : `http://alertmanager.mlops.local`

## Métriques collectées

### Métriques API Iris

Prometheus scrape automatiquement les métriques exposées par l'API Iris via l'endpoint `/metrics` :

- `model_predictions_total` : Nombre total de prédictions par classe
- `model_confidence` : Distribution de la confiance des prédictions (histogramme)
- `model_loaded` : Statut du chargement du modèle (1 = chargé, 0 = non chargé)
- `api_errors_total` : Nombre total d'erreurs par type et endpoint

### Métriques Kubernetes

Prometheus collecte également les métriques Kubernetes standard :
- Utilisation CPU et mémoire des pods
- Statut des pods
- Redémarrages

## Alertes configurées

Les règles d'alerte sont définies dans `prometheus-rules.yaml` :

### Alertes API
- **IrisAPIDown** : API non accessible (critical)
- **HighErrorRate** : Taux d'erreur > 5% (warning)
- **HighLatency** : Latence p95 > 1s (warning) - ⚠️ Nécessite métrique HTTP latency (non implémentée)
- **ModelNotLoaded** : Modèle non chargé (critical)
- **LowPredictionRate** : Taux de prédictions très bas (info)

### Alertes Infrastructure
- **PodCrashLooping** : Pod en CrashLoopBackOff (warning)
- **HighCPUUsage** : Utilisation CPU > 80% (warning)
- **HighMemoryUsage** : Utilisation mémoire > 90% (warning)

## Dashboards Grafana

Deux dashboards sont pré-configurés :

1. **Iris API - Overview** : Vue d'ensemble de l'API
   - Taux de prédictions
   - Distribution de la confiance
   - Taux d'erreurs
   - Statut du modèle
   - Total de prédictions

2. **Kubernetes - Infrastructure** : Métriques infrastructure
   - Utilisation CPU
   - Utilisation mémoire
   - Statut des pods

### Accéder aux Dashboards

1. Connectez-vous à Grafana (http://localhost:3000)
2. Allez dans **Dashboards** → **Browse**
3. Sélectionnez le dashboard souhaité

## Configuration

### Prometheus

La configuration Prometheus est dans `prometheus-configmap.yaml` :
- **Scrape interval** : 15s
- **Rétention** : 15 jours
- **Scraping targets** : Prometheus lui-même + API Iris (via ServiceMonitor)

### AlertManager

La configuration AlertManager est dans `alertmanager-configmap.yaml` :
- **Grouping** : Par `alertname`, `severity`, `component`
- **Repeat interval** : 12h
- **Receivers** : Par défaut (logs), critical, warning

**⚠️ Important** : Les notifications externes (Slack, email, PagerDuty) ne sont pas configurées par défaut. Voir la section "Configuration des Notifications" ci-dessous.

### Grafana

La configuration Grafana est dans `grafana-configmap.yaml` :
- **Datasource** : Prometheus (automatiquement configuré)
- **Dashboards** : Chargés depuis ConfigMap
- **Authentification** : Anonyme activée (Viewer)

**⚠️ Sécurité** : En production, désactiver l'authentification anonyme et configurer une authentification appropriée.

## Configuration des notifications

Pour activer les notifications (Slack, email, etc.), modifiez `alertmanager-configmap.yaml` :

### Exemple : Slack

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#mlops-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Exemple : Email

```yaml
email_configs:
  - to: 'ops-team@example.com'
    from: 'alertmanager@mlops.local'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alertmanager'
    auth_password: 'password'
```

Après modification, recharger la configuration :

```bash
# Recharger la config AlertManager
kubectl exec -n mlops -it deployment/alertmanager -- kill -HUP 1
```

## Tests

### Tester les Métriques

```bash
# Vérifier que l'API expose des métriques
curl http://localhost:8000/metrics

# Vérifier que Prometheus scrape les métriques
kubectl port-forward -n mlops svc/prometheus-service 9090:9090
# Puis dans le navigateur : http://localhost:9090
# Aller dans Status → Targets
# Vérifier que "iris-api" est "UP"
```

### Tester les Alertes

```bash
# Simuler une alerte (ex: arrêter l'API)
kubectl scale deployment iris-api -n mlops --replicas=0

# Vérifier les alertes dans Prometheus
# http://localhost:9090/alerts

# Vérifier les alertes dans AlertManager
# http://localhost:9093
```

## Dépannage

### Prometheus ne scrape pas les métriques

1. Vérifier que l'API Iris est accessible :
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

### Grafana ne charge pas les dashboards

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

### Alertes ne se déclenchent pas

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

## Nettoyage

```bash
# Supprimer tous les composants de monitoring
kubectl delete -f k8s/monitoring/

# Ou supprimer manuellement
kubectl delete deployment prometheus alertmanager grafana -n mlops
kubectl delete svc prometheus-service alertmanager-service grafana-service -n mlops
kubectl delete configmap prometheus-config prometheus-rules alertmanager-config grafana-config grafana-dashboards -n mlops
kubectl delete secret grafana-secrets -n mlops
kubectl delete servicemonitor iris-api -n mlops
kubectl delete serviceaccount prometheus -n mlops
kubectl delete clusterrole prometheus
kubectl delete clusterrolebinding prometheus
```

## Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator) (alternative pour déploiement avancé)

## Sécurité

⚠️ **Important pour la production** :

1. **Authentification Grafana** : Désactiver l'anonyme, configurer OAuth/LDAP
2. **Secrets** : Utiliser Secret Manager (GCP) ou Vault pour les mots de passe
3. **RBAC** : Vérifier que les permissions Prometheus sont minimales
4. **Network Policies** : Restreindre l'accès réseau aux composants de monitoring
5. **TLS** : Activer HTTPS pour Grafana et Prometheus en production
6. **PersistentVolumes** : Utiliser des PVs pour la persistance des données
