from flask import Flask, request, jsonify
import json, re
from difflib import get_close_matches

app = Flask(__name__)

# --- Carica i dati ---
with open("guida_olfattiva.txt", "r", encoding="utf-8") as f:
    guida = f.read()

# Leggi FAQ (D: domanda, R: risposta)
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

def trova_faq(testo):
    domande = [f["domanda"] for f in faq]
    trovate = get_close_matches(testo, domande, n=1, cutoff=0.5)
    if trovate:
        for f_item in faq:
            if f_item["domanda"] == trovate[0]:
                return f_item["risposta"]
    return None

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "").lower().strip()

    # --- Cerca nelle FAQ ---
    risposta = trova_faq(msg)
    if risposta:
        return jsonify({"reply": risposta})

    # --- Cerca nei prodotti ---
    if any(k in msg for k in ["profumo", "fragranza", "consiglia", "odore", "note"]):
        suggeriti = []
        for p in prodotti:
            descr = (p.get("olfatto") or "").lower() + " " + (p.get("descrizione") or "").lower()
            if any(k in descr for k in msg.split()):
                suggeriti.append(p)
        if suggeriti:
            risp = "Ecco alcuni profumi che potrebbero piacerti:\n"
            for p in suggeriti[:3]:
                risp += f"- {p['nome']} ({p.get('olfatto','')} - {p.get('prezzo','')})\n"
            return jsonify({"reply": risp.strip()})
        else:
            return jsonify({"reply": "Non trovo profumi con quelle note. Ti lascio qualche info generale:\n\n" + guida[:400] + "..."})

    return jsonify({"reply": "Ciao 😊! Posso consigliarti profumi o rispondere a domande su ordini e resi."})

@app.route("/")
def home():
    return "<h2>💬 Chatbot Profumeria attivo (versione leggera)</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

