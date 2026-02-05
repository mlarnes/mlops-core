# Déploiement Terraform (GCP)

Guide de déploiement de l’infrastructure GCP (VPC, VM, Storage, Secret Manager, Load Balancer). Documentation détaillée et tutoriel : [docs/infrastructure.md](../docs/infrastructure.md).

## Vue d'ensemble

Ce répertoire contient la configuration Terraform pour provisionner l'infrastructure GCP complète de l'API MLOps. Le déploiement inclut :

- **VPC Network** : Réseau privé avec sous-réseau
- **Cloud Storage** : Bucket GCS pour les modèles ML
- **Compute Engine** : VM pour héberger l'API
- **Secret Manager** : Gestion sécurisée des secrets
- **IAM** : Service account avec permissions minimales
- **Firewall** : Règles de sécurité restrictives
- **Load Balancer** : HTTP avec Cloud Armor (optionnel)
- **Monitoring** : Alertes Cloud Monitoring (optionnel)

## Structure des fichiers

```
terraform/
├── main.tf                  # Ressources principales (VPC, VM, Bucket, IAM)
├── variables.tf             # Variables d'entrée
├── outputs.tf               # Valeurs de sortie
├── providers.tf             # Configuration des providers
├── backend.tf.example       # Exemple de configuration backend distant
├── terraform.tfvars.example # Exemple de configuration
└── README.md                # Ce fichier
```

## Déploiement rapide

### Prérequis

- Terraform >= 1.0
- Google Cloud SDK (gcloud)
- Docker
- Accès à un projet GCP avec permissions suffisantes

### Étape 0 : Configuration GCP

```bash
# Variables d'environnement
export PROJECT_ID="your-project-id"
export REGION="europe-west1"

# Authentification
gcloud auth login
gcloud config set project $PROJECT_ID
gcloud auth application-default login

# Activer les APIs nécessaires
gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  iap.googleapis.com
```

### Étape 1 : Préparer les Secrets

```bash
# Générer l'API key
export API_KEY=$(openssl rand -hex 32)
echo "⚠️ SAUVEGARDEZ cette clé dans un endroit sûr !"

# Option A : Création via Terraform (Recommandé)
export TF_VAR_api_key_value="$API_KEY"

# Option B : Création manuelle
echo -n "$API_KEY" | gcloud secrets create mlops-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID
```

### Étape 2 : Configuration Terraform

```bash
# Copier les fichiers d'exemple
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Éditer terraform.tfvars avec vos valeurs
# ⚠️ Ne JAMAIS commiter terraform.tfvars !
```

**Configuration minimale dans `terraform.tfvars`** :
```hcl
project_id = "your-project-id"
iap_tunnel_users = ["votre-email@example.com"]
docker_image = "europe-west1-docker.pkg.dev/$PROJECT_ID/mlops-repo/iris-api:latest"
secret_manager_api_key_name = "mlops-api-key"

# Option A : Création via Terraform
create_secret_manager_secret = true

# Option B : Secret créé manuellement
# create_secret_manager_secret = false
```

**⚠️ Deux scénarios de sécurité** :

**Scénario 1 : Load Balancer (RECOMMANDÉ)**
```hcl
enable_load_balancer = true
enable_public_ip = false
allowed_http_ips = ["130.211.0.0/22", "35.191.0.0/16"]  # Plages IP Load Balancers GCP
allowed_ssh_ips = []  # SSH via IAP uniquement
```

**Scénario 2 : IP publique sur la VM**
```hcl
enable_load_balancer = false
enable_public_ip = true
MY_IP=$(curl -s https://checkip.amazonaws.com)
allowed_ssh_ips = ["${MY_IP}/32"]
allowed_http_ips = ["${MY_IP}/32"]
```

### Étape 3 : Build et Push de l'Image Docker

```bash
# Définir l'URI de l'image
export DOCKER_IMAGE_URI="europe-west1-docker.pkg.dev/$PROJECT_ID/mlops-repo/iris-api:latest"

# Créer le repository Artifact Registry
gcloud artifacts repositories create mlops-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="MLOps API Docker repository" \
  --project=$PROJECT_ID || true

# Configurer Docker
gcloud auth configure-docker $REGION-docker.pkg.dev

# Builder et pusher l'image
docker build --platform linux/amd64 -t $DOCKER_IMAGE_URI .
docker push $DOCKER_IMAGE_URI
```

### Étape 4 : Déployer l'Infrastructure

```bash
# Initialiser Terraform
make terraform-init

# Voir ce qui sera créé
make terraform-plan

# Appliquer la configuration
make terraform-apply
```

### Étape 5 : Uploader le Modèle vers GCS

```bash
# Récupérer le nom du bucket
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)

# Uploader mlruns/ vers GCS
gcloud storage cp -r mlruns/ gs://$BUCKET_NAME/
```

### Étape 6 : Démarrer l'API

```bash
# Récupérer les informations
VM_NAME=$(terraform -chdir=terraform output -raw vm_name)
ZONE=$(terraform -chdir=terraform output -raw vm_zone)

# Se connecter et démarrer le service
gcloud compute ssh $VM_NAME \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --tunnel-through-iap \
  --command="sudo systemctl start mlops-api && sudo systemctl status mlops-api"
```

### Étape 7 : Tester

```bash
# Récupérer l'API key
SECRET_NAME=$(terraform -chdir=terraform output -raw secret_manager_secret_name)
API_KEY=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project=$PROJECT_ID)

# Utiliser le Load Balancer (ou l'IP de la VM)
API_IP=$(terraform -chdir=terraform output -raw load_balancer_ip 2>/dev/null || terraform -chdir=terraform output -raw vm_external_ip)

# Tests
curl http://$API_IP/health
curl -X POST "http://$API_IP/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

## Commandes utiles

| Commande | Description |
|----------|-------------|
| `make terraform-init` | Initialiser Terraform |
| `make terraform-validate` | Valider la configuration |
| `make terraform-fmt` | Formater les fichiers Terraform |
| `make terraform-plan` | Planifier les changements |
| `make terraform-apply` | Déployer l'infrastructure |
| `make terraform-destroy` | Détruire l'infrastructure |
| `make terraform-output` | Afficher les outputs |
| `make terraform-refresh` | Rafraîchir l'état |

## Configuration essentielle

### Variables Obligatoires

Dans `terraform.tfvars` :
- `project_id` : ID du projet GCP
- `iap_tunnel_users` : Liste des emails autorisés pour SSH via IAP
- `docker_image` : URI complète de l'image Docker
- `secret_manager_api_key_name` : Nom du secret dans Secret Manager

### Variables de Sécurité

**Load Balancer (Recommandé)** :
```hcl
enable_load_balancer = true
enable_public_ip = false
allowed_http_ips = ["130.211.0.0/22", "35.191.0.0/16"]
allowed_ssh_ips = []
```

**IP Publique (Développement)** :
```hcl
enable_load_balancer = false
enable_public_ip = true
allowed_ssh_ips = ["VOTRE-IP/32"]
allowed_http_ips = ["VOTRE-IP/32"]
```

### Gestion des Secrets

**Option A : Via Terraform (Recommandé)**
```bash
export TF_VAR_api_key_value="votre-api-key"
# Dans terraform.tfvars
create_secret_manager_secret = true
```

**Option B : Création Manuelle**
```bash
gcloud secrets create mlops-api-key --data-file=- <<< "votre-api-key"
# Dans terraform.tfvars
create_secret_manager_secret = false
```

## Dépannage

### Erreur d'authentification

```bash
gcloud auth application-default login
gcloud config set project $PROJECT_ID
```

### Erreur "API not enabled"

```bash
gcloud services enable compute.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com
```

### Erreur de permissions

Vérifier que votre compte a :
- `roles/owner` OU
- `roles/editor` + `roles/iam.securityAdmin` + `roles/storage.admin`

### Service systemd n'existe pas

```bash
# Vérifier les logs du script de démarrage
ZONE=$(terraform -chdir=terraform output -raw vm_zone)
gcloud compute ssh iris-api-server --zone=$ZONE --project=$PROJECT_ID --tunnel-through-iap \
  --command="sudo cat /var/log/startup.log | tail -100"

# Redémarrer la VM pour relancer le script
gcloud compute instances reset iris-api-server --zone=$ZONE --project=$PROJECT_ID
```

### Modèle non trouvé

```bash
# Vérifier l'upload vers GCS
BUCKET_NAME=$(terraform -chdir=terraform output -raw bucket_name)
gcloud storage ls gs://$BUCKET_NAME/mlruns/

# Réuploader si nécessaire
gcloud storage cp -r mlruns/ gs://$BUCKET_NAME/
```

## Documentation

- [Infrastructure](../docs/infrastructure.md) — Documentation complète avec :
  - Vue d'ensemble et état du projet
  - Sécurité et améliorations
  - Tutoriel de déploiement complet
  - Ressources créées
  - Commandes Terraform utiles
  - Checklist de production
  - Dépannage détaillé
- [Makefile](../Makefile) — Toutes les commandes `make terraform-*`

## Sécurité

### Bonnes pratiques implémentées

- ✅ Firewalls restrictifs (deny by default)
- ✅ Secret Manager pour les secrets
- ✅ Service account avec permissions minimales
- ✅ Load Balancer avec Cloud Armor (optionnel)
- ✅ Monitoring et alertes (optionnel)
- ✅ Support KMS pour chiffrement (optionnel)

### Recommandations production

- 🔐 Utiliser Load Balancer au lieu d'IP publique
- 🔐 SSH via IAP uniquement
- 🔐 Activer Cloud Armor pour protection DDoS
- 🔐 Configurer les alertes de monitoring
- 🔐 Utiliser KMS pour chiffrement des données sensibles

## Nettoyage

```bash
# Détruire l'infrastructure
make terraform-destroy

# ⚠️ Attention : Cela supprimera toutes les ressources créées
# Le bucket ne sera pas supprimé si force_destroy_bucket = false
```

---

**Documentation détaillée** : [docs/infrastructure.md](../docs/infrastructure.md) (concepts, sécurité, workflows).
