"""
Script de préparation des données pour le dataset Iris
Lit les paramètres depuis params.yaml avec validation Pydantic
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

from src.config import get_config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def prepare_iris_data(
    test_size: Optional[float] = None, random_state: Optional[int] = None
) -> Tuple[Path, Path]:
    """
    Prépare le dataset Iris et le divise en train/test
    Sauvegarde les fichiers dans data/processed/

    Args:
        test_size: Proportion du dataset pour le test (surcharge params.yaml si fourni)
        random_state: Graine aléatoire (surcharge params.yaml si fourni)

    Returns:
        Tuple[Path, Path]: Chemins vers les fichiers train.csv et test.csv
    """
    config = get_config()
    test_size = test_size if test_size is not None else config.data.test_size
    random_state = (
        random_state if random_state is not None else config.data.random_state
    )

    logger.info("🌱 Chargement du dataset Iris...")
    logger.info(f"   Paramètres: test_size={test_size}, random_state={random_state}")

    iris = load_iris()

    # Créer un DataFrame
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["target"] = iris.target
    df["target_name"] = df["target"].apply(lambda x: iris.target_names[x])

    # Créer les répertoires
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le dataset complet (raw)
    raw_path = raw_dir / "iris.csv"
    df.to_csv(raw_path, index=False)
    logger.info(f"💾 Dataset brut sauvegardé dans : {raw_path}")

    # Diviser en train/test avec les paramètres validés
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=df["target"]
    )

    # Sauvegarder train et test
    train_path = processed_dir / "train.csv"
    test_path = processed_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    logger.info(f"💾 Dataset d'entraînement sauvegardé dans : {train_path}")
    logger.info(f"💾 Dataset de test sauvegardé dans : {test_path}")
    logger.info(f"   Train: {len(train_df)} échantillons")
    logger.info(f"   Test: {len(test_df)} échantillons")

    # Statistiques
    logger.info("\n📊 Statistiques du dataset :")
    logger.info(f"   Total: {len(df)} échantillons")
    logger.info(f"   Features: {len(iris.feature_names)}")
    logger.info(f"   Classes: {len(iris.target_names)}")
    logger.info(f"   Distribution des classes (train):")
    logger.info(train_df["target_name"].value_counts().to_string())

    logger.info("✅ Préparation des données terminée !")
    return train_path, test_path


if __name__ == "__main__":
    prepare_iris_data()
