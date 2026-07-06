---
id: US-FIN-004
title: Payout Settlement überwachen und bearbeiten
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/payouts
  - method: POST
    path: /financial/payouts
  - method: POST
    path: /financial/payouts/{payout_id}/check-provider-status
  - method: POST
    path: /financial/payouts/{payout_id}/cancel-at-provider
  - method: POST
    path: /financial/payouts/{payout_id}/retry
  - method: POST
    path: /financial/providers/{provider_id}/approve-dispatch
roles:
  - finance_admin
  - admin
  - finance_operator
tables:
  - payouts
  - compensations
  - payment_providers
---

# US-FIN-004 - Payout Settlement überwachen und bearbeiten

## User Story

Als **Payout Operator** möchte ich Payouts im Tab **Payments** überwachen, manuell anlegen und Provider-/Dispatch-Aktionen ausführen, damit genehmigte Vergütungen tatsächlich ausgezahlt werden.

## Kontext

`payments` ist kein Zahlungsanbieter-Konfigurationsscreen. Es ist die operative Auszahlungswarteschlange. Anbieterstatus wird pro Payout geprüft; externe Provider werden über Payment Policy und Payout Routes angebunden.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat `payments:mark:paid` oder `payments:create:payout`
- [ ] Für manuelle Payout-Erstellung existiert mindestens eine Payout Route

## Ablauf

1. Benutzer öffnet `/financial-management?tab=payments`.
2. System lädt Payouts, verknüpfte Compensations und Payout Routes.
3. Benutzer filtert/prüft ausstehende, genehmigte, fehlgeschlagene oder providerbezogene Payouts.
4. Benutzer erstellt optional einen manuellen Payout mit Teilnehmer, Route, Betrag und Notiz.
5. Benutzer prüft Provider-Status, startet Retry oder bricht Provider-Payout mit Override-Grund ab.
6. Falls Dispatch-Autorisierung nötig ist, Benutzer erteilt die Freigabe über den Dispatch-Dialog.

## Akzeptanzkriterien

- [ ] Payments-Tab zeigt Payout-Status verständlich und farblich konsistent.
- [ ] Pending-Count wird in der Navigation am Payments-Button angezeigt.
- [ ] Manuelle Payout-Erstellung validiert Betrag > 0, Teilnehmer und Route.
- [ ] Provider-Status-Refresh aktualisiert anschließend die Payout-Liste.
- [ ] Cancel/Retry verlangt einen Override-Grund mit Mindestlänge.
- [ ] Dispatch-Approval ist nur sichtbar, wenn Status, Providerroute und Berechtigung dazu passen.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Betrag fehlt oder <= 0 | Fehler: Betrag erforderlich |
| Teilnehmer oder Route fehlt | Fehler: Teilnehmer und Route erforderlich |
| Provider-Status nicht abrufbar | Fehlermeldung, Payout bleibt unverändert |
| Override-Grund fehlt oder zu kurz | Dialog bleibt offen, Validierungsfehler |
| Benutzer darf Dispatch nicht freigeben | Dispatch-Aktion nicht verfügbar |

## Notizen

- Alte Stories zu `Health Check` auf Anbieter-Karten sind hier falsch eingeordnet. Der aktuelle operative Check ist `check-provider-status` pro Payout.
