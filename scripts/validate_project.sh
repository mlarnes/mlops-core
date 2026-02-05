#!/bin/bash

# Script de validation complète du projet MLOps - Phase 1
# Usage: ./scripts/validate_project.sh

echo "🔍 Validation complète du projet MLOps - Phase 1"
echo "================================================"

# Variables
# Utilise le répertoire parent du script (plus portable que chemin hardcodé)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXIT_CODE=0

# Fonction pour afficher les résultats
print_result() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
    else
        echo "❌ $2"
        EXIT_CODE=1
    fi
}

# Vérification de la structure du projet
echo "📁 Vérification de la structure du projet..."
required_files=(
    "src/serving/app.py"
    "src/training/train.py"
    "src/config.py"
    "pyproject.toml"
    "Dockerfile"
    "docker-compose.yml"
    "Makefile"
    "README.md"
    "tests/test_api.py"
    "tests/test_model.py"
    "scripts/setup.sh"
    "scripts/validate_project.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        print_result 0 "Fichier $file présent"
    else
        print_result 1 "Fichier $file manquant"
    fi
done

# Vérification de Poetry
echo ""
echo "🐍 Vérification de Poetry..."
if command -v poetry &> /dev/null; then
    print_result 0 "Poetry installé"
    poetry --version
else
    print_result 1 "Poetry non installé"
fi

# Vérification de Python
echo ""
echo "🐍 Vérification de Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version | cut -d' ' -f2)
    print_result 0 "Python $python_version installé"
else
    print_result 1 "Python non installé"
fi

# Vérification de Docker
echo ""
echo "🐳 Vérification de Docker..."
if command -v docker &> /dev/null; then
    print_result 0 "Docker installé"
    docker --version
else
    print_result 1 "Docker non installé"
fi

# Vérification de Make
echo ""
echo "🛠️  Vérification de Make..."
if command -v make &> /dev/null; then
    print_result 0 "Make installé"
    make --version | head -1
else
    print_result 1 "Make non installé"
fi

# Test de l'entraînement du modèle
echo ""
echo "🤖 Test d'entraînement du modèle..."
cd "$PROJECT_DIR"
if python3 -m src.training.train > /dev/null 2>&1; then
    print_result 0 "Entraînement du modèle réussi"
    # Vérifier que metadata.json contient les infos MLflow
    if [ -f "models/metadata.json" ]; then
        print_result 0 "Métadonnées sauvegardées"
        # Vérifier que mlflow_run_id est présent (requis pour charger le modèle)
        if grep -q "mlflow_run_id" "models/metadata.json"; then
            print_result 0 "Référence MLflow (run_id) présente dans metadata.json"
        else
            print_result 1 "Référence MLflow (run_id) manquante dans metadata.json"
        fi
    else
        print_result 1 "Métadonnées non sauvegardées"
    fi
    if [ -f "models/metrics.json" ]; then
        print_result 0 "Métriques sauvegardées"
    else
        print_result 1 "Métriques non sauvegardées"
    fi
    # Vérifier que le modèle est dans MLflow (mlruns/)
    if [ -d "mlruns" ] && [ "$(find mlruns -name 'model' -type d | wc -l)" -gt 0 ]; then
        print_result 0 "Modèle enregistré dans MLflow"
    else
        print_result 1 "Modèle non trouvé dans MLflow"
    fi
else
    print_result 1 "Échec de l'entraînement du modèle"
fi

# Test des tests unitaires
echo ""
echo "🧪 Test des tests unitaires..."
if python3 -m pytest tests/ -v > /dev/null 2>&1; then
    print_result 0 "Tests unitaires passent"
else
    print_result 1 "Tests unitaires échouent"
fi

# Test du build Docker
echo ""
echo "🐳 Test du build Docker..."
if docker build -t iris-api-test . > /dev/null 2>&1; then
    print_result 0 "Build Docker réussi"
    # Nettoyage de l'image de test
    docker rmi iris-api-test > /dev/null 2>&1
else
    print_result 1 "Build Docker échoue"
fi

# Vérification de la qualité du code
echo ""
echo "🎨 Vérification de la qualité du code..."
if command -v flake8 &> /dev/null; then
    if flake8 src/serving/app.py src/training/train.py tests/ > /dev/null 2>&1; then
        print_result 0 "Code conforme à flake8"
    else
        print_result 1 "Code non conforme à flake8"
    fi
else
    print_result 0 "flake8 non installé (optionnel)"
fi

# Résumé
echo ""
echo "📊 Résumé de la validation"
echo "=========================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tous les tests sont passés ! Le projet est prêt."
    echo ""
    echo "🚀 Prochaines étapes :"
    echo "   1. make install    # Installer Poetry et les dépendances"
    echo "   2. make train      # Entraîner le modèle"
    echo "   3. make run        # Lancer l'API"
    echo "   4. make test       # Exécuter les tests"
    echo "   5. make build      # Construire l'image Docker"
else
    echo "❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus."
fi

exit $EXIT_CODE
