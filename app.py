import sqlite3
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
from werkzeug.security import check_password_hash
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")
CORS(app, supports_credentials=True)

DB = "tontine.db"

# Admin hash (remplace par ton vrai hash)
ADMIN_USER = "admin"
ADMIN_PASS_HASH = "pbkdf2:sha256:260000$..."

# Variables API Wave / Orange Money
WAVE_API_URL = os.environ.get("WAVE_API_URL")
WAVE_API_KEY = os.environ.get("WAVE_API_KEY")
ORANGE_API_URL = os.environ.get("ORANGE_API_URL")
ORANGE_API_KEY = os.environ.get("ORANGE_API_KEY")

def get_db():
    return sqlite3.connect(DB)

# -------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify(success=False)
    if data.get("username") == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, data.get("password")):
        session["admin"] = True
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/login", methods=["GET"])
def page_login():
    return send_from_directory('.', 'login.html')

# -------- INSCRIPTION + PAIEMENT ----------
@app.route("/creer-paiement", methods=["POST"])
def creer_paiement():
    data = request.get_json()
    nom = data.get("nom")
    montant = data.get("montant")
    paiement = data.get("paiement")  # "wave" ou "orange"

    if not nom or not montant:
        return jsonify({"message": "Données invalides"}), 400

    # Enregistrer l'inscription dans DB
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO inscriptions (nom, montant, frequence, paiement) VALUES (?, ?, ?, ?)",
              (nom, montant, data.get("frequence"), paiement))
    conn.commit()
    conn.close()

    # Créer le lien paiement selon le moyen choisi
    if paiement.lower() == "wave":
        res = requests.post(WAVE_API_URL, json={
            "amount": montant,
            "description": f"Cotisation tontine - {nom}",
            "customer_name": nom
        }, headers={"Authorization": f"Bearer {WAVE_API_KEY}"})
        url_paiement = res.json().get("payment_url")
    elif paiement.lower() == "orange money":
        res = requests.post(ORANGE_API_URL, json={
            "amount": montant,
            "description": f"Cotisation tontine - {nom}",
            "customer_name": nom
        }, headers={"Authorization": f"Bearer {ORANGE_API_KEY}"})
        url_paiement = res.json().get("payment_url")
    else:
        url_paiement = None

    if not url_paiement:
        return jsonify({"message": "Impossible de créer le paiement"}), 500

    return jsonify({"url_paiement": url_paiement})

# -------- PAGE ADMIN ----------
@app.route("/admin")
def page_admin():
    if not session.get("admin"):
        return redirect("/login")
    return send_from_directory('.', 'admin.html')

@app.route("/admin/inscriptions")
def voir_inscriptions():
    if not session.get("admin"):
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inscriptions")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "nom": r[1], "montant": r[2], "frequence": r[3], "paiement": r[4]} for r in rows])

@app.route("/admin/delete/<int:id>", methods=["DELETE"])
def delete_inscrit(id):
    if not session.get("admin"):
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM inscriptions WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Inscrit {id} supprimé ✅"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
