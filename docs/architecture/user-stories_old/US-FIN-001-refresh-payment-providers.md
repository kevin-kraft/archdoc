---
id: US-FIN-001
title: Zahlungsanbieter-Liste aktualisieren
area: finance
status: draft
priority: low
owner: Pieric Brast
endpoints:
  - method: GET
    path: routers.payment_providers.get.list-providers
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-001 - Zahlungsanbieter-Liste aktualisieren

## User Story

Als **Admin** möchte ich die Liste der Zahlungsanbieter manuell aktualisieren,
damit ich den aktuellen Status aller konfigurierten Anbieter sehe.

## Kontext

Auf der Zahlungsanbieter-Seite gibt es einen "Refresh"-Button, der die Liste der konfigurierten Anbieter neu lädt. Dies ist nützlich, wenn sich der Status eines Anbieters geändert hat und die Ansicht nicht automatisch aktualisiert wurde.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf den "Refresh"-Button (oben rechts)
3. System lädt die Liste der Anbieter neu vom Server
4. System zeigt die aktualisierte Liste an

## Akzeptanzkriterien

- [ ] Die Liste wird nach dem Klick neu geladen
- [ ] Während des Ladens dreht sich das Refresh-Icon
- [ ] Der Button ist während des Ladens deaktiviert
- [ ] Bei Erfolg wird die aktualisierte Liste angezeigt
- [ ] Bei Fehler wird eine Fehlermeldung angezeigt

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Server nicht erreichbar | Fehlermeldung anzeigen |
| Keine Berechtigung | Zugriff verweigern |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /api/payment-providers | Lädt die Liste aller konfigurierten Anbieter |

## Offene Fragen

- Wie häufig aktualisiert sich die Liste automatisch?

## Notizen

- Button befindet sich in der Actions Bar oben rechts neben "+ Anbieter hinzufügen"
- Icon: RefreshCw (dreht sich während des Ladens)
