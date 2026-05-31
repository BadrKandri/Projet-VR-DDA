import logging
from inference import DDAPredictor, LancerFeatures
from session_manager import InMemorySessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dda_inference():
    """
    Validation du comportement d'inference du pipeline DDA sur des sequences de lancers.
    """
    model_path = "preprocessors.pkl"
    
    session_manager = InMemorySessionManager()
    predictor = DDAPredictor(model_path=model_path, session_manager=session_manager)
    partie_id = "partie_validation_pipeline"
    
    lancers_test = [
        LancerFeatures(temps_reaction=3.0, vitesse_moyenne_main_droite=0.04, vitesse_max_main_droite=1.2, hesitation_axe_x=0.01),
        LancerFeatures(temps_reaction=2.8, vitesse_moyenne_main_droite=0.05, vitesse_max_main_droite=1.5, hesitation_axe_x=0.005),
        LancerFeatures(temps_reaction=3.2, vitesse_moyenne_main_droite=0.03, vitesse_max_main_droite=1.1, hesitation_axe_x=0.015),
        LancerFeatures(temps_reaction=2.9, vitesse_moyenne_main_droite=0.04, vitesse_max_main_droite=1.3, hesitation_axe_x=0.008),
        LancerFeatures(temps_reaction=3.1, vitesse_moyenne_main_droite=0.05, vitesse_max_main_droite=1.4, hesitation_axe_x=0.01)
    ]

    logger.info("Execution de la sequence de lancers de validation")
    
    for idx, lancer in enumerate(lancers_test):
        response = predictor.predict(partie_id=partie_id, new_lancer=lancer)
        logger.info(
            f"Sequence {idx + 1}/5 - "
            f"Prediction: {response.prediction} - "
            f"Lancers en cache: {response.lancers_count} - "
            f"Latence: {response.execution_time_ms:.4f} ms"
        )

    session_manager.clear_session(partie_id)
    logger.info("Tests d'inference executes")

if __name__ == "__main__":
    test_dda_inference()