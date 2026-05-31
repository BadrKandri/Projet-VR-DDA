using UnityEngine;

public class BallSpawner : MonoBehaviour
{
    [Header("Configuration du Prefab")]
    public GameObject ballPrefab;
    public Transform spawnPoint;

    [HideInInspector] public GameObject ball;
    private Vector3 startPosition;
    private Renderer ballRenderer;

    [Header("Materiaux de Couleur")]
    public Material matRouge;
    public Material matVert;
    public Material matBleu;

    [Header("Les 3 Boites (Logique Physique)")]
    public ZoneDetecteurHard detectionGauche;
    public ZoneDetecteurHard detectionMilieu;
    public ZoneDetecteurHard detectionDroite;

    [Header("Les 3 Boites (Modeles 3D Visuels)")]
    public GameObject visuelGauche;
    public GameObject visuelMilieu;
    public GameObject visuelDroite;

    [HideInInspector] public float tempsApparitionBalle;

    void Awake()
    {
        if (spawnPoint != null)
            startPosition = spawnPoint.position;
        else
            startPosition = transform.position;
    }

    public void ResetBall()
    {
        if (GameManager.Instance != null && GameManager.Instance.modeActuel != "Easy") return;

        if (ball != null) Destroy(ball);
        if (ballPrefab == null) return;

        RestaurerConfigurationEasyComplete();

        ball = Instantiate(ballPrefab, startPosition, Quaternion.identity);
        ballRenderer = ball.GetComponentInChildren<Renderer>();

        Rigidbody rb = ball.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.linearVelocity = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
            rb.useGravity = true;
            rb.isKinematic = false;
        }

        ChangerCouleurAleatoire();
        tempsApparitionBalle = Time.time;

        DataCollector dc = Object.FindFirstObjectByType<DataCollector>();
        if (dc != null) dc.DemarrerTracking();
    }

    private void RestaurerConfigurationEasyComplete()
    {
        if (detectionGauche != null) detectionGauche.couleurActuelle = "Vert";
        if (detectionMilieu != null) detectionMilieu.couleurActuelle = "Rouge";
        if (detectionDroite != null) detectionDroite.couleurActuelle = "Bleu";

        if (visuelGauche != null)
        {
            Renderer r = visuelGauche.GetComponent<Renderer>();
            if (r != null && matVert != null) r.material = matVert;
        }
        if (visuelMilieu != null)
        {
            Renderer r = visuelMilieu.GetComponent<Renderer>();
            if (r != null && matRouge != null) r.material = matRouge;
        }
        if (visuelDroite != null)
        {
            Renderer r = visuelDroite.GetComponent<Renderer>();
            if (r != null && matBleu != null) r.material = matBleu;
        }
    }

    private void ChangerCouleurAleatoire()
    {
        if (ballRenderer == null || matRouge == null || matVert == null || matBleu == null) return;

        int choix = Random.Range(0, 3);
        if (choix == 0)
        {
            ballRenderer.material = matRouge;
            ball.name = "Balle_Rouge";
        }
        else if (choix == 1)
        {
            ballRenderer.material = matVert;
            ball.name = "Balle_Vert";
        }
        else
        {
            ballRenderer.material = matBleu;
            ball.name = "Balle_Bleu";
        }
    }
}