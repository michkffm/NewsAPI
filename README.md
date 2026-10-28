# News App – BR24

React-App mit aktuellen Meldungen aus dem offiziellen BR24-RSS-Feed. Kostenlos und ohne API-Schlüssel. Nur für nichtkommerzielle Nutzung gemäß den [BR-Bedingungen](https://www.br.de/service/nutzungsbedingungen-rss-feeds-100.html).

## Funktionen
- Schlagzeilen mit unveränderten Feed-Beschreibungen, Quelle und Datum
- Suche in aktuell geladenen Meldungen (kein Volltext- oder Nachrichtenarchiv)
- Artikel und Quellenlinks öffnen in einem neuen Tab
- Lade-, Leer- und Fehlerzustände mit erneutem Abruf

## Lokal starten
Node.js 22 (mindestens 22.12) mit npm und Python 3 werden benötigt.

```sh
npm ci
npm run build
python3 server/app.py
```

App: http://localhost:8766. Für die Entwicklung zusätzlich `npm run dev` starten; Vite leitet `/api` zum Python-Server weiter.

## Hosting
Die bisherige Render Static Site kann keinen Python-Server ausführen. Eine Render Web Service ist nötig. `render.yaml` beschreibt den kostenlosen Dienst: Build `npm ci && npm run build`, Start `python3 server/app.py`. Alternativ manuell dieselben Befehle konfigurieren. `PORT` wird durch Render gesetzt; lokal standardmäßig 8766. Keine geheimen Umgebungsvariablen nötig. Kostenlose Dienste können bei Inaktivität schlafen; der erste Aufruf kann dauern.

Der Python-Server liefert das gebaute Frontend und `/api/news` von derselben Domain. Nur eine fest konfigurierte BR-URL wird abgerufen, mit Timeout und Größenlimit. Zwischenspeicherung ausschließlich im Arbeitsspeicher für fünf Minuten, keine Datenbank und kein Archiv. Keine fremden HTML-Inhalte oder Bilder werden eingebettet. Bei Fehlern werden keine alten Meldungen ausgeliefert.

## Quelle und Datenschutz
Quelle: BR24 / Bayerischer Rundfunk, [offizielle Feeds](https://www.br.de/service/br-rss-feeds-100.html). Der Browser lädt den Feed über unseren Server; beim Öffnen eines Originalartikels gelten die [Datenschutzhinweise des BR](https://www.br.de/unternehmen/service/datenschutz/index.html). Verfügbarkeit und dauerhafte Erlaubnis werden vom BR nicht garantiert.

Der bisher im Frontend enthaltene NewsAPI-Schlüssel wurde aus den aktiven Dateien entfernt. Der Kontoinhaber muss ihn bei NewsAPI deaktivieren, da er in alten Builds und der Git-Historie weiterhin vorkommen kann.

## Prüfungen
```sh
npm run build
npm run lint
python3 -m unittest discover -s server
```
