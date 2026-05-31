using UnityEngine;
using TMPro;
using System.Collections;
using UnityEngine.Networking;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance;

    [Header("Configuration du Temps")]
    public float tempsTotalConfigure = 120f;
    private float tempsRestant;
    private bool jeuEnCours = true;

    [Header("Interface UI de Jeu")]
    public TextMeshProUGUI texteChrono;
    public TextMeshProUGUI texteScore;

    [Header("Tableau des Stats de Fin (UI Canvas)")]
    public GameObject panneauFinDeJeu;
    public TextMeshProUGUI texteBallesReussies;
    public TextMeshProUGUI texteBallesRatees;
    public TextMeshProUGUI texteScoreFinal;

    [Header("Objets VR a figer")]
    public GameObject leftController;
    public GameObject rightController;

    [HideInInspector] public string modeActuel = "Easy";

    private int ballesReussies = 0;
    private int ballesRatees = 0;
    private float tempsAuDemarrage;

    void Awake()
    {
        if (Instance == null) Instance = this;
        tempsRestant = tempsTotalConfigure;
    }

    void Start()
    {
        if (panneauFinDeJeu != null) panneauFinDeJeu.SetActive(false);

        if (leftController != null)
        {
            leftController.SetActive(true);
            SetInteractionActive(leftController, true);
        }
        if (rightController != null)
        {
            rightController.SetActive(true);
            SetInteractionActive(rightController, true);
        }

        tempsAuDemarrage = Time.time;
        MettreAJourUI();

        StartCoroutine(ResetDDAServerCache());

        BallSpawner spawnerEasy = Object.FindAnyObjectByType<BallSpawner>();
        if (spawnerEasy != null)
        {
            spawnerEasy.ResetBall();
        }
    }

    void Update()
    {
        if (!jeuEnCours) return;

        if (tempsRestant > 0)
        {
            tempsRestant -= Time.deltaTime;
            MettreAJourUI();
        }
        else
        {
            tempsRestant = 0;
            FinDuJeu();
        }
    }

    void MettreAJourUI()
    {
        int minutes = Mathf.FloorToInt(tempsRestant / 60);
        int secondes = Mathf.FloorToInt(tempsRestant % 60);

        if (texteChrono != null)
            texteChrono.text = string.Format("Temps: {0:00}:{1:00}", minutes, secondes);

        if (texteScore != null)
            texteScore.text = "Score: " + ballesReussies;
    }

    public void AjouterPoint()
    {
        if (!jeuEnCours) return;
        ballesReussies++;
        MettreAJourUI();
    }

    public void BalleRatee()
    {
        if (!jeuEnCours) return;
        ballesRatees++;
    }

    public void ChangerDifficulteTempsReel(bool versHard)
    {
        if (!jeuEnCours) return;

        string nouveauMode = versHard ? "Hard" : "Easy";

        if (modeActuel == nouveauMode) return;

        modeActuel = nouveauMode;

        BallSpawner spawnerEasy = Object.FindAnyObjectByType<BallSpawner>();
        BallSpawnerHard spawnerHard = Object.FindAnyObjectByType<BallSpawnerHard>();

        GameObject[] tousLesObjets = GameObject.FindObjectsByType<GameObject>(FindObjectsSortMode.None);
        foreach (GameObject obj in tousLesObjets)
        {
            if (obj.name.Contains("Balle"))
            {
                Destroy(obj);
            }
        }

        if (modeActuel == "Hard" && spawnerHard != null)
        {
            spawnerHard.ResetBall();
        }
        else if (modeActuel == "Easy" && spawnerEasy != null)
        {
            spawnerEasy.ResetBall();
        }
    }

    void FinDuJeu()
    {
        if (!jeuEnCours) return;
        jeuEnCours = false;
        MettreAJourUI();

        StartCoroutine(ResetDDAServerCache());
        DesactiverSpawners();

        if (leftController != null) SetInteractionActive(leftController, false);
        if (rightController != null) SetInteractionActive(rightController, false);

        DataCollector dc = Object.FindAnyObjectByType<DataCollector>();
        if (dc != null)
        {
            dc.CloturerPartie(tempsTotalConfigure, ballesReussies, ballesRatees);
        }

        if (panneauFinDeJeu != null) panneauFinDeJeu.SetActive(true);
        if (texteBallesReussies != null) texteBallesReussies.text = "Balles Reussies : " + ballesReussies;
        if (texteBallesRatees != null) texteBallesRatees.text = "Balles Ratees : " + ballesRatees;
        if (texteScoreFinal != null) texteScoreFinal.text = "SCORE : " + ballesReussies + " PTS";
    }

    void OnApplicationQuit()
    {
        if (jeuEnCours)
        {
            jeuEnCours = false;
            float dureeExacteJouee = Time.time - tempsAuDemarrage;

            DataCollector dc = Object.FindAnyObjectByType<DataCollector>();
            if (dc != null)
            {
                dc.CloturerPartie(dureeExacteJouee, ballesReussies, ballesRatees);
            }
        }
    }

    void DesactiverSpawners()
    {
        BallSpawner spawnerEasy = Object.FindAnyObjectByType<BallSpawner>();
        if (spawnerEasy != null) spawnerEasy.enabled = false;

        BallSpawnerHard spawnerHard = Object.FindAnyObjectByType<BallSpawnerHard>();
        if (spawnerHard != null) spawnerHard.enabled = false;
    }

    void SetInteractionActive(GameObject controller, bool active)
    {
        var interactors = controller.GetComponentsInChildren<UnityEngine.XR.Interaction.Toolkit.Interactors.XRBaseInteractor>();
        foreach (var interactor in interactors)
        {
            interactor.enabled = active;
        }
    }

    IEnumerator ResetDDAServerCache()
    {
        string url = "http://127.0.0.1:5001/api/dda/reset";

        using (UnityWebRequest request = UnityWebRequest.PostWwwForm(url, ""))
        {
            yield return request.SendWebRequest();
        }
    }
}