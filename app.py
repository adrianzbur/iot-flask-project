"""
=============================================================================
IoT Systém s Cloudovým Backendom - Flask Backend
=============================================================================
Rozšírená verzia o prevodník jednotiek pre IoT senzory.
Každý prevod sa uloží do JSON súboru prevody.json.

Autor: [Adrián Zbur]
Predmet: Internet vecí
=============================================================================
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────────────────────
# ÚLOŽISKO (Azure-friendly)
# ─────────────────────────────────────────────────────────────────────────────
# Na Azure App Service (Linux) je najistejšie ukladať zapisovateľné súbory do:
# - $HOME  (typicky /home)  -> perzistentné
# - fallback /tmp           -> vždy zapisovateľné (ale neperzistentné)
DATA_DIR = os.environ.get("HOME", "/tmp")

DATABASE = os.path.join(DATA_DIR, "databaza.db")
SUBOR_PREVODOV = os.path.join(DATA_DIR, "prevody.json")


# ─────────────────────────────────────────────────────────────────────────────
# DATABÁZA - SQLite (kalkulačka)
# ─────────────────────────────────────────────────────────────────────────────
def inicializuj_databazu():
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vypocty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cislo1 REAL NOT NULL,
            cislo2 REAL NOT NULL,
            operacia TEXT NOT NULL,
            vysledok REAL NOT NULL,
            cas TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ Databáza inicializovaná: {DATABASE}")


# ✅ Dôležité pre Azure: spustí sa aj pri importe cez gunicorn (app:app)
inicializuj_databazu()


def uloz_do_databazy(cislo1, cislo2, operacia, vysledok):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cas = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO vypocty (cislo1, cislo2, operacia, vysledok, cas) VALUES (?, ?, ?, ?, ?)",
        (cislo1, cislo2, operacia, vysledok, cas)
    )
    conn.commit()
    nove_id = cursor.lastrowid
    conn.close()
    return nove_id


def nacitaj_vsetky_vypocty():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vypocty ORDER BY id DESC")
    riadky = cursor.fetchall()
    conn.close()
    return [dict(riadok) for riadok in riadky]


# ─────────────────────────────────────────────────────────────────────────────
# JSON SÚBOR - Prevodník jednotiek
# ─────────────────────────────────────────────────────────────────────────────
def nacitaj_prevody():
    if not os.path.exists(SUBOR_PREVODOV):
        return []
    with open(SUBOR_PREVODOV, "r", encoding="utf-8") as f:
        return json.load(f)


def uloz_prevod(zaznam):
    os.makedirs(DATA_DIR, exist_ok=True)

    prevody = nacitaj_prevody()
    prevody.append(zaznam)
    with open(SUBOR_PREVODOV, "w", encoding="utf-8") as f:
        json.dump(prevody, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def hlavna_stranka():
    return render_template("frontend_a.html")


@app.route("/vypocet")
def vypocet():
    cislo1_str = request.args.get("cislo1", "0")
    cislo2_str = request.args.get("cislo2", "0")
    operacia = request.args.get("operacia", "plus")

    try:
        cislo1 = float(cislo1_str)
        cislo2 = float(cislo2_str)
    except ValueError:
        return jsonify({"chyba": "Neplatné čísla! Zadajte číselné hodnoty."}), 400

    if operacia == "plus":
        vysledok = cislo1 + cislo2
    elif operacia == "minus":
        vysledok = cislo1 - cislo2
    elif operacia == "krat":
        vysledok = cislo1 * cislo2
    elif operacia == "deleno":
        if cislo2 == 0:
            return jsonify({"chyba": "Delenie nulou nie je možné!"}), 400
        vysledok = cislo1 / cislo2
    else:
        return jsonify({"chyba": f"Neznáma operácia: {operacia}"}), 400

    nove_id = uloz_do_databazy(cislo1, cislo2, operacia, vysledok)

    return jsonify({
        "id": nove_id,
        "cislo1": cislo1,
        "cislo2": cislo2,
        "operacia": operacia,
        "vysledok": round(vysledok, 4),
        "cas": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/historia")
def historia():
    return jsonify(nacitaj_vsetky_vypocty())


@app.route("/api/posledny")
def posledny_vypocet():
    vypocty = nacitaj_vsetky_vypocty()
    if vypocty:
        return jsonify(vypocty[0])
    return jsonify({"info": "Zatiaľ neboli vykonané žiadne výpočty."}), 404


@app.route("/api/statistiky")
def statistiky():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vypocty")
    pocet = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(vysledok) FROM vypocty")
    priemer = cursor.fetchone()[0]

    cursor.execute("SELECT operacia, COUNT(*) as pocet FROM vypocty GROUP BY operacia")
    podla_operacie = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return jsonify({
        "celkovy_pocet": pocet,
        "priemerny_vysledok": round(priemer, 4) if priemer else 0,
        "podla_operacie": podla_operacie
    })


@app.route("/klient")
def klientsky_pohlad():
    return render_template("frontend_b.html")


@app.route("/iot/odosli")
def iot_odosli():
    teplota = request.args.get("teplota", type=float)
    vlhkost = request.args.get("vlhkost", type=float)

    if teplota is None or vlhkost is None:
        return jsonify({"chyba": "Chýbajú parametre teplota a vlhkost!"}), 400

    return jsonify({
        "status": "ok",
        "prijate_data": {
            "teplota": teplota,
            "vlhkost": vlhkost,
            "cas": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "sprava": "Dáta zo senzora boli úspešne prijaté."
    })


@app.route("/api/prevod")
def prevod():
    hodnota = request.args.get("hodnota", type=float)
    typ = request.args.get("typ", "c_to_f")

    if hodnota is None:
        return jsonify({"chyba": "Zadajte hodnotu! (parameter: hodnota)"}), 400

    if typ == "c_to_f":
        vysledok = (hodnota * 9 / 5) + 32
        popis = f"{hodnota} °C = {vysledok:.2f} °F"
    elif typ == "hpa_to_mmhg":
        vysledok = hodnota * 0.75006
        popis = f"{hodnota} hPa = {vysledok:.2f} mmHg"
    elif typ == "ms_to_kmh":
        vysledok = hodnota * 3.6
        popis = f"{hodnota} m/s = {vysledok:.2f} km/h"
    else:
        return jsonify({
            "chyba": f"Neznámy typ prevodu: {typ}. Platné typy: c_to_f, hpa_to_mmhg, ms_to_kmh"
        }), 400

    zaznam = {
        "hodnota": hodnota,
        "typ": typ,
        "vysledok": round(vysledok, 2),
        "popis": popis,
        "cas": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    uloz_prevod(zaznam)
    return jsonify(zaznam)


@app.route("/api/historia-prevodov")
def historia_prevodov():
    return jsonify(nacitaj_prevody())


# ─────────────────────────────────────────────────────────────────────────────
# Lokálne spúšťanie
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 IoT Backend Server beží!")
    print("=" * 60)
    print("   Frontend A (Admin):       http://localhost:5000/")
    print("   Frontend B (Klient):      http://localhost:5000/klient")
    print("   API História:             http://localhost:5000/api/historia")
    print("   API Štatistiky:           http://localhost:5000/api/statistiky")
    print("   IoT Odosli:               http://localhost:5000/iot/odosli?teplota=22&vlhkost=60")
    print("   --- PREVODNÍK ---")
    print("   API Prevod (°C→°F):       http://localhost:5000/api/prevod?hodnota=100&typ=c_to_f")
    print("   API História prevodov:    http://localhost:5000/api/historia-prevodov")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)