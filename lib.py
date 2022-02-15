# coding: utf-8


''' Bibliothèques utiles '''

import os
import smbus
import RPI.GPIO as GPIO
from pn532 import *
import time
import grovepi
import serial
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
from fpdf import FPDF
import pdfkit
import threading


''' Variables utiles '''
# variable de débugage
DEBUG = False

# variables du programme principal
killDate = True #variable tuant le processus dateThread()
killTimer = True # variable tuant le processus timerThread()
killb = True # variable tuant le processus bTestThread()
killc = True # variable tuant le processus cTestThread()
timer = 0   # variable incrémentée représentant le temps passé pour les test bouton et/ou carte
Tref = 90 # temps d'attente avant que les test bouton et carte ne soient stoppés


''' Entrées '''

# Bouton ON/OFF
start_button = 6 # port D6
grovepi.pinMode(start_button,"INPUT")

# Bouton de sélection
select_button = 3 # port D3
grovepi.pinMode(select_button,"INPUT")

# Potentiomètre de navigation
potentiometer = 0 # port A0
grovepi.pinMode(potentiometer,"INPUT")

# Capteur de proximité à ultrasons
ultrasonic_ranger = 4 # port D4
grovepi.set_bus("RPI_1")

# Capteur RFID PN532
rfid = 2 # port I2C-2
rfidbus = smbus.SMBus(rfid) # bus I2C


''' Sorties '''

# Ecran LCD
lcd = 1 # port I2C-1
buslcd = smbus.SMBus(lcd) # bus I2C
DISPLAY_RGB_ADDR = 0x62 # adresse couleur
DISPLAY_TEXT_ADDR = 0x3e # adresse texte

# LED
led = 5 # port D5
grovepi.pinMode(led,"OUTPUT")


''' Fonctions d'acquisition '''

# Capteur de proximité à ultrasons
# retourne la distance captée si elle existe
def distance():
        try:
                return grovepi.ultrasonicRead(ultrasonic_ranger)
        except:
                return -1

# Bouton de sélection
# retourne la liste des valeurs prises par le bouton (1 si appuyé et 0 sinon) de taille itermax désignant le nombre de test sur le capteur (par défaut 10000)
# chaque test étant séparé de 0.2sec du suivant (soit environ 2000sec max d'acquisition)
def selectButton(itermax=10000):
        l =[]
        i=0
        while i<itermax:
                try:
                        l.append(grovepi.digitalRead(select_button))
                        if DEBUG: print(l)
                        time.sleep(.2)
                except IOError:
                        print("ERROR")
                i+=1
        return l

# Bouton ON/OFF
# retourne la liste des valeurs prises par le bouton (1 si appuyé et 0 sinon) d$
# chaque test étant séparé de 0.2sec du suivant (soit environ 2000sec max d'acq$
def startButton(itermax=10000):
        l =[]
        i=0
        while i<itermax:
                try:
                        l.append(grovepi.digitalRead(start_button))
                        if DEBUG: print(l)
                        time.sleep(.2)
                except IOError:
                        print("ERROR")
                i+=1
        return l


# Potentiomètre de navigation
# retourne une liste de 3 int [nombre d'incréments, tension associée, angle associé]
def potentio():
        adc_ref = 5 # tension de référence du potentiomètre
        grove_vcc = 5 # tension courant continu délivrée par le shield
        full_angle = 300 # angle maximal du potentiomètre
        try:
                sensor_value = grovepi.analogRead(potentiometer) # valeur du capteur
                voltage = round((float)(sensor_value) * adc_ref / 1023, 2) # calcul de la tension
                degrees = round((voltage * full_angle) / grove_vcc, 2) # calcul de l'angle
                l = [sensor_value,voltage,degrees]
                if DEBUG: print(l)
        except IOError:
                print("ERROR")
        return l

# Capteur RFID


''' Fonctions d'exportation '''


# fonction permettant de choisir la couleur de l'écran LCD
def setRGB(rouge,vert,bleu):
        #initialisation couleur
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x00,0x00)
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x01,0x00)
        #changement de couleur
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x02,bleu)
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x03,vert)
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x04,rouge)
        #retour de la couleur
        buslcd.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xAA)
        if DEBUG: print("color changed")


# fonction permettant l'affichage d'un caractère à l'écran LCD
def textCmd(cmd):
        buslcd.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)
        if DEBUG:
                print("caractère affiché avec codage")
                print(cmd)


# fonction initialisant le texte de l'écran LCD
def initScreen(r,g,b):
        setRGB(r,g,b)
        textCmd(0x01)
        textCmd(0x0F)
        textCmd(0x38)


# fonction permettant d'ecrire le texte recu en parametre
# Si le texte contient un \n ou plus de 16 caracteres, retour à la ligne
# si le texte dépasse 32 caractères passage à écran suivant après 3sec d'intervalle
def setTextColor(text,r,g,b):
        setRGB(r,g,b)
        textCmd(0x02)
        time.sleep(.05)
        textCmd(0x08 | 0x04) # affichage allumé, pas de curseur
        textCmd(0x28) # 2 lignes
        time.sleep(.05)
        count = 0
        row = 0
        while len(text) < 32: # nettoie le reste de l'écran
                text += ' '
        for c in text:
                if c == '\n' or count == 16: # test dépassement ligne
                        count = 0
                        row += 1
                        if row == 2: # test dépassement taille écran
                                time.sleep(3)
                                initScreen(r,g,b)
                                row = 0
                        textCmd(0xc0)
                        if c == '\n':
                                continue
                count += 1
                buslcd.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))
                if DEBUG: print(c)



# fonction affichant sur l'écran LCD: Accès autorisé et le texte voulu sur la/les $
def accessGranted(text):
        setTextColor("Bienvenue M/Mme\n"+text,0,20,0)
        time.sleep(5)
        initScreen(0,0,0)


# fonction affichant sur l'écran LCD: ERREUR, un code puis un texte sur la/les lig$
def accessDenied(code,text):
        setTextColor("ERREUR "+ code +"\n"+ text,20,0,0)
        time.sleep(5)
        initScreen(0,0,0)


# fonction affichant l'heure et l'actualisant en continu sur l'écran LCD
def date():
        initScreen(25,25,25)
        now = time.localtime(time.time())
        setTextColor(time.strftime("   %d/%m/%y\n     %H:%M", now),25,25,25)
        while True:
                now2=time.localtime(time.time())
                if (time.strftime("   %d/%m/%y\n     %H:%M", now2)!=time.strftime("   %d/%m/%y\n     %H:%M"$
                        initScreen(25,25,25)
                        setTextColor(time.strftime("   %d/%m/%y\n     %H:%M", now2),25,25,25)
                        now = now2

# Fonction permettant d'allumer (etat=1) ou d'éteindre (etat=0) la led
def light(etat):
        grovepi.digitalWrite(led,etat)
        if DEBUG: print(etat)




''' Fonctions test '''

# fonction testant si l'heure actuelle >= heure
# avec heure string de la forme "hh:mm" désignant une heure
def testSup(heure):
        h = time.strftime("%H:%M", time.localtime(time.time()))
        return h >= heure

# fonction testant si l'heure actuelle <= heure
# avec heure string de la forme "hh:mm" désignant une heure
def testInf(heure):
        h = time.strftime("%H:%M", time.localtime(time.time()))
        return h <= heure

# fonction testant si la distance captée <= distance
# avec distance entier désignant une distance en centimètres
def testDist(dist):
        d = int(distance())
        if d == -1:
                return False
        else:
                if d <= dist:
                        return True
                else:
                        return False

# fonction testant si le bouton select est appuyé dans la seconde qui suit
def testSelect():
        for i in sButton(5):
                if i == 1:
                        return True
        return False

# fonction testant si le bouton start est appuyé dans la seconde qui suit
def testStart():
        for i in startButton(5):
                if i == 1:
                        return True
        return False

# fonction testant l'utilisation du potentiomètre par rapport à une postion de référence pour une sensib$
# retourne -1 s'il est dans la zone gauche = [0-340] (incréments)
# retourne 0 s'il est dans la zone centrale = [341-681] (incréments)
# retourne 1 s'il est dans la zone droite = [682-1023] (incréments)
def testPotentio():
        l = potentio()
        if l[0] < 341:
                return -1
        if l[0] > 681:
                return 1
        return 0

    

# fonction testant si le string en paramètre se trouve dans la liste de string en paramètre
def testIn(text,l):
        for x in l:
                if x == text:
                        return True
        return False


''' Fonctions de gestion de données '''

# fonction initialisant un fichier csv dans le répertoire courant
def initFile(nom):
        os.system(" >" + nom + ".csv")

# fonction ajoutant un string dans un fichier csv (sans en écraser le contenu)
def addToFile(texte,nom):
        os.system("echo " + texte + ">> " + nom + ".csv")

# fonction récupérant le contenu d'un fichier csv dans une liste ayant pour élément chaque ligne du fichier
def recovery(nom):
        os.system("")

# fonction envoyant un mail au destinataire selon un sujet et un texte donnés en paramètres
def sendMail(destinataire,sujet,texte):
        msg = MIMEMultipart()
        msg['From'] = 'me'
        msg['To'] = 'you'
        msg['Subject'] = sujet
        message = texte
        msg.attach(MIMEText(message))
        mailserver = smtplib.SMTP('smtp.gmail.com', 587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login('vicoqnt@gmail.com', 'ccarre2020')
        mailserver.sendmail('vicoQnt@gmail.com', destinataire , msg.as_string())
        mailserver.quit()
        print("Pas d'erreur")

def csvToPdf2(nom):
        '''config = pdfkit.configuration(wkhtmltopdf='/usr/local/lib/python2.7/$
        pdfkit.from_file('/home/pi/ProjetRasp/Programmes/'+ nom + '.csv','/home$
'''

''' Processus '''

# affichage de la date
def dateThread():
        global killDate
        initScreen(0,0,0)
        now = time.localtime(time.time())
        setTextColor(time.strftime("   %d/%m/%y\n     %H:%M", now),0,0,0)
        while killDate == False:
                now2=time.localtime(time.time())
                if (time.strftime("   %d/%m/%y\n     %H:%M", now2)!=time.strftime("   %d/%m/%y\n     %H:%M", now)):
                        initScreen(0,0,0)
                        setTextColor(time.strftime("   %d/%m/%y\n     %H:%M", now2),0,0,0)
                        now = now2
date_update = threading.Thread(target=dateThread) # variable permettant de lancer le processus

# timer
def timerThread():
    global Tref
    global timer
    timer = 0
    global killTimer
    while (killTimer == False):
        time.sleep(1)
        timer += 1
    kill... = True
timer_update = threading.Thread(target=timerThread) # variable permettant de lancer le processus

# Programme avec boutons (utilisation manuelle)
def bTestThread():
    global killb
    killb = False
    if DEBUG1: print(killb,recoverFile("Lcurrent"))
    while killb == False: # on boucle jusqu'à ce que le processus soit arrêté
        l = set.nameStudent
        i = 0
        while  killb == False:
            initScreen(25,25,25)
            setTextColor("Choisissez \n"+l[i],25,25,25)
            time.sleep(.2)
            a = testSelect() # utiliser thread
            c = testPotentio() # utiliser thread
            while c == 0:
                a = testSelect()
                if a: # bouton select appuyé
                    setTextColor("Validez le choix\n"+l[i],25,25,25) # demande de validation
                    time.sleep(1)
                    a = testSelect()
                    test = 0
                    while test < 10:
                        if a: # bouton select appuyé
                            b = testIn(l[i],recoverFile("Lcurrent")) # teste si l'étudiant i est dans Lcurrent (déjà$
                            if DEBUG1: print("dans Lcurrent?",b)
                            if b: # si l'étudiant est déjà passé
                                accessDenied("4","Deja passe(e)")
                                return False
                            else: # si c'est le premier passage
                                accessGranted(l[i])
                                addToFile(l[i],"Lcurrent")
                                return True
                        test += 1
                        a = testSelect()
                c = testPotentio()
            if c == 0: # si laissé au milieu
                print("retenter la même personne")
            if c == 1: # si tourné vers la droite
                i += 1
                if i >= len(l): # si après incrémentation on dépasse la taille de la liste
                    i -= len(l)
            if c == -1:
                i -= 1 # si après décrémentation on est inférieur à 0
                if i < 0:
                    i += len(l)
    if DEBUG1: print(recoverFile("Lcurrent"))

bTest_update = threading.Thread(target=bTestThread) # variable permettant de lancer le processus

    
# Programme avec carte (utilisation automatique)
def cTestThread():
    initScreen(25,25,25)
    setTextColor("Passez votre \n carte",25,25,25)
    global killc
    killc = False
    while killc == False:
        card = rfid()
        if DEBUG: print("card = ",card)
        id = set.idStudent
        name = set.nameStudent
        i = 0
        while i < len(id):
            if id[i] == card: # test si l'id de la carte correspond à un étudiant
                n = name[i] # n contient le nom associé à la carte
                if testIn(n,recoverFile("Lcurrent")):
                    time.sleep(.5)
                    accessDenied("4","Deja passe(e)")
                    return False
                else:
                    time.sleep(.5)
                    accessGranted(n)
                    addToFile(n,"Lcurrent")
                    return True
            i += 1
            accessDenied("2","Non reconnue")
            break
    return False

cTest_update = threading.Thread(target=cTestThread) # variable permettant de lancer le processus

# fonction lançant le pointage par utilisation de la carte ou des boutons en fonction du choix de l'étudiant
def choice():
    a = testPotentio()
    if a != 0:
        initScreen(25,25,25)
        setTextColor("Recentrez le \n potentiometre",25,25,25)
    while a != 0:
        a = testPotentio()
    initScreen(25,25,25)
    setTextColor("Gauche -> Bouton\nDroite -> carte",25,25,25)
    a = testPotentio()
    while a == 0:
        a = testPotentio()
    if a == -1:
        initScreen(25,25,25)
        setTextColor("Recentrez le \n potentiometre",25,25,25)
        time.sleep(3)
        return bTestThread()
    if a == 1:
        initScreen(25,25,25)
        setTextColor("Recentrez le \n potentiometre",25,25,25)
        time.sleep(3)
        return cTestThread()
