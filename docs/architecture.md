# Architektur

## Ein Player, eine eigene Steuerung

Lichtspiel besteht aus einer React-Oberfläche, einer Electron-Desktop-Hülle und einem separat installierten mpv-Prozess. Diese Aufteilung hält Vorführplanung und Bedienung unabhängig von Videodekodierung und Bildausgabe.

```text
Bedienoberfläche auf dem Computer
       │ geprüfte Desktop-Aufrufe
       ▼
Electron-Hauptprozess
       ├── mpv-Prozesssteuerung ──► Beamer / Audioausgabe
       └── optionale Lichtregeln ──► Home Assistant REST API
```

Die Oberfläche verwaltet Einrichtung, Medienauswahl, Reihenfolge, geplanten Start und Lichtregeln. Electron vermittelt lokale Dateiauswahl, Bildschirminformationen und Player-Steuerung. mpv übernimmt das Abspielen lokaler Medien. Die Browseranwendung verwendet dieselbe Oberfläche und spielt Videos in einem separaten Browserfenster ab; sie bietet keine native Displaysteuerung und schaltet keine echten Lampen.

## Warum mpv?

Für einen einzelnen Computer mit HDMI-Beamer ist mpv eine passende erste Wiedergabebasis: Es ist für macOS und Windows verfügbar, unterstützt viele lokale Medienformate und lässt sich als eigener Prozess steuern. Lichtspiel muss dadurch keinen Videoplayer selbst entwickeln.

CasparCG eignet sich für umfangreicheres Broadcast-Playout und komplexe Ausgaben. Sein Server unterstützt Windows und Linux; für eine kleine Anwendung mit macOS als gleichwertigem Ziel bringt das zusätzliche Infrastruktur mit sich. Deshalb ist CasparCG nicht Bestandteil dieses MVP. Auch Quellcode aus PreShow Experience oder QLab wird nicht eingebunden.

## Daten und Ablauf

- Eine Show beschreibt die geordnete Liste lokaler Mediendateien und ihre Vorführkonfiguration. In der Desktop-App verweisen die Einträge auf die Originaldateien. Im Browser werden importierte Videokopien zusätzlich in IndexedDB gespeichert und für die Wiedergabe als lokale Blob-URLs bereitgestellt.
- Eine geplante Uhrzeit startet die Show einmalig innerhalb der laufenden Anwendung. Es gibt keinen Hintergrunddienst und keine Aufweckfunktion. Der Scheduler überspringt einen um mehr als zehn Sekunden verpassten Start sowie einen Start während einer bereits laufenden Vorstellung.
- Bedienmonitor und Wiedergabe-Bildschirm sind getrennte Rollen. Die Auswahl eines zweiten Displays erfordert einen erweiterten Desktop.
- Die Desktop-Grenze bündelt Zugriffe auf Dateien und Prozesse. Die Weboberfläche soll nicht selbst beliebige Betriebssystembefehle ausführen.

## Browserwiedergabe

Der Browseradapter steuert ein separates Fenster mit einem HTML-Videoelement. Eine Freigabe per Klick kann nötig sein, damit Video mit Ton startet. Popup-Blocker, unterstützte Codecs und verfügbare Browser-Speicherquoten bleiben Grenzen dieses Modus. Geplante Starts dürfen diese Browserregeln nicht umgehen. Native mpv-Ausgabe und Home-Assistant-Aufrufe sind ausschließlich Funktionen des Desktop-Adapters.

## Optionale Lichtautomation

`electron/lighting.cjs` kapselt den Home-Assistant-Zugriff. Verbindung und Lampenliste werden über die REST API gelesen. Lichtaktionen verwenden `light.turn_on` mit Helligkeit und Übergangszeit oder bei 0 % `light.turn_off`. Die Oberfläche kann eine Regel ohne Netzwerkänderung beschreiben lassen; nur Automatik oder ein expliziter Live-Test lösen einen schreibenden Aufruf aus.

Die Automatik ist opt-in. Vorprogramm, Hauptfilm, Pause und Ende haben jeweils einen Aktivierungsschalter, eine Zielhelligkeit und eine Übergangszeit. Voreinstellungen sind 20 %, 0 %, 40 % und 80 %. Die aktuelle Clip-Kategorie unterscheidet Vorprogramm von Hauptfilm. Fortsetzen verwendet wieder diese Kategorie; Ende und manueller Stopp verwenden die Endregel. Schwarzbild hat keine eigene Lichtaktion. Die Anwendung stellt beim Beenden nicht automatisch den Zustand vor der Vorstellung wieder her.

Der Hauptprozess speichert den Zugriffstoken mit `safeStorage`. Ist sichere Speicherung nicht möglich, wird keine Klartext-Alternative verwendet. Konfiguration und Token bleiben außerhalb der portablen Showdaten; an die Oberfläche wird nur übermittelt, ob ein Token vorhanden ist. Fehler bei Lichtaktionen werden als Status angezeigt und stoppen den Player nicht.

Die Integration setzt eine vom Nutzer eingerichtete Home-Assistant-Instanz und ein geeignetes `light.*`-Gerät voraus. Verhalten und Übergänge hängen von diesem Gerät ab. In der Entwicklungsumgebung wurde keine echte Instanz verbunden und keine reale Lampe geschaltet.

## Nächste technische Schritte

Vor einem produktiven Einsatz sollten reale Mac- und Windows-Setups geprüft werden: Gerätewechsel, fehlende Dateien, Decoderfehler, HDMI-Ton, lange Filme, Lichtregeln und Verhalten nach Unterbrechungen. Vor dem nativen Start wird bereits geprüft, ob die Mediendateien vorhanden und lesbar sind. Sinnvolle Erweiterungen sind eine umfassendere Prüfung von Codecs und Ausgabekompatibilität, ein dauerhaftes Vorführprotokoll und weitere ausdrücklich konfigurierte Geräteautomation.

`npm test` führt Logiktests aus. `node tests/browser.mjs` prüft die Browseroberfläche und lokale Videowiedergabe mit Playwright gegen den laufenden Vite-Server. Voraussetzungen und Grenzen stehen im [README](../README.md#tests). Diese Tests belegen keine native Hardwarekompatibilität oder reale Lampensteuerung.

Für garantiert bildgenaue Übergänge braucht es zusätzliche Wiedergabetechnik und Tests. Ein DCP-/KDM-Workflow wäre ein eigenes Vorhaben und ist nicht durch die aktuelle Architektur abgedeckt.
