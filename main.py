from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import numpy as np
import os
import csv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["VR_Db"]
collection_parties = db["parties"]

partie_en_cours_id = None
nom_fichier_csv = "data.csv"


def initialiser_fichier_csv():
    """Verifie l'existence du fichier d'acquisition et initialise les entetes si necessaire."""
    if not os.path.exists(nom_fichier_csv):
        with open(nom_fichier_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "partie_id", "action_id", "couleur_balle", "temps_reaction",
                "vitesse_moyenne_main_droite", "vitesse_max_main_droite",
                "hesitation_axe_x", "nb_frames_capturees", "reussite"
            ])
        logger.info(f"Initialisation du fichier d'acquisition : {nom_fichier_csv}")
    else:
        logger.info(f"Fichier d'acquisition existant detecte : {nom_fichier_csv}")


def calculer_et_ajouter_au_csv(partie_id, action_data):
    """Calcule les metriques cinematiques et synchronise les donnees avec le fichier CSV."""
    flux = action_data.get("fluxMouvements", [])
    vitesses_main_droite = []
    positions_x_main_droite = []
    
    for i in range(1, len(flux)):
        p1 = flux[i-1]["mainDroite"]
        p2 = flux[i]["mainDroite"]
        t1 = flux[i-1]["timestamp"]
        t2 = flux[i]["timestamp"]
        
        distance = np.sqrt((p2["x"] - p1["x"])**2 + (p2["y"] - p1["y"])**2 + (p2["z"] - p1["z"])**2)
        dt = t2 - t1
        if dt > 0:
            vitesses_main_droite.append(distance / dt)
        
        positions_x_main_droite.append(p2["x"])

    vitesse_moyenne = np.mean(vitesses_main_droite) if vitesses_main_droite else 0
    vitesse_max = np.max(vitesses_main_droite) if vitesses_main_droite else 0
    hesitation_x = np.std(positions_x_main_droite) if positions_x_main_droite else 0
    reussite_numerique = 1 if action_data.get("reussite", False) else 0

    with open(nom_fichier_csv, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            partie_id,
            action_data["action_id"],
            action_data["couleur_balle"],
            action_data["temps_reaction"],
            vitesse_moyenne,
            vitesse_max,
            hesitation_x,
            len(flux),
            reussite_numerique
        ])


initialiser_fichier_csv()


@app.route('/api/partie/demarrer', methods=['POST'])
def demarrer_partie():
    global partie_en_cours_id
    try:
        nouvelle_partie = {
            "duree_partie": 0,
            "date_enregistrement": datetime.utcnow(),
            "score": {
                "score_final": 0,
                "balle_reussi": 0,
                "balle_rattees": 0
            },
            "actions": []
        }
        
        resultat = collection_parties.insert_one(nouvelle_partie)
        
        if resultat.acknowledged:
            partie_en_cours_id = str(resultat.inserted_id)
            logger.info(f"Nouvelle session initialisee dans MongoDB. ID: {partie_en_cours_id}")
            return jsonify({"status": "success", "partie_id": partie_en_cours_id}), 201
        else:
            return jsonify({"status": "error", "message": "Echec de l'insertion dans la base de donnees"}), 500
            
    except Exception as e:
        logger.error(f"Erreur lors du demarrage de la partie : {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/partie/ajouter_action', methods=['POST'])
def ajouter_action():
    try:
        data = request.json
        partie_id = data.get("partie_id") or partie_en_cours_id
        action_id = int(data.get("action_id", 0))
        
        if not partie_id:
            return jsonify({"status": "error", "message": "Aucune session active identifiee"}), 400
        
        nouvelle_action = {
            "action_id": action_id,
            "couleur_balle": data["couleur_balle"],
            "temps_reaction": data["temps_reaction"],
            "reussite": data["reussite"],
            "fluxMouvements": data["fluxMouvements"]
        }
        
        resultat_mongo = collection_parties.update_one(
            {"_id": ObjectId(partie_id)},
            {"$push": {"actions": nouvelle_action}}
        )
        
        calculer_et_ajouter_au_csv(partie_id, nouvelle_action)
        
        if resultat_mongo.modified_count > 0:
            return jsonify({
                "status": "success", 
                "message": "Donnes persistees avec succes (MongoDB + CSV)"
            }), 200
        else:
            return jsonify({"status": "error", "message": "Echec de la mise a jour de la session"}), 404
            
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'action : {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/partie/terminer', methods=['POST'])
def terminer_partie():
    global partie_en_cours_id
    try:
        data = request.json
        partie_id = data.get("partie_id") or partie_en_cours_id
        
        if not partie_id:
            return jsonify({"status": "error", "message": "Aucune session active a cloturer"}), 400
        
        collection_parties.update_one(
            {"_id": ObjectId(partie_id)},
            {"$set": {
                "duree_partie": data["duree_partie"],
                "date_enregistrement": datetime.utcnow(),
                "score": {
                    "score_final": data["score_final"],
                    "balle_reussi": data["balle_reussi"],
                    "balle_rattees": data["balle_rattees"]
                }
            }}
        )
        
        logger.info(f"Session {partie_id} cloturee et archivee avec succes.")
        partie_en_cours_id = None
        return jsonify({"status": "success", "message": "Session cloturee"}), 200
            
    except Exception as e:
        logger.error(f"Erreur lors de la cloture de la session : {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info("Serveur d'acquisition de donnees principal en ligne sur le PORT 5000")
    app.run(port=5000, debug=False)