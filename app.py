import csv
from datetime import date, datetime
import io
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
import streamlit as st

# =========================
# 1. KONFIGURATION & DICTIONARY
# =========================

st.set_page_config(
    page_title="Football Performance Tracker", page_icon="⚽", layout="wide"
)

# Standard Trainer-Passwort
TRAINER_PASSWORT = "coach123"

disziplinen = {
    "Sprint": {
        "schluessel": "Beste Zeit",
        "anzeigename": "Sprint",
        "einheit": "Sekunden",
        "kleiner_ist_besser": True,
        "toleranz": 0.002,
    },
    "Sprung": {
        "schluessel": "Sprunghoehe",
        "anzeigename": "Sprung",
        "einheit": "cm",
        "kleiner_ist_besser": False,
        "toleranz": 0.05,
    },
    "505_Test": {
        "schluessel": "Test_505_Zeit",
        "anzeigename": "505-Test",
        "einheit": "Sekunden",
        "kleiner_ist_besser": True,
        "toleranz": 0.003,
    },
    "YoYo_Test": {
        "schluessel": "YoYo_Test",
        "anzeigename": "Yo-Yo Ausdauer",
        "einheit": "Meter",
        "kleiner_ist_besser": False,
        "toleranz": 10.0,
    },
    "Kniebeuge": {
        "schluessel": "Kniebeuge",
        "anzeigename": "1RM Kniebeuge",
        "einheit": "kg",
        "kleiner_ist_besser": False,
        "toleranz": 1.0,
    },
    "Gesamtscore": {
        "schluessel": "Gesamtscore",
        "anzeigename": "Gesamtscore",
        "einheit": "Punkte",
        "kleiner_ist_besser": False,
        "toleranz": 0.05,
    },
}

# =========================
# 2. BEWERTUNGS- LOGIK & DATENBANK
# =========================


def yoyo_bewerten(meter):
    if meter < 800:
        return "Ausdauer-Ausbaubedarf", 50
    elif meter < 1200:
        return "Solide Grundlagen", 70
    elif meter < 1600:
        return "Gute Ausdauer", 85
    else:
        return "Herausragende Ausdauer", 100


def kniebeuge_bewerten(kg, gewicht):
    verhaeltnis = kg / gewicht if gewicht > 0 else 1.0
    if verhaeltnis < 1.2:
        return "Grundkraft vorhanden", 50
    elif verhaeltnis < 1.5:
        return "Gutes Kraftniveau", 70
    elif verhaeltnis < 1.8:
        return "Starkes Kraftniveau", 85
    else:
        return "Extrem stark", 100


def sprung_bewerten(hoehe):
    if hoehe < 50:
        return "Verbesserungspotenzial", 50
    elif hoehe < 70:
        return "Du bist solide gesprungen.", 70
    elif hoehe < 100:
        return "Du bist sehr hoch gesprungen!", 85
    else:
        return "Du bist extrem hoch gesprungen!", 100


def sprint_analyse(zeiten):
    return min(zeiten), max(zeiten), sum(zeiten) / len(zeiten)


def sprint_bewerten(zeit):
    if zeit < 1.70:
        return "Extrem schnell", 100
    elif zeit < 1.80:
        return "Sehr schnell", 85
    elif zeit < 1.90:
        return "Solide", 70
    else:
        return "Daran können wir arbeiten", 50


def test505_bewerten(zeit):
    if zeit < 2.30:
        return "Sehr schnell", 100
    elif zeit < 2.50:
        return "Gut", 85
    elif zeit < 2.70:
        return "Solide", 70
    else:
        return "Verbesserungspotenzial", 50


def gesamtscore_bewerten(score):
    if score < 60:
        return "Verbesserungspotenzial"
    elif score <= 74:
        return "Solide"
    elif score <= 89:
        return "Sehr gut"
    else:
        return "Herausragend"


def generiere_ki_empfehlung(
    sprint, sprung, test505, yoyo, kniebeuge, gewicht, gesamtscore
):
    empfehlungen = []

    # Sprint
    if sprint > 4.3:
        empfehlungen.append(
            "⚡ **Sprint & Antritt:** Fokus auf Beschleunigung & Schrittfrequenz. Empfehlung: 3x5 Schlitten-Sprints (Sled Pushes)."
        )
    elif sprint <= 4.0:
        empfehlungen.append(
            "⚡ **Sprint & Antritt:** Hervorragende Geschwindigkeit! Erhalte diese durch Fliegende Sprints (Fly-Sprints)."
        )

    # Sprungkraft
    if sprung < 45.0:
        empfehlungen.append(
            "💥 **Explosivkraft (Sprung):** Empfohlenes Training: Plyometrie (Box Jumps, Depth Jumps)."
        )

    # 505 Agilität
    if test505 > 2.5:
        empfehlungen.append(
            "🔄 **Richtungswechsel (505-Test):** Fokus auf Abbremsbewegung & Deceleration Drills."
        )

    # Yo-Yo Ausdauer
    if yoyo < 1000:
        empfehlungen.append(
            "🫁 **Ausdauer (Yo-Yo):** Intervalltraining einbauen (z. B. High-Intensity Interval Training - HIIT)."
        )

    # Kniebeuge Kraft
    verhaeltnis = kniebeuge / gewicht if gewicht > 0 else 0
    if verhaeltnis < 1.3:
        empfehlungen.append(
            "🏋️ **Maximalkraft:** Beinkraft steigern mit Kniebeugen & Kreuzheben im Bereich 3-5 Wiederholungen."
        )

    if gesamtscore >= 80:
        status = "🟢 **Top-Athlet-Status:** Ausgeglichenes, sehr hohes Leistungsniveau."
    elif gesamtscore >= 60:
        status = (
            "🟡 **Solides Fundament:** Gezielte Arbeit an den Schwachstellen ansetzen."
        )
    else:
        status = "🔴 **Aufbauphase:** Fokus auf athletische Grundlagenausdauer & Kraft legen."

    return status, empfehlungen


def init_db():
    conn = sqlite3.connect("performance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS testtage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            gewicht REAL,
            datum TEXT,
            beste_zeit REAL,
            sprunghoehe REAL,
            test_505_zeit REAL,
            yoyo_test REAL DEFAULT 0,
            kniebeuge REAL DEFAULT 0,
            gesamtscore REAL
        )
    """)

    # Spalten ergänzen falls ältere Datenbank vorhanden ist
    cursor.execute("PRAGMA table_info(testtage)")
    spalten = [row[1] for row in cursor.fetchall()]
    if "yoyo_test" not in spalten:
        cursor.execute(
            "ALTER TABLE testtage ADD COLUMN yoyo_test REAL DEFAULT 0"
        )
    if "kniebeuge" not in spalten:
        cursor.execute(
            "ALTER TABLE testtage ADD COLUMN kniebeuge REAL DEFAULT 0"
        )

    conn.commit()
    conn.close()


def testtag_speichern_sqlite(daten):
    conn = sqlite3.connect("performance.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO testtage (name, gewicht, datum, beste_zeit, sprunghoehe, test_505_zeit, yoyo_test, kniebeuge, gesamtscore)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            daten["Name"],
            daten["Gewicht"],
            daten["Datum"],
            daten["Beste Zeit"],
            daten["Sprunghoehe"],
            daten["Test_505_Zeit"],
            daten.get("YoYo_Test", 0),
            daten.get("Kniebeuge", 0),
            daten["Gesamtscore"],
        ),
    )
    conn.commit()
    conn.close()


def testtage_laden_sqlite():
    conn = sqlite3.connect("performance.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testtage")
    rows = cursor.fetchall()

    testtage = []
    for row in rows:
        testtage.append(
            {
                "id": row["id"],
                "Name": row["name"],
                "Gewicht": row["gewicht"],
                "Datum": row["datum"],
                "Beste Zeit": row["beste_zeit"],
                "Sprunghoehe": row["sprunghoehe"],
                "Test_505_Zeit": row["test_505_zeit"],
                "YoYo_Test": row["yoyo_test"] if "yoyo_test" in row.keys() else 0,
                "Kniebeuge": row["kniebeuge"] if "kniebeuge" in row.keys() else 0,
                "Gesamtscore": row["gesamtscore"],
            }
        )

    conn.close()
    return testtage


def test_auswerten(
    sprintzeiten, sprunghoehe, test_505_eingabe, yoyo_meter, kniebeuge_kg, gewicht
):
    beste_zeit, schlechteste_zeit, durchschnitt = sprint_analyse(sprintzeiten)
    _, p_sprint = sprint_bewerten(beste_zeit)
    _, p_sprung = sprung_bewerten(sprunghoehe)
    _, p_505 = test505_bewerten(test_505_eingabe)
    _, p_yoyo = yoyo_bewerten(yoyo_meter)
    _, p_kraft = kniebeuge_bewerten(kniebeuge_kg, gewicht)

    gesamtscore = (p_sprint + p_sprung + p_505 + p_yoyo + p_kraft) / 5
    gesamtscore_bewertung = gesamtscore_bewerten(gesamtscore)

    return {
        "Beste_Zeit": beste_zeit,
        "Sprint_Punkte": p_sprint,
        "Sprung_Punkte": p_sprung,
        "Test_505_Punkte": p_505,
        "YoYo_Punkte": p_yoyo,
        "Kraft_Punkte": p_kraft,
        "Gesamtscore": gesamtscore,
        "Gesamtscore_bewertung": gesamtscore_bewertung,
    }


def radar_chart_erstellen(p1_daten, p2_daten=None):
    kategorien = ["Sprint", "Sprung", "505-Agilität", "Ausdauer", "Kraft (Kniebeuge)"]
    num_vars = len(kategorien)

    winkel = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    winkel += winkel[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    # Spieler 1
    werte1 = p1_daten["werte"] + [p1_daten["werte"][0]]
    ax.fill(winkel, werte1, color="#003399", alpha=0.25)
    ax.plot(
        winkel,
        werte1,
        color="#003399",
        linewidth=2,
        label=p1_daten.get("name", "Spieler 1"),
    )

    # Spieler 2
    if p2_daten:
        werte2 = p2_daten["werte"] + [p2_daten["werte"][0]]
        ax.fill(winkel, werte2, color="#E74C3C", alpha=0.2, linestyle="--")
        ax.plot(
            winkel,
            werte2,
            color="#E74C3C",
            linewidth=2,
            linestyle="--",
            label=p2_daten.get("name", "Spieler 2"),
        )

    ax.set_xticks(winkel[:-1])
    ax.set_xticklabels(kategorien, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))

    return fig


def pdf_bericht_erstellen(spieler, dateiname="Performance_Bericht.pdf"):
    pdf = canvas.Canvas(dateiname, pagesize=letter)
    pdf.setFillColorRGB(0.0, 0.2, 0.6)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, 750, "ATHLETIC PERFORMANCE REPORT")

    pdf.setLineWidth(2)
    pdf.line(50, 735, 550, 735)

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 700, f"Name: {spieler.get('Name', 'Unbekannt')}")
    pdf.drawString(50, 680, f"Gewicht: {spieler.get('Gewicht', '-')} kg")
    pdf.drawString(50, 660, f"Datum: {spieler.get('Datum', 'Unbekannt')}")

    pdf.setLineWidth(0.5)
    pdf.setFillColorRGB(0.7, 0.7, 0.7)
    pdf.line(50, 645, 550, 645)

    daten = [
        ["Test-Kategorie", "Messergebnis"],
        ["Beste Sprintzeit", f"{spieler.get('Beste Zeit', '-')} s"],
        ["505-Test Zeit", f"{spieler.get('Test_505_Zeit', '-')} s"],
        ["Sprunghöhe", f"{spieler.get('Sprunghoehe', '-')} cm"],
        ["Yo-Yo Ausdauer", f"{spieler.get('YoYo_Test', '-')} m"],
        ["1RM Kniebeuge", f"{spieler.get('Kniebeuge', '-')} kg"],
    ]

    tabelle = Table(daten, colWidths=[250, 250])
    tabelle.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003399")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ]
        )
    )

    tabelle.wrapOn(pdf, 500, 200)
    tabelle.drawOn(pdf, 50, 470)

    pdf.setFillColorRGB(0.9, 0.94, 1.0)
    pdf.rect(50, 390, 500, 50, fill=1, stroke=0)

    pdf.setFillColorRGB(0.0, 0.2, 0.6)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(
        65,
        408,
        f"Gesamtscore: {round(spieler.get('Gesamtscore', 0), 1)} Punkte",
    )

    pdf.save()
    return dateiname


# =========================
# 3. STREAMLIT OBERFLÄCHE
# =========================

init_db()
testtage = testtage_laden_sqlite()

st.title("⚽ Football Performance Dashboard")

# --- SEITENLEISTE & TRAINER LOGIN ---
st.sidebar.title("Einstellungen & Filter")

# Trainer Login
st.sidebar.subheader("🔑 Trainer-Bereich")
passwort_eingabe = st.sidebar.text_input(
    "Trainer-Passwort eingeben", type="password"
)
ist_trainer = passwort_eingabe == TRAINER_PASSWORT

if ist_trainer:
    st.sidebar.success("🔓 Als Trainer angemeldet")
elif passwort_eingabe:
    st.sidebar.error("❌ Falsches Passwort")

st.sidebar.markdown("---")

# Spieler Filter
verfuegbare_spieler = sorted(
    list(set(t.get("Name") for t in testtage if t.get("Name")))
)
auswahl_optionen = ["Alle Spieler"] + verfuegbare_spieler
gewaehlter_spieler = st.sidebar.selectbox(
    "👤 Spieler filtern:", auswahl_optionen
)

if gewaehlter_spieler != "Alle Spieler":
    gefilterte_testtage = [
        t for t in testtage if t.get("Name") == gewaehlter_spieler
    ]
else:
    gefilterte_testtage = testtage

# Navigation
menue = st.sidebar.radio(
    "Navigation",
    [
        "📝 Neuen Test erfassen",
        "📊 Testhistorie & Bestwerte",
        "📈 Graph & Trends",
        "🏆 Leaderboard & Radar",
        "📄 PDF Export",
    ],
)

# --- MENÜ 1: NEUEN TEST ERFASSEN ---
if menue == "📝 Neuen Test erfassen":
    st.header("Neuen Testtag erfassen")

    if not ist_trainer:
        st.warning(
            "🔒 **Trainer-Bereich geschützt:** Bitte gib in der Seitenleiste links das Trainer-Passwort ein, um neuen Test einzutragen. (Standard-Passwort: `coach123`)"
        )
    else:
        with st.form("test_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name des Athleten", value="Max Mustermann")
                gewicht = st.number_input(
                    "Gewicht (kg)", min_value=20.0, max_value=250.0, value=75.0
                )
                sprunghoehe = st.number_input(
                    "Sprunghöhe (cm)",
                    min_value=1.0,
                    max_value=150.0,
                    value=55.0,
                )
                yoyo_meter = st.number_input(
                    "Yo-Yo Ausdauertest (Meter)",
                    min_value=0.0,
                    max_value=3000.0,
                    value=1200.0,
                    step=40.0,
                )

            with col2:
                test_505 = st.number_input(
                    "505-Test Zeit (Sekunden)",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.4,
                    step=0.01,
                )
                kniebeuge_kg = st.number_input(
                    "1RM Kniebeuge (kg)",
                    min_value=0.0,
                    max_value=350.0,
                    value=110.0,
                    step=2.5,
                )
                sprint_anzahl = st.number_input(
                    "Anzahl Sprint-Versuche", min_value=1, max_value=5, value=2
                )

            st.subheader("Sprintzeiten")
            sprintzeiten = []
            s_cols = st.columns(sprint_anzahl)
            for i in range(sprint_anzahl):
                zeit = s_cols[i].number_input(
                    f"Sprint {i+1} (s)",
                    min_value=0.5,
                    max_value=5.0,
                    value=1.85,
                    step=0.01,
                )
                sprintzeiten.append(zeit)

            submitted = st.form_submit_button("Testtag Speichern")

            if submitted:
                ergebnisse = test_auswerten(
                    sprintzeiten,
                    sprunghoehe,
                    test_505,
                    yoyo_meter,
                    kniebeuge_kg,
                    gewicht,
                )
                datum_heute = date.today().strftime("%d.%m.%Y")

                neuer_testtag = {
                    "Name": name,
                    "Gewicht": gewicht,
                    "Datum": datum_heute,
                    "Beste Zeit": ergebnisse["Beste_Zeit"],
                    "Sprunghoehe": sprunghoehe,
                    "Test_505_Zeit": test_505,
                    "YoYo_Test": yoyo_meter,
                    "Kniebeuge": kniebeuge_kg,
                    "Gesamtscore": ergebnisse["Gesamtscore"],
                }

                testtag_speichern_sqlite(neuer_testtag)
                st.success(f"Testtag für {name} erfolgreich gespeichert!")
                st.metric(
                    "Erreichter Gesamtscore",
                    f"{ergebnisse['Gesamtscore']:.1f} / 100",
                )


# --- MENÜ 2: HISTORIE & BESTWERTE ---
elif menue == "📊 Testhistorie & Bestwerte":
    st.header("📊 Testhistorie & Bestwerte")

    if not gefilterte_testtage:
        st.info("Noch keine Testtage gespeichert.")
    else:
        st.subheader("🏆 deine Bestwerte")
        b1, b2, b3, b4, b5 = st.columns(5)

        v_sprint = [t for t in gefilterte_testtage if "Beste Zeit" in t]
        v_sprung = [t for t in gefilterte_testtage if "Sprunghoehe" in t]
        v_yoyo = [t for t in gefilterte_testtage if "YoYo_Test" in t]
        v_kraft = [t for t in gefilterte_testtage if "Kniebeuge" in t]
        v_score = [t for t in gefilterte_testtage if "Gesamtscore" in t]

        if v_sprint:
            b1.metric(
                "Sprint",
                f"{min(v_sprint, key=lambda x: x['Beste Zeit'])['Beste Zeit']} s",
            )
        if v_sprung:
            b2.metric(
                "Sprung",
                f"{max(v_sprung, key=lambda x: x['Sprunghoehe'])['Sprunghoehe']} cm",
            )
        if v_yoyo:
            b3.metric(
                "Yo-Yo",
                f"{max(v_yoyo, key=lambda x: x['YoYo_Test'])['YoYo_Test']} m",
            )
        if v_kraft:
            b4.metric(
                "Kniebeuge",
                f"{max(v_kraft, key=lambda x: x['Kniebeuge'])['Kniebeuge']} kg",
            )
        if v_score:
            b5.metric(
                "Score",
                f"{round(max(v_score, key=lambda x: x['Gesamtscore'])['Gesamtscore'], 1)} Pkt",
            )

        st.divider()
        st.subheader("📋 Historie aller Tests")
        st.dataframe(gefilterte_testtage, use_container_width=True)

        buffer = io.StringIO()
        fieldnames = list(gefilterte_testtage[0].keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(gefilterte_testtage)
        csv_daten = buffer.getvalue()

        st.download_button(
            label="📥 Historie als CSV herunterladen (Excel)",
            data=csv_daten,
            file_name=f"Performance_Historie_{gewaehlter_spieler}.csv",
            mime="text/csv",
        )


# --- MENÜ 3: GRAPH & TRENDS ---
elif menue == "📈 Graph & Trends":
    st.header("📈 Leistungskurve & Trendanalyse")

    if len(gefilterte_testtage) < 2:
        st.warning(
            "Du benötigst mindestens 2 Testtage, um Verläufe und Trendlinien anzuzeigen."
        )
    else:
        disziplin_auswahl = st.selectbox(
            "Wähle eine Disziplin:", list(disziplinen.keys())
        )
        info = disziplinen[disziplin_auswahl]
        schluessel = info["schluessel"]

        gefilterte_tests = [t for t in gefilterte_testtage if schluessel in t]

        if len(gefilterte_tests) < 2:
            st.warning(
                f"Nicht genügend Daten für '{info['anzeigename']}' vorhanden."
            )
        else:
            daten = [t.get("Datum", "-") for t in gefilterte_tests]
            werte = [t[schluessel] for t in gefilterte_tests]

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(
                daten,
                werte,
                marker="o",
                color="#003399",
                linewidth=2,
                label=info["anzeigename"],
            )

            x_indizes = np.arange(len(werte))
            z = np.polyfit(x_indizes, werte, 1)
            trend_funktion = np.poly1d(z)

            ax.plot(
                daten,
                trend_funktion(x_indizes),
                linestyle="--",
                color="#e74c3c",
                linewidth=1.5,
                label="Trendlinie",
            )
            ax.set_ylabel(f"{info['anzeigename']} ({info['einheit']})")
            ax.set_title(f"Entwicklung & Trend: {info['anzeigename']}")
            ax.grid(True, linestyle="--", alpha=0.6)
            ax.legend()

            st.pyplot(fig)

            steigung = z[0]
            kleiner_ist_besser = info["kleiner_ist_besser"]

            if abs(steigung) < info["toleranz"]:
                st.info("ℹ️ **Trend:** Deine Leistung bleibt aktuell stabil.")
            elif (steigung < 0 and kleiner_ist_besser) or (
                steigung > 0 and not kleiner_ist_besser
            ):
                st.success(
                    "🔥 **Trend:** Positive Entwicklung! Du verbesserst dich."
                )
            else:
                st.warning("⚠️ **Trend:** Leicht rückläufige Performance.")


# --- MENÜ 4: LEADERBOARD & RADAR ---
elif menue == "🏆 Leaderboard & Radar":
    st.header("🏆 Team-Leaderboard & Stärkenprofil")

    col_radar, col_leaderboard = st.columns([1, 1])

    with col_radar:
        st.subheader("🕸️ Stärkenprofil & Vergleich (5 Achsen)")
        if not testtage:
            st.info("Keine Daten vorhanden.")
        else:
            alle_namen = sorted(
                list(set(t.get("Name") for t in testtage if t.get("Name")))
            )

            p1_name = st.selectbox("Hauptspieler:", alle_namen, index=0)
            vergleich_aktiv = st.checkbox(
                "Zweiten Spieler zum Vergleich anzeigen"
            )

            p1_tests = [t for t in testtage if t.get("Name") == p1_name]
            p1_letzter = p1_tests[-1] if p1_tests else {}

            _, p1_sprint = sprint_bewerten(p1_letzter.get("Beste Zeit", 2.0))
            _, p1_sprung = sprung_bewerten(p1_letzter.get("Sprunghoehe", 0))
            _, p1_505 = test505_bewerten(p1_letzter.get("Test_505_Zeit", 3.0))
            _, p1_yoyo = yoyo_bewerten(p1_letzter.get("YoYo_Test", 0))
            _, p1_kraft = kniebeuge_bewerten(
                p1_letzter.get("Kniebeuge", 0), p1_letzter.get("Gewicht", 75)
            )

            p1_daten = {
                "name": p1_name,
                "werte": [p1_sprint, p1_sprung, p1_505, p1_yoyo, p1_kraft],
            }

            p2_daten = None
            if vergleich_aktiv:
                p2_namen_options = [n for n in alle_namen if n != p1_name]
                if p2_namen_options:
                    p2_name = st.selectbox(
                        "Vergleichsspieler:", p2_namen_options
                    )
                    p2_tests = [t for t in testtage if t.get("Name") == p2_name]
                    p2_letzter = p2_tests[-1] if p2_tests else {}

                    _, p2_sprint = sprint_bewerten(
                        p2_letzter.get("Beste Zeit", 2.0)
                    )
                    _, p2_sprung = sprung_bewerten(
                        p2_letzter.get("Sprunghoehe", 0)
                    )
                    _, p2_505 = test505_bewerten(
                        p2_letzter.get("Test_505_Zeit", 3.0)
                    )
                    _, p2_yoyo = yoyo_bewerten(p2_letzter.get("YoYo_Test", 0))
                    _, p2_kraft = kniebeuge_bewerten(
                        p2_letzter.get("Kniebeuge", 0),
                        p2_letzter.get("Gewicht", 75),
                    )

                    p2_daten = {
                        "name": p2_name,
                        "werte": [
                            p2_sprint,
                            p2_sprung,
                            p2_505,
                            p2_yoyo,
                            p2_kraft,
                        ],
                    }

            fig_radar = radar_chart_erstellen(p1_daten, p2_daten)
            st.pyplot(fig_radar)

            st.divider()
            st.subheader(f"🤖 KI-Empfehlung für {p1_name}")

            status, tipps = generiere_ki_empfehlung(
                p1_letzter.get("Beste Zeit", 4.0),
                p1_letzter.get("Sprunghoehe", 50.0),
                p1_letzter.get("Test_505_Zeit", 2.5),
                p1_letzter.get("YoYo_Test", 1000.0),
                p1_letzter.get("Kniebeuge", 100.0),
                p1_letzter.get("Gewicht", 75.0),
                p1_letzter.get("Gesamtscore", 70.0),
            )

            st.info(status)
            for tipp in tipps:
                st.write(f"- {tipp}")

    with col_leaderboard:
        st.subheader("🥇 Team-Bestenliste")
        if not testtage:
            st.info("Keine Teamdaten vorhanden.")
        else:
            bestenliste = {}
            for t in testtage:
                spieler_name = t.get("Name", "Unbekannt")
                score = t.get("Gesamtscore", 0)

                if (
                    spieler_name not in bestenliste
                    or score > bestenliste[spieler_name]
                ):
                    bestenliste[spieler_name] = round(score, 1)

            rangliste = sorted(
                bestenliste.items(), key=lambda x: x[1], reverse=True
            )

            st.table(
                [
                    {
                        "Rang": i + 1,
                        "Spieler": name,
                        "Bester Score": f"{score} Pkt",
                    }
                    for i, (name, score) in enumerate(rangliste)
                ]
            )


# --- MENÜ 5: PDF EXPORT ---
elif menue == "📄 PDF Export":
    st.header("📄 PDF-Bericht generieren")

    if not gefilterte_testtage:
        st.info("Keine Daten zum Exportieren vorhanden.")
    else:
        letzter_test = gefilterte_testtage[-1]
        name = letzter_test.get("Name", "Unbekannt")
        datum = letzter_test.get("Datum", "-")

        st.write(
            f"Bericht für den letzten Test von **{name}** ({datum}) erstellen:"
        )

        pdf_pfad = pdf_bericht_erstellen(letzter_test)

        with open(pdf_pfad, "rb") as file:
            st.download_button(
                label="📥 PDF-Bericht herunterladen",
                data=file,
                file_name=f"Performance_{name}.pdf",
                mime="application/pdf",
            )