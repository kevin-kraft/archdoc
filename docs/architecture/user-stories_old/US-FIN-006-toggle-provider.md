---
id: US-FIN-006
title: Zahlungsanbieter aktivieren oder deaktivieren
area: finance
status: draft
priority: high
owner: Pieric Brast
endpoints: #Hier war PATCH zuvor, aber PUT ist tatsächliche Methode
  - method: PUT
    path: /{provider_id}
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-006 - Zahlungsanbieter aktivieren oder deaktivieren

## User Story

Als **Admin** möchte ich einen Zahlungsanbieter aktivieren oder deaktivieren,
damit ich steuern kann, welche Anbieter für Auszahlungen verwendet werden dürfen.

## Kontext

Auf jeder Anbieter-Karte gibt es einen Toggle-Schalter (Ein/Aus), mit dem der Anbieter aktiviert oder deaktiviert werden kann, ohne ihn zu löschen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Der Anbieter ist konfiguriert

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf den Toggle-Schalter einer Anbieter-Karte
3. System aktualisiert den Status des Anbieters
4. Die Karte zeigt den neuen Status an

## Akzeptanzkriterien

- [ ] Toggle wechselt sofort den Zustand (aktiv/inaktiv)
- [ ] Der Status-Badge auf der Karte aktualisiert sich
- [ ] Das Anbieter-Icon wechselt die Farbe (blau = aktiv, grau = inaktiv)
- [ ] Bei Fehler bleibt der Toggle im alten Zustand und eine Fehlermeldung erscheint

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Serverfehler | Meldung "Anbieter konnte nicht aktualisiert werden" |
| Keine Berechtigung | Zugriff verweigern |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| PATCH | /api/payment-providers/{id} | Aktualisiert `is_enabled` des Anbieters |

## Offene Fragen

- Was passiert mit laufenden Auszahlungen wenn ein aktiver Anbieter deaktiviert wird?

## Notizen

- Aktiv: Icon in blau, Label "Aktiviert"
- Inaktiv: Icon in grau, Label "Deaktiviert"
