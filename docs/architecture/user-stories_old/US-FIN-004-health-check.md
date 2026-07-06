---
id: US-FIN-004
title: Verbindung eines Zahlungsanbieters prüfen
area: finance
status: draft
priority: high
owner: Pieric Brast
endpoints:
  - method: POST
    path: /{provider_id}/health-check
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-004 - Verbindung eines Zahlungsanbieters prüfen

## User Story

Als **Admin** möchte ich die Verbindung und Zugangsdaten eines Zahlungsanbieters prüfen,
damit ich sicherstellen kann, dass der Anbieter korrekt konfiguriert ist und Auszahlungen durchführen kann.

## Kontext

Über das Aktionsmenü (⋯) einer Anbieter-Karte kann ein Health Check ausgelöst werden. Das System prüft dabei, ob die hinterlegten Zugangsdaten gültig sind und der Anbieter erreichbar ist.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Der Anbieter ist konfiguriert

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf "⋯" einer Anbieter-Karte
3. Benutzer wählt "Health Check"
4. System sendet eine Anfrage an den Anbieter
5. Auf der Karte erscheint ein "Wird geprüft..."-Badge
6. System zeigt das Ergebnis als Meldung an

## Akzeptanzkriterien

- [ ] Während der Prüfung wird ein Lade-Badge auf der Karte angezeigt
- [ ] Bei Erfolg: Meldung "Zugangsdaten von [Name] sind gültig"
- [ ] Bei Fehler: Meldung mit konkreter Fehlerbeschreibung
- [ ] Nach der Prüfung wird der Zeitstempel "Zuletzt geprüft" auf der Karte aktualisiert
- [ ] Die Karte zeigt anschließend den neuen Status

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Zugangsdaten ungültig | Fehlermeldung mit Beschreibung des Problems |
| Anbieter nicht erreichbar | Fehlermeldung anzeigen |
| Serverfehler | Meldung "Health Check fehlgeschlagen" |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/payment-providers/{id}/health-check | Führt den Health Check durch |

## Offene Fragen

- Wie lange dauert der Health Check maximal?

## Notizen

- Icon: Shield
- Während der Prüfung: Badge mit drehendem RefreshCw-Icon
- Zeitstempel wird nach der Prüfung aktualisiert
