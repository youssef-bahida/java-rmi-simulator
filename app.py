import time
import html
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Java RMI — visualisation", page_icon="🌐", layout="wide")

st.markdown("""
<style>
:root { color-scheme: light; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background:#f4f7fb !important; }
html, body, p, span, label, div, h1, h2, h3, h4, li { color:#111827; }
.block-container { max-width:1350px; padding-top:.8rem; padding-bottom:1rem; }
h1 {font-size:1.55rem !important; margin-bottom:.1rem;}
h2 {font-size:1.12rem !important;}
h3 {font-size:1rem !important;}
.stButton>button {color:#111827 !important;background:#fff !important;border:1px solid #9aa9bb !important;font-weight:650;border-radius:9px;}
.stButton>button:hover {background:#eaf2ff !important;border-color:#3977c6 !important;}
.client {background:#eaf2ff;border:1.5px solid #6b9de0;border-radius:10px;padding:10px 5px;text-align:center;}
.server {background:#e9f7ed;border:2px solid #48a36a;border-radius:12px;padding:11px;text-align:center;}
.remote {background:#fff7df;border:1px solid #d7ad48;border-radius:8px;padding:9px;margin-top:7px;text-align:left;}
.local {background:#fff0db;border:2px dashed #d58a20;border-radius:8px;padding:9px;margin-top:7px;text-align:left;}
.result {background:#e6f6eb;border:1px solid #57a36b;border-radius:8px;padding:9px;margin:5px 0;}
.small {font-size:.82rem;color:#374151 !important;}
.packet {background:#fff;border:1px solid #d5deea;border-radius:10px;padding:8px 12px;margin:4px 0 10px;}
.packet-head {display:flex;justify-content:space-between;font-size:12px;font-weight:750;}
.packet-track {height:35px;position:relative;margin-top:5px;background:#f1f5f9;border-radius:7px;overflow:hidden;}
.packet-track:after {content:"";position:absolute;left:5%;right:5%;top:17px;height:2px;background:#94a3b8;}
.packet-icon {position:absolute;z-index:2;top:5px;font-size:19px;animation:go-right 4s linear forwards;}
.packet-icon.back {animation:go-left 4s linear forwards;}
@keyframes go-right {from{left:5%}to{left:91%}}
@keyframes go-left {from{left:91%}to{left:5%}}
.payload {font-size:12px;text-align:center;margin-top:5px;color:#111827;}
</style>
""", unsafe_allow_html=True)

st.title("Java RMI — visualisation des échanges")
st.caption("Un serveur RMI · trois clients · un objet distant partagé · appels distants et exécution locale")

if "results" not in st.session_state: st.session_state.results = []
if "log" not in st.session_state: st.session_state.log = []
if "last_action" not in st.session_state: st.session_state.last_action = "Aucun échange lancé."
if "local_active" not in st.session_state: st.session_state.local_active = False

with st.sidebar:
    st.subheader("Paramètres")
    sync = st.toggle("Méthode distante synchronized", True)
    st.caption("Activé : les appels sur la même instance sont exécutés l'un après l'autre.")
    anim_duration = st.slider("Durée de chaque animation réseau", 1, 8, 4, help="Durée par défaut : 4 secondes pour l'envoi et 4 secondes pour la réponse.")
    process_delay = st.slider("Durée du traitement serveur", 1, 5, 2)
    if st.button("Réinitialiser", use_container_width=True):
        st.session_state.results = []
        st.session_state.log = []
        st.session_state.last_action = "Aucun échange lancé."
        st.rerun()

def packet(client_names, direction, method, args, duration, result=None):
    """Affiche une ou plusieurs trajectoires en haut, entre clients et serveur."""
    outgoing = direction == "request"
    title = "ENVOI — CLIENT → SERVEUR" if outgoing else "RETOUR — SERVEUR → CLIENT"
    rows = []
    for name in client_names:
        start, end = (name, "SERVEUR RMI") if outgoing else ("SERVEUR RMI", name)
        detail = f"Méthode : {method}({args})" if outgoing else f"Résultat retourné à {name} : {result}"
        rows.append(f"""
        <div style="margin-top:6px">
          <div class="packet-head"><span>{html.escape(start)}</span><span>{html.escape(end)}</span></div>
          <div class="packet-track">
            <div class="packet-icon {' ' if outgoing else 'back'}" style="animation-duration:{duration}s">📦</div>
          </div>
          <div class="payload">{html.escape(detail)}</div>
        </div>""")
    markup = f"""
    <div class="packet">
      <div style="font-size:13px;font-weight:800;text-align:center">{title}</div>
      {''.join(rows)}
    </div>
    """
    components.html(markup, height=92 + 82 * len(rows), scrolling=False)
    time.sleep(duration)

def server_processing(client, method, args, value):
    st.info(f"🖥️ Serveur : appel de **{method}({args})** reçu depuis **{client}**.")
    with st.status(f"Traitement de {client} sur l'objet distant Impl_Compte…", expanded=True) as status:
        st.write(f"Méthode exécutée : `{method}({args})`")
        st.write(f"Données reçues : `{args}`")
        time.sleep(process_delay)
        status.update(label=f"Traitement de {client} terminé", state="complete")
    return value

# Communication lane is deliberately placed ABOVE the architecture.
st.subheader("1. Communication réseau — envoi et réception")
st.caption(st.session_state.last_action)

st.subheader("3. Contrôle manuel")
c1, c23, clocal = st.columns(3)
with c1:
    send1 = st.button("📤 Envoyer depuis Client 1", use_container_width=True)
with c23:
    send23 = st.button("📤 Clients 2 + 3 simultanément", use_container_width=True)
with clocal:
    local = st.button("⚙ Exécution locale serveur", use_container_width=True)

if local:
    st.session_state.local_active = True

# Architecture: temporary object appears INSIDE the server, beside the persistent remote object.
st.subheader("2. Architecture et objets présents dans le serveur")
client_cols = st.columns([1, 1, 1, 1.65])
for col, name in zip(client_cols[:3], ("CLIENT 1", "CLIENT 2", "CLIENT 3")):
    with col:
        st.markdown(f'<div class="client"><b>💻 {name}</b><br><span class="small">Application cliente</span></div>', unsafe_allow_html=True)

with client_cols[3]:
    local_html = """
    <div class="local">
      <b>🟠 Objet local temporaire : CalculLocal</b><br>
      <span class="small">① Créé dans le serveur uniquement<br>② Non exporté — aucun registre RMI<br>③ Exécution : calculer(20, 22)<br><b>ÉTAT : EN COURS</b></span>
    </div>
    """ if st.session_state.local_active else ""
    st.markdown(f"""
    <div class="server">
      <b>🖥️ SERVEUR RMI UNIQUE</b><br>
      <span class="small">Registry — port 1099</span>
      <div class="remote">
        <b>🟡 Objet distant permanent : Impl_Compte</b><br>
        <span class="small">① new Impl_Compte()<br>② exporté par UnicastRemoteObject<br>③ registry.rebind("Service_Compte", obj)<br><b>ÉTAT : ACTIF — reste dans le serveur</b></span>
      </div>
      {local_html}
    </div>
    """, unsafe_allow_html=True)

st.caption("Les trois clients obtiennent la référence du même objet distant enregistré sous « Service_Compte ».")

if send1:
    st.session_state.results = []
    method, args, value = "deposer", "250", 250
    st.session_state.last_action = f"Client 1 envoie {method}({args}) — animation de {anim_duration} s."
    packet(["CLIENT 1"], "request", method, args, anim_duration)
    st.session_state.log = [f"CLIENT 1 → Serveur : {method}({args})"]
    result = server_processing("CLIENT 1", method, args, value)
    packet(["CLIENT 1"], "response", method, args, anim_duration, result)
    st.session_state.results.append(("CLIENT 1", result))
    st.session_state.log.append(f"Serveur → CLIENT 1 : résultat {result}")
    st.session_state.last_action = f"Échange terminé : Client 1 a appelé {method}({args}) et reçu {result}."

if send23:
    st.session_state.results = []
    method, args = "transferer", "100, 40"
    st.session_state.last_action = f"Clients 2 et 3 envoient simultanément {method}({args})."
    packet(["CLIENT 2", "CLIENT 3"], "request", method, args, anim_duration)
    st.session_state.log = [f"CLIENT 2 et CLIENT 3 → Serveur : {method}({args}) (simultanément)"]
    if sync:
        st.warning("🔒 synchronized : un seul thread entre dans la méthode à la fois. Le second attend la libération du verrou.")
        for client, value in (("CLIENT 2", 60), ("CLIENT 3", 60)):
            result = server_processing(client, method, args, value)
            packet([client], "response", method, args, anim_duration, result)
            st.session_state.results.append((client, result))
            st.session_state.log.append(f"Serveur → {client} : résultat {result}")
            if client == "CLIENT 2":
                st.info("CLIENT 2 a terminé : le verrou est libéré, CLIENT 3 peut entrer dans la méthode.")
    else:
        st.info("Sans synchronized, les deux appels peuvent se chevaucher sur la même instance.")
        with st.status("Le serveur traite les deux appels sans verrou…", expanded=True) as status:
            st.write(f"CLIENT 2 : `{method}({args})`")
            st.write(f"CLIENT 3 : `{method}({args})`")
            time.sleep(process_delay)
            status.update(label="Les deux traitements sont terminés", state="complete")
        for client in ("CLIENT 2", "CLIENT 3"):
            packet([client], "response", method, args, anim_duration, 60)
            st.session_state.results.append((client, 60))
            st.session_state.log.append(f"Serveur → {client} : résultat 60")
    st.session_state.last_action = "Échange terminé : les deux clients ont reçu la réponse du serveur."

if local:
    st.session_state.results = []
    st.session_state.last_action = "Exécution locale : CalculLocal est visible à côté de Impl_Compte dans le serveur."
    st.session_state.log = ["Serveur : création de CalculLocal (objet local, non exporté)."]
    with st.status("Exécution directe dans le serveur — aucun paquet réseau…", expanded=True) as status:
        st.write("Méthode locale : `calculer(20, 22)`")
        st.write("Données utilisées : `20` et `22`")
        time.sleep(process_delay)
        result = 42
        status.update(label="Méthode locale terminée", state="complete")
    st.session_state.results.append(("SERVEUR (local)", result))
    st.session_state.log.append("CalculLocal : résultat 42.")
    st.session_state.local_active = False
    st.session_state.log.append("CalculLocal : référence libérée, objet éligible au Garbage Collector.")
    st.session_state.last_action = "Exécution locale terminée : CalculLocal a disparu ; Impl_Compte est toujours présent."
    st.success("Résultat local = 42. CalculLocal disparaît du serveur ; sa référence est libérée et l'objet devient éligible au Garbage Collector.")
    st.rerun()

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Résultats reçus")
    if st.session_state.results:
        for who, result in st.session_state.results:
            st.markdown(f'<div class="result"><b>{who}</b> — Résultat : <b>{result}</b> ✓</div>', unsafe_allow_html=True)
    else:
        st.caption("Aucun résultat pour le moment.")
with right:
    st.subheader("Journal du serveur")
    if st.session_state.log:
        for item in st.session_state.log[-8:]:
            st.write("• " + item)
    else:
        st.caption("Serveur prêt — objet distant permanent et enregistré.")

with st.expander("Code Java correspondant"):
    st.code("""// Serveur : un seul objet distant, conservé dans le registre
Registry registry = LocateRegistry.createRegistry(1099);
Impl_Compte distant = new Impl_Compte();
registry.rebind("Service_Compte", distant);

// Exemple de méthode distante : méthode + paramètres envoyés par le client
public synchronized int deposer(int montant) throws RemoteException {
    solde += montant;
    return solde;
}

// Objet local temporaire : aucun appel RMI
CalculLocal temporaire = new CalculLocal();
int resultat = temporaire.calculer(20, 22);
temporaire = null; // référence libérée : éligible au Garbage Collector
""", language="java")

st.caption("Simulation pédagogique : les paquets sont animés dans l'interface ; aucun véritable appel Java RMI/JRMP n'est envoyé.")
