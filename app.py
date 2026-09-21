from datetime import date, datetime
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
import sqlite3 
import csv
import io

# =========================
# 1. KONFIGURATION & DICTIONARY
# =========================

st.set_page_config(
    page_title="Football Performance Tracker", page_icon="⚽", layout="wide"
)


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
    "Gesamtscore": {
        "schluessel": "Gesamtscore",
        "anzeigename": "Gesamtscore",
        "einheit": "Punkte",
        "kleiner_ist_besser": False,
        "toleranz": 0.05,
    },
}

# =========================
# 2. BERECHNUNGS-LOGIK & SPEICHERUNG
# =========================


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
            gesamtscore REAL
        )
    """)
    conn.commit()
    conn.close()


def testtag_speichern_sqlite(daten):
    conn = sqlite3.connect("performance.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO testtage (name, gewicht, datum, beste_zeit, sprunghoehe, test_505_zeit, gesamtscore)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            daten["Name"],
            daten["Gewicht"],
            daten["Datum"],
            daten["Beste Zeit"],
            daten["Sprunghoehe"],
            daten["Test_505_Zeit"],
            daten["Gesamtscore"],
        ),
    )
    conn.commit()
    conn.close()

def testtage_laden_sqlite():
    conn = sqlite3.connect("performance.db")
    # Damit wir auf Spalten per Namen zugreifen können (wie im Dictionary)
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
                "Gesamtscore": row["gesamtscore"],
            }
        )

    conn.close()
    return testtage
# 1. Daten laden
init_db()
testtage = testtage_laden_sqlite()

# 2. Alle eindeutigen Spielernamen für das Dropdown ermitteln
verfuegbare_spieler = sorted(
    list(set(t.get("Name") for t in testtage if t.get("Name")))
)
auswahl_optionen = ["Alle Spieler"] + verfuegbare_spieler

# 3. Filter in der Seitenleiste anzeigen
st.sidebar.markdown("---")
gewaehlter_spieler = st.sidebar.selectbox(
    "👤 Spieler filtern:", auswahl_optionen
)

# 4. Datensatz basierend auf der Auswahl filtern
if gewaehlter_spieler != "Alle Spieler":
    gefilterte_testtage = [
        t for t in testtage if t.get("Name") == gewaehlter_spieler
    ]
else:
    gefilterte_testtage = testtage

def radar_chart_erstellen(sprint_pkt, sprung_pkt, test505_pkt, name):
    kategorien = ["Sprint", "Sprung", "505-Agilität"]
    werte = [sprint_pkt, sprung_pkt, test505_pkt]

    # Kreis schließen (ersten Wert am Ende wiederholen)
    werte += werte[:1]
    winkel = np.linspace(0, 2 * np.pi, len(kategorien), endpoint=False).tolist()
    winkel += winkel[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    # Fläche zeichnen
    ax.fill(winkel, werte, color="#003399", alpha=0.25)
    ax.plot(winkel, werte, color="#003399", linewidth=2)

    # Achsen-Beschriftung
    ax.set_xticks(winkel[:-1])
    ax.set_xticklabels(kategorien, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 100)

    ax.set_title(f"Stärkenprofil: {name}", y=1.1, fontsize=13)
    return fig

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


def test_auswerten(sprintzeiten, sprunghoehe, test_505_eingabe):
    beste_zeit, schlechteste_zeit, durchschnitt = sprint_analyse(sprintzeiten)
    bewertung, punkte = sprint_bewerten(beste_zeit)
    bewertung2, punkte2 = sprung_bewerten(sprunghoehe)
    test_505, punktzahl = test505_bewerten(test_505_eingabe)

    gesamtscore = (punkte + punkte2 + punktzahl) / 3
    gesamtscore_bewertung = gesamtscore_bewerten(gesamtscore)

    return {
        "Beste_Zeit": beste_zeit,
        "Schlechteste_Zeit": schlechteste_zeit,
        "Durchschnitt": durchschnitt,
        "Sprint_Bewertung": bewertung,
        "Sprint_Punkte": punkte,
        "Sprung_Bewertung": bewertung2,
        "Sprung_Punkte": punkte2,
        "Test_505": test_505,
        "Test_505_Punkte": punktzahl,
        "Gesamtscore": gesamtscore,
        "Gesamtscore_bewertung": gesamtscore_bewertung,
    }


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
        ["Beste Sprintzeit", f"{spieler.get('Beste Zeit', '-')} Sekunden"],
        [
            "Beste 505-Test Zeit",
            f"{spieler.get('Test_505_Zeit', '-')} Sekunden",
        ],
        ["Beste Sprunghöhe", f"{spieler.get('Sprunghoehe', '-')} cm"],
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
    tabelle.drawOn(pdf, 50, 510)

    pdf.setFillColorRGB(0.9, 0.94, 1.0)
    pdf.rect(50, 430, 500, 50, fill=1, stroke=0)

    pdf.setFillColorRGB(0.0, 0.2, 0.6)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(
        65,
        448,
        f"Gesamtscore: {round(spieler.get('Gesamtscore', 0), 1)} Punkte",
    )

    pdf.save()
    return dateiname


# =========================
# 3. STREAMLIT OBERFLÄCHE
# =========================


st.title("⚽ Football Performance Dashboard")

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

    with st.form("test_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name des Athleten", value="Max Mustermann")
            gewicht = st.number_input(
                "Gewicht (kg)", min_value=20.0, max_value=250.0, value=75.0
            )
            sprunghoehe = st.number_input(
                "Sprunghöhe (cm)", min_value=1.0, max_value=150.0, value=55.0
            )

        with col2:
            test_505 = st.number_input(
                "505-Test Zeit (Sekunden)",
                min_value=1.0,
                max_value=5.0,
                value=2.4,
                step=0.01,
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
            ergebnisse = test_auswerten(sprintzeiten, sprunghoehe, test_505)
            datum_heute = date.today().strftime("%d.%m.%Y")

            neuer_testtag = {
                "Name": name,
                "Gewicht": gewicht,
                "Datum": datum_heute,
                "Beste Zeit": ergebnisse["Beste_Zeit"],
                "Sprunghoehe": sprunghoehe,
                "Test_505_Zeit": test_505,
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
        st.subheader("🏆 Deine Bestwerte")
        b_col1, b_col2, b_col3 = st.columns(3)

        # Sicheres Filtern veralteter/unvollständiger JSON-Datensätze
        valid_sprint = [t for t in gefilterte_testtage if "Beste Zeit" in t]
        valid_sprung = [t for t in gefilterte_testtage if "Sprunghoehe" in t]
        valid_score = [t for t in gefilterte_testtage if "Gesamtscore" in t]

        if valid_sprint:
            best_sprint = min(valid_sprint, key=lambda x: x["Beste Zeit"])
            b_col1.metric("Bester Sprint", f"{best_sprint['Beste Zeit']} s")
        if valid_sprung:
            best_sprung = max(valid_sprung, key=lambda x: x["Sprunghoehe"])
            b_col2.metric("Bester Sprung", f"{best_sprung['Sprunghoehe']} cm")
        if valid_score:
            best_score = max(valid_score, key=lambda x: x["Gesamtscore"])
            b_col3.metric(
                "Höchster Score", f"{round(best_score['Gesamtscore'], 1)} Pkt"
            )

        st.divider()
        st.subheader("📋 Historie aller Tests")
        st.dataframe(gefilterte_testtage, use_container_width=True)

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

            # Messwerte als Kurve
            ax.plot(
                daten,
                werte,
                marker="o",
                color="#003399",
                linewidth=2,
                label=info["anzeigename"],
            )

            # Trendlinie berechnen (Lineare Regression)
            x_indizes = np.arange(len(werte))
            z = np.polyfit(x_indizes, werte, 1)
            trend_funktion = np.poly1d(z)

            # Trendlinie im Plot zeichnen
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

            # Automatische Auswertung der Trendlinie unter Berücksichtigung der Toleranz
            steigung = z[0]
            kleiner_ist_besser = info["kleiner_ist_besser"]

            if abs(steigung) < info["toleranz"]:
                st.info("ℹ️ **Trend:** Deine Leistung bleibt aktuell stabil.")
            elif (steigung < 0 and kleiner_ist_besser) or (
                steigung > 0 and not kleiner_ist_besser
            ):
                st.success("🔥 **Trend:** Positive Entwicklung! Du verbesserst dich.")
            else:
                st.warning("⚠️ **Trend:** Leicht rückläufige Performance.")

# --- MENÜ 4: PDF EXPORT ---
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
# --- MENÜ 4: LEADERBOARD & RADAR ---
elif menue == "🏆 Leaderboard & Radar":
    st.header("🏆 Team-Leaderboard & Stärkenprofil")

    col_radar, col_leaderboard = st.columns([1, 1])

    # --- RADAR CHART (Einzelsportler) ---
    with col_radar:
        st.subheader("🕸️ Stärkenprofil (Radar)")
        if not gefilterte_testtage:
            st.info("Keine Daten vorhanden.")
        else:
            letzter = gefilterte_testtage[-1]

            # Punktzahlen auswerten
            _, p_sprint = sprint_bewerten(letzter.get("Beste Zeit", 2.0))
            _, p_sprung = sprung_bewerten(letzter.get("Sprunghoehe", 0))
            _, p_505 = test505_bewerten(letzter.get("Test_505_Zeit", 3.0))

            fig_radar = radar_chart_erstellen(
                p_sprint, p_sprung, p_505, letzter.get("Name", "Athlet")
            )
            st.pyplot(fig_radar)

    # --- LEADERBOARD (Gesamtes Team) ---
    with col_leaderboard:
        st.subheader("🥇 Team-Bestenliste")
        if not testtage:
            st.info("Keine Teamdaten vorhanden.")
        else:
            # Beste Gesamtscores pro Spieler ermitteln
            bestenliste = {}
            for t in testtage:
                spieler_name = t.get("Name", "Unbekannt")
                score = t.get("Gesamtscore", 0)

                if (
                    spieler_name not in bestenliste
                    or score > bestenliste[spieler_name]
                ):
                    bestenliste[spieler_name] = round(score, 1)

            # Sortieren nach höchstem Score
            rangliste = sorted(
                bestenliste.items(), key=lambda x: x[1], reverse=True
            )

            # Als Tabelle ausgeben
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