---
id: US-FIN-010
title: Neuen Zahlungsanbieter speichern
area: finance
status: draft
priority: high
owner: Pieric Brast
endpoints:
  - method: POST
    path: routers.payment_providers.post.create-provider
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-010 - Neuen Zahlungsanbieter speichern

## User Story

Als **Admin** möchte ich die Eingaben im Dialog bestätigen und den Anbieter speichern,
damit der neue Zahlungsanbieter für Auszahlungen verwendet werden kann.

## Kontext

Im Dialog zum Hinzufügen eines Zahlungsanbieters gibt es den finalen "Anbieter hinzufügen"-Button im Footer. Dieser übermittelt die eingegebenen Daten an das System und schließt den Dialog bei Erfolg.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Der Hinzufügen-Dialog ist geöffnet
- [ ] Ein Anbieter ist ausgewählt
- [ ] Ein Anzeigename ist eingegeben

## Ablauf

1. Benutzer hat alle Pflichtfelder ausgefüllt
2. Benutzer klickt auf "Anbieter hinzufügen"
3. Button zeigt "Wird gespeichert..." und ist deaktiviert
4. System validiert und parst die JSON-Felder
5. System erstellt den neuen Anbieter
6. Dialog schließt sich
7. Erfolgsmeldung wird angezeigt
8. Anbieter erscheint in der Liste

## Akzeptanzkriterien

- [ ] Button ist deaktiviert solange Pflichtfelder fehlen
- [ ] Button zeigt Ladezustand während des Speicherns
- [ ] Bei Erfolg: Dialog schließt sich, Erfolgsmeldung, Liste aktualisiert
- [ ] Ungültiges JSON wird als Fehler behandelt
- [ ] Bei Fehler: Dialog bleibt offen, Fehlermeldung wird angezeigt

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Pflichtfeld fehlt | Button bleibt deaktiviert |
| Ungültiges JSON in Credentials/Config | Fehler beim Speichern |
| Serverfehler | Meldung "Anbieter konnte nicht hinzugefügt werden" |
| Keine Berechtigung | Zugriff verweigern |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/payment-providers | Erstellt den neuen Anbieter |

## Offene Fragen

- Wird das JSON vor dem Absenden clientseitig validiert?

## Notizen

- Button ist deaktiviert wenn `!addKey || !addName`
- Während des Speicherns: `saving = true`, Button zeigt "Wird gespeichert..."
