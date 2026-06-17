---
id: US-FIN-008
title: Ersten Zahlungsanbieter hinzufügen (leerer Zustand)
area: finance
status: draft
priority: medium
owner: Pieric Brast
endpoints:
  - method: POST
    path: routers.payment_providers.post.create-provider
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-008 - Ersten Zahlungsanbieter hinzufügen (leerer Zustand)

## User Story

Als **Admin** möchte ich den ersten Zahlungsanbieter hinzufügen wenn noch keiner konfiguriert ist,
damit ich direkt aus dem leeren Zustand heraus starten kann ohne nach dem Button suchen zu müssen.

## Kontext

Wenn noch kein Zahlungsanbieter konfiguriert ist, zeigt die Seite anstelle der Anbieter-Liste eine leere Karte mit einer Erklärung und einem zentralen "Anbieter hinzufügen"-Button. Dieser Button hat dieselbe Funktion wie der Button in der Actions Bar (US-FIN-002).

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Kein Zahlungsanbieter ist bisher konfiguriert

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Seite zeigt leeren Zustand mit Hinweistext
3. Benutzer klickt auf "Anbieter hinzufügen" in der Mitte der Seite
4. Der Hinzufügen-Dialog öffnet sich
5. Weiterer Ablauf entspricht US-FIN-002

## Akzeptanzkriterien

- [ ] Leerer Zustand wird angezeigt wenn keine Anbieter konfiguriert sind
- [ ] Button öffnet denselben Dialog wie in US-FIN-002
- [ ] Nach dem Hinzufügen wird die normale Listenansicht angezeigt

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Serverfehler | Fehlermeldung anzeigen |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/payment-providers | Erstellt neuen Anbieter |

## Offene Fragen

- ...

## Notizen

- Dieser Button ist nur sichtbar wenn `providers.length === 0`
- Icon: Plug (zentriert in rundem Hintergrund)
- Funktional identisch mit US-FIN-002
