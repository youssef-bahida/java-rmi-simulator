# Java RMI Simulator 

## Lancement

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La durée par défaut de chaque animation d'envoi et de réponse est de **4 secondes**.
L'objet `CalculLocal` apparaît dans le cadre du serveur, juste à côté de l'objet distant permanent `Impl_Compte`, puis disparaît à la fin de l'exécution locale.

Cette application est une simulation pédagogique visuelle et non un serveur Java RMI réel.
