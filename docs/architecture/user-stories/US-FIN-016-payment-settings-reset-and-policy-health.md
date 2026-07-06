---
id: US-FIN-016
title: Payment Settings zurücksetzen und Policy Health prüfen
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /admin/settings/payments
  - method: PUT
    path: /admin/settings/payments
  - method: POST
    path: /admin/settings/payments/reset
  - method: GET
    path: /admin/settings/payments/eligible-approvers
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
  - payment_providers
  - payouts
---

# US-FIN-016 - Payment Settings zurücksetzen und Policy Health prüfen

## User Story

Als **Finance Admin** möchte ich Payment Settings speichern, zurücksetzen und Policy-Health-Warnungen sehen, damit Fehlkonfigurationen bei Auszahlungsrouting und Providerbindung nicht unbemerkt bleiben.

## Kontext

Payment Settings liegen unter `/admin/payment-settings`, nicht als Tab innerhalb der Finance-Workflow-Navigation. Aktuelle Abschnitte sind Participant payout experience, Budget gates, Payout routing and cadence, Payment methods und Approval workflow. Die UI erkennt Risiken wie externe Provider-Verarbeitung ohne Providerbindung oder ungebundene externe Provider-Routen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat `payments:settings:manage`
- [ ] Payment Settings wurden geladen

## Ablauf

1. Benutzer öffnet `/admin/payment-settings` über den Payment-Policy-Link.
2. Benutzer bearbeitet Payment-Settings-Abschnitte.
3. System zeigt Policy-Health-Warnungen, wenn externe Providerverarbeitung ohne gültige Providerbindung konfiguriert ist.
4. Benutzer klickt **Save Changes**.
5. Optional klickt Benutzer **Reset to Defaults** und bestätigt.
6. System speichert oder setzt Settings zurück und lädt die normalisierte Konfiguration neu.

## Akzeptanzkriterien

- [ ] Settings-Seite lädt bestehende Payment Settings und eligible Approvers.
- [ ] Save nutzt `PUT /admin/settings/payments`.
- [ ] Reset nutzt `POST /admin/settings/payments/reset` und ist nicht mit Budget-Erstellung zu verwechseln.
- [ ] Accordion-Abschnitte sind klar getrennt: Participant payout experience, Budget gates, Payout routing and cadence, Payment methods, Approval workflow.
- [ ] Externe Providerverarbeitung ohne Provider-Konfiguration erzeugt eine sichtbare Health-Warnung.
- [ ] Ungebundene externe Provider-Routen erzeugen eine sichtbare Health-Warnung.
- [ ] Nach Save/Reset wird die UI aus Backend-Daten normalisiert aktualisiert.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Manage-Permission | Speichern/Reset nicht verfügbar oder Backend Forbidden |
| Externe Route ohne Provider Key | Policy-Health-Warnung/blockierender Hinweis |
| Reset schlägt fehl | Fehlermeldung; bestehende Settings bleiben erhalten |
| Save schlägt fehl | Fehlermeldung; Formular bleibt gefüllt |

## Offene Fragen

- Ist Policy Health nur Warnung oder muss sie Save blockieren?
- Welche Defaults sind produktiv final und welche nur Entwicklungswerte?

## Notizen

- Diese Story ersetzt die alte Vermischung von Reset-to-Defaults und Budget-Erstellung. Das alte `US-FIN-016_create_budget.md` war fachlich Müll: gleicher Ablauf wie Reset, falscher Endpoint und falsche Vorbedingungen.
