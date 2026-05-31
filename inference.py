import os
import time
import logging
import joblib
import numpy as np
from pydantic import BaseModel, Field
from session_manager import SessionManager, InMemorySessionManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modèle de validation Pydantic pour assurer la qualité des données en entrée (production-ready)
class LancerFeatures(BaseModel):
    temps_reaction: float = Field(..., ge=0.0, description="Temps écoulé en secondes avant le lancer")
    vitesse_moyenne_main_droite: float = Field(..., ge=0.0, description="Vitesse moyenne du contrôleur droit en m/s")
    vitesse_max_main_droite: float = Field(..., ge=0.0, description="Pic de vitesse atteint pendant le lancer en m/s")
    hesitation_axe_x: float = Field(..., ge=0.0, description="Écart-type de la position sur l'axe X (hésitation)")

class InferenceResponse(BaseModel):
    partie_id: str
    prediction: int = Field(..., description="0 = Stable, 1 = Ennui, 2 = Stress")
    status: str = Field(..., description="Détail sur l'état de l'inférence (démarrage à froid ou prédiction active)")
    lancers_count: int = Field(..., description="Nombre de lancers actuellement dans la fenêtre de session")
    execution_time_ms: float = Field(..., description="Temps d'exécution de l'inférence en millisecondes")


class DDAPredictor:
    """
    Moteur de prédiction DDA temps réel.
    Gère le chargement du pipeline et coordonne l'historique et la prédiction.
    """
    def __init__(self, model_path: str, session_manager: SessionManager):
        self.session_manager = session_manager
        self.model_path = model_path
        self._pipeline = None
        self._load_model()

    def _load_model(self):
        """
        Charge de manière thread-safe le pipeline sérialisé preprocessors.pkl.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Le fichier de modèle {self.model_path} est introuvable. Veuillez d'abord exécuter train.py.")
        
        start_time = time.time()
        logger.info(f"Chargement du pipeline DDA : {self.model_path}...")
        self._pipeline = joblib.load(self.model_path)
        duration = time.time() - start_time
        logger.info(f"Pipeline chargé avec succès en {duration:.4f} secondes.")

    def predict(self, partie_id: str, new_lancer: LancerFeatures) -> InferenceResponse:
        """
        Orchestre le cycle complet d'inférence pour un nouveau lancer :
        1. Feature engineering / validation
        2. Intégration dans l'historique glissant de la session
        3. Inférence si la fenêtre de 5 lancers est complète
        4. Gestion du démarrage à froid (renvoi de la classe 0 par défaut si < 5 lancers)
        """
        start_time = time.time()

        try:
            # Conversion des caractéristiques Pydantic en liste brute
            features_list = [
                new_lancer.temps_reaction,
                new_lancer.vitesse_moyenne_main_droite,
                new_lancer.vitesse_max_main_droite,
                new_lancer.hesitation_axe_x
            ]

            # 1. Ajout au gestionnaire de session
            history = self.session_manager.add_lancer(partie_id, features_list)
            lancers_count = len(history)

            # 2. Gestion du Démarrage à Froid
            if lancers_count < 5:
                execution_time = (time.time() - start_time) * 1000.0
                return InferenceResponse(
                    partie_id=partie_id,
                    prediction=0, # Par défaut, on maintient l'état Stable
                    status="démarrage à froid (historique insuffisant)",
                    lancers_count=lancers_count,
                    execution_time_ms=round(execution_time, 4)
                )

            # 3. Préparation du vecteur glissant de taille 20
            # Conversion de la liste de 5 lancers de taille 4 en un vecteur 1D plat
            input_vector = np.array(history).flatten().reshape(1, -1)

            # 4. Inférence via le pipeline Scikit-Learn (normalisation + classification)
            prediction_class = int(self._pipeline.predict(input_vector)[0])
            
            execution_time = (time.time() - start_time) * 1000.0
            return InferenceResponse(
                partie_id=partie_id,
                prediction=prediction_class,
                status="prédiction active (modèle interrogé)",
                lancers_count=lancers_count,
                execution_time_ms=round(execution_time, 4)
            )

        except Exception as e:
            logger.error(f"Erreur durant l'inférence pour la session {partie_id} : {str(e)}", exc_info=True)
            raise
