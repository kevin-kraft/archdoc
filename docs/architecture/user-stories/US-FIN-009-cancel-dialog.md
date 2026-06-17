---
id: US-FIN-009
title: Hinzufügen-Dialog abbrechen
area: finance
status: draft
priority: low
owner: Pieric Brast
endpoints: []
roles:
  - admin
tables: []
---

# US-FIN-009 - Hinzufügen-Dialog abbrechen

## User Story

Als **Admin** möchte ich den Hinzufügen-Dialog schließen ohne etwas zu speichern,
damit ich den Vorgang abbrechen kann wenn ich mich umentschieden habe.

## Kontext

Im Dialog zum Hinzufügen eines Zahlungsanbieters gibt es einen "Abbrechen"-Button. Dieser schließt den Dialog und verwirft alle eingegebenen Daten.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Der Hinzufügen-Dialog ist geöffnet

## Ablauf

1. Benutzer hat den Hinzufügen-Dialog geöffnet
2. Benutzer klickt auf "Abbrechen"
3. Dialog schließt sich
4. Alle eingegebenen Daten werden verworfen
5. Die Anbieter-Liste bleibt unverändert

## Akzeptanzkriterien

- [ ] Dialog schließt sich beim Klick
- [ ] Alle Formularfelder werden zurückgesetzt
- [ ] Kein neuer Anbieter wird erstellt
- [ ] Dialog schließt sich auch beim Klick außerhalb

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| - | - |

## Beteiligte API-Endpunkte

Keine (nur UI-Aktion)

## Offene Fragen

- Soll eine Bestätigungsabfrage erscheinen wenn bereits Daten eingegeben wurden?

## Notizen

- `variant="outline"` Button
- Formular wird über `resetAddForm()` zurückgesetzt
