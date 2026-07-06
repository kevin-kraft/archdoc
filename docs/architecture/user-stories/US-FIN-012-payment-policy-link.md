---
id: US-FIN-012
title: Payment Policy aus Finance Operations öffnen
area: finance
status: draft
priority: high
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
---

# US-FIN-012 - Payment Policy aus Finance Operations öffnen

## User Story

Als **Finance Admin** möchte ich aus Finance Operations zur Payment Policy wechseln, damit ich Auszahlungsregeln, Methoden, Budget Gates und Approval-Regeln zentral konfigurieren kann.

## Kontext

Payment Settings sind nicht mehr Teil der Finance-Workflow-Tabs. In der aktuellen UI gibt es im Header von `/financial-management` einen Link **Payment Policy** bzw. Zahlungseinstellungen nach `/admin/payment-settings`, wenn der Benutzer `payments:settings:view` oder `payments:settings:manage` besitzt.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat `payments:settings:view` oder `payments:settings:manage`

## Ablauf

1. Benutzer öffnet `/financial-management`.
2. System prüft Payment-Settings-Berechtigung.
3. System zeigt im Header den Button **Payment Policy**.
4. Benutzer klickt den Button.
5. System navigiert zu `/admin/payment-settings`.
6. Payment Settings öffnet den zuletzt genutzten oder standardmäßigen Accordion-Abschnitt.

## Akzeptanzkriterien

- [ ] Payment-Policy-Link ist nur mit Settings-Rechten sichtbar.
- [ ] Link führt nach `/admin/payment-settings`.
- [ ] Payment Settings enthält die Abschnitte: Participant payout experience, Budget gates, Payout routing and cadence, Payment methods, Approval workflow.
- [ ] Der zuletzt geöffnete Abschnitt wird pro User/Org in Local Storage persistiert.
- [ ] Ohne Settings-Rechte wird der Link nicht angezeigt.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Settings-Rechte | Kein Payment-Policy-Button |
| Payment Settings laden nicht | Skeleton/Fehlerzustand statt leerer Konfiguration |
| Local Storage nicht verfügbar | Seite funktioniert, Abschnitt wird nur nicht persistiert |

## Notizen

- Alte Payment-Provider-Stories dürfen nicht mehr als primärer Finance-Workflow verstanden werden. Providerbindung ist Teil der Payment Policy bzw. der Payout Routes.
