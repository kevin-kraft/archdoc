---
id: US-FIN-016
title: Participant-seitige Auszahlungserfahrung konfigurieren
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /payment-settings
  - method: PATCH
    path: /payment-settings
  - method: GET
    path: /public/payment-policy
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
---

# US-FIN-016 – Participant-seitige Auszahlungserfahrung konfigurieren

## User Story

Als **Finance Admin** möchte ich festlegen, was Participants im Auszahlungsportal sehen und tun können (Methodenwahl, Datenpflege, Anweisungstext),
damit die Participant-Erfahrung klar, korrekt und sicher ist.

## Kontext

Der Abschnitt "Participant payout experience" steuert drei Dinge: ob Participants eine Zahlungsmethode selbst wählen dürfen, ob sie ihre Empfängerfelder (IBAN etc.) selbst bearbeiten dürfen, und welchen Informationstext sie sehen. Die Einstellungen werden über `build_public_payment_policy_payload()` ans Participant-Portal ausgeliefert.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Abschnitt "Participant payout experience" ist aufgeklappt

## Ablauf

1. Benutzer aktiviert/deaktiviert **"Participants can choose payout method"**
   - Aktiviert: Participants sehen alle Methoden mit `participant_selectable: true` im Portal
   - Deaktiviert: Organisation legt Route fest; Participants sehen nur die konfigurierte Standardroute
2. Benutzer aktiviert/deaktiviert **"Participants can update payout details"**
   - Aktiviert: Participants können ihre Empfängerfelder (IBAN, PayPal-Email etc.) im Portal selbst bearbeiten
   - Deaktiviert: Felder sind im Portal read-only
3. Benutzer wählt **Participant default method** aus Dropdown (nur aktivierte Methoden wählbar)
4. Benutzer trägt optionale **Participant instructions** ein (Freitext)
5. Benutzer klickt **Save Changes**

## Akzeptanzkriterien

- [ ] Toggle "Participants can choose payout method" korrekt gespeichert und nach Reload beibehalten
- [ ] Toggle "Participants can update payout details" korrekt gespeichert und nach Reload beibehalten
- [ ] Dropdown "Participant default method" zeigt nur aktivierte Methoden
- [ ] Wenn `participant_can_select_method: true`, aber keine selectable Methode aktiv → Validierungsfehler
- [ ] `participant_default_method` muss eine aktivierte Methode referenzieren – sonst fällt Backend auf erste selectable Methode zurück
- [ ] Participant instructions werden als Freitext gespeichert (oder `null` wenn leer)
- [ ] Operating Summary zeigt korrekt "Participant selection is enabled/disabled" und "Editable in portal / Not editable"

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| `participant_can_select_method: true`, keine selectable Methode aktiv | Validierungsfehler: "Participant payout-method selection requires at least one enabled participant-selectable method" |
| `participant_default_method` referenziert deaktivierte Methode | Backend normalisiert automatisch auf erste verfügbare selectable Methode |
| Beide Toggles deaktiviert, kein Default gesetzt | Kein Fehler; Participants sehen feste Route ohne Wahlmöglichkeit |
| Keine Berechtigung | ForbiddenError |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /api/payment-settings | Lädt participant_* Felder |
| PATCH | /api/payment-settings | Speichert participant_* Felder |
| GET | /api/public/payment-policy | Liefert `build_public_payment_policy_payload()` ans Participant-Portal |

## Offene Fragen

- Wo genau sehen Participants die `participant_payout_instructions`? Im Portal-Header oder bei jeder Methode?
- Welche Auswirkung hat `participant_can_update_payout_details: false` auf bestehende Payout-Daten?
- Gibt es eine Vorschau-Funktion, wie das Portal für Participants aussieht?

## Notizen

- `build_public_payment_policy_payload()` filtert disabled Methoden heraus und liefert nur aktivierte Methoden mit ihren Field-Definitionen ans Portal
- Default: beide Toggles `true`, default method `bank_transfer`
- `participant_payout_instructions` ist im Default `null` (kein Anweisungstext)
