import os
import time
import logging
import pandas as pd
import numpy as np

# Configuration du logging de production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_eda(csv_path: str):
    """
    Effectue une analyse exploratoire des données (EDA) sur le dataset cinématique.
    Calcule les percentiles clés pour déterminer les seuils métiers d'annotation.
    """
    start_time = time.time()
    logger.info(f"Démarrage de l'analyse exploratoire sur : {csv_path}")

    try:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Le fichier {csv_path} n'existe pas.")

        # Chargement des données
        df = pd.read_csv(csv_path)
        row_count = len(df)
        logger.info(f"Chargement réussi. Nombre de lignes traitées : {row_count}")

        # Sélection des colonnes d'intérêt cinématique et de performance
        target_features = [
            'temps_reaction', 
            'vitesse_moyenne_main_droite', 
            'vitesse_max_main_droite', 
            'hesitation_axe_x',
            'nb_frames_capturees',
            'reussite'
        ]

        # Vérification de la présence des colonnes
        missing_cols = [col for col in target_features if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Colonnes manquantes dans le CSV : {missing_cols}")

        # Description statistique de base (moyenne, écart-type, min, max)
        desc_stats = df[target_features].describe()
        logger.info("Statistiques descriptives de base calculées.")

        # Calcul spécifique des percentiles pour l'analyse des seuils d'étiquetage
        percentiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
        percentiles_df = df[target_features].quantile(percentiles)
        logger.info("Percentiles (5%, 10%, 25%, 50%, 75%, 90%, 95%) calculés.")

        # Taux de réussite global
        overall_success_rate = df['reussite'].mean()
        logger.info(f"Taux de réussite moyen global : {overall_success_rate:.2%}")

        # Log des statistiques descriptives
        logger.info("\n--- STATISTIQUES DESCRIPTIVES GENERALES ---\n%s", desc_stats.to_string())
        logger.info("\n--- TABLEAU DES PERCENTILES CLÉS (SEUILS) ---\n%s", percentiles_df.to_string())

        # Exemple d'analyse de corrélation
        corr_matrix = df[target_features].corr()
        logger.info("\n--- MATRICE DE CORRELATION ---\n%s", corr_matrix.to_string())

        duration = time.time() - start_time
        logger.info(f"Analyse terminée avec succès en {duration:.4f} secondes. {row_count} lignes analysées.")

    except Exception as e:
        logger.error(f"Une erreur est survenue lors de l'exécution de l'EDA : {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    csv_file_path = r"c:\Users\saady\Documents\Unity ML\data.csv"
    run_eda(csv_file_path)
