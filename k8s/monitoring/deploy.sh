#!/bin/bash
# Script de déploiement de la stack de monitoring

set -e

echo "📊 Déploiement de la stack de monitoring (Prometheus, Grafana, AlertManager)"
echo ""

# Vérifier que kubectl est disponible
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier que le namespace mlops existe
if ! kubectl get namespace mlops &> /dev/null; then
    echo "⚠️  Le namespace 'mlops' n'existe pas. Création..."
    kubectl create namespace mlops
fi

# Vérifier que l'API Iris est déployée
if ! kubectl get deployment iris-api -n mlops &> /dev/null; then
    echo "⚠️  L'API Iris n'est pas déployée. Déployez-la d'abord avec:"
    echo "   make k8s-deploy-mlflow"
    echo ""
    read -p "Continuer quand même ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔧 Déploiement des composants..."

# Déployer dans l'ordre (dépendances)
echo "  1. RBAC pour Prometheus..."
kubectl apply -f prometheus-rbac.yaml

echo "  2. Configuration Prometheus..."
kubectl apply -f prometheus-configmap.yaml
kubectl apply -f prometheus-rules.yaml

echo "  3. Prometheus..."
kubectl apply -f prometheus-deployment.yaml

echo "  4. ServiceMonitor pour l'API Iris..."
kubectl apply -f servicemonitor-iris-api.yaml

echo "  5. Configuration AlertManager..."
kubectl apply -f alertmanager-configmap.yaml

echo "  6. AlertManager..."
kubectl apply -f alertmanager-deployment.yaml

echo "  7. Configuration Grafana..."
kubectl apply -f grafana-configmap.yaml
kubectl apply -f grafana-dashboards-configmap.yaml

echo "  8. Grafana..."
kubectl apply -f grafana-deployment.yaml

echo ""
echo "⏳ Attente du démarrage des pods..."
sleep 5

echo ""
echo "📊 Statut des pods:"
kubectl get pods -n mlops -l component=monitoring

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "🔌 Pour accéder aux interfaces:"
echo ""
echo "  Prometheus:"
echo "    kubectl port-forward -n mlops svc/prometheus-service 9090:9090"
echo "    http://localhost:9090"
echo ""
echo "  Grafana:"
echo "    kubectl port-forward -n mlops svc/grafana-service 3000:3000"
echo "    http://localhost:3000"
echo "    Identifiants: admin / admin"
echo ""
echo "  AlertManager:"
echo "    kubectl port-forward -n mlops svc/alertmanager-service 9093:9093"
echo "    http://localhost:9093"
echo ""
echo "  Ou utilisez: make k8s-monitoring-port-forward"
echo ""
