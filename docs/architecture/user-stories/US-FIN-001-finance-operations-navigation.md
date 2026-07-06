---
id: US-FIN-001
title: Finance Operations Navigation öffnen
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
tables:
  []
---

# US-FIN-001 - Finance Operations Navigation öffnen

## User Story

Als **Finance User** möchte ich die Finanzverwaltung als zentralen Arbeitsbereich öffnen, damit ich Payment Requests, Zahlungen, Budgets, Exporte, Ledger, Reports, Analytics und Voucher aus einer Oberfläche erreiche.

## Kontext

Die frühere Finanz-Navigation über einzelne Zahlungsanbieter-Stories ist veraltet. Die aktuelle Seite ist `/financial-management`. Ohne gültigen `tab`-Parameter startet sie im Tab `payment-requests`. Die sichtbare Navigation ist in vier Gruppen strukturiert:

- **Standard workflow**: `payment-requests`, `payments`, `budgets`
- **Evidence and audit**: `exports`, `ledger`
- **Management insight**: `reports`, `analytics`
- **Specialized tools**: `vouchers`

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf die Finanzverwaltung, z. B. `payments:view`

## Ablauf

1. Benutzer öffnet **Finance Operations** in der Hauptnavigation.
2. System lädt `/financial-management`.
3. System setzt ohne oder bei ungültigem `tab` den aktiven Arbeitsbereich auf `payment-requests`.
4. System zeigt die Workflow-Gruppen und die Buttons für alle unterstützten Tabs.
5. Benutzer klickt einen Tab-Button.
6. System aktualisiert die URL mit `?tab=<tab>` und zeigt den gewählten Arbeitsbereich an.

## Akzeptanzkriterien

- [ ] `/financial-management` öffnet standardmäßig `payment-requests`.
- [ ] Ungültige Tabs wie `?tab=unknown` fallen auf `payment-requests` zurück.
- [ ] Unterstützte Tabs sind: `payment-requests`, `payments`, `budgets`, `exports`, `ledger`, `reports`, `analytics`, `vouchers`.
- [ ] Beim Tab-Wechsel bleibt die Navigation auf derselben Seite und aktualisiert den Query-String.
- [ ] Die Gruppe **Standard workflow** steht sichtbar vor Evidence, Insight und Specialized.
- [ ] Der aktive Tab ist visuell hervorgehoben.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Finanzberechtigung | Seite zeigt Access-restricted-Hinweis statt Finanzdaten |
| Ungültiger Tab-Parameter | Fallback auf `payment-requests` |
| Einzelne Finanzdaten laden nicht | Seite zeigt Load-Error-Alert mit Retry für fehlgeschlagene Bereiche |

## Beteiligte Frontend-Komponenten

| Komponente | Zweck |
|---|---|
| `FinancialManagementPage.tsx` | Container, Query-Tab-State, Berechtigungen, Datenladen |
| `FinancialManagementOverview.tsx` | Inbox, Workflow-Gruppen und Tab-Buttons |
| `financialManagementPage.ts` | Definition der Workflow-Gruppen |
| `workflow.ts` | Tab-Auflösung und Finance-Handoff-Links |

## Notizen

- Die alten Zahlungsanbieter-Stories 001–010 sind für diese Navigation fachlich falsch. Zahlungsanbieter/Payment Policy liegen nicht mehr als primärer Finance-Tab vor, sondern werden über **Payment Policy** unter `/admin/payment-settings` erreicht.
