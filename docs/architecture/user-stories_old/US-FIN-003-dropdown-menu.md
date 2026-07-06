---
id: US-FIN-003
title: Anbieter-Aktionsmenü öffnen
area: finance
status: draft
priority: medium
owner: Pieric Brast
endpoints: []
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-003 - Anbieter-Aktionsmenü öffnen

## User Story

Als **Admin** möchte ich ein Aktionsmenü für einen konfigurierten Zahlungsanbieter öffnen,
damit ich schnell auf verfügbare Aktionen (Health Check, Löschen) zugreifen kann.

## Kontext

Auf jeder Anbieter-Karte gibt es einen "⋯"-Button (drei Punkte), der ein Dropdown-Menü mit weiteren Aktionen öffnet.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Mindestens ein Zahlungsanbieter ist konfiguriert

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf den "⋯"-Button einer Anbieter-Karte
3. Ein Dropdown-Menü öffnet sich mit den Optionen:
   - Health Check
   - Löschen

## Akzeptanzkriterien

- [ ] Dropdown-Menü öffnet sich beim Klick
- [ ] Menü enthält die Optionen "Health Check" und "Löschen"
- [ ] Menü schließt sich beim Klick außerhalb

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine konfigurierten Anbieter | Button nicht sichtbar |

## Beteiligte API-Endpunkte

Keine (nur UI-Aktion)

## Offene Fragen

- ...

## Notizen

- Icon: MoreHorizontal (drei Punkte)
- Button: `variant="ghost"`, 8x8px
