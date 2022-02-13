Votre espace de stockage est plein. … Vous ne pouvez plus importer de nouveaux fichiers dans Drive, et risquez de ne plus pouvoir envoyer ni recevoir d'e-mails via Gmail.En savoir plus
from lib import *
import lib

''' Variables globales '''

hd = set.Hd
hf = set.Hf
mail = set.default_mail
dref = set.Dref
tref = set.Tref
DEBUG2 = True



''' Programme principal '''


def mainProg(h):
    hd = h - "00:15"
    hf = h + "00:05"
    initScreen(0,0,0)
    if DEBUG2: print("test de dÃ©but de programme...")
    while testSup(hd) == False:
        continue
    initScreen(25,25,25)
    setTextColor("Debut du \n pointage...",25,25,25)
    if DEBUG2: print("Initialisation de Lcurrent")
    initFile("Lcurrent")
    if DEBUG2: print("test de fin de programme")
    a = testInf(hf)
    if DEBUG2: print(a)
    time.sleep(2)
    initScreen(25,25,25)
    setTextColor("Approchez-vous !",25,25,25)
    while a:
        #if DEBUG2: print("test de proximitÃ©")
        b = testDist(dref)
        c = testBack()
        if DEBUG: print(b,c)
        while testDist(dref) and c == False:
            if DEBUG2: print("Une personne est Ã  proximitÃ©")
            #killDate = True
            #timer_update.start() # lancement du timer
            initScreen(25,25,25)
            setTextColor("Choisissez votre\n methode",25,25,25)
            time.sleep(3)
            choice()
            a = testInf(hf)
            break

    initScreen(25,25,25)
    setTextColor("Fin d'appel \n Extinction...",25,25,25)
    setFile()
    for i in range(len(mail)):
        sendMail(mail[i],"pointage des etudiants","Voici la liste des etudiants presents en PJ","setFile.txt")
    time.sleep(2)
    initScreen(0,0,0)

i = 0
while i < len(H):
    mainProg(H[i])
    i += 1
i = 0
