---
id: US-FIN-015
title: Rollen- und Permission-basierte Finance UI anzeigen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  []
roles:
  - finance_admin
  - admin
  - finance_operator
  - experimenter
tables:
  []
---

# US-FIN-015 - Rollen- und Permission-basierte Finance UI anzeigen

## User Story

Als **Systemverantwortlicher** möchte ich, dass Finance Operations Aktionen strikt nach Permissions anzeigt, damit Benutzer keine Finanzaktionen sehen oder auslösen, die nicht zu ihrer Rolle gehören.

## Kontext

Die Finanzseite nutzt nicht nur Rollenlabels, sondern konkrete Permissions. Beispiele: `payments:view`, `payments:approve`, `payments:approve:dual`, `payments:mark:paid`, `payments:create:payout`, `payments:settings:view`, `payments:settings:manage`, `payments:budget:add`, `payments:budget:edit`, `payments:budget:delete`, `payments:override:status`.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer besitzt eine definierte Rolle und effektive Permissions

## Ablauf

1. Benutzer öffnet `/financial-management`.
2. System prüft Zugriff auf Finance Area.
3. System zeigt je nach Permission Header-Aktionen, Inbox-Aktionen, Tab-Aktionen und Dialoge.
4. Benutzer sieht nur zulässige Aktionen.

## Akzeptanzkriterien

- [ ] Ohne Finance-Zugriff erscheint Access restricted.
- [ ] Approval-Aktion erscheint nur mit `payments:approve` oder `payments:approve:dual`.
- [ ] Settlement-/Payout-Aktionen erscheinen nur mit `payments:mark:paid` oder `payments:create:payout`.
- [ ] Payment-Policy-Link erscheint nur mit `payments:settings:view` oder `payments:settings:manage`.
- [ ] Budget Create/Edit/Delete erscheinen nur mit passenden Budget-Permissions.
- [ ] Override Cancel/Retry erscheint nur mit `payments:override:status`.
- [ ] Role-Badges erklären grob die aktuelle Funktion, ersetzen aber keine Permission-Prüfung.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Rolle vorhanden, Permission fehlt | Aktion nicht anzeigen |
| Permission vorhanden, Rolle ungewohnt | Permission entscheidet über Aktion |
| Benutzer versucht Direkt-URL ohne Zugriff | Access restricted oder Backend Forbidden |

## Notizen

- Nur Rollennamen in User Stories zu schreiben ist zu schwach. Für Tests müssen Permissions genannt werden, sonst wird die Story nicht prüfbar.
