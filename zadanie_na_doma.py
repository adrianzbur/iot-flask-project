"""
=============================================================================
ZADANIE NA DOMA — IoT Backend Rozšírenie
=============================================================================
Predmet: Internet vecí
Deadline: [doplniť]

ÚLOHA:
Implementujte vlastnú funkciu v backende, ktorá spracuje nový typ vstupu
z HTML formulára a výsledok vráti na druhú doménu (Frontend B).

=============================================================================
POŽIADAVKY:
=============================================================================

1. BACKEND (app.py):
   - Pridajte nový endpoint /api/prevod  (alebo vlastný názov)
   - Endpoint musí prijať minimálne 2 GET parametre
   - Vykonajte nejakú transformáciu/výpočet nad vstupmi
   - Uložte výsledok do databázy
   - Vráťte JSON odpoveď

2. FRONTEND A (formulár):
   - Pridajte nový formulár alebo sekciu na stránke
   - Použite minimálne:
     ✅ 1x <input type="text"> alebo <input type="number">
     ✅ 1x <select> alebo <input type="checkbox">
     ✅ 1x <button type="submit">
   - Dáta odošlite cez GET request

3. FRONTEND B (zobrazenie):
   - Zobrazte výsledky z vášho nového endpointu
   - Dáta načítajte cez fetch() API

=============================================================================
NÁPADY NA IMPLEMENTÁCIU (vyberte si jednu):
=============================================================================

A) Prevodník jednotiek:
   - Vstup: číslo + typ prevodu (km→míle, °C→°F, kg→libry)
   - Výstup: prevedená hodnota

B) BMI Kalkulačka:
   - Vstup: výška (cm) + váha (kg)
   - Výstup: BMI hodnota + kategória (podváha/norma/nadváha)

C) Prevod meny:
   - Vstup: suma + mena (EUR→USD, EUR→CZK)
   - Výstup: prevedená suma (kurzy môžu byť hardcoded)

D) Rýchlostný kalkulátor:
   - Vstup: vzdialenosť + čas
   - Výstup: priemerná rýchlosť

E) Vlastný nápad:
   - Čokoľvek čo spĺňa požiadavky vyššie

=============================================================================
PRÍKLAD RIEŠENIA (Prevodník teploty):
=============================================================================
"""

# ---- Toto pridajte do app.py (pod existujúce routy): ----

# POZNÁMKA: Tento kód je len ukážka! Nepoužívajte ho ako svoje riešenie.

"""
@app.route("/api/prevod")
def prevod_teploty():
    # Prečítanie parametrov z URL
    hodnota = request.args.get("hodnota", type=float)
    smer = request.args.get("smer", "c_to_f")  # c_to_f alebo f_to_c

    if hodnota is None:
        return jsonify({"chyba": "Zadajte hodnotu!"}), 400

    # Výpočet
    if smer == "c_to_f":
        vysledok = (hodnota * 9/5) + 32
        popis = f"{hodnota}°C = {vysledok:.1f}°F"
    elif smer == "f_to_c":
        vysledok = (hodnota - 32) * 5/9
        popis = f"{hodnota}°F = {vysledok:.1f}°C"
    else:
        return jsonify({"chyba": "Neznámy smer prevodu!"}), 400

    # Návrat JSON odpovede
    return jsonify({
        "vstup": hodnota,
        "smer": smer,
        "vysledok": round(vysledok, 2),
        "popis": popis
    })
"""

# ---- A toto pridajte do frontend_a.html: ----

"""
<form onsubmit="return odosliPrevod(event)">
    <input type="number" id="teplotaVstup" placeholder="Zadajte teplotu" step="any">
    <select id="smerPrevodu">
        <option value="c_to_f">°C → °F</option>
        <option value="f_to_c">°F → °C</option>
    </select>
    <button type="submit">Previesť</button>
</form>

<script>
async function odosliPrevod(event) {
    event.preventDefault();
    const hodnota = document.getElementById("teplotaVstup").value;
    const smer = document.getElementById("smerPrevodu").value;
    const url = `${BACKEND_URL}/api/prevod?hodnota=${hodnota}&smer=${smer}`;
    const response = await fetch(url);
    const data = await response.json();
    alert(data.popis);
    return false;
}
</script>
"""

# =============================================================================
# HODNOTENIE:
# =============================================================================
# ✅ Backend endpoint funkčný a vracia JSON          (3 body)
# ✅ Frontend formulár s požadovanými HTML prvkami     (3 body)
# ✅ Frontend B zobrazuje výsledky z nového endpointu  (2 body)
# ✅ GET parametre viditeľné v URL                     (1 bod)
# ✅ Kód je okomentovaný                              (1 bod)
# ─────────────────────────────────────────────────────
# SPOLU: 10 bodov
# =============================================================================
