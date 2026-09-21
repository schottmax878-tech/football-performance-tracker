def sprint_bewerten(zeit):
    if zeit < 1.7 :
        return "extrem schnell"
    elif zeit < 1.8 :
        return "sehr schnell"
    elif zeit < 1.90 : 
        return "solide"
    else :
        return "Verbesserungspotenzial" 
bewertung = sprint_bewerten(1.76)
print(bewertung)

sprintzeiten = [1.78, 1.81, 1.76, 1.74]

def durchschnitt_berechnen(zeiten):
     return sum(zeiten)/ len(zeiten)

ergebnis = durchschnitt_berechnen(sprintzeiten)
print(f"Durchschnitt: {ergebnis:.2f} Sekunden")

def schnellste_zeit_finden(zeiten): 
     return min(zeiten)

schnellste_zeit = schnellste_zeit_finden(sprintzeiten)
print(schnellste_zeit)

def langsamste_zeit_finden(zeiten):
     return max(zeiten)

langsamste_zeit = langsamste_zeit_finden(sprintzeiten)
print(langsamste_zeit)

def fortschritt_berechnen (erste_zeit, letzte_zeit) :
     return abs(erste_zeit - letzte_zeit)


fortschritt = fortschritt_berechnen(1.85, 1.76)
print(f"{fortschritt:.2f}")

def fortschritt_bewerten(erste_zeit, letzte_zeit):
    if erste_zeit > letzte_zeit:
        return "du hast dich verbessert"
    elif erste_zeit == letzte_zeit:
        return "Gleich Geblieben"
    else :
        return "du hast dich verschlechtert"
bewertung= fortschritt_bewerten (1.85,1.76)
print(f"Bewertung deines Fortschrittes: {bewertung}")

def sprint_analyse(zeiten):
    schlechteste_zeit =  max(zeiten)
    beste_zeit = min(zeiten)
    durchschnitt=  sum(zeiten) / len(zeiten)
    return schlechteste_zeit, beste_zeit, durchschnitt


schlechteste_zeit2, beste_zeit2, durchschnitt2= sprint_analyse(sprintzeiten)
print(beste_zeit2)
print (schlechteste_zeit2)
print (f"{durchschnitt2:.2f}")

