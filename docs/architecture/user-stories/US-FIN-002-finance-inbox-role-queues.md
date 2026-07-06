---
id: US-FIN-002
title: Finance Inbox mit rollenbasierten Warteschlangen nutzen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/session-payment-requests
  - method: GET
    path: /compensations
  - method: GET
    path: /financial/payouts
roles:
  - finance_admin
  - admin
  - finance_operator
tables:
  - compensations
  - payouts
  - session_payment_requests
---

# US-FIN-002 - Finance Inbox mit rollenbasierten Warteschlangen nutzen

## User Story

Als **Finance User** möchte ich in der Finance Inbox sehen, welche Finanzaufgaben als Nächstes anstehen, damit ich nicht blind zwischen getrennten Finanzseiten springen muss.

## Kontext

Die aktuelle Finanzseite zeigt oberhalb der Tabs eine **Finance Inbox** mit phasenbasierten Warteschlangen. Relevante Bereiche sind Genehmigung, Settlement/Zur Auszahlung bereit, Monitoring und Settings. Die Header-Aktion priorisiert Approval vor Settlement, wenn der Benutzer beide Rechte hat.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf `/financial-management`
- [ ] Für aktive Aktionen besitzt der Benutzer passende Rechte, z. B. `payments:approve`, `payments:approve:dual`, `payments:mark:paid` oder `payments:create:payout`

## Ablauf

1. Benutzer öffnet `/financial-management`.
2. System lädt Payment Requests, Compensations und Payouts.
3. System berechnet Inbox-Sektionen und Zähler.
4. System zeigt Rollen-Badges wie Genehmiger, Auszahlungsbearbeitung oder Finanzadmin.
5. Benutzer öffnet eine Warteschlange oder einen einzelnen Inbox-Eintrag.

## Akzeptanzkriterien

- [ ] Inbox-Zähler werden aus den geladenen Finanzdaten gebildet.
- [ ] Genehmigungsaufgaben führen nach `/financial-management?tab=payment-requests`.
- [ ] Settlement-Aufgaben führen nach `/financial-management?tab=payments` oder bei externen Exporten nach `/financial-management?tab=exports`.
- [ ] Einzelne Payment Requests können mit `requestId`, `sessionId` und `experimentId` im Query-String geöffnet/gefiltert werden.
- [ ] Benutzer ohne passende Aktionsrechte sehen einen rollenbewussten No-Action-Hinweis statt falscher Buttons.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Aufgaben vorhanden | Section zeigt Empty-State |
| Daten werden noch geladen | Loading-Hinweis für Warteschlangen |
| Benutzer darf sehen, aber nicht handeln | No-Action-Hinweis mit Rücksprung in Session-/Experiment-Kontext |

## Beteiligte Frontend-Komponenten

| Komponente | Zweck |
|---|---|
| `useFinancialManagementOverviewState.ts` | Berechnet Inbox-Sektionen, Role-Badges und Summary Metrics |
| `FinancialManagementOverview.tsx` | Rendert Inbox-Karten und Links |
| `workflow.ts` | Bestimmt Next-Step-Routen abhängig von Status und Rolle |
