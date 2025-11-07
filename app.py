from flask import Flask, request, jsonify
import json, re
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# ---- Caricamento dati ----
with open("guida_olfattiva.txt", "r", encoding="utf-8") as f:
    guida = f.read()

with open("faq_servizio_clienti.txt", "r", encoding="utf-8") as f:
    righe = f.read().splitlines()

faq = []
for i in range(len(righe)):
    if righe[i].startswith("D:"):
        domanda = righe[i][2:].strip()
        risposta = ""
        j = i + 1
        while j < len(righe) and not righe[j].startswith("D:"):
            if righe[j].startswith("R:"):
                risposta += righe[j][2:].strip() + " "
            j += 1
        faq.append({"domanda": domanda, "risposta": risposta.strip()})

with open("docs.json", "r", encoding="utf-8") as f:
    prodotti = json.load(f)

# ---- Modello per similarità ----
embedder = SentenceTransformer("all-MiniLM-L6-v2")

faq_embeddings = embedder.encode([f["domanda"] for f in faq], convert_to_tensor=True)

def cerca_faq(testo):
    emb = embedder.encode(testo, convert_to_tensor=True)
    sim = util.cos_sim(emb, faq_embeddings)
    idx = sim.argmax().item()
    score = sim[0][idx].item()
    if score > 0.55:
        return faq[idx]["risposta"]
    return None

# ---- Chatbot principale ----
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").lower().strip()

    # 1️⃣ Se è una domanda di servizio clienti
    risposta_faq = cerca_faq(user_input)
    if risposta_faq:
        return jsonify({"reply": risposta_faq})

    # 2️⃣ Se parla di profumi o note
    if any(k in user_input for k in ["profumo", "note", "fragranza", "odore", "consiglia"]):
        suggeriti = []
        for p in prodotti:
            note = (p.get("olfatto") or "").lower() + " " + (p.get("descrizione") or "").lower()
            if any(k in note for k in user_input.split()):
                suggeriti.append(p)
        if suggeriti:
            risp = "Ecco alcuni profumi che potrebbero piacerti:\n"
            for p in suggeriti[:3]:
                risp += f"- {p['nome']} ({p.get('olfatto','')} - {p.get('prezzo','')})\n"
            return jsonify({"reply": risp.strip()})
        else:
            return jsonify({"reply": "Non trovo profumi precisi con quelle note, ma ecco qualche informazione utile:\n\n" + guida[:600] + "..."})

    # 3️⃣ fallback
    return jsonify({"reply": "Ciao 😊! Posso aiutarti a scegliere un profumo o rispondere su ordini, spedizioni e resi."})

@app.route("/")
def home():
    return "<h2>💬 Chatbot Profumeria attivo!</h2><p>Invia POST /chat con {'message': 'testo utente'}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

