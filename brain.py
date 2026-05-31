from flask import Flask, jsonify, request
import pandas as pd
import os
import logging
import numpy as np

from inference import DDAPredictor, LancerFeatures
from session_manager import InMemorySessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

nom_fichier_csv = "data.csv"
path_modele_pkl = "preprocessors.pkl" 
PARTIE_SESSION_ID = "partie_vr_dda_live"

logger.info("Initialisation du moteur de prediction Random Forest Classifier")
session_manager = InMemorySessionManager()
predictor = DDAPredictor(model_path=path_modele_pkl, session_manager=session_manager)

decision_actuelle = 0
dernier_action_id_traite = 0  
to_decide = 0 
lancers_du_paquet_courant = [] 


def executer_inference_sur_paquet_strict():
    """ Orchestre l'accumulation des paquets et l'inference multivariee du modele """
    global decision_actuelle, dernier_action_id_traite, to_decide, lancers_du_paquet_courant
    
    if not os.path.exists(nom_fichier_csv) or os.path.getsize(nom_fichier_csv) == 0:
        return decision_actuelle
        
    try:
        df = pd.read_csv(nom_fichier_csv)
        if len(df) == 0:
            return decision_actuelle

        dernier_lancer_df = df.iloc[-1]
        action_id_actuel = int(dernier_lancer_df['action_id'])
        
        if action_id_actuel == dernier_action_id_traite:
            return decision_actuelle

        dernier_action_id_traite = action_id_actuel
        to_decide += 1 

        features_list = [
            float(dernier_lancer_df['temps_reaction']),
            float(dernier_lancer_df['vitesse_moyenne_main_droite']),
            float(dernier_lancer_df['vitesse_max_main_droite']),
            float(dernier_lancer_df['hesitation_axe_x'])
        ]
        
        lancers_du_paquet_courant.append(features_list)
        
        if to_decide < 5:
            decision_actuelle = 0
            return decision_actuelle

        input_vector = np.array(lancers_du_paquet_courant).flatten().reshape(1, -1)
        
        # Extraction des probabilites calculees par la foret d'arbres
        probabilites = predictor._pipeline.predict_proba(input_vector)[0]
        
        # Ajustement du seuil algorithmique (Threshold Tuning à 35%) pour casser le biais de l'état nominal
        seuil_adaptation = 0.35
        
        if len(probabilites) > 1 and probabilites[1] >= seuil_adaptation:
            prediction_class = 1  # Priorite a l'Ennui (Transition HARD)
        elif len(probabilites) > 2 and probabilites[2] >= seuil_adaptation:
            prediction_class = 2  # Priorite au Stress (Transition EASY)
        else:
            prediction_class = 0  # Maintien du comportement Stable
            
        status_text = "Stable"
        if prediction_class == 1: 
            status_text = "Ennuie"
        elif prediction_class == 2: 
            status_text = "Stress"
        
        print("\n" + "="*60)
        print("RAPPORT D'INFERENCE MATRICIELLE - SYSTEME DDA")
        print(f"Lancer traite ID          : #{action_id_actuel}")
        print("Distribution des certitudes de la Foret :")
        print(f"  -> Classe 0 (Stable)    : {probabilites[0]:.2%}")
        print(f"  -> Classe 1 (Ennui)     : {probabilites[1]:.2%}" if len(probabilites) > 1 else "  -> Classe 1 (Ennui)     : 0.00%")
        print(f"  -> Classe 2 (Stress)    : {probabilites[2]:.2%}" if len(probabilites) > 2 else "  -> Classe 2 (Stress)    : 0.00%")
        print(f"Decision predictive d'IA  : Code {prediction_class} ({status_text})")
        print("="*60 + "\n")

        decision_actuelle = prediction_class

        to_decide = 0
        lancers_du_paquet_courant = []
        session_manager.clear_session(PARTIE_SESSION_ID)

    except Exception as e:
        logger.error(f"Erreur lors de l'execution du pipeline d'inference : {str(e)}")
        to_decide = 0
        lancers_du_paquet_courant = []

    return decision_actuelle


@app.route('/api/dda/decision', methods=['GET'])
def obtenir_decision():
    code_calcule = executer_inference_sur_paquet_strict()
    status_text = "Stable"
    if code_calcule == 1: 
        status_text = "Ennuie"
    elif code_calcule == 2: 
        status_text = "Stress"
    return jsonify({"prediction": code_calcule, "status": status_text}), 200


@app.route('/api/dda/reset', methods=['POST'])
def réinitialiser_ia_partie():
    global decision_actuelle, dernier_action_id_traite, to_decide, lancers_du_paquet_courant
    try:
        session_manager.clear_session(PARTIE_SESSION_ID)
        decision_actuelle = 0
        dernier_action_id_traite = 0
        to_decide = 0
        lancers_du_paquet_courant = []
        return jsonify({"message": "Fermeture de session reussie", "status": "reset"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Serveur de decision en temps reel operationnel sur le PORT 5001")
    app.run(port=5001, debug=False, host='0.0.0.0')