using UnityEngine;

public class ZoneDetecteur : MonoBehaviour
{
    private BallSpawner ballSpawner;
    private DataCollector dataCollector;

    [Header("Configuration de la Zone")]
    public bool estLeSol = false;
    public string couleurAttendue;

    void Start()
    {
        ballSpawner = Object.FindFirstObjectByType<BallSpawner>();
        dataCollector = Object.FindFirstObjectByType<DataCollector>();
    }

    private void OnTriggerEnter(Collider other)
    {
        if (GameManager.Instance != null && GameManager.Instance.modeActuel != "Easy") return;

        if (other.CompareTag("Balle"))
        {
            var interactable = other.GetComponent<UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable>();
            if (interactable != null && interactable.isSelected) return;

            string nomBalle = other.gameObject.name;
            string couleurBallePure = nomBalle.Replace("Balle_", "");
            bool estCorrect = false;
            float tempsEcoule = 0f;

            if (ballSpawner != null)
            {
                tempsEcoule = Time.time - ballSpawner.tempsApparitionBalle;
            }

            if (estLeSol)
            {
                if (GameManager.Instance != null)
                {
                    GameManager.Instance.BalleRatee();
                }

                if (dataCollector != null)
                {
                    dataCollector.EnregistrerEssai("Sol_" + couleurBallePure, tempsEcoule, false);
                }
            }
            else
            {
                if (nomBalle == "Balle_Rouge" && couleurAttendue == "Rouge") estCorrect = true;
                if (nomBalle == "Balle_Vert" && couleurAttendue == "Vert") estCorrect = true;
                if (nomBalle == "Balle_Bleu" && couleurAttendue == "Bleu") estCorrect = true;

                if (GameManager.Instance != null)
                {
                    if (estCorrect)
                    {
                        GameManager.Instance.AjouterPoint();
                    }
                    else
                    {
                        GameManager.Instance.BalleRatee();
                    }
                }

                if (dataCollector != null)
                {
                    dataCollector.EnregistrerEssai(couleurBallePure, tempsEcoule, estCorrect);
                }
            }

            if (ballSpawner != null)
            {
                ballSpawner.ResetBall();
            }
        }
    }
}