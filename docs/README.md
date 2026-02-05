# Documentation pédagogique — Parcours MLOps

Ce dossier contient la **documentation détaillée et pédagogique** du projet, organisée par thème : serving, CI/CD, infrastructure, expérimentation, orchestration, observabilité. Elle s’adresse aux personnes qui souhaitent comprendre pas à pas les concepts, les choix techniques et les bonnes pratiques.

## Contenu par thème

| Thème | Fichier | Objectif |
|-------|---------|----------|
| **Serving & Containerisation** | [serving-containerisation.md](serving-containerisation.md) | API FastAPI + Docker, premiers tests |
| **CI/CD** | [cicd.md](cicd.md) | GitHub Actions, build et push d’images |
| **Infrastructure** | [infrastructure.md](infrastructure.md) | Terraform, GCP, sécurité, déploiement |
| **Expérimentation** | [experimentation.md](experimentation.md) | MLflow, DVC, reproductibilité |
| **Orchestration** | [orchestration.md](orchestration.md) | Kubernetes, HPA, workflows MLflow |
| **Observabilité** | [observability.md](observability.md) | Prometheus, Grafana, AlertManager |

Chaque thème inclut :
- objectifs et questions clés ;
- répartition indicative du temps ;
- tâches et livrables ;
- instructions détaillées et exemples ;
- validation des objectifs et dépannage.

## Utilisation

- **Suivi du parcours** : enchaîner les thèmes dans l’ordre (serving → CI/CD → infrastructure → expérimentation → orchestration → observabilité).
- **Référence** : utiliser la table des matières de chaque fichier pour cibler une section.
- **Déploiement rapide** : pour des commandes directes sans tutoriel, voir le [README principal](../README.md) et les README des dossiers `terraform/` et `k8s/`.

## Navigation

- [Retour au README principal](../README.md)
