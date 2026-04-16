"""
=============================================================================
IoT Systém s Cloudovým Backendom - Flask Backend
=============================================================================
Tento súbor je SRDCE celého projektu. Je to server (backend), ktorý:
  1. Prijíma dáta z HTML formulárov (Frontend A)
  2. Spracováva výpočty (kalkulačka)
  3. Ukladá výsledky do SQLite databázy
  4. Poskytuje API endpointy pre Frontend B (IoT klient)

Autor: [Adrián Zbur]
Predmet: Internet vecí
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT KNIŽNÍC
# ─────────────────────────────────────────────────────────────────────────────
# Flask       = webový framework (základ servera)
# request     = objekt na čítanie dát z URL parametrov (?cislo1=10&...)
# jsonify     = pomocník na odosielanie JSON odpovedí (pre API)
# render_template = načítanie HTML šablón z priečinka "templates/"
# flask_cors  = riešenie CORS politiky (povolenie komunikácie medzi doménami)
# sqlite3     = vstavaná Python knižnica na prácu s databázou
# datetime    = práca s dátumom a časom

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import datetime

# ─────────────────────────────────────────────────────────────────────────────
# VYTVORENIE APLIKÁCIE
# ─────────────────────────────────────────────────────────────────────────────
# Flask(__name__) = vytvorí inštanciu Flask aplikácie
# CORS(app)       = povolí komunikáciu z INÝCH domén (Frontend B má inú URL!)
#
# 🔑 Prečo CORS? Prehliadač štandardne BLOKUJE požiadavky medzi rôznymi
#    doménami (napr. frontend-a.com → backend.com). CORS to povolí.

app = Flask(__name__)
CORS(app)  # Bez tohto by Frontend B nemohol komunikovať s backendom!

# ─────────────────────────────────────────────────────────────────────────────
# DATABÁZA - SQLite
# ─────────────────────────────────────────────────────────────────────────────
# SQLite je jednoduchá databáza uložená v jednom súbore (databaza.db).
# Netreba inštalovať žiadny databázový server — ideálne pre výuku.
#
# Schéma tabuľky "vypocty":
#   id        = automatické číslovanie (PRIMARY KEY)
#   cislo1    = prvé zadané číslo
#   cislo2    = druhé zadané číslo
#   operacia  = typ operácie (plus, minus, krat, deleno)
#   vysledok  = výsledok výpočtu
#   cas       = kedy bol výpočet vykonaný

DATABASE = "databaza.db"


def inicializuj_databazu():
    """
    Vytvorí tabuľku 'vypocty', ak ešte neexistuje.
    Volá sa raz pri štarte servera.
    
    IF NOT EXISTS = ak tabuľka už existuje, nič sa nestane (bezpečné).
    """
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
    print("✅ Databáza inicializovaná.")


def uloz_do_databazy(cislo1, cislo2, operacia, vysledok):
    """
    Uloží jeden záznam o výpočte do databázy.
    
    Parametre:
        cislo1    (float): Prvé číslo
        cislo2    (float): Druhé číslo
        operacia  (str):   Typ operácie
        vysledok  (float): Výsledok výpočtu
    
    Vracia:
        int: ID nového záznamu
    """
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
    """
    Načíta VŠETKY záznamy z tabuľky 'vypocty'.
    
    Vracia:
        list: Zoznam slovníkov (dict), každý predstavuje jeden výpočet.
    
    Poznámka: row_factory = sqlite3.Row umožňuje pristupovať k stĺpcom
              cez mená (row["cislo1"]) namiesto indexov (row[0]).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Výsledky ako slovníky
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vypocty ORDER BY id DESC")
    riadky = cursor.fetchall()
    conn.close()
    # Konverzia sqlite3.Row objektov na bežné Python slovníky
    return [dict(riadok) for riadok in riadky]


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1: Hlavná stránka (Frontend A - Administračný)
# ─────────────────────────────────────────────────────────────────────────────
# URL: http://tvoj-backend.azurewebsites.net/
# Metóda: GET
# Čo robí: Zobrazí hlavnú HTML stránku s formulárom kalkulačky.

@app.route("/")
def hlavna_stranka():
    """
    Zobrazí hlavnú stránku - Frontend A.
    render_template() hľadá súbor v priečinku templates/
    """
    return render_template("frontend_a.html")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2: Výpočet (spracovanie formulára)
# ─────────────────────────────────────────────────────────────────────────────
# URL: http://tvoj-backend.azurewebsites.net/vypocet?cislo1=10&cislo2=5&operacia=plus
# Metóda: GET
# 
# 🔑 Prečo GET a nie POST?
#    - Parametre sú VIDITEĽNÉ v URL riadku prehliadača
#    - Vedúci to chce kvôli demonštrácii, ako fungujú HTTP requesty
#    - V reálnom IoT prostredí sa GET často používa pre jednoduchosť
#
# request.args.get("cislo1") = prečíta hodnotu parametra "cislo1" z URL

@app.route("/vypocet")
def vypocet():
    """
    Prijme čísla a operáciu cez GET parametre, vykoná výpočet,
    uloží do databázy a vráti výsledok.
    
    Príklad URL:
        /vypocet?cislo1=10&cislo2=5&operacia=plus
    
    Výstup (JSON):
        {"cislo1": 10, "cislo2": 5, "operacia": "plus", "vysledok": 15, "id": 1}
    """
    # --- Krok 1: Prečítanie parametrov z URL ---
    # request.args.get() = bezpečné čítanie GET parametrov
    # Ak parameter chýba, vráti None (default)
    cislo1_str = request.args.get("cislo1", "0")
    cislo2_str = request.args.get("cislo2", "0")
    operacia = request.args.get("operacia", "plus")

    # --- Krok 2: Validácia vstupov ---
    # Skúsime previesť text na čísla. Ak sa nepodarí → chyba.
    try:
        cislo1 = float(cislo1_str)
        cislo2 = float(cislo2_str)
    except ValueError:
        return jsonify({"chyba": "Neplatné čísla! Zadajte číselné hodnoty."}), 400

    # --- Krok 3: Výpočet podľa zvolenej operácie ---
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

    # --- Krok 4: Uloženie do databázy ---
    nove_id = uloz_do_databazy(cislo1, cislo2, operacia, vysledok)

    # --- Krok 5: Vrátenie výsledku ako JSON ---
    # jsonify() = vytvorí JSON odpoveď (štandard pre API komunikáciu)
    return jsonify({
        "id": nove_id,
        "cislo1": cislo1,
        "cislo2": cislo2,
        "operacia": operacia,
        "vysledok": round(vysledok, 4),
        "cas": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3: API - Získanie histórie výpočtov
# ─────────────────────────────────────────────────────────────────────────────
# URL: http://tvoj-backend.azurewebsites.net/api/historia
# Metóda: GET
# Čo robí: Vráti VŠETKY výpočty z databázy ako JSON (pre Frontend B).
#
# 🔑 Toto je kľúčový endpoint pre Frontend B!
#    Frontend B pravidelne volá tento endpoint a zobrazuje výsledky.

@app.route("/api/historia")
def historia():
    """
    API endpoint - vráti celú históriu výpočtov ako JSON pole.
    
    Výstup (JSON):
        [
            {"id": 3, "cislo1": 10, "cislo2": 5, "operacia": "plus", "vysledok": 15, "cas": "..."},
            {"id": 2, "cislo1": 7, "cislo2": 3, "operacia": "minus", "vysledok": 4, "cas": "..."},
            ...
        ]
    """
    vypocty = nacitaj_vsetky_vypocty()
    return jsonify(vypocty)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4: API - Posledný výpočet
# ─────────────────────────────────────────────────────────────────────────────
# URL: http://tvoj-backend.azurewebsites.net/api/posledny
# Metóda: GET
# Čo robí: Vráti IBA posledný výpočet (napr. pre IoT displej).

@app.route("/api/posledny")
def posledny_vypocet():
    """
    API endpoint - vráti iba posledný vykonaný výpočet.
    Užitočné pre IoT zariadenia, ktoré chcú zobraziť len aktuálny stav.
    """
    vypocty = nacitaj_vsetky_vypocty()
    if vypocty:
        return jsonify(vypocty[0])  # Prvý záznam = najnovší (ORDER BY DESC)
    else:
        return jsonify({"info": "Zatiaľ neboli vykonané žiadne výpočty."}), 404


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5: API - Štatistiky
# ─────────────────────────────────────────────────────────────────────────────
# URL: http://tvoj-backend.azurewebsites.net/api/statistiky
# Metóda: GET
# Čo robí: Vráti súhrn štatistík (celkový počet, priemer, atď.)

@app.route("/api/statistiky")
def statistiky():
    """
    API endpoint - vráti základné štatistiky o výpočtoch.
    Demonštruje prácu s SQL agregačnými funkciami.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Celkový počet výpočtov
    cursor.execute("SELECT COUNT(*) FROM vypocty")
    pocet = cursor.fetchone()[0]

    # Priemerný výsledok
    cursor.execute("SELECT AVG(vysledok) FROM vypocty")
    priemer = cursor.fetchone()[0]

    # Počet výpočtov podľa operácie
    cursor.execute("SELECT operacia, COUNT(*) as pocet FROM vypocty GROUP BY operacia")
    podla_operacie = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return jsonify({
        "celkovy_pocet": pocet,
        "priemerny_vysledok": round(priemer, 4) if priemer else 0,
        "podla_operacie": podla_operacie
    })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 6: Frontend B (Klientsky/IoT pohľad)
# ─────────────────────────────────────────────────────────────────────────────
# V reálnom nasadení by Frontend B bežal na INEJ doméne.
# Pre jednoduchosť ho servírujeme aj z tohto servera.
# V produkcii by bol na: http://iot-klient.azurewebsites.net/

@app.route("/klient")
def klientsky_pohlad():
    """
    Zobrazí Frontend B - klientsky/IoT pohľad.
    Táto stránka len ČÍTA dáta z API a zobrazuje výsledky.
    """
    return render_template("frontend_b.html")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 7: IoT Simulácia (ESP32 / senzor)
# ─────────────────────────────────────────────────────────────────────────────
# Tento endpoint simuluje, ako by IoT zariadenie (napr. ESP32) posielalo dáta.
# URL: /iot/odosli?teplota=22.5&vlhkost=60
# 
# V reálnom svete by ESP32 posielal HTTP GET request na tento endpoint.

@app.route("/iot/odosli")
def iot_odosli():
    """
    Simulácia IoT endpointu - prijíma dáta zo senzora.
    
    Príklad volania z ESP32 (Arduino kód):
        http.begin("http://tvoj-backend.azurewebsites.net/iot/odosli?teplota=22.5&vlhkost=60");
    """
    teplota = request.args.get("teplota", type=float)
    vlhkost = request.args.get("vlhkost", type=float)

    if teplota is None or vlhkost is None:
        return jsonify({"chyba": "Chýbajú parametre teplota a vlhkost!"}), 400

    # Tu by sme dáta uložili do databázy (zjednodušené pre ukážku)
    return jsonify({
        "status": "ok",
        "prijate_data": {
            "teplota": teplota,
            "vlhkost": vlhkost,
            "cas": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "sprava": "Dáta zo senzora boli úspešne prijaté."
    })


# ─────────────────────────────────────────────────────────────────────────────
# ŠTART SERVERA
# ─────────────────────────────────────────────────────────────────────────────
# __name__ == "__main__" = tento blok sa spustí len ak spustíme súbor priamo
#                          (nie ak ho importujeme z iného súboru)
# host="0.0.0.0" = server počúva na všetkých sieťových rozhraniach
# port=5000      = štandardný Flask port
# debug=True     = automaticky reštartuje server pri zmene kódu (len pre vývoj!)

if __name__ == "__main__":
    inicializuj_databazu()  # Vytvorí tabuľku pri prvom spustení
    print("=" * 60)
    print("🚀 IoT Backend Server beží!")
    print("=" * 60)
    print("   Frontend A (Admin):  http://localhost:5000/")
    print("   Frontend B (Klient): http://localhost:5000/klient")
    print("   API História:        http://localhost:5000/api/historia")
    print("   API Štatistiky:      http://localhost:5000/api/statistiky")
    print("   IoT Endpoint:        http://localhost:5000/iot/odosli?teplota=22&vlhkost=60")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
