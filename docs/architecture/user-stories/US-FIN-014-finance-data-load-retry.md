---
id: US-FIN-014
title: Fehlgeschlagene Finanzdaten gezielt neu laden
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/budgets
  - method: GET
    path: /financial/payout-routes
  - method: GET
    path: /financial/payouts
  - method: GET
    path: /compensations
  - method: GET
    path: /financial/session-payment-requests
  - method: GET
    path: /financial/vouchers
  - method: GET
    path: /financial/currencies
  - method: POST
    path: /financial/reports/financial-stats
roles:
  - finance_admin
  - admin
  - finance_operator
tables:
  []
---

# US-FIN-014 - Fehlgeschlagene Finanzdaten gezielt neu laden

## User Story

Als **Finance User** möchte ich erkennen, wenn einzelne Finanzdaten nicht geladen wurden, und nur diese fehlgeschlagenen Bereiche erneut laden, damit die Finanzseite nicht still falsche oder unvollständige Daten zeigt.

## Kontext

Die aktuelle Finanzseite sammelt Daten aus mehreren APIs. Fehler werden als `dataLoadIssues` aggregiert und mit Quelle plus Fehlermeldung angezeigt. Ein Retry-Button lädt die fehlgeschlagenen Bereiche erneut.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf `/financial-management`
- [ ] Mindestens eine Finanzdaten-Query ist fehlgeschlagen

## Ablauf

1. Benutzer öffnet Finance Operations.
2. Eine oder mehrere Datenquellen schlagen fehl.
3. System zeigt Alert **Finanzdaten konnten nicht geladen werden** mit betroffenen Quellen.
4. Benutzer klickt **Fehlgeschlagene Bereiche erneut laden**.
5. System versucht nur die fehlgeschlagenen Queries erneut zu laden.

## Akzeptanzkriterien

- [ ] Alert nennt konkrete Quellen, z. B. Budgets, Payouts, Compensations, Vouchers oder Financial Stats.
- [ ] Backend-Fehlermeldung wird pro Quelle ergänzt, sofern vorhanden.
- [ ] Retry-Button ist sichtbar, wenn `dataLoadIssues` nicht leer ist.
- [ ] Erfolgreich geladene Datenbereiche bleiben nutzbar; die ganze Seite wird nicht blockiert.
- [ ] Nach erfolgreichem Retry verschwindet der Alert.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Retry schlägt erneut fehl | Alert bleibt mit aktueller Fehlermeldung sichtbar |
| Nur optionale Daten fehlen | Hauptworkflow bleibt soweit möglich bedienbar |
| Mehrere Quellen fehlen | Alle Quellen werden im Alert getrennt genannt |

## Notizen

- Das ist wichtig für Demos: Eine halb geladene Finance-Seite ohne Warnung wäre gefährlicher als ein harter Fehler.
