---
id: US-FIN-013
title: Compensation Approval-Workflow konfigurieren
area: finance
status: draft
priority: critical
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /settings/payments
  - method: PUT
    path: /settings/payments
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
  - payouts
---

# US-FIN-013 – Compensation Approval-Workflow konfigurieren

## User Story

Als **Finance Admin** möchte ich den Compensation-Approval-Workflow konfigurieren (Schwellenwerte, Vier-Augen-Prinzip, Benachrichtigungen),
damit Auszahlungen erst nach korrekter Prüfung und Freigabe ausgeführt werden und die internen Kontrollpflichten eingehalten werden.

## Kontext

Der Approval-Workflow trennt die inhaltliche Prüfung (Entitlement Review) vom finalen Dispatch. Er steuert, ob Auszahlungen automatisch genehmigt werden, wann ein Vier-Augen-Prinzip greift und wer als Standard-Genehmiger agiert. Die Validierung `auto_approve_threshold < dual_approval_threshold` ist serverseitig erzwungen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Abschnitt "Approval workflow" → "Compensation approval" ist aufgeklappt

## Ablauf
Navbar: Payout Settings
1. Benutzer aktiviert/deaktiviert Toggle **"Enable approval workflow"**
   - Deaktiviert: Payouts warten nicht auf explizite Approval-Schritte
2. Bei aktiviertem Workflow:
   a. Benutzer setzt **Auto-approve under (EUR)**: Beträge unter diesem Wert werden automatisch genehmigt (optional, leer = nie auto-approve)
   b. Benutzer setzt **Require dual approval over (EUR)**: Beträge darüber erfordern 2 Genehmigungen (Standard: 500 €)
   c. Benutzer wählt **Default approver role** (z. B. `finance_admin`)
   d. Benutzer aktiviert/deaktiviert **"Notify approvers on pending payouts"**
3. Benutzer klickt **Save Changes**
4. System validiert: `auto_approve_threshold` muss < `dual_approval_threshold` wenn beide gesetzt

## Akzeptanzkriterien

- [ ] Toggle "Enable approval workflow" schaltet die weiteren Felder aktiv/inaktiv
- [ ] `Auto-approve under` kann leer bleiben (= kein Auto-Approve)
- [ ] `Require dual approval over` ist Standard 500 € und editierbar
- [ ] Validierungsfehler wenn `auto_approve >= dual_approval` (beide gesetzt)
- [ ] Notify-Toggle wird korrekt gespeichert und nach Reload beibehalten
- [ ] Default approver role wird korrekt gespeichert
- [ ] Deaktivierter Workflow: Payouts erhalten keinen `pending_approval`-Status mehr

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| `auto_approve_threshold >= dual_approval_threshold` (beide gesetzt) | Validierungsfehler: "Auto-approve threshold must be less than dual approval threshold" |
| `dual_approval_threshold` = 0 oder negativ | Validierungsfehler (Schwellenwert muss > 0) |
| Default approver role leer | `null`-Fallback – prüfen ob das zu Routing-Fehlern führt |
| Keine Berechtigung | ForbiddenError |
| Serverfehler beim Save | Fehlermeldung; Formular bleibt gefüllt |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /admin/settings/payments | Lädt approval_config |
| PUT | /admin/settings/payments | Speichert approval_config |

## Offene Fragen

- Was passiert mit laufenden Payouts im Status `pending_approval`, wenn der Workflow deaktiviert wird?
- Kann die `default_approver_role` auf eine benutzerdefinierte Rolle gesetzt werden oder nur auf Systemrollen?
- Wird eine Benachrichtigung ausgelöst, wenn ein Auto-Approve greift?

## Notizen

- Default: `enabled: true`, `require_dual_approval_over: 500.0`, `notify_on_pending: true`
- `auto_approve_under_threshold` ist im Default `null` (kein Auto-Approve)
- Diese User Story gilt nur für die Compensation Approval (Entitlement Review); die Dispatch Authorization ist in US-FIN-005 beschrieben
