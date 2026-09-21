name = input("Wie heißt du?")
alter = int(input("wie alt bist du"))
if alter < 16 and name !="":
    print( name,"Du nist zu jung um hier mitzumachen")
elif alter == 16 and name !="": 
      print( name,"Du darfst gerade so mitmachen")
else:
    print( name,"du bist nicht berechtigt")
