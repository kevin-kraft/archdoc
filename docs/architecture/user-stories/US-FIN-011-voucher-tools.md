---
id: US-FIN-011
title: Voucher als Specialized Tool verwalten
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/vouchers
  - method: POST
    path: /financial/vouchers
roles:
  - finance_admin
  - admin
tables:
  - vouchers
---

# US-FIN-011 - Voucher als Specialized Tool verwalten

## User Story

Als **Finance Admin** möchte ich im Tab **Vouchers** Gutscheine erstellen und deren Status sehen, damit Sonderfälle oder voucherbasierte Auszahlungen getrennt vom Standard-Payout-Workflow verwaltet werden.

## Kontext

`vouchers` liegt bewusst in der Gruppe **Specialized tools**. Das ist kein Standardweg für normale Session-Auszahlungen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf Finanzverwaltung
- [ ] Für Erstellung hat Benutzer eine passende Finance-Admin-Rolle

## Ablauf

1. Benutzer öffnet `/financial-management?tab=vouchers`.
2. System lädt bestehende Voucher.
3. Benutzer klickt **Voucher erstellen**.
4. Benutzer gibt Code, Betrag, Währung und optional Ablaufdatum an.
5. System erstellt Voucher und aktualisiert die Liste.
6. Benutzer sieht Status: verfügbar, verwendet oder abgelaufen.

## Akzeptanzkriterien

- [ ] Voucher-Liste zeigt Code, Betrag, Status, Used-by und Ablaufdatum.
- [ ] Betrag muss > 0 sein.
- [ ] Code ist Pflicht.
- [ ] Abgelaufene Voucher werden anhand `expires_at` als expired dargestellt.
- [ ] Verwendete Voucher werden als used dargestellt.
- [ ] Nach erfolgreicher Erstellung schließt der Dialog und die Liste wird neu geladen.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Code fehlt | Validierungsfehler |
| Betrag fehlt oder <= 0 | Validierungsfehler |
| Code bereits vergeben | Backend-Fehler anzeigen |
| Voucher-Liste lädt nicht | Load-Error/Empty-State statt kaputter Tabelle |

## Offene Fragen

- Sind Voucher produktiver Zahlungsweg oder nur Demo-/Fallback-Mechanismus?
- Soll Voucher-Erstellung an Budgets gekoppelt werden?
