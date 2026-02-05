#!/bin/bash
# Script d'installation et configuration de Kubernetes (minikube ou kind)
# Usage: ./scripts/setup-k8s.sh [minikube|kind]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que kubectl est installé
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl n'est pas installé"
        echo "Installez kubectl : https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    info "kubectl est installé : $(kubectl version --client --short)"
}

# Installation de minikube
install_minikube() {
    info "Installation de minikube..."
    
    if command -v minikube &> /dev/null; then
        info "minikube est déjà installé : $(minikube version --short)"
    else
        warn "minikube n'est pas installé"
        
        # macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            info "Installation via Homebrew..."
            if command -v brew &> /dev/null; then
                brew install minikube
            else
                error "Homebrew n'est pas installé. Installez minikube manuellement : https://minikube.sigs.k8s.io/docs/start/"
                exit 1
            fi
        # Linux
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            info "Installation via curl..."
            if ! curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64; then
                error "Échec du téléchargement de minikube"
                exit 1
            fi
            if ! sudo install minikube-linux-amd64 /usr/local/bin/minikube; then
                error "Échec de l'installation de minikube"
                rm -f minikube-linux-amd64
                exit 1
            fi
            rm -f minikube-linux-amd64
        else
            error "OS non supporté. Installez minikube manuellement : https://minikube.sigs.k8s.io/docs/start/"
            exit 1
        fi
    fi
    
    # Démarrer minikube
    if minikube status &> /dev/null; then
        info "minikube est déjà démarré"
    else
        info "Démarrage de minikube..."
        minikube start --driver=docker --memory=4096 --cpus=2
    fi
    
    # Configurer kubectl
    minikube kubectl -- get nodes
    
    info "minikube est prêt !"
    info "Pour utiliser minikube : eval \$(minikube docker-env)"
}

# Installation de kind
install_kind() {
    info "Installation de kind..."
    
    if command -v kind &> /dev/null; then
        info "kind est déjà installé : $(kind version)"
    else
        warn "kind n'est pas installé"
        
        # macOS et Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            ARCH="darwin-amd64"
        else
            ARCH="linux-amd64"
        fi
        
        info "Téléchargement de kind..."
        if ! curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-${ARCH}; then
            error "Échec du téléchargement de kind"
            exit 1
        fi
        chmod +x ./kind
        if ! sudo mv ./kind /usr/local/bin/kind; then
            error "Échec de l'installation de kind"
            exit 1
        fi
    fi
    
    # Créer le cluster
    if kind get clusters | grep -q "mlops-cluster"; then
        info "Le cluster kind 'mlops-cluster' existe déjà"
    else
        info "Création du cluster kind 'mlops-cluster'..."
        kind create cluster --name mlops-cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
EOF
    fi
    
    info "kind est prêt !"
    info "Cluster créé : mlops-cluster"
}

# Installation de metrics-server (pour HPA)
install_metrics_server() {
    info "Vérification de metrics-server..."
    
    if kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        info "metrics-server est déjà installé"
    else
        info "Installation de metrics-server..."
        kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        
        # Attendre que metrics-server soit prêt
        info "Attente de metrics-server..."
        kubectl wait --for=condition=available --timeout=120s deployment/metrics-server -n kube-system || true
    fi
}

# Vérification du cluster
check_cluster() {
    info "Vérification du cluster Kubernetes..."
    
    if kubectl cluster-info &> /dev/null; then
        info "Cluster Kubernetes accessible"
        kubectl get nodes
    else
        error "Impossible de se connecter au cluster Kubernetes"
        exit 1
    fi
}

# Main
main() {
    info "🚀 Configuration de Kubernetes pour MLOps"
    echo ""
    
    check_kubectl
    
    # Choix de l'outil
    TOOL="${1:-minikube}"
    
    case "$TOOL" in
        minikube)
            install_minikube
            ;;
        kind)
            install_kind
            ;;
        *)
            error "Outil non reconnu : $TOOL"
            echo "Usage: $0 [minikube|kind]"
            exit 1
            ;;
    esac
    
    check_cluster
    install_metrics_server
    
    echo ""
    info "✅ Configuration terminée !"
    echo ""
    info "Prochaines étapes :"
    echo "  1. Préparer les secrets : cp k8s/secret.yaml.example k8s/secret.yaml"
    echo "  2. Déployer l'application : make k8s-deploy"
    echo "  3. Vérifier : make k8s-status"
    echo ""
    
    if [ "$TOOL" == "minikube" ]; then
        warn "Pour utiliser l'image Docker locale avec minikube :"
        echo "  eval \$(minikube docker-env)"
        echo "  docker build -t iris-api:latest ."
    fi
}

main "$@"

