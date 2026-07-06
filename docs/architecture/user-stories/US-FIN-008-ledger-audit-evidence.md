---
id: US-FIN-008
title: Ledger und Audit Evidence prüfen
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/ledger/summary
roles:
  - finance_admin
  - admin
  - finance_operator
tables:
  - ledger_transactions
  - payouts
  - budgets
---

# US-FIN-008 - Ledger und Audit Evidence prüfen

## User Story

Als **Finance Admin** möchte ich im Tab **Ledger** die Finanztransaktionen und deren Settlement-Stufe prüfen, damit ich Auszahlungen und Budgetbewegungen nachvollziehen kann.

## Kontext

`ledger` liegt in der Gruppe **Evidence and audit**. Der Tab ist kein operativer Primär-Workflow, sondern dient Nachvollziehbarkeit, Abstimmung und Prüfung.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf Finanzdaten

## Ablauf

1. Benutzer öffnet `/financial-management?tab=ledger`.
2. System lädt Ledger Summary.
3. System zeigt Total Credits, Total Debits, Net Balance, Transaction Count und Recent Transactions.
4. Benutzer filtert nach Settlement Stage oder Transaction Type.
5. Benutzer prüft Referenzen zu Budgets oder Payouts.

## Akzeptanzkriterien

- [ ] Ledger Summary zeigt aggregierte Beträge in der Basiswährung.
- [ ] Recent Transactions zeigen Betrag, Typ, Beschreibung, Referenz und Erstellzeit.
- [ ] Payout-bezogene Transaktionen werden einer Stage zugeordnet: incoming, awaiting approval, approved not paid, paid out, released, reserved oder other.
- [ ] Mixed-Currency-Warnung erscheint, wenn Finanzsummen mehrere Währungen enthalten.
- [ ] Bei leerem Ledger erscheint ein Empty-State.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Ledger Summary lädt nicht | Fehlerhinweis statt falscher Summen |
| Transaktion ohne Stage | Fallback auf `incoming` bei Credit, sonst `other` |
| Mehrere Währungen | Warnung, dass Aggregate vor Abstimmung geprüft werden müssen |

## Offene Fragen

- Soll Ledger-Ansicht direkt auf Payout-/Budget-Details verlinken?
- Braucht der Audit Use Case Exportfunktionen aus dem Ledger heraus?
