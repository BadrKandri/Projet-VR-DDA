import os
import time
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def label_window(window: pd.DataFrame) -> int:
    """
    Labelisation multivariee basee sur le profilage cinematique et de performance.
    0 = Stable / Flow (Comportement nominal regulier)
    1 = Ennui (Sur-performance structurelle : haute vitesse, faible hesitation)
    2 = Stress / Frustration (Sous-performance cinematique : forte hesitation, blocages)
    """
    reussite_sum = window['reussite'].sum()
    mean_reaction = window['temps_reaction'].mean()
    mean_hesitation = window['hesitation_axe_x'].mean()
    mean_vitesse_max = window['vitesse_max_main_droite'].mean()

    if reussite_sum >= 4:
        if mean_reaction <= 3.8 or (mean_vitesse_max >= 1.2 and mean_hesitation <= 0.015):
            return 1
    elif reussite_sum <= 2 or mean_reaction >= 5.0 or mean_hesitation >= 0.04:
        return 2

    return 0

def prepare_data(csv_path: str):
    """Charge le dataset d'acquisition et construit les tenseurs d'apprentissage."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Le fichier {csv_path} est introuvable.")

    df = pd.read_csv(csv_path)
    
    features_cols = [
        'temps_reaction', 
        'vitesse_moyenne_main_droite', 
        'vitesse_max_main_droite', 
        'hesitation_axe_x'
    ]

    X_sequences = []
    y_labels = []
    groups = []  

    for pid, group in df.groupby('partie_id'):
        group_sorted = group.sort_values('action_id')
        n_lancers = len(group_sorted)
        
        if n_lancers < 5:
            continue

        for i in range(n_lancers - 4):
            window_df = group_sorted.iloc[i:i+5]
            window_features = window_df[features_cols].values.flatten()
            X_sequences.append(window_features)
            
            label = label_window(window_df)
            y_labels.append(label)
            groups.append(pid)

    return np.array(X_sequences), np.array(y_labels), np.array(groups)

def train_pipeline(csv_path: str, model_export_path: str):
    """Execute le pipeline complet d'apprentissage et de serialisation du modele."""
    start_time = time.time()
    logger.info("Initialisation du pipeline d'apprentissage et de validation croisee")

    try:
        X, y, groups = prepare_data(csv_path)
        logger.info(f"Matrice de caracteristiques generee : X Shape = {X.shape}, y Shape = {y.shape}")
        
        unique_classes, class_counts = np.unique(y, return_counts=True)
        class_distribution = dict(zip(unique_classes, class_counts))
        logger.info(f"Distribution des classes cible : {class_distribution}")

        if len(unique_classes) < 3:
            logger.error("Rupture du pipeline : representation des classes insuffisante")
            return

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_split=4,
                random_state=42,
                class_weight='balanced'
            ))
        ])

        sgkf = StratifiedGroupKFold(n_splits=5)
        fold_reports = []

        for fold_idx, (train_idx, test_idx) in enumerate(sgkf.split(X, y, groups)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)

            report = classification_report(y_test, y_pred, zero_division=0, output_dict=True)
            fold_reports.append(report)

        mean_accuracy = np.mean([r['accuracy'] for r in fold_reports])
        mean_f1_macro = np.mean([r['macro avg']['f1-score'] for r in fold_reports])
        logger.info(f"Metriques de validation - Accuracy: {mean_accuracy:.4f} - F1 Macro: {mean_f1_macro:.4f}")

        logger.info("Entrainement final du modele sur l'integralite du dataset d'acquisition")
        pipeline.fit(X, y)

        export_dir = os.path.dirname(model_export_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        joblib.dump(pipeline, model_export_path)
        logger.info(f"Pipeline serialise exporte avec succes : {model_export_path}")

    except Exception as e:
        logger.error(f"Erreur fatale durant l'execution du pipeline : {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    csv_file = "data.csv"
    model_output = "preprocessors.pkl"
    train_pipeline(csv_file, model_output)