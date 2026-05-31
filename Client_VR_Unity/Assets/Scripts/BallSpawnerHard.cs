using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class BallSpawnerHard : MonoBehaviour
{
    [Header("Configuration de la Balle")]
    public GameObject ballPrefab;
    [Tooltip("Temps en secondes pendant lequel les boites affichent leur couleur au debut")]
    public float dureeFlashCouleurs = 1.0f;

    private Vector3 startPosition;
    [HideInInspector] public GameObject ball;
    [HideInInspector] public float tempsApparitionBalle;

    [Header("Materiaux de Couleur (Balle & Boites)")]
    public Material matRouge;
    public Material matVert;
    public Material matBleu;
    public Material matGrisNeutre;

    [Header("Les 3 Boites de Tri (Logique Physique)")]
    public ZoneDetecteurHard detectionGauche;
    public ZoneDetecteurHard detectionMilieu;
    public ZoneDetecteurHard detectionDroite;

    [Header("Les 3 Boites de Tri (Modeles 3D Visuels)")]
    public GameObject visuelGauche;
    public GameObject visuelMilieu;
    public GameObject visuelDroite;

    private Renderer rendererGauche;
    private Renderer rendererMilieu;
    private Renderer rendererDroite;
    private Renderer ballRenderer;

    void Awake()
    {
        startPosition = transform.position;
        InitialiserRenderers();
    }

    private void InitialiserRenderers()
    {
        if (visuelGauche != null && rendererGauche == null) rendererGauche = visuelGauche.GetComponent<Renderer>();
        if (visuelMilieu != null && rendererMilieu == null) rendererMilieu = visuelMilieu.GetComponent<Renderer>();
        if (visuelDroite != null && rendererDroite == null) rendererDroite = visuelDroite.GetComponent<Renderer>();
    }

    public void SpawnNouvelleBalle()
    {
        if (GameManager.Instance != null && GameManager.Instance.modeActuel != "Hard") return;
        if (ballPrefab == null) return;

        ball = Instantiate(ballPrefab, startPosition, Quaternion.identity);
        ballRenderer = ball.GetComponentInChildren<Renderer>();

        Rigidbody rb = ball.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.isKinematic = true;
            rb.linearVelocity = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
        }

        ChangerCouleurBalleAleatoire();
        StartCoroutine(LibererBalleApresStabilisation(rb));
        StartCoroutine(FlashCouleursBoites());

        DataCollector dc = Object.FindAnyObjectByType<DataCollector>();
        if (dc != null) dc.DemarrerTracking();

        tempsApparitionBalle = Time.time;
    }

    void ChangerCouleurBalleAleatoire()
    {
        if (ball == null) return;

        int choix = Random.Range(0, 3);
        if (choix == 0)
        {
            ball.name = "Balle_Rouge";
            if (ballRenderer != null) ballRenderer.material = matRouge;
        }
        else if (choix == 1)
        {
            ball.name = "Balle_Vert";
            if (ballRenderer != null) ballRenderer.material = matVert;
        }
        else
        {
            ball.name = "Balle_Bleu";
            if (ballRenderer != null) ballRenderer.material = matBleu;
        }
    }

    IEnumerator LibererBalleApresStabilisation(Rigidbody rb)
    {
        yield return new WaitForSeconds(0.05f);
        if (rb != null)
        {
            rb.isKinematic = false;
            rb.linearVelocity = Vector3.zero;
            rb.WakeUp();
        }
    }

    IEnumerator FlashCouleursBoites()
    {
        List<string> couleurs = new List<string> { "Rouge", "Vert", "Bleu" };

        for (int i = couleurs.Count - 1; i > 0; i--)
        {
            int r = Random.Range(0, i + 1);
            string tmp = couleurs[i];
            couleurs[i] = couleurs[r];
            couleurs[r] = tmp;
        }

        if (detectionGauche != null) detectionGauche.couleurActuelle = couleurs[0];
        if (detectionMilieu != null) detectionMilieu.couleurActuelle = couleurs[1];
        if (detectionDroite != null) detectionDroite.couleurActuelle = couleurs[2];

        InitialiserRenderers();

        AppliquerMateriauBoite(rendererGauche, couleurs[0]);
        AppliquerMateriauBoite(rendererMilieu, couleurs[1]);
        AppliquerMateriauBoite(rendererDroite, couleurs[2]);

        yield return new WaitForSeconds(dureeFlashCouleurs);

        if (rendererGauche != null) rendererGauche.material = matGrisNeutre;
        if (rendererMilieu != null) rendererMilieu.material = matGrisNeutre;
        if (rendererDroite != null) rendererDroite.material = matGrisNeutre;
    }

    void AppliquerMateriauBoite(Renderer rend, string couleur)
    {
        if (rend == null) return;
        if (couleur == "Rouge") rend.material = matRouge;
        else if (couleur == "Vert") rend.material = matVert;
        else if (couleur == "Bleu") rend.material = matBleu;
    }

    public void ResetBall()
    {
        StopAllCoroutines();
        if (ball != null) Destroy(ball);
        SpawnNouvelleBalle();
    }
}