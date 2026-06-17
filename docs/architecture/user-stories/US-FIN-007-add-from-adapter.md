---
id: US-FIN-007
title: Anbieter aus verfügbaren Adaptern hinzufügen
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

# US-FIN-007 - Anbieter aus verfügbaren Adaptern hinzufügen

## User Story

Als **Admin** möchte ich einen Anbieter direkt aus der "Verfügbare Adapter"-Liste hinzufügen,
damit ich schneller einen neuen Anbieter konfigurieren kann ohne ihn manuell aus einer Dropdown-Liste suchen zu müssen.

## Kontext

Im unteren Bereich der Seite werden alle noch nicht konfigurierten Anbieter als Karten angezeigt. Jede dieser Karten hat einen "+"-Button, der den Hinzufügen-Dialog vorausgefüllt mit dem entsprechenden Anbieter öffnet.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Es gibt noch nicht konfigurierte Anbieter

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer sieht den Bereich "Verfügbare Adapter" unten auf der Seite
3. Benutzer klickt auf "+" bei einem Adapter
4. Der Hinzufügen-Dialog öffnet sich mit dem Anbieter und Namen bereits ausgewählt
5. Benutzer ergänzt die restlichen Felder (Zugangsdaten etc.)
6. Benutzer klickt auf "Anbieter hinzufügen"

## Akzeptanzkriterien

- [ ] Dialog öffnet sich mit dem richtigen Anbieter vorausgewählt
- [ ] Anzeigename wird automatisch befüllt
- [ ] Restlicher Ablauf entspricht US-FIN-002

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Stub-Anbieter | Warnhinweis im Dialog wird angezeigt |
| Serverfehler | Fehlermeldung anzeigen |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/payment-providers | Erstellt neuen Anbieter |

## Offene Fragen

- ...

## Notizen

- Adapter-Karten haben gestrichelten Rand (border-dashed)
- Stub-Anbieter zeigen ein "Demnächst verfügbar"-Badge
- Dieser Button ist eine Abkürzung zu US-FIN-002
