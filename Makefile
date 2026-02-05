# Makefile pour le projet MLOps
# Usage: make <command>
#
# Les principales "stories" du portfolio sont regroupées par sections :
# - Développement local (install, train, test, run, mlflow-ui)
# - Qualité (format, lint, ci)
# - Données & pipeline (DVC)
# - Déploiement & infra (Docker, Kubernetes, Terraform)
# - Observabilité (monitoring, métriques Prometheus)
#
.PHONY: help install uninstall train test run run-prod build run-docker run-docker-bg stop-docker
.PHONY: clean clean-models clean-dvc format lint ci dev-setup docs health deploy
.PHONY: terraform-init terraform-plan terraform-apply terraform-destroy terraform-output terraform-validate terraform-fmt terraform-refresh
.PHONY: mlflow-ui mlflow-experiments dvc-init dvc-repro dvc-status dvc-push dvc-pull dvc-pipeline
.PHONY: _k8s-check-secret k8s-setup k8s-deploy k8s-deploy-mlflow k8s-status k8s-logs k8s-delete k8s-port-forward k8s-mlflow-ui k8s-test k8s-clean
.PHONY: k8s-monitoring-deploy k8s-monitoring-delete k8s-monitoring-status k8s-monitoring-logs k8s-monitoring-logs-grafana k8s-monitoring-port-forward

# Variables (surchargeables: make DOCKER_IMAGE=mon-image build)
PYTHON := poetry run python
PIP := poetry run pip
PYTEST := poetry run pytest
BLACK := poetry run black
FLAKE8 := poetry run flake8
ISORT := poetry run isort
DOCKER_IMAGE ?= iris-api:latest
K8S_NS ?= mlops
TERRAFORM_DIR := terraform
FLAKE8_EXCLUDE := .venv,venv,__pycache__,.git,.env,build,dist,*.egg-info,.pytest_cache,.mypy_cache,poetry.lock

### === AIDE GÉNÉRALE ===
help: ## Afficher cette aide
	@echo "🌸 MLOps Iris API - Commandes disponibles"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

### === ENVIRONNEMENT LOCAL & DÉVELOPPEMENT ===
install: ## Installer Poetry et les dépendances
	@echo "📦 Installation de l'environnement..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

uninstall: ## Supprimer l'environnement Poetry
	@echo "🗑️ Suppression complète de l'environnement Poetry..."
	@echo "   Suppression de l'environnement virtuel..."
	@rm -rf .venv
	@echo "   Suppression du fichier poetry.lock..."
	@rm -f poetry.lock
	@echo "   Suppression des caches Python..."
	@rm -rf .pytest_cache/ __pycache__/ *.pyc
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "   Suppression des fichiers de build..."
	@rm -rf build/ dist/ *.egg-info/
	@echo "   Désinstallation de Poetry..."
	@echo "⚠️  Téléchargement et exécution de script depuis internet"
	@curl -sSL https://install.python-poetry.org | python3 - --uninstall || echo "Poetry non installé"
	@echo "   Suppression du binaire Poetry..."
	@rm -f ~/.local/bin/poetry
	@echo "   Nettoyage des caches et données Poetry..."
	@rm -rf ~/.config/pypoetry ~/.cache/pypoetry ~/.local/share/pypoetry
	@echo "   Suppression de Poetry du PATH (à faire manuellement)..."
	@echo "   Éditez ~/.zshrc ou ~/.bashrc pour supprimer la ligne:"
	@echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
	@echo "✅ Nettoyage complet terminé !"

### === ENTRAÎNEMENT & TESTS ===
train: ## Entraîner le modèle ML
	@echo "🤖 Entraînement du modèle..."
	$(PYTHON) -m src.training.train

# Tests (options alignées avec la CI)
test: ## Exécuter tous les tests
	@echo "🧪 Exécution des tests..."
	$(PYTEST) -v --tb=short

### === API LOCALE (FastAPI / Uvicorn) ===
run: ## Lancer l'API en mode développement
	@echo "🚀 Lancement de l'API..."
	poetry run uvicorn src.serving.app:app --reload --host 127.0.0.1 --port 8000

run-prod: ## Lancer l'API en mode production
	@echo "🚀 Lancement de l'API en production..."
	poetry run uvicorn src.serving.app:app --host 0.0.0.0 --port 8000

### === DOCKER (BUILD & RUN) ===
build: ## Construire l'image Docker
	@echo "🐳 Construction de l'image Docker..."
	docker build -t $(DOCKER_IMAGE) .

run-docker: ## Lancer l'API avec Docker
	@echo "🐳 Lancement avec Docker..."
	docker run -p 127.0.0.1:8000:8000 $(DOCKER_IMAGE)

run-docker-bg: ## Lancer l'API avec Docker en arrière-plan
	@echo "🐳 Lancement avec Docker en arrière-plan..."
	docker run -d -p 127.0.0.1:8000:8000 --name iris-api $(DOCKER_IMAGE)

stop-docker: ## Arrêter le conteneur Docker
	@echo "🛑 Arrêt du conteneur Docker..."
	docker stop iris-api || true
	docker rm iris-api || true

### === QUALITÉ DU CODE (Black / isort / Flake8) ===
format: ## Formater le code avec Black et isort
	@echo "🎨 Formatage du code..."
	$(BLACK) .
	$(ISORT) .

lint: ## Vérifier la qualité du code
	@echo "🔍 Vérification de la qualité du code..."
	$(FLAKE8) --exclude=$(FLAKE8_EXCLUDE) --count --select=E9,F63,F7,F82 --show-source --statistics .
	$(BLACK) --check .
	$(ISORT) --check-only .

### === CI/CD LOCALE ===
ci: lint test ## Exécuter les vérifications CI (lint + test, aligné sur GitHub Actions)
	@echo "✅ Toutes les vérifications CI sont passées !"

### === NETTOYAGE (artefacts locaux, DVC, MLflow) ===
clean: ## Nettoyer les fichiers temporaires
	@echo "🧹 Nettoyage..."
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ dist/ build/
	@echo "🧹 Nettoyage DVC (fichiers de sortie)..."
	rm -rf data/
	rm -rf models/
	@echo "🧹 Nettoyage MLflow..."
	rm -rf mlruns/
	@echo "🧹 Nettoyage cache DVC..."
	rm -rf .dvc/cache
	@echo "   Suppression du lock DVC..."
	rm -f dvc.lock
	@echo "✅ Nettoyage terminé !"

clean-models: ## Nettoyer les modèles entraînés
	@echo "🧹 Nettoyage des modèles..."
	rm -rf models/

clean-dvc: ## Nettoyer complètement DVC (cache + fichiers générés)
	@echo "🧹 Nettoyage complet DVC..."
	@echo "   Suppression des fichiers de sortie..."
	rm -rf data/
	rm -rf models/
	@echo "   Suppression du cache DVC..."
	rm -rf .dvc/cache
	@echo "   Suppression du lock DVC..."
	rm -f dvc.lock
	@echo "✅ Nettoyage DVC terminé !"

### === RACCOURCIS DÉVELOPPEMENT ===
dev-setup: install train ## Configuration complète pour le développement
	@echo "✅ Configuration de développement terminée !"

### === DOCUMENTATION ===
docs: ## Afficher l’URL de la doc API (Swagger) — l’API doit être lancée (make run)
	@echo "📚 Documentation API (Swagger) : http://localhost:8000/docs"
	@echo "   Lancez l’API avec: make run"

### === SANTÉ / VÉRIFICATIONS LOCALES ===
health: ## Vérifier la santé de l'API
	@echo "❤️  Vérification de la santé de l'API..."
	@curl -f http://localhost:8000/health || echo "❌ API non accessible"

### === DÉPLOIEMENT DOCKER SIMPLE ===
deploy: build run-docker-bg ## Déployer l'API (build + run)
	@echo "🚀 Déploiement terminé !"
	@echo "API disponible sur: http://localhost:8000"
	@echo "Documentation: http://localhost:8000/docs"

### === INFRASTRUCTURE (TERRAFORM) ===
terraform-init: ## Initialiser Terraform
	@echo "🏗️  Initialisation de Terraform..."
	@cd $(TERRAFORM_DIR) && terraform init

terraform-validate: ## Valider la configuration Terraform
	@echo "✅ Validation de la configuration Terraform..."
	@cd $(TERRAFORM_DIR) && terraform validate

terraform-fmt: ## Formater les fichiers Terraform
	@echo "🎨 Formatage des fichiers Terraform..."
	@cd $(TERRAFORM_DIR) && terraform fmt -recursive

terraform-plan: terraform-init ## Planifier les changements Terraform
	@echo "📋 Planification des changements Terraform..."
	@cd $(TERRAFORM_DIR) && terraform plan

terraform-apply: terraform-init ## Appliquer la configuration Terraform
	@echo "🚀 Application de la configuration Terraform..."
	@cd $(TERRAFORM_DIR) && terraform apply

terraform-destroy: ## Détruire l'infrastructure Terraform
	@echo "⚠️  Destruction de l'infrastructure Terraform..."
	@cd $(TERRAFORM_DIR) && terraform destroy

terraform-output: ## Afficher les outputs Terraform
	@echo "📊 Outputs Terraform:"
	@cd $(TERRAFORM_DIR) && terraform output

terraform-refresh: ## Rafraîchir l'état Terraform
	@echo "🔄 Rafraîchissement de l'état Terraform..."
	@cd $(TERRAFORM_DIR) && terraform refresh

### === MLFLOW (LOCAL) ===
mlflow-ui: ## Lancer l'interface MLflow UI
	@echo "📊 Lancement de MLflow UI..."
	@echo "Interface disponible sur: http://localhost:5000"
	@poetry run mlflow ui --host 127.0.0.1 --port 5000

mlflow-experiments: ## Lister les expériences MLflow
	@echo "📊 Expériences MLflow:"
	@poetry run mlflow experiments search 2>/dev/null || echo "Aucune expérience trouvée"

### === DVC (PIPELINE DE DONNÉES) ===
dvc-init: ## Initialiser DVC dans le projet
	@echo "🔄 Initialisation de DVC..."
	@poetry run dvc init || echo "DVC déjà initialisé"

dvc-repro: ## Réexécuter le pipeline DVC
	@echo "🔄 Réexécution du pipeline DVC..."
	@poetry run dvc repro

dvc-status: ## Vérifier l'état du pipeline DVC
	@echo "📊 État du pipeline DVC:"
	@poetry run dvc status || echo "DVC non initialisé"

dvc-push: ## Pousser les données versionnées (si remote configuré)
	@echo "📤 Push des données DVC..."
	@poetry run dvc push || echo "Aucun remote configuré"

dvc-pull: ## Télécharger les données versionnées
	@echo "📥 Pull des données DVC..."
	@poetry run dvc pull || echo "Aucun remote configuré"

dvc-pipeline: ## Afficher le pipeline DVC
	@echo "📊 Pipeline DVC:"
	@poetry run dvc dag || echo "Pipeline non configuré"

### === KUBERNETES (CLUSTER LOCAL / CLOUD) ===
# Cible interne: vérifie que k8s/secret.yaml existe (évite duplication)
_k8s-check-secret:
	@if [ ! -f k8s/secret.yaml ]; then \
		echo "⚠️  secret.yaml n'existe pas. Créez-le depuis secret.yaml.example"; \
		echo "   cp k8s/secret.yaml.example k8s/secret.yaml"; \
		echo "   # Puis éditez k8s/secret.yaml avec vos valeurs"; \
		exit 1; \
	fi

k8s-setup: ## Installer minikube/kind et créer le cluster
	@echo "🚀 Configuration de Kubernetes..."
	@chmod +x scripts/setup-k8s.sh
	@./scripts/setup-k8s.sh minikube

k8s-setup-kind: ## Installer kind et créer le cluster
	@echo "🚀 Configuration de Kubernetes avec kind..."
	@chmod +x scripts/setup-k8s.sh
	@./scripts/setup-k8s.sh kind

k8s-deploy: _k8s-check-secret ## Déployer l'API sur Kubernetes (avec PVC, sans serveur MLflow)
	@echo "🚀 Déploiement sur Kubernetes..."
	@kubectl apply -f k8s/namespace.yaml
	@kubectl apply -f k8s/configmap.yaml
	@kubectl apply -f k8s/secret.yaml
	@echo "📦 Déploiement des volumes persistants (MLflow + modèles)..."
	@kubectl apply -f k8s/mlflow-pvc.yaml
	@kubectl apply -f k8s/models-pvc.yaml
	@kubectl apply -f k8s/deployment.yaml
	@kubectl apply -f k8s/service.yaml
	@echo "✅ Déploiement terminé !"
	@echo "Vérifiez avec: make k8s-status"

k8s-deploy-mlflow: _k8s-check-secret ## Déployer l'API + MLflow server sur Kubernetes (recommandé)
	@echo "🚀 Déploiement complet sur Kubernetes (API + MLflow)..."
	@kubectl apply -f k8s/namespace.yaml
	@kubectl apply -f k8s/configmap.yaml
	@kubectl apply -f k8s/secret.yaml
	@echo "📦 Déploiement des volumes persistants (MLflow + modèles)..."
	@kubectl apply -f k8s/mlflow-pvc.yaml
	@kubectl apply -f k8s/models-pvc.yaml
	@echo "📊 Déploiement du serveur MLflow..."
	@kubectl apply -f k8s/mlflow-deployment.yaml
	@kubectl apply -f k8s/mlflow-service.yaml
	@echo "🚀 Déploiement de l'API..."
	@kubectl apply -f k8s/deployment.yaml
	@kubectl apply -f k8s/service.yaml
	@echo "✅ Déploiement terminé !"
	@echo "Vérifiez avec: make k8s-status"
	@echo ""
	@echo "Pour accéder à MLflow UI:"
	@echo "  make k8s-mlflow-ui"

k8s-status: ## Vérifier le statut du déploiement Kubernetes
	@echo "📊 Statut du déploiement Kubernetes (namespace=$(K8S_NS)):"
	@echo ""
	@echo "=== Namespace ==="
	@kubectl get namespace $(K8S_NS) 2>/dev/null || echo "Namespace $(K8S_NS) n'existe pas"
	@echo ""
	@echo "=== Pods ==="
	@kubectl get pods -n $(K8S_NS)
	@echo ""
	@echo "=== Services ==="
	@kubectl get services -n $(K8S_NS)
	@echo ""
	@echo "=== Deployments ==="
	@kubectl get deployments -n $(K8S_NS)
	@echo ""
	@echo "=== MLflow Server (si déployé) ==="
	@kubectl get deployment mlflow-server -n $(K8S_NS) 2>/dev/null || echo "MLflow server non déployé"
	@echo ""
	@echo "=== PersistentVolumeClaims ==="
	@kubectl get pvc -n $(K8S_NS) 2>/dev/null || echo "Aucun PVC trouvé dans le namespace $(K8S_NS)"
	@echo ""
	@echo "=== PersistentVolumes (liés à mlflow/models) ==="
	@kubectl get pv | grep -E 'mlflow-pvc|models-pvc' || echo "Aucun PV lié à mlflow-pvc/models-pvc"

k8s-logs: ## Voir les logs des pods Kubernetes
	@echo "📋 Logs des pods:"
	@kubectl logs -f deployment/iris-api -n $(K8S_NS) || echo "Aucun pod trouvé"

k8s-delete: ## Supprimer le déploiement Kubernetes
	@echo "🗑️  Suppression du déploiement Kubernetes..."
	@kubectl delete -f k8s/ --ignore-not-found=true
	@echo "✅ Suppression terminée !"

k8s-port-forward: ## Port-forward vers l'API Kubernetes
	@echo "🔌 Port-forward vers l'API..."
	@echo "API accessible sur: http://localhost:8000"
	@echo "Appuyez sur Ctrl+C pour arrêter"
	@kubectl port-forward service/iris-api-service 8000:8000 -n $(K8S_NS)

k8s-mlflow-ui: ## Port-forward vers MLflow UI
	@echo "📊 Port-forward vers MLflow UI..."
	@echo "MLflow UI accessible sur: http://localhost:5000"
	@echo "Appuyez sur Ctrl+C pour arrêter"
	@kubectl port-forward service/mlflow-server-service 5000:5000 -n $(K8S_NS)

k8s-test: ## Tester l'API déployée sur Kubernetes
	@echo "🧪 Test de l'API Kubernetes..."
	@echo "⚠️  Assurez-vous que le port-forward est actif (make k8s-port-forward dans un autre terminal)"
	@sleep 2
	@curl -f http://localhost:8000/health || echo "❌ API non accessible. Vérifiez que le port-forward est actif."
	@echo ""
	@echo "Pour tester avec API key:"
	@echo "  export API_KEY=\$$(kubectl get secret iris-api-secrets -n $(K8S_NS) -o jsonpath='{.data.API_KEY}' | base64 -d)"
	@echo "  curl -H \"X-API-Key: \$$API_KEY\" http://localhost:8000/health"

k8s-clean: ## Nettoyer complètement le déploiement Kubernetes
	@echo "🧹 Nettoyage complet Kubernetes..."
	@kubectl delete namespace $(K8S_NS) --ignore-not-found=true
	@echo "✅ Nettoyage terminé !"

### === MONITORING (PROMETHEUS / GRAFANA / ALERTMANAGER) ===
k8s-monitoring-deploy: ## Déployer la stack de monitoring (Prometheus, Grafana, AlertManager)
	@echo "📊 Déploiement de la stack de monitoring..."
	@kubectl apply -f k8s/monitoring/
	@echo "✅ Monitoring déployé"
	@echo "   Prometheus: kubectl port-forward -n $(K8S_NS) svc/prometheus-service 9090:9090"
	@echo "   Grafana: kubectl port-forward -n $(K8S_NS) svc/grafana-service 3000:3000"
	@echo "   AlertManager: kubectl port-forward -n $(K8S_NS) svc/alertmanager-service 9093:9093"

k8s-monitoring-delete: ## Supprimer la stack de monitoring
	@echo "🗑️  Suppression de la stack de monitoring..."
	@kubectl delete -f k8s/monitoring/ --ignore-not-found=true
	@echo "✅ Monitoring supprimé"

k8s-monitoring-status: ## Vérifier le statut de la stack de monitoring
	@echo "📊 Statut de la stack de monitoring..."
	@kubectl get pods -n $(K8S_NS) -l component=monitoring
	@kubectl get svc -n $(K8S_NS) -l component=monitoring

k8s-monitoring-logs: ## Afficher les logs de Prometheus
	@echo "📋 Logs Prometheus..."
	@kubectl logs -n $(K8S_NS) -l app=prometheus --tail=50

k8s-monitoring-logs-grafana: ## Afficher les logs de Grafana
	@echo "📋 Logs Grafana..."
	@kubectl logs -n $(K8S_NS) -l app=grafana --tail=50

k8s-monitoring-port-forward: ## Port-forward pour Prometheus, Grafana et AlertManager
	@echo "🔌 Port-forward monitoring (Ctrl+C pour arrêter)..."
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana: http://localhost:3000 (admin/admin)"
	@echo "   AlertManager: http://localhost:9093"
	@kubectl port-forward -n $(K8S_NS) svc/prometheus-service 9090:9090 & \
	kubectl port-forward -n $(K8S_NS) svc/grafana-service 3000:3000 & \
	kubectl port-forward -n $(K8S_NS) svc/alertmanager-service 9093:9093 & \
	wait
