import sqlite3

conn = sqlite3.connect("tontine.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS inscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    montant INTEGER,
    frequence TEXT,
    paiement TEXT
)
""")

conn.commit()
conn.close()

print("✅ Base de données créée avec succès")
