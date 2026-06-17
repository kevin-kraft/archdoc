---
id: US-FIN-005
title: Zahlungsanbieter löschen
area: finance
status: draft
priority: high
owner: Pieric Brast
endpoints:
  - method: DELETE
    path: /{provider_id}
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-005 - Zahlungsanbieter löschen

## User Story

Als **Admin** möchte ich einen konfigurierten Zahlungsanbieter löschen,
damit nicht mehr benötigte oder fehlerhafte Anbieter aus dem System entfernt werden können.

## Kontext

Über das Aktionsmenü (⋯) einer Anbieter-Karte kann der Anbieter gelöscht werden. Diese Aktion ist nicht rückgängig zu machen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Der Anbieter ist konfiguriert

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf "⋯" einer Anbieter-Karte
3. Benutzer wählt "Löschen"
4. System löscht den Anbieter
5. System zeigt Erfolgsmeldung
6. Anbieter verschwindet aus der Liste

## Akzeptanzkriterien

- [ ] Anbieter wird nach dem Klick gelöscht
- [ ] Erfolgsmeldung "Anbieter wurde entfernt" wird angezeigt
- [ ] Anbieter erscheint danach wieder in der "Verfügbare Adapter"-Liste
- [ ] Bei Fehler wird eine Fehlermeldung angezeigt

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Anbieter wird aktuell verwendet | Fehlermeldung anzeigen |
| Serverfehler | Meldung "Anbieter konnte nicht entfernt werden" |
| Keine Berechtigung | Zugriff verweigern |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| DELETE | /api/payment-providers/{id} | Löscht den Anbieter |

## Offene Fragen

- Gibt es eine Bestätigungsabfrage vor dem Löschen?
- Was passiert mit offenen Auszahlungen dieses Anbieters?

## Notizen

- Icon: Trash2 (rot/destructive)
- Kein Bestätigungsdialog im aktuellen Code vorhanden — möglicher Bug
