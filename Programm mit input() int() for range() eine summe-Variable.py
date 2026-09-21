summe = 0

grenze = int (input("Bis zu welcher Zahl soll ich addieren?"))

for zahl in range(1, grenze +1):
    if zahl % 2 == 0:
     summe = summe + zahl


print(summe)