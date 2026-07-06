---
id: US-FIN-015
title: Zahlungseinstellungen auf Standardwerte zurücksetzen
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: POST
    path: /payment-settings/reset
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
  - payouts
---

# US-FIN-015 – Zahlungseinstellungen auf Standardwerte zurücksetzen

## User Story

Als **Finance Admin** möchte ich alle Zahlungseinstellungen auf die systemseitigen Standardwerte zurücksetzen können,
damit ich nach fehlerhafter Konfiguration schnell einen definierten Ausgangszustand wiederherstellen kann.

## Kontext

Der Reset entfernt den `payment_settings`-Eintrag aus der Org-Config vollständig. Das Backend normalisiert daraufhin alle Felder mit den Defaults aus `_DEFAULT_PAYMENT_SETTINGS`. Gleichzeitig werden alle offenen Payouts reconciliert. Der Reset wird im Audit Trail geloggt. Die UI zeigt nach dem Reset den Hinweis "Payment settings reset to defaults".

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Finance → Payment Settings ist geöffnet
- [ ] Button "Reset to Defaults" ist sichtbar (oben rechts neben "Save Changes")

## Ablauf

1. Benutzer klickt **Reset to Defaults**
2. System zeigt Bestätigungs-Dialog (erwartet – in Screenshots nicht eindeutig sichtbar)
3. Benutzer bestätigt
4. Backend löscht `payment_settings` aus `org.config`, normalisiert Defaults, reconciliert offene Payouts, schreibt Audit Log
5. UI lädt neu und zeigt Hinweis: **"Payment settings reset to defaults"**
6. Alle Felder zeigen die Default-Werte:
   - Trigger: `per_study`, Modus: `manual`, Minimum payout: 5 €
   - Einzige aktive Methode: Bank transfer
   - Approval: enabled, dual_approval_over: 500 €, notify: true
   - Dispatch: single, separate approver: true, notify: true

## Akzeptanzkriterien

- [ ] Reset-Button ist sichtbar und klickbar für berechtigte Rollen
- [ ] Ein Bestätigungs-Dialog erscheint vor Ausführung (kein sofortiger Reset ohne Rückfrage)
- [ ] Nach Reset: Alle Felder zeigen korrekte Default-Werte
- [ ] Nach Reset: `Last Updated`-Timestamp ist zurückgesetzt auf "No saved update timestamp yet"
- [ ] Nach Reset: Hinweis "Payment settings reset to defaults" ist sichtbar
- [ ] Operating Summary zeigt die Default-Konfiguration
- [ ] Audit Trail enthält den Reset-Event mit before/after-Snapshot
- [ ] Offene Payouts werden automatisch reconciliert (kein manueller Eingriff nötig)

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Berechtigung | ForbiddenError; Reset-Button nicht sichtbar oder deaktiviert |
| Benutzer bricht Bestätigungs-Dialog ab | Kein Reset; Einstellungen unverändert |
| Serverfehler beim Reset | Fehlermeldung; Einstellungen unverändert |
| Aktive offene Payouts vorhanden | Reset trotzdem möglich; Payouts werden reconciliert (kein Blocker) |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/payment-settings/reset | Setzt alle Einstellungen auf Default zurück |

## Offene Fragen

- Gibt es einen Bestätigungs-Dialog in der UI? (In den Screenshots nicht eindeutig sichtbar)
- Wird `Last Updated` nach einem Reset auf `null` gesetzt oder auf den Zeitpunkt des Resets?
- Werden Participants benachrichtigt, wenn sich ihre Zahlungsmethode durch den Reset ändert?

## Notizen

- Der Reset entfernt den Key `payment_settings` aus `org.config` – es wird kein expliziter Default-Wert geschrieben, sondern die Normalisierung generiert ihn beim nächsten Read
- Default-Werte: `bank_transfer` (enabled), alle anderen Methoden disabled; `minimum_payout: 5.0`; `payout_trigger: per_study`; `approval enabled`, `dual_approval_over: 500.0`
