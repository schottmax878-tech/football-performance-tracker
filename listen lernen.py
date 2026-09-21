sprintzeiten = []
anzahl = int(input("Wie viele Sprintzeiten möchtest du eingeben?: "))



for i in range (anzahl): 
    benutzerdefinierte_zeit = float(input("Nenne mir deine letzten sprintzeiten auf 10 Metern: "))
    sprintzeiten.append(benutzerdefinierte_zeit)
print(sprintzeiten)

durchschnitt = sum(sprintzeiten) / len(sprintzeiten)

for zeit in sprintzeiten:
    print(f"Sprintzeiten:{zeit}")


print("=== Auswertung ===")
print(f"Anzahl der Sprints: {anzahl}")
print(f"Schnellste Sprintzeit: {min(sprintzeiten)} Sekunden")
print(f"Langsamste Sprintzeit: {max(sprintzeiten)} Sekunden")
print(f"Durchschnittliche Sprintzeit: {durchschnitt:.2f}")

erste_zeit=sprintzeiten[0]
letzte_zeit=sprintzeiten[-1]
veraenderung = abs(erste_zeit - letzte_zeit)

if erste_zeit > letzte_zeit:
    bewertung = "Du hast dich verbessert! Stark mach weiter so!" 
    veraenderungs_text = f"Du hast dich um {veraenderung:.2f} sekunden verbessert"

elif erste_zeit == letzte_zeit:
    bewertung = "Du hast dich weder verbessert noch verschlechtert! Egal weiter so.."
    veraenderungs_text = "Es gab keine Veränderung."


else :
    bewertung = "Du hast dich verschlechtert! Egal dran bleiben" 
    veraenderungs_text = f"Du hast dich um {veraenderung:.2f} Sekunden verschlechtert."

print(f"Bewertung des Fortschritts: {bewertung}")
print(veraenderungs_text)
