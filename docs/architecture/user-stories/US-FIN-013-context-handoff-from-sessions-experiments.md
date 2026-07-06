---
id: US-FIN-013
title: Session- und Experiment-Kontext in Finance übernehmen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/session-payment-requests
roles:
  - finance_admin
  - admin
  - experimenter
tables:
  - sessions
  - experiments
  - session_payment_requests
---

# US-FIN-013 - Session- und Experiment-Kontext in Finance übernehmen

## User Story

Als **Benutzer mit Session- oder Experiment-Kontext** möchte ich direkt in die passende Finance-Ansicht springen, damit ich Payment Requests ohne erneutes Suchen prüfen oder verfolgen kann.

## Kontext

Mehrere Session- und Experiment-Seiten verlinken nach `/financial-management?tab=payment-requests&sessionId=...&experimentId=...`. Die Finance-Seite übernimmt diese Filter und bleibt im Payment-Requests-Tab.

## Vorbedingungen

- [ ] Benutzer befindet sich auf einer Session- oder Experiment-Seite
- [ ] Ein Session Payment Request existiert oder kann für diesen Kontext erwartet werden
- [ ] Benutzer hat Zugriff auf Finance oder erhält zumindest rollenbewusste Rückführung

## Ablauf

1. Benutzer klickt im Session-/Experiment-Kontext den Finance-/Payment-Request-Link.
2. System navigiert zu `/financial-management?tab=payment-requests&sessionId=<id>&experimentId=<id>`.
3. Finance lädt Payment Requests gefiltert nach Session und/oder Experiment.
4. Benutzer öffnet den Request oder kehrt bei fehlender Aktionsberechtigung in den Kontext zurück.

## Akzeptanzkriterien

- [ ] `sessionId` bleibt im Query-String erhalten.
- [ ] `experimentId` bleibt im Query-String erhalten.
- [ ] `tab=payment-requests` wird gesetzt.
- [ ] Direkte Handoff-Links aus Sessions und Experiments zeigen keine falsche Payments-Ansicht.
- [ ] Benutzer ohne Payment-Aktionsrechte sehen eine rollenbewusste No-Action-Message mit Rücksprung in den Kontext.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| SessionId ungültig | Leerer/fehlerhafter Payment-Request-Filter statt Crash |
| User darf Finance nicht sehen | Access restricted |
| Request noch nicht erstellt | Empty-State mit Hinweis, dass Experimenter Requests aus Session Workflows erzeugen |

## Offene Fragen

- Soll ein Experimenter ohne Finance-Rechte überhaupt die Finance-Seite sehen oder immer im Session-Kontext bleiben?
