using UnityEngine;
using System.Collections.Generic;
using UnityEngine.Networking;
using System.Collections;

public class DataCollector : MonoBehaviour
{
    [Header("Objets a Tracker")]
    public Transform head;
    public Transform leftHand;
    public Transform rightHand;

    private string apiBaseURL = "http://localhost:5000/api/partie";
    private string apiDdaURL = "http://localhost:5001/api/dda/decision";

    private string partieId = "";
    private int compteurActionId = 0;

    [System.Serializable]
    public struct Vector3Data { public float x; public float y; public float z; }

    [System.Serializable]
    public struct FrameTracking
    {
        public float timestamp;
        public Vector3Data positionTete;
        public Vector3Data mainGauche;
        public Vector3Data mainDroite;
    }

    [System.Serializable]
    public class ActionPayload
    {
        public string partie_id;
        public int action_id;
        public string couleur_balle;
        public float temps_reaction;
        public bool reussite;
        public List<FrameTracking> fluxMouvements;
    }

    [System.Serializable]
    public class FinalScorePayload
    {
        public string partie_id;
        public float duree_partie;
        public int score_final;
        public int balle_reussi;
        public int balle_rattees;
    }

    [System.Serializable]
    private class InitResponse { public string status; public string partie_id; }

    [System.Serializable]
    public class DDAPredictionResponse
    {
        public int prediction;
        public string status;
    }

    private List<FrameTracking> donnéesMouvementActuel = new List<FrameTracking>();
    private bool estEnTrainDeTracker = false;
    private float chronoDebutEssai;
    private float decompteTemps = 0f;

    void Start()
    {
        StartCoroutine(InitialiserPartieSurServeur());
    }

    void Update()
    {
        if (estEnTrainDeTracker)
        {
            EnregistrerFrameFréquentielle();
        }
    }

    public void DemarrerTracking()
    {
        donnéesMouvementActuel.Clear();
        chronoDebutEssai = Time.time;
        estEnTrainDeTracker = true;
    }

    private void EnregistrerFrameFréquentielle()
    {
        decompteTemps += Time.deltaTime;
        if (decompteTemps >= 0.1f)
        {
            decompteTemps = 0f;

            FrameTracking frame = new FrameTracking
            {
                timestamp = Time.time - chronoDebutEssai,
                positionTete = FormaterVector3(head),
                mainGauche = FormaterVector3(leftHand),
                mainDroite = FormaterVector3(rightHand)
            };
            donnéesMouvementActuel.Add(frame);
        }
    }

    private Vector3Data FormaterVector3(Transform t)
    {
        if (t == null) return new Vector3Data { x = 0, y = 0, z = 0 };
        return new Vector3Data { x = t.position.x, y = t.position.y, z = t.position.z };
    }

    public void EnregistrerEssai(string couleur, float temps, bool estReussi)
    {
        estEnTrainDeTracker = false;
        compteurActionId++;

        ActionPayload payload = new ActionPayload
        {
            partie_id = partieId,
            action_id = compteurActionId,
            couleur_balle = couleur,
            temps_reaction = temps,
            reussite = estReussi,
            fluxMouvements = new List<FrameTracking>(donnéesMouvementActuel)
        };

        string jsonText = JsonUtility.ToJson(payload);
        StartCoroutine(EnvoyerRequetePOST(apiBaseURL + "/ajouter_action", jsonText));
    }

    public void CloturerPartie(float dureeTotale, int réussies, int ratées)
    {
        FinalScorePayload payload = new FinalScorePayload
        {
            partie_id = partieId,
            duree_partie = dureeTotale,
            score_final = réussies,
            balle_reussi = réussies,
            balle_rattees = ratées
        };

        string jsonText = JsonUtility.ToJson(payload);
        StartCoroutine(EnvoyerRequetePOST(apiBaseURL + "/terminer", jsonText));
    }

    private IEnumerator InitialiserPartieSurServeur()
    {
        using (UnityWebRequest request = new UnityWebRequest(apiBaseURL + "/demarrer", "POST"))
        {
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                InitResponse res = JsonUtility.FromJson<InitResponse>(request.downloadHandler.text);
                partieId = res.partie_id;
                Debug.Log($"Session initialisee avec succes dans la base de donnees. ID : {partieId}");
            }
            else
            {
                Debug.LogError($"Echec de l'initialisation de la session : {request.error}");
            }
        }
    }

    private IEnumerator EnvoyerRequetePOST(string url, string json)
    {
        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                if (url.Contains("/ajouter_action"))
                {
                    StartCoroutine(InterrogerMoteurDecisionDDA());
                }
            }
            else
            {
                Debug.LogError($"Erreur lors de la transmission des donnees : {request.error}");
            }
        }
    }

    private IEnumerator InterrogerMoteurDecisionDDA()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(apiDdaURL))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string jsonResponse = request.downloadHandler.text;
                DDAPredictionResponse res = JsonUtility.FromJson<DDAPredictionResponse>(jsonResponse);

                Debug.Log($"Etat comportemental determine par le modele d'IA - Code : {res.prediction} ({res.status})");

                if (res.prediction == 1)
                {
                    GameManager.Instance.ChangerDifficulteTempsReel(true);
                }
                else if (res.prediction == 2)
                {
                    GameManager.Instance.ChangerDifficulteTempsReel(false);
                }
            }
            else
            {
                Debug.LogError($"Impossible de recuperer la decision du modele predictif : {request.error}");
            }
        }
    }
}