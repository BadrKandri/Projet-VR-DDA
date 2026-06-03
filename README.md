# Infrastructure d'Adaptation Cognitive Événementielle en Réalité Virtuelle (DDA)

Ce projet de fin de module (**PFA**) présente une architecture logicielle distribuée pour l'**Ajustement Dynamique de la Difficulté (**DDA**)** dans un environnement immersif en réalité virtuelle.

L'objectif est de maintenir l'utilisateur dans sa **Zone de Flow** en estimant en temps réel sa charge cognitive à partir de ses flux cinématiques, sans recours à des signaux haptiques ou biologiques.

## Aperçu

Le système repose sur deux briques principales:

- un client Unity qui capture les mouvements du joueur et pilote l'expérience VR;
- un backend Python qui agrège les données, exécute l'inférence et ajuste la difficulté.

Cette séparation limite l'impact du calcul d'inférence sur le rendu 3D et aide à conserver un framerate stable dans le casque.

## Architecture du projet

```
projet-final/
├── Client_VR_Unity/          # Application cliente immersive (Unity 3D / C#)
│   ├── Assets/
│   │   ├── Scripts/          # GameManager.cs, DataCollector.cs, spawners...
│   │   └── Prefabs/          # Projectiles, environnements physiques
│   └── ProjectSettings/
├── brain.py                  # Serveur d'inférence temps réel et **API** **DDA** (Flask / Python)
├── train.py                  # Pipeline d'apprentissage supervisé (Scikit-Learn)
├── session_manager.py        # Gestionnaire de sessions de jeu en mémoire
├── preprocessors.pkl         # Pipeline du modèle sérialisé
└── data.csv                  # Base de caractéristiques cinématiques condensées
```

## Fonctionnement

### Captation

Le script `DataCollector.cs` échantillonne à 10 Hz les positions de la tête et des deux contrôleurs XR.

### Ingestion et stockage

À la fin de chaque lancer, les trames brutes sont envoyées à l'**API** d'acquisition, puis historisées dans MongoDB. En parallèle, les variables condensées de performance alimentent `data.csv`.

### Inférence

Le serveur `brain.py` attend l'accumulation d'un paquet strict de 5 lancers avant d'évaluer l'état du joueur. Le modèle Random Forest calcule alors la distribution des probabilités.

### Régulation de la difficulté

Si la probabilité d'un état d'Ennui ou de Stress dépasse le seuil calibré de 35 %, le serveur déclenche une transition immédiate de difficulté. Unity bascule alors entre:

- une scène `Easy`, statique et prédictible;
- une scène `Hard`, avec permutations aléatoires de Fisher-Yates et masquage temporaire des couleurs.

## Étapes de réalisation

### 1. Conception de l'environnement immersif

- Développement du *Tube Magique* pour l'instanciation de projectiles rigides avec attribution stochastique de couleurs.
- Implémentation du système de tri basé sur des zones de collision physiques (`OnTriggerEnter`).
- Ajout d'une logique de jeu avancée avec mélange de Fisher-Yates et masquage de textures après 1 seconde.

### 2. Développement du pipeline de collecte

- Création d'une routine d'échantillonnage temporel discret avec une garde de $\Delta t \ge 0.1\text{s}$.
- Mise en place d'une ingestion bi-cible: historisation dans MongoDB et écriture continue dans `data.csv`.

### 3. Ingénierie des caractéristiques

- Temps de réaction: latence entre l'apparition et le tri.
- Vitesse moyenne et vitesse maximale: calculées par différences euclidiennes successives.
- Indice d'hésitation latérale: écart-type du mouvement sur l'axe X.

### 4. Labellisation et apprentissage statistique

- Création d'un algorithme d'annotation automatique sur les données historiques.
- Configuration d'un pipeline Scikit-Learn avec standardisation via `StandardScaler`.
- Entraînement d'un classifieur Random Forest avec **200** arbres et `class_weight='balanced'`.

### 5. Sécurisation contre la fuite de données

- Mise en place d'une validation croisée `StratifiedGroupKFold` avec $K = 5$.
- Regroupement des fenêtres glissantes d'une même session dans un seul pli afin d'éviter toute fuite d'information.

### 6. Inférence événementielle et calibration des seuils

- Migration de la prédiction vers un fonctionnement asynchrone piloté par événements.
- Réglage d'un seuil à 35 % pour limiter le biais vers la classe majoritaire `Stable`.

## Installation et lancement

### Prérequis

- Python 3.10+
- Unity **2022**.3 **LTS** ou plus récent, avec support OpenXR / XR Interaction Toolkit
- MongoDB, en local ou via Atlas

### Backend IA

```bash
pip install flask pandas numpy scikit-learn python brain.py
```

### Client VR

Ouvre le dossier `Client_VR_Unity` depuis Unity Hub.

Vérifie que les serveurs Flask tournent en arrière-plan. Lance le mode Play dans l'éditeur Unity ou déploie le build sur le casque VR.

Le système de tracking se synchronise alors automatiquement. ## Répartition des tâches (Rôles de l'équipe)

Pour mener à bien ce projet de fin de module, les différentes fonctionnalités et briques de l'architecture ont été réparties comme suit :

| Membre de l'équipe | Responsabilités et Livrables |
| :--- | :--- |
| **Latifa Ait Alla** | Choix, intégration et optimisation des assets 3D + Rédaction et consolidation du rapport final. |
| **Idrissi Kandri Badreddine** | Conception et développement des boîtes de tri physiques et du système d'instanciation du *Tube Magique*. |
| **Khouloud Bennouby** | Développement et paramétrage de la scène de jeu en mode **Easy** (comportements statiques et prédictibles). |
| **Asmaa Talal** | Développement et paramétrage de la scène de jeu en mode **Hard** (mélange de Fisher-Yates, masquage de couleurs). |
| **Hamza Elmourabit** | Développement de l'infrastructure backend : conception de l'API Flask et intégration de la base de données MongoDB. |
| **Saad Benhaimer** | Ingénierie des caractéristiques, entraînement du modèle de Machine Learning (Random Forest) et pipeline de validation. |
