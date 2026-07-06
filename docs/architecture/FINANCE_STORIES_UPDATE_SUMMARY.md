# Finance User Stories Update Summary

## Was aktualisiert wurde

Die alten Finanz-Stories waren größtenteils auf eine separate Zahlungsanbieter-Seite ausgerichtet. Diese Annahme passt nicht mehr zum aktuellen Frontend. Die aktuelle Finanznavigation läuft über `/financial-management` und ist in Workflow-Gruppen organisiert:

- Standard workflow: `payment-requests`, `payments`, `budgets`
- Evidence and audit: `exports`, `ledger`
- Management insight: `reports`, `analytics`
- Specialized tools: `vouchers`

Zusätzlich wird Payment Policy/Zahlungseinstellungen über `/admin/payment-settings` geöffnet, nicht als primärer Finance-Tab.

## Ersetzte Altlogik

- Alte Zahlungsanbieter-Stories 001–010 wurden ersetzt.
- Die fehlerhafte Budget-Story wurde korrigiert. Sie nutzt jetzt Budget-Endpoints statt Reset-to-Defaults.
- Payment Settings bleiben als eigene Admin-Route dokumentiert.
- Stories enthalten jetzt konkrete Query-Parameter, Permissions und aktuelle Tabs.

## Relevante Frontend-Quellen

- `src/features/finance/pages/FinancialManagementPage.tsx`
- `src/features/finance/components/FinancialManagementOverview.tsx`
- `src/features/finance/utils/financialManagementPage.ts`
- `src/features/finance/utils/workflow.ts`
- `src/pages/admin/PaymentSettings.tsx`
- `src/pages/admin/utils/paymentSettingsAccordion.ts`
