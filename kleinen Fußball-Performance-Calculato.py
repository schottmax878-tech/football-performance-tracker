# =========================
# IMPORTS
# =========================

from datetime import date , datetime
import json
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors



# =========================
# Dictionary
# =========================

disziplinen = {
    "Sprint":
    {
      "schluessel" : "Beste Zeit",
      "anzeigename" : "Sprint",
      "einheit" : "Sekunden",
      "kleiner_ist_besser" : True, 
      "toleranz" : 0.002,

    },
    "Sprung":
    {
      "schluessel" : "Sprunghoehe",
      "anzeigename" : "Sprung",
      "einheit" : "cm",
      "kleiner_ist_besser" : False, 
      "toleranz" : 0.05,

    },
    "505_Test":
    {
      "schluessel" : "Test_505_Zeit",
      "anzeigename" : "505-Test",
      "einheit" : "Sekunden",
      "kleiner_ist_besser" : True, 
      "toleranz" : 0.003,

    },
    "Gesamtscore":
    {
      "schluessel" : "Gesamtscore",
      "anzeigename" : "Gesamtscore",
      "einheit" : "Punkte",
      "kleiner_ist_besser" : False, 
      "toleranz" : 0.05,

    }
}


# =========================
# FUNKTIONEN
# =========================

def zahl_eingeben(frage, minimum, maximum):
    while True:
        try:
            eingabe = input(frage)
            eingabe = eingabe.replace(",", ".")
            eingabe = float(eingabe)

            if minimum <= eingabe <= maximum:
                return eingabe
            else:
                print(
                    f"Du musst eine Zahl im Bereich zwischen "
                    f"{minimum} und {maximum} eingeben."
                )

        except ValueError:
            print("Du musst eine gültige Zahl eingeben!")


def ganze_zahl_eingeben(frage, minimum, maximum):
    while True:
        try:
            eingabe = input(frage)
            eingabe = int(eingabe)

            if minimum <= eingabe <= maximum:
                return eingabe
            else:
                print(
                    f"Du musst eine Zahl im Bereich zwischen "
                    f"{minimum} und {maximum} eingeben."
                )

        except ValueError:
            print("Du musst eine gültige ganze Zahl eingeben!")


def testtage_speichern(testtage):
    with open("testtage.json", "w") as datei:
        json.dump(testtage,datei, indent=4)


def testtage_laden():
    try:
        with open("testtage.json", "r") as datei:
            return json.load(datei)
    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        print("Die Datei testtage.json konnte nicht korrekt gelesen werden.")
        return []

    
def testtage_anzeigen(testtage):

    sortierte_testtage = sorted(
        testtage,
        key=lambda testtag: datetime.strptime(testtag["Datum"], "%d.%m.%Y"), 
    reverse=True
    )

    for nummer, testtag in enumerate(sortierte_testtage, start=1):
        disziplin_ausgaben = []
        for disziplin_info in disziplinen.values():
            schluessel = disziplin_info["schluessel"]
            anzeigename = disziplin_info["anzeigename"]
            einheit = disziplin_info["einheit"]
            wert = testtag[schluessel]
            disziplin_ausgaben.append(
                f"{anzeigename}: {wert} {einheit}"
                )
        ausgabe_text = " | ".join(disziplin_ausgaben)
        print(
                f'Testtag {nummer} | {testtag["Datum"]} | {ausgabe_text}'
                )

        
def bestwerte_anzeigen(testtage):
    if len(testtage) == 0:
        print("Es sind noch keine Testtage gespeichert.")
        return

    for disziplin_info in disziplinen.values():
        schluessel = disziplin_info["schluessel"]
        anzeigename = disziplin_info["anzeigename"]
        einheit = disziplin_info["einheit"]
        kleiner_ist_besser = disziplin_info["kleiner_ist_besser"]

        if kleiner_ist_besser:
            bester_testtag = min(
                testtage,
                key=lambda testtag: testtag[schluessel]
            )
        else:
            bester_testtag = max(
                testtage,
                key=lambda testtag: testtag[schluessel]
            )

        bester_wert = bester_testtag[schluessel]

        print(
            f"Dein Bestwert in der Disziplin {anzeigename} war "
            f"{bester_wert} {einheit} am {bester_testtag['Datum']}"
            )


def durchschnitt_berechnen_fuer_trend_anzeigen(testtage, schluessel):
    werte = [testtag[schluessel] for testtag in testtage]

    durchschnitt_werte = sum(werte) / len(werte)
    return durchschnitt_werte


def trend_berechnen(werte, tage_seit_start): 
    if len(werte) < 2:
        print(
            "Für einen Vergleich brauchst du mindestens 2 Testtage, "
            "die miteinander verglichen werden können"
        )
        return None, None


    # 2. Mittelwerte berechnen
    durchschnitt_x = sum(tage_seit_start) / len(tage_seit_start)
    durchschnitt_y = sum(werte) / len(werte)

    # 3. Summen vorbereiten
    zaehler = 0
    nenner = 0

    # 4. Zähler und Nenner aufsummieren
    for x, y in zip(tage_seit_start, werte):
        zaehler += (x - durchschnitt_x) * (y - durchschnitt_y)
        nenner += (x - durchschnitt_x) ** 2

    if nenner == 0:
       print("Du musst Tests an mehreren Tagen haben")
       return None, None

    # 5. Steigung berechnen
    steigung = zaehler / nenner

    # 6. Achsenabschnitt berechnen
    achsenabschnitt = durchschnitt_y - steigung * durchschnitt_x


    return steigung, achsenabschnitt

    
def trend_interpretieren(steigung, disziplin, kleiner_ist_besser, toleranz, einheit):


    if steigung is None:
        return
    if abs(steigung) < toleranz:
        print(f"Dein Trend in der Disziplin {disziplin} ist gleich geblieben.")
        print(f"Trendsteigung: {steigung:.3f} {einheit} pro Tag")
        return
    if kleiner_ist_besser:
        verbessert = steigung < 0
        
    else:
        verbessert = steigung > 0

    if verbessert:
        print(f"Dein Trend in der Disziplin {disziplin} zeigt eine Verbesserung.")
        
    else:
        print(f"Dein Trend in der Disziplin {disziplin} zeigt eine Verschlechterung.")

    print(f"Trendsteigung: {steigung:.3f} {einheit} pro Tag")


def trend_anzeigen(testtage):

    sortierte_testtage = sorted(
        testtage,
        key=lambda testtag: datetime.strptime(
            testtag["Datum"],
            "%d.%m.%Y"
        )
    )

    daten = [testtag["Datum"] for testtag in sortierte_testtage]

    if len(set(daten)) < 3:
        print(
            "Du brauchst mindestens 3 durchgeführte Tests "
            "an unterschiedlichen Tagen"
        )
        return

    # Trends berechnen und interpretieren
    for disziplin_info in disziplinen.values():

        schluessel = disziplin_info["schluessel"]

        werte_liste = [testtag[schluessel] for testtag in sortierte_testtage]

        kleiner_ist_besser = disziplin_info["kleiner_ist_besser"]
        toleranz = disziplin_info["toleranz"]
        einheit = disziplin_info["einheit"]
        anzeigename = disziplin_info["anzeigename"]

        gemittelte_daten, gemittelte_werte = tagesdurchschnitte_berechnen(
            daten,
            werte_liste
        )

        gemittelte_tage_seit_start, _ = datumsdaten_vorbereiten(
            gemittelte_daten
        )

        trend_steigung, _ = trend_berechnen(
            gemittelte_werte,
            gemittelte_tage_seit_start
        )

        trend_interpretieren(
            trend_steigung,
            anzeigename,
            kleiner_ist_besser,
            toleranz,
            einheit
        )


def durchschnittswerte_anzeigen(testtage):

    if len(testtage) == 0:
        print("Du hast noch keine Tests durchgeführt")
        return
    
    for disziplin_info in disziplinen.values():

        schluessel = disziplin_info["schluessel"]
        anzeigename = disziplin_info["anzeigename"]
        einheit = disziplin_info["einheit"]

        durchschnitt = durchschnitt_berechnen_fuer_trend_anzeigen(testtage, schluessel)
        print(f"Der Durchschnitt in der Disziplin {anzeigename} beträgt {durchschnitt:.2f} {einheit}")


def tagesdurchschnitte_berechnen(daten, werte):
    werte_nach_datum = {}
    gemittelte_daten = []
    gemittelte_werte = []

    for datum, wert in zip(daten, werte):
        if datum in werte_nach_datum:
            werte_nach_datum[datum].append(wert)
        else:
            werte_nach_datum[datum] = [wert]

    for datum, werte_liste in werte_nach_datum.items():
        durchschnitt = sum(werte_liste) / len(werte_liste)
        gemittelte_daten.append(datum)
        gemittelte_werte.append(durchschnitt)

    
    return gemittelte_daten, gemittelte_werte

        
def datumsdaten_vorbereiten(gemittelte_daten):
    gemittelte_tage_seit_start = []
    gemittelte_daten_labels = []
    startdatum = datetime.strptime(gemittelte_daten[0],"%d.%m.%Y")

    for datum in gemittelte_daten:
        umgewandeltes_datum = datetime.strptime(datum,"%d.%m.%Y")
        differenz = umgewandeltes_datum - startdatum
        gemittelte_tage_seit_start.append(differenz.days)
        datum_label = umgewandeltes_datum.strftime( "%d.%m.")
        gemittelte_daten_labels.append(datum_label)


    return gemittelte_tage_seit_start, gemittelte_daten_labels


def graph_abstand_berechnen(werte):
    spannweite = max(werte) - min(werte)
    abstand = spannweite * 0.1

    if abstand == 0:
        if max(werte) == 0:
            abstand = 0.1
        else:
            abstand = max(werte) * 0.02
    return abstand


def trendlinie_berechnen(x_werte, steigung, achsenabschnitt):
    trendlinie = [steigung * x + achsenabschnitt for x in x_werte]

    return trendlinie


def messwerte_anzeigen(x_werte, y_werte):
    plt.plot(
        x_werte,
        y_werte,
        marker="o",
        color="blue",
        label="Messwerte"
    )


def trendlinie_anzeigen(x_werte, y_werte):
        plt.plot(
            x_werte,
            y_werte,
            linestyle="--",
            color="red",
            label="Trendlinie"
    )


def punktbeschriftungen_anzeigen(x_werte, y_werte):
    for x, y in zip(x_werte, y_werte):
        plt.annotate(
            f"{y:.2f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center"
        )

  
def graph_layout_einstellen(titel, y_beschriftung, x_positionen, datum_labels, gemittelte_werte, abstand):
    plt.title(f"{titel}")
    plt.xlabel("Datum")
    plt.ylabel(f"{titel} in {y_beschriftung}")
    plt.legend()
    plt.grid(True)
    plt.ylim(top=max(gemittelte_werte) + abstand)
    
    plt.xticks(x_positionen, datum_labels)


def graph_anzeigen(testtage, disziplin_info):
    
    schluessel = disziplin_info["schluessel"]
    titel = disziplin_info["anzeigename"]
    y_beschriftung = disziplin_info["einheit"]
    kleiner_ist_besser = disziplin_info["kleiner_ist_besser"]
    toleranz = disziplin_info["toleranz"]

    sortierte_testtage = sorted(
        testtage, 
        key=lambda testtag: datetime.strptime(
            testtag["Datum"],
            "%d.%m.%Y"

        )

    )
    daten = [testtag["Datum"] for testtag in sortierte_testtage]
    werte = [testtag[schluessel] for testtag in sortierte_testtage]

    

    gemittelte_daten, gemittelte_werte  = tagesdurchschnitte_berechnen(
        daten, werte
    )

    if len(gemittelte_daten) < 3:
        print("Du hast noch nicht genügend Tests an unterschiedlichen Tagen durchgeführt. Du brauchst mindestens: 3")
        return

    gemittelte_tage_seit_start, gemittelte_daten_labels = datumsdaten_vorbereiten(
        gemittelte_daten
    )

    abstand = graph_abstand_berechnen(
        gemittelte_werte
    )

    steigung_werte, achsenabschnitt_werte = trend_berechnen(
        gemittelte_werte, 
        gemittelte_tage_seit_start
    )  
     
    if steigung_werte is None or achsenabschnitt_werte is None:
        return

    trend_interpretieren(
        steigung_werte,
        titel,
        kleiner_ist_besser,
        toleranz,
        y_beschriftung
    )

    trendlinie = trendlinie_berechnen(
        gemittelte_tage_seit_start, 
        steigung_werte, 
        achsenabschnitt_werte
    )
    

    messwerte_anzeigen(
        gemittelte_tage_seit_start, 
        gemittelte_werte
    )

    trendlinie_anzeigen(
        gemittelte_tage_seit_start, 
        trendlinie
    )


    punktbeschriftungen_anzeigen(
        gemittelte_tage_seit_start, 
        gemittelte_werte
    )

    graph_layout_einstellen(
        titel,
        y_beschriftung,
        gemittelte_tage_seit_start,
        gemittelte_daten_labels,
        gemittelte_werte, abstand
    )



    plt.show()

    
def graph_menue(testtage):
    disziplinen_liste = list(disziplinen.keys())
    zurueck_nummer = len(disziplinen_liste) + 1
    
    for nummer, disziplin_name in enumerate(disziplinen_liste, start=1):
        disziplin_info = disziplinen[disziplin_name]
        print(f"{nummer}   {disziplin_info['anzeigename']}-Graph anzeigen")

    print(f"{zurueck_nummer}   Zurück")

    auswahl = ganze_zahl_eingeben(
        "Gib deine Menü-Auswahl ein: ",
        1,
        zurueck_nummer
    )

    if auswahl == zurueck_nummer:
        return

    disziplin_name = disziplinen_liste[auswahl -1]
    disziplin_info = disziplinen[disziplin_name]

    graph_anzeigen(
        testtage,
        disziplin_info
    )


def testtage_vergleichen(testtage):
    if len(testtage) < 2:
        print(
            "Für einen Vergleich brauchst du mindestens 2 Testtage, "
            "die miteinander verglichen werden können"
        )
        return
    sortierte_testtage = sorted(testtage,
        key=lambda testtag: datetime.strptime(testtag["Datum"], "%d.%m.%Y")
    )
    erster_testtag = sortierte_testtage[0]
    letzter_testtag = sortierte_testtage[-1]

    for disziplin_info in disziplinen.values():
        schluessel = disziplin_info["schluessel"]
        anzeigename = disziplin_info["anzeigename"]
        einheit = disziplin_info["einheit"]
        kleiner_ist_besser = disziplin_info["kleiner_ist_besser"]
        alter_wert = erster_testtag[schluessel]
        neuer_wert = letzter_testtag[schluessel]

        wert_vergleichen(alter_wert, neuer_wert, anzeigename, einheit, kleiner_ist_besser)


def wert_vergleichen(alter_wert, neuer_wert, disziplin, einheit, kleiner_ist_besser):

    if alter_wert == neuer_wert:
       print(f"Dein Wert in der Disziplin {disziplin} ist gleich geblieben.")
       return

    if alter_wert == 0:
        print("Eine prozentuale Berechnung ist bei dem Ausgangswert 0 nicht möglich")
        return
    
    differenz = abs(neuer_wert - alter_wert)

    prozentuale_veraenderung = differenz / alter_wert *100

    if kleiner_ist_besser:
        verbessert = neuer_wert < alter_wert
    else:
        verbessert = neuer_wert > alter_wert

    if verbessert:
        print(f"Du hast dich in der Disziplin {disziplin} verbessert.")
        print(f"Veränderung: {differenz:.2f} {einheit}.")
        print(f"Prozentuale Veränderung: {prozentuale_veraenderung:.2f} %")
    else:
        print(f"Du hast dich in der Disziplin {disziplin} verschlechtert.")
        print(f"Veränderung: {differenz:.2f} {einheit}.")
        print(f"Prozentuale Veränderung: {prozentuale_veraenderung:.2f} %")


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
    beste_zeit = min(zeiten)
    schlechteste_zeit = max(zeiten)
    durchschnitt = sum(zeiten) / len(zeiten)

    return beste_zeit, schlechteste_zeit, durchschnitt


def sprint_bewerten(zeit):
    if zeit < 1.70:
        return "Extrem schnell", 100
    elif zeit < 1.80:
        return "Sehr schnell", 85
    elif zeit < 1.90:
        return "Solide", 70
    else:
        return "Daran können wir arbeiten", 50


def fortschritt_bewerten(erste_zeit, letzte_zeit):
    if erste_zeit > letzte_zeit:
        return "Du hast dich verbessert!"
    elif erste_zeit == letzte_zeit:
        return "Deine Zeiten sind gleich geblieben!"
    else:
        return "Du hast dich leider verschlechtert!"


def veraenderung_berechnen(erste_zeit, letzte_zeit):
    return abs(erste_zeit - letzte_zeit)


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
    
def pdf_bericht_erstellen(spieler):
    # 1. Das PDF-Dokument erstellen
    pdf = canvas.Canvas("Performance_Bericht.pdf", pagesize=letter)
    
    # 2. Hauptüberschrift in Dunkelblau
    pdf.setFillColorRGB(0.0, 0.2, 0.6)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, 750, "ATHLETIC PERFORMANCE REPORT")
    
    # 3. Blaue Trennlinie unter der Überschrift
    pdf.setLineWidth(2)
    pdf.line(50, 735, 550, 735)
    
    # 4. Textfarbe für Athleten-Daten auf Schwarz stellen
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 12)
    
    # --- BLOCK 1: ATHLETEN-DATEN ---
    pdf.drawString(50, 700, f"Name: {spieler.get('Name', 'Unbekannt')}")
    pdf.drawString(50, 680, f"Gewicht: {spieler.get('Gewicht', '-')} kg")
    pdf.drawString(50, 660, f"Datum: {spieler.get('Datum', 'Unbekannt')}")
    
    # Feine graue Trennlinie UNTER dem Datum (bei Y = 645)
    pdf.setLineWidth(0.5)
    pdf.setFillColorRGB(0.7, 0.7, 0.7)
    pdf.line(50, 645, 550, 645)
    
    # --- BLOCK 2: MESSWERTE ALS TABELLE ---
    daten = [
        ["Test-Kategorie", "Messergebnis"],
        ["Beste Sprintzeit", f"{spieler.get('Beste Zeit', '-')} Sekunden"],
        ["Beste 505-Test Zeit", f"{spieler.get('Test_505_Zeit', '-')} Sekunden"],
        ["Beste Sprunghöhe", f"{spieler.get('Sprunghoehe', '-')} cm"]
    ]

    tabelle = Table(daten, colWidths=[250, 250])
    tabelle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003399")), # Dunkelblauer Header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                # Weiße Schrift
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),             # Fett im Header
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")), # Graues Gitter
    ]))

    # Tabelle auf Canvas platzieren
    tabelle.wrapOn(pdf, 500, 200)
    tabelle.drawOn(pdf, 50, 510)
    
    # --- BLOCK 3: SCORE-HIGHLIGHT-KASTEN ---
    pdf.setFillColorRGB(0.9, 0.94, 1.0) # Helles Blau
    pdf.rect(50, 430, 500, 50, fill=1, stroke=0)
    
    pdf.setFillColorRGB(0.0, 0.2, 0.6) # Dunkelblauer Text (NUR EINMAL)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(65, 448, f"Gesamtscore: {spieler.get('Gesamtscore', '-')} Punkte")
    
    # 5. Speichern
    pdf.save()

def ergebnis_anzeigen(spieler):
    print("\n=== FOOTBALL PERFORMANCE ===")
    print(f"Name: {spieler['Name']}")
    print(f"Gewicht: {spieler['Gewicht']} kg")
    print(f"10-Meter-Sprintzeiten: {spieler['Sprintzeiten']}")
    print(f"Beste Zeit: {spieler['Beste Zeit']} Sekunden")
    print(f"Schlechteste Zeit: {spieler['Schlechteste Zeit']} Sekunden")
    print(f"Durchschnitt: {spieler['Durchschnitt']:.2f} Sekunden")
    print(f"Bewertung deiner Sprintleistung: {spieler['Sprint_Bewertung']}")
    print(f"Performance-Punkte Sprint: {spieler['Sprint_Punkte']}/100")
    print(f"Fortschritt: {spieler['Fortschritt']}")
    print(f"Veränderung: {spieler['Veränderung']:.2f} Sekunden")
    print(f"Deine Sprunghöhe: {spieler['Sprunghoehe']} cm")
    print(f"Bewertung deiner Sprunghöhe: {spieler['Sprung_Bewertung']}")
    print(f"Performance-Punkte Sprung: {spieler['Sprung_Punkte']}/100")
    print(f"Bewertung deines 505-Tests: {spieler['Test_505']}")
    print(f"Performance-Punkte 505-Test: {spieler['Test_505_Punkte']}/100")
    print(f"Gesamtscore: {spieler['Gesamtscore']:.1f}/100")
    print(f"Gesamtscore-Bewertung: {spieler['Gesamtscore_bewertung']}")

def sprintzeiten_eingeben():

    sprintzeiten = []
    anzahl = ganze_zahl_eingeben(
        "Wie viele Sprintzeiten möchtest du eingeben? ",
        1,
        100
    )

    while len(sprintzeiten) < anzahl:
        zeit = zahl_eingeben(
            "Gib deine Sprintzeit in Sekunden ein: ",
            0.5,
            5
        )
        sprintzeiten.append(zeit)

    return sprintzeiten

def test_auswerten(sprintzeiten, sprunghoehe, test_505_eingabe):
    beste_zeit, schlechteste_zeit, durchschnitt = sprint_analyse(
            sprintzeiten
        )

    bewertung, punkte = sprint_bewerten(
        beste_zeit
       )
    fortschritt = fortschritt_bewerten(
            sprintzeiten[0],
            sprintzeiten[-1]
        )
    
    veraenderung = veraenderung_berechnen(
            sprintzeiten[0],
            sprintzeiten[-1]
        )
    bewertung2, punkte2 = sprung_bewerten(
        sprunghoehe
    )
    test_505, punktzahl = test505_bewerten(
        test_505_eingabe
    )
    gesamtscore = (
            punkte +
            punkte2 +
            punktzahl
        ) / 3
    
    gesamtscore_bewertung = gesamtscore_bewerten(
            gesamtscore
        )

    ergebnisse = {
        "Beste_Zeit": beste_zeit,
        "Schlechteste_Zeit": schlechteste_zeit, 
        "Durchschnitt": durchschnitt,
        "Sprint_Bewertung": bewertung,
        "Sprint_Punkte": punkte,
        "Fortschritt": fortschritt,
        "Veraenderung": veraenderung,
        "Sprung_Bewertung": bewertung2,
        "Test_505": test_505,
        "Gesamtscore": gesamtscore,
        "Gesamtscore_bewertung": gesamtscore_bewertung, 
        "Sprung_Punkte": punkte2,
        "Test_505_Punkte":punktzahl
    }
    return ergebnisse

def testtag_erstellen(name, gewicht, datum, sprunghoehe, test_505_eingabe, ergebnisse):
    testtag = {
        "Name" : name,
        "Gewicht" : gewicht,
        "Datum": datum,
        "Beste Zeit": ergebnisse["Beste_Zeit"],
        "Sprunghoehe": sprunghoehe,
        "Test_505_Zeit": test_505_eingabe,
        "Gesamtscore": ergebnisse["Gesamtscore"]
    }
    return testtag

def spieler_erstellen(name, gewicht, sprintzeiten, sprunghoehe, ergebnisse):
        spieler = {
        "Name": name,
        "Gewicht": gewicht,
        "Sprintzeiten": sprintzeiten,
        "Veränderung": ergebnisse["Veraenderung"],
        "Sprunghoehe": sprunghoehe,
        "Beste Zeit": ergebnisse["Beste_Zeit"],
        "Schlechteste Zeit": ergebnisse["Schlechteste_Zeit"],
        "Durchschnitt": ergebnisse["Durchschnitt"],
        "Sprint_Bewertung": ergebnisse["Sprint_Bewertung"],
        "Sprint_Punkte": ergebnisse["Sprint_Punkte"],
        "Fortschritt": ergebnisse["Fortschritt"],
        "Sprung_Bewertung": ergebnisse["Sprung_Bewertung"],
        "Sprung_Punkte": ergebnisse["Sprung_Punkte"],
        "Test_505": ergebnisse["Test_505"],
        "Test_505_Punkte": ergebnisse["Test_505_Punkte"],
        "Gesamtscore": ergebnisse["Gesamtscore"],
        "Gesamtscore_bewertung": ergebnisse["Gesamtscore_bewertung"]
    }
        return spieler

def neuen_test_durchfuehren(testtage):

    name = input("Wie heißt du? ")

    gewicht = zahl_eingeben(
        "Gib dein Gewicht in kg ein: ",
        20,
        250
    )

    sprintzeiten = sprintzeiten_eingeben()

    sprunghoehe = zahl_eingeben(
        "Gib deine Sprunghöhe in cm ein: ",
        1,
        150
    )

    test_505_eingabe = zahl_eingeben(
        "Gib deine Bestzeit beim absolvierten 505-Test ein: ",
        1,
        5
    )

    ergebnisse = test_auswerten(
    sprintzeiten,
    sprunghoehe,
    test_505_eingabe
)

    heute = date.today()
    datum = heute.strftime("%d.%m.%Y")

    testtag = testtag_erstellen(name, gewicht, datum, sprunghoehe, test_505_eingabe, ergebnisse)

    testtage.append(testtag)
    testtage_speichern(testtage)

    spieler = spieler_erstellen(name, gewicht, sprintzeiten, sprunghoehe, ergebnisse)
     
    ergebnis_anzeigen(spieler)
# =========================
# HAUPTPROGRAMM
# =========================



def main():
    testtage = testtage_laden()
    
    while True:

        print("1    Neuen Test eingeben")
        print("2    Testhistorie anzeigen")
        print("3    Fortschritt vergleichen")
        print("4    Bestwerte anzeigen")
        print("5    Trend anzeigen")
        print("6    Graph Menue")
        print("7    Durchschnittswerte anzeigen")
        print("8    PDF-Bericht erstellen")
        print("9   Programm beenden")
        auswahl = ganze_zahl_eingeben(
            "Gib deine Menü-Auswahl ein: ",
            1,
            9 
        )

        if auswahl == 1:
           neuen_test_durchfuehren(testtage)

        elif auswahl == 2:
            testtage_anzeigen(testtage)

        elif auswahl == 3:
            testtage_vergleichen(testtage)

        elif auswahl == 4:
            bestwerte_anzeigen(testtage)

        elif auswahl == 5:
            trend_anzeigen(testtage)

        elif auswahl == 6:
            graph_menue(testtage)

        elif auswahl == 7:
            durchschnittswerte_anzeigen(testtage)

        elif auswahl == 8:
            if len(testtage) == 0:
               print("Es sind noch keine Testtage gespeichert. Wähle Option 1, um einen zu erstellen.")
            else:
               aktueller_testtag = testtage[-1]
               pdf_bericht_erstellen(aktueller_testtag)
               print("\n--> PDF-Bericht wurde erfolgreich als 'Performance_Bericht.pdf' gespeichert!\n")

        elif auswahl == 9:
            print("Dein Programm wird beendet.")
            break


if __name__ == "__main__":
    main()
