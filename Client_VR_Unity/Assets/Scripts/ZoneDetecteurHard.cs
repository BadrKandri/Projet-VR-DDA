using UnityEngine;

public class ZoneDetecteurHard : MonoBehaviour
{
    private BallSpawnerHard ballSpawner;
    private DataCollector dataCollector;

    [Header("Configuration de la Zone")]
    public bool estLeSol = false;

    [HideInInspector] public string couleurActuelle = "";

    void Start()
    {
        ballSpawner = Object.FindFirstObjectByType<BallSpawnerHard>();
        dataCollector = Object.FindFirstObjectByType<DataCollector>();
    }

    private void OnTriggerEnter(Collider other)
    {
        if (GameManager.Instance != null && GameManager.Instance.modeActuel != "Hard") return;

        if (other.CompareTag("Balle"))
        {
            var interactable = other.GetComponent<UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable>();
            if (interactable != null && interactable.isSelected) return;

            string nomBalle = other.gameObject.name;
            string couleurBallePure = nomBalle.Replace("Balle_", "").Replace("(Clone)", "").Trim().ToLower();
            bool estCorrect = false;
            float tempsEcoule = 0f;

            if (ballSpawner != null)
            {
                tempsEcoule = Time.time - ballSpawner.tempsApparitionBalle;
            }

            if (estLeSol)
            {
                if (GameManager.Instance != null)
                    GameManager.Instance.BalleRatee();

                if (dataCollector != null)
                    dataCollector.EnregistrerEssai("Sol_" + couleurBallePure, tempsEcoule, false);
            }
            else
            {
                string attendueMinuscule = couleurActuelle.ToLower();

                if (couleurBallePure == attendueMinuscule && attendueMinuscule != "")
                {
                    estCorrect = true;
                }

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