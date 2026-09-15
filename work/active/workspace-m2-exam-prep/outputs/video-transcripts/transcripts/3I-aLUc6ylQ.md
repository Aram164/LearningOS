---
video_id: 3I-aLUc6ylQ
url: https://www.youtube.com/watch?v=3I-aLUc6ylQ
title: Streudiagramm & Korrelationskoeffizient einfach erklärt – anschaulich mit Alwins Restaurant
channel: Kurzes Tutorium Statistik
duration: 9:09
language: de
unit: L03
status: OK
---

[00:02] In diesem Video geht es um den metrischen Korrelationskoeffizienten,
[00:06] metrischen Korrelationskoeffizienten, auch Korrelationskoeffizient nach
[00:09] auch Korrelationskoeffizient nach Piercen oder Produktmomentkorrelation
[00:11] Piercen oder Produktmomentkorrelation [musik] genannt. Ich werde
[00:13] [musik] genannt. Ich werde veranschaulichen, was man von der
[00:14] veranschaulichen, was man von der Berechnung hat, die Rechenidee erläutern
[00:17] Berechnung hat, die Rechenidee erläutern und auch die Rechnung vorführen,
[00:19] und auch die Rechnung vorführen, wägleich man die heute natürlich in
[00:21] wägleich man die heute natürlich in aller Regel durch eine Software
[00:23] aller Regel durch eine Software erledigen lässt. Hierzu besuchen wir
[00:26] erledigen lässt. Hierzu besuchen wir Alvins Restaurant. Das ist nämlich
[00:28] Alvins Restaurant. Das ist nämlich beliebt und zwar so sehr, dass man ohne
[00:30] beliebt und zwar so sehr, dass man ohne Reservierung fast nie einen Platz
[00:33] Reservierung fast nie einen Platz bekommt.
[00:34] bekommt. Wenn Alwin eine Reservierung
[00:35] Wenn Alwin eine Reservierung entgegennimmt, plant er für jeden Tisch
[00:38] entgegennimmt, plant er für jeden Tisch 90 Minuten ein.
[00:41] 90 Minuten ein. Allerdings sind seine Gäste durchaus
[00:43] Allerdings sind seine Gäste durchaus unterschiedlich. Manche essen schnell
[00:46] unterschiedlich. Manche essen schnell und verlassen bereits nach kurzer Zeit
[00:48] und verlassen bereits nach kurzer Zeit das Restaurant wieder. Andere dehnen ihr
[00:51] das Restaurant wieder. Andere dehnen ihr Essen hingegen deutlich länger aus.
[00:55] Essen hingegen deutlich länger aus. Das ist ein Problem, denn essen die
[00:57] Das ist ein Problem, denn essen die Gäste schnell, hätte Alwien ohne
[00:59] Gäste schnell, hätte Alwien ohne weiteres noch eine Reservierung für den
[01:01] weiteres noch eine Reservierung für den Tisch entgegennehmen können, der
[01:02] Tisch entgegennehmen können, der stattdessen jetzt leer steht.
[01:05] stattdessen jetzt leer steht. Essen die Gäste hingegen langsam,
[01:07] Essen die Gäste hingegen langsam, erscheint bereits die
[01:08] erscheint bereits die Nachfolgereservierung,
[01:10] Nachfolgereservierung, während der Tisch noch gar nicht wieder
[01:11] während der Tisch noch gar nicht wieder frei ist.
[01:14] frei ist. Alwien sucht deswegen nach einer
[01:16] Alwien sucht deswegen nach einer Möglichkeit besser einzuschätzen, wie
[01:18] Möglichkeit besser einzuschätzen, wie lange Gäste für das Essen in Anspruch
[01:20] lange Gäste für das Essen in Anspruch nehmen. Weil er gerne systematisch
[01:23] nehmen. Weil er gerne systematisch vorgeht, notiert er für eine Weile, wie
[01:25] vorgeht, notiert er für eine Weile, wie lange Besucher den Tisch tatsächlich in
[01:27] lange Besucher den Tisch tatsächlich in Anspruch genommen haben. Gemeinsam mit
[01:30] Anspruch genommen haben. Gemeinsam mit den Informationen zu den Reservierungen
[01:32] den Informationen zu den Reservierungen erhält er damit diesen Datensatz.
[01:37] Alwien hat nun den Verdacht, dass man vielleicht aus der Uhrzeit oder der Zahl
[01:41] vielleicht aus der Uhrzeit oder der Zahl der Gäste in etwa erkennen kann, wie
[01:44] der Gäste in etwa erkennen kann, wie lange der Tisch in Anspruch genommen
[01:46] lange der Tisch in Anspruch genommen wird.
[01:47] wird. Er veranschaulicht das in einem
[01:49] Er veranschaulicht das in einem Diagramm, indem er auf der X-Achse die
[01:51] Diagramm, indem er auf der X-Achse die Uhrzeit abträgt und auf der Y-Achse die
[01:53] Uhrzeit abträgt und auf der Y-Achse die Dauer des Besuchs und für jede
[01:56] Dauer des Besuchs und für jede Reservierung eine Markierung an der
[01:57] Reservierung eine Markierung an der Stelle macht, die der jeweiligen Uhrzeit
[02:00] Stelle macht, die der jeweiligen Uhrzeit und Dauer entspricht.
[02:02] und Dauer entspricht. Die erste Markierung also bei 1780,
[02:06] Die erste Markierung also bei 1780, die zweite bei 12:30 und 75 Minuten und
[02:10] die zweite bei 12:30 und 75 Minuten und so weiter. [musik]
[02:17] Danach macht ihr dasselbe erneut. Diesmal aber für die Zahl der Gäste und
[02:21] Diesmal aber für die Zahl der Gäste und die Belegungsdauer des Tischs.
[02:30] Solche Diagramme, die zwei Merkmale auf
[02:33] Solche Diagramme, die zwei Merkmale auf diese Art gegenüberstellen, heißen
[02:36] diese Art gegenüberstellen, heißen Streudiagramme.
[02:38] Streudiagramme. Streudiagramme helfen schnell einen
[02:40] Streudiagramme helfen schnell einen ersten Eindruck über eventuelle
[02:41] ersten Eindruck über eventuelle Zusammenhänge zu bekommen. Z.B. sehen
[02:44] Zusammenhänge zu bekommen. Z.B. sehen wir im linken Diagramm, dass es zu
[02:46] wir im linken Diagramm, dass es zu frühen genauso wie zu späten Tageszeiten
[02:49] frühen genauso wie zu späten Tageszeiten Reservierungen gibt, die mal kurz und
[02:51] Reservierungen gibt, die mal kurz und mal lang einzelne Tische belegen,
[02:54] mal lang einzelne Tische belegen, weswegen die Uhrzeit der Reservierung
[02:55] weswegen die Uhrzeit der Reservierung wohl kein guter Indikator für die
[02:57] wohl kein guter Indikator für die Besuchsdauer ist.
[02:59] Besuchsdauer ist. Schauen wir uns hingegen das Diagramm
[03:01] Schauen wir uns hingegen das Diagramm zur Zahl der Gäste und der Dauer [musik]
[03:03] zur Zahl der Gäste und der Dauer [musik] an, erkennen wir, dass kleine
[03:05] an, erkennen wir, dass kleine Personengruppen Tische zumindest
[03:07] Personengruppen Tische zumindest tendenziell kurz belegen, während
[03:09] tendenziell kurz belegen, während größere Personengruppen länger bleiben.
[03:12] größere Personengruppen länger bleiben. Wenn sich dieser Zusammenhang auch
[03:14] Wenn sich dieser Zusammenhang auch längerfristig bewahrheitet, hätte Alwin
[03:16] längerfristig bewahrheitet, hätte Alwin eine gute Möglichkeit gefunden, die
[03:19] eine gute Möglichkeit gefunden, die Dauer der Tischbelegung besser
[03:20] Dauer der Tischbelegung besser abzuschätzen.
[03:23] Natürlich wird man selten so viel Glück wie Alwin haben und direkt bei der
[03:28] wie Alwin haben und direkt bei der Auswertung von zwei Merkmalspaaren einen
[03:30] Auswertung von zwei Merkmalspaaren einen guten Zusammenhang finden. Wenn man
[03:33] guten Zusammenhang finden. Wenn man sehr, sehr viele Merkmalspaare
[03:34] sehr, sehr viele Merkmalspaare untersuchen muss oder möchte, hätte man
[03:37] untersuchen muss oder möchte, hätte man natürlich auch viele Streudiagramme zu
[03:39] natürlich auch viele Streudiagramme zu zeichnen und auszuwerten.
[03:41] zeichnen und auszuwerten. In so einem Fall wäre es doch nützlich,
[03:44] In so einem Fall wäre es doch nützlich, wenn man statt zu zeichnen schnell eine
[03:46] wenn man statt zu zeichnen schnell eine Kennzahl berechnen könnte, die ebenfalls
[03:49] Kennzahl berechnen könnte, die ebenfalls ein Indiz für einen Zusammenhang
[03:51] ein Indiz für einen Zusammenhang liefert. So könnte man aus der Vielzahl
[03:53] liefert. So könnte man aus der Vielzahl der Möglichkeiten schnell die
[03:55] der Möglichkeiten schnell die herausfinden, deren detailliertere
[03:57] herausfinden, deren detailliertere Untersuchung am lohnenswertesten
[03:59] Untersuchung am lohnenswertesten erscheint. Genau das macht der metrische
[04:02] erscheint. Genau das macht der metrische Korrelationskoeffizient.
[04:04] Korrelationskoeffizient. Der hat ein kleines R als Symbol und ist
[04:06] Der hat ein kleines R als Symbol und ist eine Kennzahl, die angibt, wie gut die
[04:09] eine Kennzahl, die angibt, wie gut die Punkte in einem Streudiagramm [musik]
[04:11] Punkte in einem Streudiagramm [musik] eine Linie formen.
[04:13] eine Linie formen. Liegen die Punkte nämlich perfekt auf
[04:15] Liegen die Punkte nämlich perfekt auf einer Linie mit positiver Steigung, ist
[04:18] einer Linie mit positiver Steigung, ist der + 1 perfekt auf einer Linie mit
[04:21] der + 1 perfekt auf einer Linie mit negativer Steigung. -1 völlig
[04:23] negativer Steigung. -1 völlig willkürlich verstreut 0 und dann gibt es
[04:27] willkürlich verstreut 0 und dann gibt es natürlich noch so Zwischenformen
[04:29] natürlich noch so Zwischenformen tendenziell positiv
[04:31] tendenziell positiv oder eben auch tendenziell negative
[04:34] oder eben auch tendenziell negative Zusammenhänge.
[04:36] Zusammenhänge. Aber wie funktioniert jetzt die
[04:37] Aber wie funktioniert jetzt die Berechnung? Die Formel sieht erstmal
[04:40] Berechnung? Die Formel sieht erstmal etwas einschüchternd aus, aber keine
[04:42] etwas einschüchternd aus, aber keine Angst, es ist nur eine Formel. Wir
[04:44] Angst, es ist nur eine Formel. Wir müssen einfach der Reihe nach Werte
[04:46] müssen einfach der Reihe nach Werte einsetzen und das machen wir auch
[04:48] einsetzen und das machen wir auch gleich, aber erstmal versuchen wir die
[04:50] gleich, aber erstmal versuchen wir die Idee hinter der Formel auf uns wirken zu
[04:53] Idee hinter der Formel auf uns wirken zu lassen.
[04:55] lassen. Dazu konzentrieren wir uns auf den
[04:56] Dazu konzentrieren wir uns auf den Zähler, in dem ein arithmetisches Mittel
[04:58] Zähler, in dem ein arithmetisches Mittel von x, das könnte [musik] die Uhrzeit
[05:00] von x, das könnte [musik] die Uhrzeit sein, zu berechnen ist. Damit ist
[05:03] sein, zu berechnen ist. Damit ist gemeint, wir ignorieren die y Werte und
[05:06] gemeint, wir ignorieren die y Werte und rechnen nur aus den X-Werten einen
[05:08] rechnen nur aus den X-Werten einen Durchschnitt aus. Bei den Uhrzeiten ist
[05:11] Durchschnitt aus. Bei den Uhrzeiten ist der bei 15 Uhr.
[05:14] der bei 15 Uhr. Analog machen wir das noch mal für die Y
[05:17] Analog machen wir das noch mal für die Y Werte bei uns also die Besuchsdauer.
[05:19] Werte bei uns also die Besuchsdauer. Dabei kommen wir auf einen Wert von 65
[05:22] Dabei kommen wir auf einen Wert von 65 Minuten.
[05:24] Minuten. Jetzt sollen wir für jeden X-Wert die
[05:26] Jetzt sollen wir für jeden X-Wert die Differenz zum X Mittelwert bestimmen und
[05:29] Differenz zum X Mittelwert bestimmen und mit der zugehörigen Differenz zwischen
[05:31] mit der zugehörigen Differenz zwischen YWT und Y Mittelwert [musik]
[05:34] YWT und Y Mittelwert [musik] multiplizieren.
[05:36] multiplizieren. Wenn dabei sowohl X größer ist als der
[05:39] Wenn dabei sowohl X größer ist als der X-Mittelwert und Y größer als der y
[05:42] X-Mittelwert und Y größer als der y Mittelwert, das ist im oberen rechten
[05:45] Mittelwert, das ist im oberen rechten Quadranten des Mittelwertkreuzes immer
[05:47] Quadranten des Mittelwertkreuzes immer so, erhalten wir eine positive Differenz
[05:50] so, erhalten wir eine positive Differenz mal positive Differenz, also etwas
[05:52] mal positive Differenz, also etwas positives.
[05:55] positives. habe ich bei einem Paar eine positive,
[05:57] habe ich bei einem Paar eine positive, bei dem anderen Paar eine negative
[05:59] bei dem anderen Paar eine negative Differenz. Das ist immer so. Im linken
[06:01] Differenz. Das ist immer so. Im linken oberen und rechten unteren Quadranten
[06:04] oberen und rechten unteren Quadranten erhalte ich plus mal minus, also etwas
[06:06] erhalte ich plus mal minus, also etwas [musik] Negatives.
[06:08] [musik] Negatives. Und sind beide Differenzen negativ,
[06:11] Und sind beide Differenzen negativ, ergibt sich minus mal minus, also wieder
[06:13] ergibt sich minus mal minus, also wieder etwas positives.
[06:16] etwas positives. Habe ich nun also eine Mischung von
[06:18] Habe ich nun also eine Mischung von Punkten [musik] in allen vier
[06:20] Punkten [musik] in allen vier Quadranten, erhalte ich teils positive,
[06:23] Quadranten, erhalte ich teils positive, teils negative Summanten, die sich in
[06:25] teils negative Summanten, die sich in Richtung 0 ausgleichen.
[06:29] liegen die Punkte hingegen mehrheitlich im rechten oberen und linken unteren
[06:34] im rechten oberen und linken unteren Quadranten habe ich viele positive
[06:36] Quadranten habe ich viele positive Beiträge und komme in der Summe auf
[06:38] Beiträge und komme in der Summe auf einen hohen Wert.
[06:41] einen hohen Wert. Bei mehrheitlich Punkten im linken
[06:43] Bei mehrheitlich Punkten im linken oberen und rechten unteren Quadranten
[06:46] oberen und rechten unteren Quadranten ergibt sich eine weit im Negativen
[06:48] ergibt sich eine weit im Negativen liegende Summe.
[06:51] liegende Summe. Der Ausdruck im Zähler hat auch einen
[06:53] Der Ausdruck im Zähler hat auch einen Namen, nämlich Kovarianz zwischen X und
[06:56] Namen, nämlich Kovarianz zwischen X und Y. Bei uns also Kovarianz von Uhrzeit
[06:59] Y. Bei uns also Kovarianz von Uhrzeit und Besuchsdauer.
[07:01] und Besuchsdauer. Im Nenner sehen wir die Varianzen von x
[07:03] Im Nenner sehen wir die Varianzen von x und Y, die aufgrund des Quadrats immer
[07:06] und Y, die aufgrund des Quadrats immer positiv sind und dafür sorgen, dass der
[07:09] positiv sind und dafür sorgen, dass der Korrelationskoeffizient
[07:10] Korrelationskoeffizient auf dem Bereich zwischen [musik] -1 und
[07:12] auf dem Bereich zwischen [musik] -1 und +1 normiert wird.
[07:16] +1 normiert wird. So, jetzt berechnen wir endlich mal den
[07:18] So, jetzt berechnen wir endlich mal den Korrelationskoeffizienten zur Uhrzeit
[07:20] Korrelationskoeffizienten zur Uhrzeit und der Dauer der Reservierung. Als
[07:23] und der Dauer der Reservierung. Als erstes brauchen wir das arithmetische
[07:24] erstes brauchen wir das arithmetische Mittel. Einmal der Uhrzeit und einmal
[07:26] Mittel. Einmal der Uhrzeit und einmal der Dauer des Besuchs. Das ergibt 15 und
[07:29] der Dauer des Besuchs. Das ergibt 15 und 65.
[07:32] 65. Dann bilden wir die Differenzen zwischen
[07:34] Dann bilden wir die Differenzen zwischen X-Werten und 15
[07:37] X-Werten und 15 sowie zwischen Y Werten und 65.
[07:42] Diese Zwischenergebnisse müssen multipliziert werden.
[07:47] multipliziert werden. Dann die Summe
[07:50] Dann die Summe geteilt durch n. Das n steht für die
[07:52] geteilt durch n. Das n steht für die Anzahl der Messwertepare bei uns also 6.
[07:59] Im Nenner brauchen wir einmal für die x-Differenzen die Quadrate
[08:04] x-Differenzen die Quadrate und auch für die ydi Differenzen.
[08:08] und auch für die ydi Differenzen. Davon jeweils wieder die Summe geteilt
[08:11] Davon jeweils wieder die Summe geteilt durch n, [musik] also jeweils durch 6.
[08:16] durch n, [musik] also jeweils durch 6. Die metrische Korrelation zwischen
[08:18] Die metrische Korrelation zwischen Buchungszeit und Besuchsdauer liegt also
[08:21] Buchungszeit und Besuchsdauer liegt also bei rund -0,02
[08:23] bei rund -0,02 und sagt uns genau wie das
[08:25] und sagt uns genau wie das Streudiagramm, es gibt keinen linearen
[08:27] Streudiagramm, es gibt keinen linearen Zusammenhang zwischen Uhrzeit des
[08:29] Zusammenhang zwischen Uhrzeit des Besuchs und Besuchsdauer.
[08:33] Besuchs und Besuchsdauer. Vollständigkeit halber. Hier noch die
[08:35] Vollständigkeit halber. Hier noch die Berechnung für Gästzahl und
[08:37] Berechnung für Gästzahl und Besuchsdauer.
[08:53] Ergebnis erhalten wir rund 0,93 und
[08:56] Ergebnis erhalten wir rund 0,93 und wissen, es gibt einen starken, positiven
[08:59] wissen, es gibt einen starken, positiven linearen Zusammenhang zwischen der Zahl
[09:01] linearen Zusammenhang zwischen der Zahl der Gäste und der Besuchsdauer.
