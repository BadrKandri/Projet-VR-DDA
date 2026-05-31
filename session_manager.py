import logging
import threading
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SessionManager:
    """Contrat d'interface pour le stockage et la gestion des sessions de jeu."""
    
    def add_lancer(self, partie_id: str, features: List[float]) -> List[List[float]]:
        raise NotImplementedError

    def get_lancers(self, partie_id: str) -> List[List[float]]:
        raise NotImplementedError

    def clear_session(self, partie_id: str) -> None:
        raise NotImplementedError


class InMemorySessionManager(SessionManager):
    """Gestionnaire de session thread-safe en memoire conservant un historique strict."""
    
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self._sessions: Dict[str, List[List[float]]] = {}
        self._lock = threading.Lock()
        logger.info("InMemorySessionManager initialise pour la gestion des blocs de donnees")

    def add_lancer(self, partie_id: str, features: List[float]) -> List[List[float]]:
        """Ajoute un vecteur de caracteristiques cinematiques a l'historique de session."""
        if len(features) != 4:
            raise ValueError(f"Le vecteur de caracteristiques doit etre de taille 4. Recu: {len(features)}")

        with self._lock:
            if partie_id not in self._sessions:
                self._sessions[partie_id] = []
            
            self._sessions[partie_id].append(features)
            
            if len(self._sessions[partie_id]) > self.max_history:
                self._sessions[partie_id].pop(0)
            
            current_history = self._sessions[partie_id].copy()
            
        return current_history

    def get_lancers(self, partie_id: str) -> List[List[float]]:
        """Recupere l'historique des lancers pour une session donnee."""
        with self._lock:
            return self._sessions.get(partie_id, []).copy()

    def clear_session(self, partie_id: str) -> None:
        """Supprime integralement la session specifiee du cache memoire."""
        with self._lock:
            if partie_id in self._sessions:
                del self._sessions[partie_id]