---
video_id: Ekbw28n6IX0
url: https://www.youtube.com/watch?v=Ekbw28n6IX0
title: Regression - Methode der kleinsten Fehlerquadrate
channel: Kurzes Tutorium Statistik
duration: 15:32
language: de
unit: L03
status: OK
---

[00:00] hallo internetstudent herzlich willkommen zum kurzen tutorialum
[00:03] willkommen zum kurzen tutorialum Statistik mein Name ist Matthias Bertel
[00:05] Statistik mein Name ist Matthias Bertel und ich bin Professor für Mathematik und
[00:06] und ich bin Professor für Mathematik und Statistik an der Hochschule für Technik
[00:08] Statistik an der Hochschule für Technik Wirtschaft und Medien in Offenburg in
[00:10] Wirtschaft und Medien in Offenburg in einem anderen Video habe ich bereits
[00:12] einem anderen Video habe ich bereits erklärt wofür wir die
[00:13] erklärt wofür wir die regressionsrechnung brauchen und heute
[00:15] regressionsrechnung brauchen und heute erkläre ich noch das gebräuchlichste
[00:17] erkläre ich noch das gebräuchlichste Verfahren der regressionsrechnung
[00:18] Verfahren der regressionsrechnung nämlich die Methode der kleinsten
[00:20] nämlich die Methode der kleinsten Fehlerquadrate viel Spaß beim
[00:23] Fehlerquadrate viel Spaß beim Zuschauen wozu wir die Regression
[00:26] Zuschauen wozu wir die Regression brauchen habe ich bereits in einem
[00:27] brauchen habe ich bereits in einem anderen Video erklärt in kurz Form geht
[00:30] anderen Video erklärt in kurz Form geht es darum dass wir die Realität so gut
[00:32] es darum dass wir die Realität so gut wie immer nur schnappschussartig
[00:33] wie immer nur schnappschussartig aufnehmen als Beispiel hatten wir
[00:36] aufnehmen als Beispiel hatten wir verschiedene Umsätze die aus
[00:37] verschiedene Umsätze die aus verschiedenen Preisen resultieren
[00:39] verschiedenen Preisen resultieren betrachtet als Messung bekommen wir also
[00:41] betrachtet als Messung bekommen wir also immer diskrete Punkte Wolken für viele
[00:45] immer diskrete Punkte Wolken für viele Analysen also z.B zur Bestimmung von
[00:47] Analysen also z.B zur Bestimmung von maximal oder Minimalwerten
[00:49] maximal oder Minimalwerten Veränderungsraten Nullstellen oder für
[00:52] Veränderungsraten Nullstellen oder für Prognosen brauchen wir aber stetige
[00:54] Prognosen brauchen wir aber stetige Funktionen die Regression verbindet die
[00:57] Funktionen die Regression verbindet die diskreten Messungen mit der für Analysen
[00:59] diskreten Messungen mit der für Analysen wichtigen
[01:02] Tätigkeit durch das Video begkleidet uns
[01:05] Tätigkeit durch das Video begkleidet uns Julius der uns schon erklärt hat wofür
[01:06] Julius der uns schon erklärt hat wofür wir die Regression brauchen um die
[01:08] wir die Regression brauchen um die Rechentechnik zur Bestimmung der
[01:10] Rechentechnik zur Bestimmung der stetigen Funktion nachvollziehen zu
[01:12] stetigen Funktion nachvollziehen zu können sollte man ein paar mathematische
[01:14] können sollte man ein paar mathematische Vorkenntnisse haben nämlich erstens
[01:16] Vorkenntnisse haben nämlich erstens sollte man mit dem summenoperator
[01:18] sollte man mit dem summenoperator umgehen können zweitens sollte man im
[01:20] umgehen können zweitens sollte man im standande sein lineare Gleichungssysteme
[01:22] standande sein lineare Gleichungssysteme zu lösen und drittens sollte man wissen
[01:25] zu lösen und drittens sollte man wissen wie man Funktionen mit mehr als einer
[01:27] wie man Funktionen mit mehr als einer Variable ableitet aber wenn man das so
[01:30] Variable ableitet aber wenn man das so halbwegs blickt ist der Rest kein
[01:32] halbwegs blickt ist der Rest kein Problem
[01:34] mehr beginnen wir einfach mal mit einer
[01:37] mehr beginnen wir einfach mal mit einer Problemstellung die genau wie Julius
[01:39] Problemstellung die genau wie Julius quasi jeden Studenten quält wie viele
[01:42] quasi jeden Studenten quält wie viele Tassen Kaffee brauche ich für eine
[01:45] Tassen Kaffee brauche ich für eine Lerneinheit sagen wir Julius hat
[01:47] Lerneinheit sagen wir Julius hat festgestellt dass wenn er eine Stunde
[01:49] festgestellt dass wenn er eine Stunde lernt mit 1,5 Tassen Kaffee auskommt bei
[01:52] lernt mit 1,5 Tassen Kaffee auskommt bei 3 Stunden braucht er zwei Tassen Kaffee
[01:55] 3 Stunden braucht er zwei Tassen Kaffee und wenn er vier Stunden lernt sind es
[01:57] und wenn er vier Stunden lernt sind es vier Tassen er hat also drei Messpunkte
[02:00] vier Tassen er hat also drei Messpunkte und die habe ich direkt in ein Diagramm
[02:03] und die habe ich direkt in ein Diagramm eingetragen jetzt sucht Julius hier zu
[02:06] eingetragen jetzt sucht Julius hier zu eine gerade um abzuschätzen wie viele
[02:08] eine gerade um abzuschätzen wie viele Tassen Kaffee er brauchen wird wenn er
[02:10] Tassen Kaffee er brauchen wird wenn er demnächst 5 Stunden lernen
[02:12] demnächst 5 Stunden lernen muss es kann im vorliegenden Fall keine
[02:16] muss es kann im vorliegenden Fall keine gerade geben die perfekt durch alle drei
[02:18] gerade geben die perfekt durch alle drei Punkte geht egal wie wir die gerade
[02:20] Punkte geht egal wie wir die gerade legen irgendwelche Abweichungen zwischen
[02:22] legen irgendwelche Abweichungen zwischen Messpunkten und gerade gibt es immer mal
[02:25] Messpunkten und gerade gibt es immer mal sind sie größer und mal kleiner unser
[02:28] sind sie größer und mal kleiner unser Ziel sollte es also sein die
[02:30] Ziel sollte es also sein die Abweichungen so klein wie möglich zu
[02:32] Abweichungen so klein wie möglich zu machen eine Gerade hat immer die
[02:34] machen eine Gerade hat immer die Struktur y= A + B mal x und es hängt
[02:39] Struktur y= A + B mal x und es hängt immer von A und B ab wo und wie die
[02:41] immer von A und B ab wo und wie die gerade liegt mache ich z.B B größer so
[02:45] gerade liegt mache ich z.B B größer so wird die Steigung steiler mache ich B
[02:47] wird die Steigung steiler mache ich B kleiner wird sie flacher mache ich a
[02:50] kleiner wird sie flacher mache ich a größer verschiebt sich die gerade nach
[02:52] größer verschiebt sich die gerade nach oben mache ich a kleiner verschiebt sie
[02:54] oben mache ich a kleiner verschiebt sie sich nach
[02:55] sich nach unten das merken wir uns schon mal die
[02:58] unten das merken wir uns schon mal die Abweichung hängt von dem Parameter A und
[03:00] Abweichung hängt von dem Parameter A und B der Funktion y = a + b mal x ab und
[03:04] B der Funktion y = a + b mal x ab und sie soll möglichst klein
[03:06] sie soll möglichst klein [Musik]
[03:08] [Musik] sein aber was ist eigentlich die
[03:10] sein aber was ist eigentlich die Abweichung zwischen den Punkten und der
[03:12] Abweichung zwischen den Punkten und der Geraden tatsächlich gibt es viele
[03:14] Geraden tatsächlich gibt es viele Möglichkeiten die Abweichung zu
[03:16] Möglichkeiten die Abweichung zu bestimmen aber bei der Methode der
[03:18] bestimmen aber bei der Methode der kleinsten Fehlerquadrate wählt man eine
[03:19] kleinsten Fehlerquadrate wählt man eine ganz bestimmte und zwar sagt man
[03:22] ganz bestimmte und zwar sagt man folgendes bei uns soll x für die
[03:24] folgendes bei uns soll x für die Lerndauer und Y für die Zahl der
[03:26] Lerndauer und Y für die Zahl der getrunkenen Tassen Kaffee stehen habe
[03:29] getrunkenen Tassen Kaffee stehen habe ich für die gerade eine bestimmte
[03:30] ich für die gerade eine bestimmte Funktion gegeben sagen wir mal y= 0,7 +
[03:34] Funktion gegeben sagen wir mal y= 0,7 + 0,6* X dann würde ich bei x = 1 als
[03:39] 0,6* X dann würde ich bei x = 1 als theoretischen y Wert 0,7 + 0,6 x 1 = 1,3
[03:44] theoretischen y Wert 0,7 + 0,6 x 1 = 1,3 erhalten tatsächlich habe ich als
[03:46] erhalten tatsächlich habe ich als Messwert bei x = 1 aber ein Y von 1,5
[03:49] Messwert bei x = 1 aber ein Y von 1,5 gehabt die Abweichung oder der Fehler
[03:52] gehabt die Abweichung oder der Fehler zwischen dem tatsächlich g messenden y
[03:54] zwischen dem tatsächlich g messenden y und dem y nach der Formel ist also 1,5 -
[03:58] und dem y nach der Formel ist also 1,5 - 1,3 =
[04:02] 1,3 = 0,2 beim zweiten x-Wert nämlich x = 3
[04:05] 0,2 beim zweiten x-Wert nämlich x = 3 bekäme ich bei der gegebenen Funktion y
[04:08] bekäme ich bei der gegebenen Funktion y = 2,5 der Fehler beträgt hier also 2 -
[04:12] = 2,5 der Fehler beträgt hier also 2 - 2,5 = -0,5 und beim letzten x-Wert bekme
[04:16] 2,5 = -0,5 und beim letzten x-Wert bekme ich einen Funktionswert von 3,1 weil der
[04:18] ich einen Funktionswert von 3,1 weil der wirkliche Messwert aber 4 ist beträgt
[04:20] wirkliche Messwert aber 4 ist beträgt der Fehler hier
[04:23] der Fehler hier 0,9 um die Gesamtabweichung der Geraden
[04:26] 0,9 um die Gesamtabweichung der Geraden von der Punktewolke zu berechnen könnten
[04:28] von der Punktewolke zu berechnen könnten wir jetzt einfach alle Einzel Fehler
[04:30] wir jetzt einfach alle Einzel Fehler addieren aber da würden wir wenn wir
[04:32] addieren aber da würden wir wenn wir gleich nach der Funktion suchen bei der
[04:34] gleich nach der Funktion suchen bei der der Gesamtfehler möglichst klein wird
[04:36] der Gesamtfehler möglichst klein wird ein Problem kriegen wenn wir sagen die
[04:39] ein Problem kriegen wenn wir sagen die Summe der Messwerte minus Funktionswerte
[04:41] Summe der Messwerte minus Funktionswerte soll möglichst klein sein würde das
[04:43] soll möglichst klein sein würde das bedeuten dass die gerade irgendwo bei
[04:45] bedeuten dass die gerade irgendwo bei Plus unendlich liegen müsste denn dann
[04:47] Plus unendlich liegen müsste denn dann wäre die Differenz zwischen Punkten und
[04:49] wäre die Differenz zwischen Punkten und gerade minus unendlich also möglichst
[04:53] gerade minus unendlich also möglichst klein was wir eigentlich mit Abweichung
[04:56] klein was wir eigentlich mit Abweichung meinen ist wir wollen einen Gesamtfehler
[04:58] meinen ist wir wollen einen Gesamtfehler möglichst in der Nähe von
[05:00] möglichst in der Nähe von die gerade zu irgendwo zwischen den
[05:02] die gerade zu irgendwo zwischen den Punkten
[05:02] Punkten [Musik]
[05:04] [Musik] liegen um das rechnerisch zu
[05:06] liegen um das rechnerisch zu berücksichtigen könnte man einfach den
[05:08] berücksichtigen könnte man einfach den Betrag der Fehler bilden das macht man
[05:11] Betrag der Fehler bilden das macht man aber auch nicht weil sich mit der
[05:12] aber auch nicht weil sich mit der Betragsfunktion einfach nicht sonderlich
[05:14] Betragsfunktion einfach nicht sonderlich gut rechnen lässt stattdessen nimmt man
[05:17] gut rechnen lässt stattdessen nimmt man daher das Quadrat des Fehlers dann wird
[05:19] daher das Quadrat des Fehlers dann wird aus 0,2 eine 0,04 aus -0,5 wird 0,25 als
[05:25] aus 0,2 eine 0,04 aus -0,5 wird 0,25 als 0,9 wir
[05:26] 0,9 wir 0,81 und weil wir das Quadrat wählen
[05:29] 0,81 und weil wir das Quadrat wählen heißt das Verfahren auch Methode der
[05:31] heißt das Verfahren auch Methode der kleinsten Fehlerquadrate addieren wir
[05:34] kleinsten Fehlerquadrate addieren wir hier die quadrierten Fehler kommen wir
[05:35] hier die quadrierten Fehler kommen wir auf eine Gesamtabweichung von
[05:38] auf eine Gesamtabweichung von 1,1 und auch das merken wir uns die
[05:41] 1,1 und auch das merken wir uns die Abweichung berechnen wir als Summe der
[05:44] Abweichung berechnen wir als Summe der quadrierten Differenzen zwischen
[05:45] quadrierten Differenzen zwischen Messwerten Yi und Werten der Funktion y
[05:49] Messwerten Yi und Werten der Funktion y = fon XI wobei im einfachsten Fall fon
[05:52] = fon XI wobei im einfachsten Fall fon XI = A + B mal XI
[05:56] XI = A + B mal XI [Musik]
[05:58] [Musik] ist 1,1 haben wir bei a = 0,7 und b= 0,6
[06:03] ist 1,1 haben wir bei a = 0,7 und b= 0,6 bekommen aber die Frage ist natürlich ob
[06:05] bekommen aber die Frage ist natürlich ob bei anderen Werten die Gesamtabweichung
[06:08] bei anderen Werten die Gesamtabweichung nicht doch noch kleiner
[06:10] nicht doch noch kleiner wird etwas platzsparender und allgemein
[06:13] wird etwas platzsparender und allgemein geschrieben ist die
[06:14] geschrieben ist die quadratfehlerfunktion die Summe aller
[06:17] quadratfehlerfunktion die Summe aller yi- FXI ins Quadrat also die Summe über
[06:21] yi- FXI ins Quadrat also die Summe über Yi - A- B mal XI Quad denn die Funktion
[06:25] Yi - A- B mal XI Quad denn die Funktion f von XI ist ja A + b* XI und die ziehen
[06:28] f von XI ist ja A + b* XI und die ziehen wir eben von y ab das große e was ich
[06:31] wir eben von y ab das große e was ich ganz vorne hin geschrieben habe steht
[06:33] ganz vorne hin geschrieben habe steht für error also
[06:36] Fehler die Abweichung soll möglichst
[06:39] Fehler die Abweichung soll möglichst klein sein heißt wir suchen das Minimum
[06:41] klein sein heißt wir suchen das Minimum der fehlerfunktion wie findet man das
[06:43] der fehlerfunktion wie findet man das Minimum einer Funktion richtig wir
[06:45] Minimum einer Funktion richtig wir müssen die Funktion ableiten und die
[06:47] müssen die Funktion ableiten und die erste Ableitung gleich 0 setzen aber
[06:50] erste Ableitung gleich 0 setzen aber wichtig ist der Fehler oder die
[06:52] wichtig ist der Fehler oder die Abweichung hängt von A und B ab wie es
[06:56] Abweichung hängt von A und B ab wie es ja auch hier in der Formulierung steht
[06:58] ja auch hier in der Formulierung steht abgeleitet werden muss also nach A und B
[07:00] abgeleitet werden muss also nach A und B die x i und Yi sind Messwerte also
[07:04] die x i und Yi sind Messwerte also feststehende Zahlen aus unserer
[07:08] Datentabelle die Ableitung einer
[07:11] Datentabelle die Ableitung einer Funktion mit mehreren Variablen
[07:12] Funktion mit mehreren Variablen funktioniert so dass ich einzeln nach
[07:14] funktioniert so dass ich einzeln nach jeder variable
[07:16] jeder variable ableite was auch ab und zu zur
[07:18] ableite was auch ab und zu zur Verwirrung führt ist das Summenzeichen
[07:20] Verwirrung führt ist das Summenzeichen aber nichts ist einfacher als das
[07:22] aber nichts ist einfacher als das Ableiten einer Summe denn die Ableitung
[07:25] Ableiten einer Summe denn die Ableitung einer Summe ist die Summe der
[07:27] einer Summe ist die Summe der Ableitungen nehmen wir mal als einfaches
[07:29] Ableitungen nehmen wir mal als einfaches Beispiel die Summe von i = 1 bis 3 über
[07:32] Beispiel die Summe von i = 1 bis 3 über XI mal a und zwar mit den selben xis die
[07:35] XI mal a und zwar mit den selben xis die wir bei unserem kaffprem verwenden also
[07:38] wir bei unserem kaffprem verwenden also X1 = 1 X2 = 2 und X3 =
[07:42] X1 = 1 X2 = 2 und X3 = 4 ausgeschrieben lautet die Funktion
[07:45] 4 ausgeschrieben lautet die Funktion also 1 x A + 3 x A + 4 x
[07:49] also 1 x A + 3 x A + 4 x a wenn wir jetzt nach a ableiten
[07:52] a wenn wir jetzt nach a ableiten bekommen wir e von A = 1 A nach a
[07:55] bekommen wir e von A = 1 A nach a abgeleitet ist 1 dann + Ableitung von 3
[07:59] abgeleitet ist 1 dann + Ableitung von 3 nach a also 3 plus Ableitung von 4A nach
[08:02] nach a also 3 plus Ableitung von 4A nach a also 4 insgesamt also die Summe über
[08:06] a also 4 insgesamt also die Summe über allen
[08:08] allen XI genau das bekommen wir auch wenn wir
[08:11] XI genau das bekommen wir auch wenn wir uns einfach den Term XI mal a anschauen
[08:14] uns einfach den Term XI mal a anschauen wenn wir den nach a ableiten bleibt XI
[08:16] wenn wir den nach a ableiten bleibt XI übrig denn a kommt in der ersten Potenz
[08:18] übrig denn a kommt in der ersten Potenz vor wird also in der ersten Ableitung
[08:20] vor wird also in der ersten Ableitung selbst zu ein kurz gefasst wir brauchen
[08:24] selbst zu ein kurz gefasst wir brauchen uns bei der Ableitung also gar nicht so
[08:25] uns bei der Ableitung also gar nicht so tierisch um das Summenzeichen zu kümmern
[08:27] tierisch um das Summenzeichen zu kümmern und konzentrieren uns einfach auf den
[08:29] und konzentrieren uns einfach auf den inneren
[08:31] inneren term zurück zu unserer eigentlichen
[08:33] term zurück zu unserer eigentlichen fehlergleichung bei der Ableitung nach a
[08:36] fehlergleichung bei der Ableitung nach a brauche ich die Kettenregel die äußere
[08:38] brauche ich die Kettenregel die äußere Funktion ist ein Quadrat die Ableitung
[08:41] Funktion ist ein Quadrat die Ableitung daher zweimal der Ausdruck in der
[08:43] daher zweimal der Ausdruck in der Klammer die Ableitung der inneren
[08:46] Klammer die Ableitung der inneren Funktion ist einfach
[08:49] Funktion ist einfach -1 die Ableitung nach B funktioniert
[08:52] -1 die Ableitung nach B funktioniert analog äußere Ableitung also zweimal der
[08:55] analog äußere Ableitung also zweimal der Term in der Klammer und die Ableitung
[08:58] Term in der Klammer und die Ableitung der in ktion ist hier -
[09:01] der in ktion ist hier - XI und für das Minimum müssen beide
[09:04] XI und für das Minimum müssen beide partiellen Ableitungen gleich 0
[09:06] partiellen Ableitungen gleich 0 [Musik]
[09:08] [Musik] sein das forme ich jetzt alles noch so
[09:11] sein das forme ich jetzt alles noch so ein bisschen um die Z ziehe ich weil ein
[09:14] ein bisschen um die Z ziehe ich weil ein konstanter Faktor ist jeweils vor die
[09:16] konstanter Faktor ist jeweils vor die Summe aber ich teile beide Seiten auch
[09:18] Summe aber ich teile beide Seiten auch direkt durch 2 dann bin ich die Z los
[09:20] direkt durch 2 dann bin ich die Z los denn 0 dur 2 ist immer noch 0 dann
[09:23] denn 0 dur 2 ist immer noch 0 dann multipliziere ich in der oberen Summe
[09:26] multipliziere ich in der oberen Summe erstmal die Klammern aus da bekomme ich
[09:29] erstmal die Klammern aus da bekomme ich y + A + b*
[09:33] y + A + b* XI in der unteren Summe mache ich das
[09:36] XI in der unteren Summe mache ich das gleiche und erhalte - XI mal Yi + A* XI
[09:41] gleiche und erhalte - XI mal Yi + A* XI + b*
[09:46] xi² als nächstes Spalte ich die Summe auf und schreibe den summenoperator
[09:50] auf und schreibe den summenoperator separat für alle summanten eigentlich
[09:52] separat für alle summanten eigentlich müsste man um die einzelnen summenterme
[09:54] müsste man um die einzelnen summenterme noch Klammern setzen Klammern sind aber
[09:56] noch Klammern setzen Klammern sind aber aus deswegen lasse ich das der
[09:57] aus deswegen lasse ich das der Einfachheit halbe mal weg fehlen noch
[09:59] Einfachheit halbe mal weg fehlen noch zwei Schritte ich bringe in der oberen
[10:02] zwei Schritte ich bringe in der oberen Gleichung die Summe Yi auf die rechte
[10:04] Gleichung die Summe Yi auf die rechte Seite und in der unteren Gleichung die
[10:06] Seite und in der unteren Gleichung die Summe XI mal Yi ebenfalls auf die rechte
[10:10] Summe XI mal Yi ebenfalls auf die rechte Seite als letztes ziehe ich die
[10:13] Seite als letztes ziehe ich die Parameter a und b jeweils vor die Summe
[10:15] Parameter a und b jeweils vor die Summe das kann ich weil die ja als Faktoren
[10:17] das kann ich weil die ja als Faktoren unter der Summe stehen aber mit dem
[10:19] unter der Summe stehen aber mit dem summenindex i nichts zu tun
[10:22] summenindex i nichts zu tun haben damit haben wir ein
[10:24] haben damit haben wir ein Gleichungssystem erhalten das sieht zwar
[10:26] Gleichungssystem erhalten das sieht zwar ganz schön kompliziert aus ist es aber
[10:27] ganz schön kompliziert aus ist es aber nicht denn die ganzen Summen Terme
[10:29] nicht denn die ganzen Summen Terme beziehen sich auf unsere Messwerte die
[10:31] beziehen sich auf unsere Messwerte die einfach nur irgendwie addiert werden
[10:33] einfach nur irgendwie addiert werden müssen am einfachsten ist der summenterm
[10:36] müssen am einfachsten ist der summenterm links oben hier wird a dreimal zu sich
[10:38] links oben hier wird a dreimal zu sich selbst addiert denn der Index i läuft ja
[10:40] selbst addiert denn der Index i läuft ja von 1 bis 3 deswegen kann ich das
[10:43] von 1 bis 3 deswegen kann ich das Umschreiben zu A* 3 als nächstes die
[10:46] Umschreiben zu A* 3 als nächstes die Summe über alle XI die ist ganz einfach
[10:49] Summe über alle XI die ist ganz einfach 1 + 3 + 4 also
[10:53] 1 + 3 + 4 also 8 die Summe über alle y e ist 1,5 + 2 +
[10:58] 8 die Summe über alle y e ist 1,5 + 2 + 4
[11:00] 4 7,5 auch das tausche ich aus dann
[11:03] 7,5 auch das tausche ich aus dann brauche ich noch die Summe der
[11:05] brauche ich noch die Summe der quadrierten XI die kenne ich noch nicht
[11:07] quadrierten XI die kenne ich noch nicht kann ich aber einfach ausrechnen und
[11:09] kann ich aber einfach ausrechnen und komme auf
[11:11] komme auf 26 und zuletzt noch die Summe aller XI
[11:14] 26 und zuletzt noch die Summe aller XI mal Yi auch das muss ich noch ausrechnen
[11:17] mal Yi auch das muss ich noch ausrechnen kann ich aber unterhalte
[11:19] kann ich aber unterhalte [Musik]
[11:22] [Musik] 23,5 und jetzt ist offensichtlich dass
[11:25] 23,5 und jetzt ist offensichtlich dass wir ein völlig einfaches lineares
[11:27] wir ein völlig einfaches lineares Gleichungssystem vor uns haben was wir
[11:28] Gleichungssystem vor uns haben was wir z. mit Hilfe des gausalgorithmus lösen
[11:31] z. mit Hilfe des gausalgorithmus lösen können wenn wir das machen finden wir
[11:33] können wenn wir das machen finden wir raus a muss 0,5 sein und B
[11:38] 0,75 damit haben wir die gerade bestimmt und können ganz einfach prognostizieren
[11:42] und können ganz einfach prognostizieren bei fünf Lernstunden bräuchten wir etwa
[11:45] bei fünf Lernstunden bräuchten wir etwa 0,5 + 0,75 x 5 = 4,25
[11:53] tassenkaffee die Methode der kleinsten Fehlerquadrate funktioniert oft auch bei
[11:57] Fehlerquadrate funktioniert oft auch bei nichtlinearen regussionsansätzen
[12:00] nichtlinearen regussionsansätzen nehmen wir z.B aus irgendeinem Grund an
[12:02] nehmen wir z.B aus irgendeinem Grund an dass der Zusammenhang zwischen zwei
[12:04] dass der Zusammenhang zwischen zwei Merkmalen stark überlinear ist also
[12:06] Merkmalen stark überlinear ist also vielleicht sogar exponentiell dann
[12:09] vielleicht sogar exponentiell dann würden wir als regressionsansatz eine
[12:11] würden wir als regressionsansatz eine Exponentialfunktion nehmen z.B y= a mal
[12:15] Exponentialfunktion nehmen z.B y= a mal e hoch B mal x und versuchen für diesen
[12:18] e hoch B mal x und versuchen für diesen Ansatz die Werte A und B zu bestimmen
[12:21] Ansatz die Werte A und B zu bestimmen hier brauchen wir aber einen kleinen
[12:23] hier brauchen wir aber einen kleinen Trick für die Methode der kleinsten
[12:26] Trick für die Methode der kleinsten Fehlerquadrate ist es nämlich wichtig
[12:28] Fehlerquadrate ist es nämlich wichtig dass die Parameter
[12:29] dass die Parameter nur in ihrer ersten Potenz und
[12:31] nur in ihrer ersten Potenz und untereinander nur Additiv verknüpft
[12:33] untereinander nur Additiv verknüpft vorkommen ist hier beides nicht der Fall
[12:36] vorkommen ist hier beides nicht der Fall B steht dem Exponenten und zwischen a
[12:38] B steht dem Exponenten und zwischen a und der efunktion steht ein mallzeichen
[12:41] und der efunktion steht ein mallzeichen aber das können wir sehr schnell
[12:43] aber das können wir sehr schnell korrigieren indem wir den
[12:44] korrigieren indem wir den regressionansatz einfach logarithmieren
[12:47] regressionansatz einfach logarithmieren dann wird daraus lnyy = LNA + b* x zur
[12:52] dann wird daraus lnyy = LNA + b* x zur schreibvereinfachung vereinbaren wir
[12:54] schreibvereinfachung vereinbaren wir jetzt noch lnyy soll y Stern heißen und
[12:57] jetzt noch lnyy soll y Stern heißen und LNA nennen wir a sten und jetzt kommen
[13:01] LNA nennen wir a sten und jetzt kommen die beiden Parameter in ihrer ersten
[13:03] die beiden Parameter in ihrer ersten Potenz vor und zwischen ihnen steht ein
[13:05] Potenz vor und zwischen ihnen steht ein Plus so wie es sein
[13:09] soll und jetzt funktioniert alles wie vorher fehlerfunktion bilden nach dem
[13:15] vorher fehlerfunktion bilden nach dem Parametern ableiten Null
[13:19] Parametern ableiten Null setzen zum Gleichungssystem umformen und
[13:22] setzen zum Gleichungssystem umformen und dann die Werte
[13:24] dann die Werte einsetzen Summe XI ist einfach das
[13:27] einsetzen Summe XI ist einfach das ergibt 9,5
[13:29] ergibt 9,5 der nächste term lautet y i Stern y
[13:33] der nächste term lautet y i Stern y Stern hieß aber Logarithmus bilden wir
[13:36] Stern hieß aber Logarithmus bilden wir brauchen jetzt also die Logarithmen der
[13:38] brauchen jetzt also die Logarithmen der y i auch das kriegen wir hin der
[13:40] y i auch das kriegen wir hin der Logarithmus von 3 ist etwa
[13:42] Logarithmus von 3 ist etwa 1,10 und so weiter und wenn wir alle
[13:45] 1,10 und so weiter und wenn wir alle Logarithmen haben wen wir die Summe und
[13:47] Logarithmen haben wen wir die Summe und kommen auf etwa
[13:49] kommen auf etwa [Musik]
[13:50] [Musik] 7,37 dann noch die XI Quadrat die
[13:53] 7,37 dann noch die XI Quadrat die ergeben in der Summe 27,25
[13:59] und XI mal y i Stern dran denken y Stern
[14:03] und XI mal y i Stern dran denken y Stern sind die logarithmierten Messwerte aber
[14:05] sind die logarithmierten Messwerte aber auch das ist kein großer Aufwand und wir
[14:07] auch das ist kein großer Aufwand und wir erhalten etwa
[14:09] erhalten etwa 20,04 alles einsetzen und
[14:11] 20,04 alles einsetzen und Gleichungssystem
[14:14] Gleichungssystem lösen allerdings erhalten wir hier a
[14:17] lösen allerdings erhalten wir hier a stern und das war ja der Logarithmus von
[14:19] stern und das war ja der Logarithmus von A wir suchen aber a müssen also einfach
[14:21] A wir suchen aber a müssen also einfach e hoch a ST berechnen wir bekommen a ist
[14:25] e hoch a ST berechnen wir bekommen a ist etwa 1,75 und bei B mussten wir nichts
[14:28] etwa 1,75 und bei B mussten wir nichts weiter Maen B ist
[14:31] 0,54 und so sehe die
[14:34] 0,54 und so sehe die regressionsrechnerisch bestimmte
[14:36] regressionsrechnerisch bestimmte Exponentialfunktion
[14:40] aus zusammenfassend funktioniert die Methode der kleinsten Fehlerquadrate
[14:45] Methode der kleinsten Fehlerquadrate immer nach dem Schema fehlerfunktion
[14:47] immer nach dem Schema fehlerfunktion aufstellen ableiten und null setzen
[14:50] aufstellen ableiten und null setzen umstellen Summen berechnen und einsetzen
[14:53] umstellen Summen berechnen und einsetzen und zu guter Letzt das Gleichungssystem
[14:56] und zu guter Letzt das Gleichungssystem lösen
[14:59] das war meine Erklärung zur Methode der
[15:02] das war meine Erklärung zur Methode der kleinsten Fehlerquadrate und es war auch
[15:04] kleinsten Fehlerquadrate und es war auch das erste Video in dem ich relativ viel
[15:06] das erste Video in dem ich relativ viel gerechnet habe eigentlich wollte ich
[15:08] gerechnet habe eigentlich wollte ich alle meine Videos darauf beschränken zu
[15:10] alle meine Videos darauf beschränken zu erläutern wofür wir die verschiedenen
[15:11] erläutern wofür wir die verschiedenen statistischen Verfahren brauchen allein
[15:13] statistischen Verfahren brauchen allein weil es oft auch schwierig ist die ganze
[15:15] weil es oft auch schwierig ist die ganze Rechnung in ein 10 Minuten Video
[15:17] Rechnung in ein 10 Minuten Video hineinzuquetschen aber unabhängig davon
[15:19] hineinzuquetschen aber unabhängig davon es wurde relativ oft gewünscht deswegen
[15:22] es wurde relativ oft gewünscht deswegen lasst mich wissen ob es was bringt und
[15:24] lasst mich wissen ob es was bringt und ob es ein nützliches Video war ansonsten
[15:26] ob es ein nützliches Video war ansonsten vielen Dank fürs zuschauen und bis zum
[15:28] vielen Dank fürs zuschauen und bis zum näch mal
