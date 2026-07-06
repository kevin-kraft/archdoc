---
id: US-FIN-012
title: Zahlungsmethoden aktivieren und konfigurieren
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /settings/payments
  - method: PUT
    path: /settings/payments
  - method: GET
    path: /available
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
  - payment_providers
---

# US-FIN-012 – Zahlungsmethoden aktivieren und konfigurieren

## User Story

Als **Finance Admin** möchte ich jede Zahlungsmethode einzeln aktivieren, konfigurieren und mit den richtigen Empfängerfeldern versehen,
damit Participants ihre Auszahlung über den korrekten Kanal erhalten und alle nötigen Daten erfasst werden.

## Kontext

Utilis unterstützt fünf Zahlungsmethoden: Bank transfer, PayPal, Wero, Institution backoffice und External payout provider. Jede Methode hat eigene Routing-Logik, Recipient-Felder und Sichtbarkeitsregeln für das Participant-Portal. Mindestens eine Methode muss immer aktiv sein. Die `external_provider`-Methode erfordert zusätzlich eine aktive Provider-Bindung (`provider_key`).

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Abschnitt "Payment methods" ist aufgeklappt
- [ ] Für `external_provider`: Mind. ein aktiver Payment Provider ist unter "Payment Providers" konfiguriert

## Ablauf
Navbar: Payout Settings
1. Benutzer sieht alle 5 Methoden mit Status-Badge (*Enabled*/*Disabled*) und Typ-Badge (*Participant Selectable* / *Organization Managed*)
2. Benutzer klappt eine Methode auf (Chevron-Icon)
3. Benutzer bearbeitet:
   - **Display name** (Freitext, Pflicht)
   - **Processing time (days)** (Integer >= 0, Pflicht)
   - **Recipient source** (Dropdown): `participant_profile`, `institution_backoffice`, `external_provider`, `on_site`
   - **Bound provider** (nur bei `external_provider`-Methode): Dropdown aktiver Provider-Keys
   - **Participant instructions** (Freitext, optional)
   - **Minimum amount (EUR)** und **Maximum amount (EUR)** (optional, min <= max)
   - Toggle: **Participant can select this method**
4. Benutzer konfiguriert **Required recipient fields** und **Optional recipient fields** via Toggles:
   - Verfügbare Felder: Account holder, IBAN, BIC/SWIFT, Bank name, PayPal email, Wero identifier, External payout account
   - Ein Feld kann nicht gleichzeitig required und optional sein
5. Benutzer aktiviert/deaktiviert die Methode über den Toggle oben rechts in der Methodenkarte
6. Benutzer klickt **Save Changes** → System validiert, speichert, reconciliert

## Akzeptanzkriterien

- [ ] Alle 5 Methoden sind sichtbar und einzeln aufklappbar
- [ ] Jede Methode hat unabhängigen Enable/Disable-Toggle
- [ ] Mindestens eine Methode muss aktiviert bleiben – Deaktivierung der letzten aktiven Methode ist blockiert
- [ ] `external_provider`-Methode zeigt "Bound provider"-Dropdown; wird sie ohne `provider_key` aktiviert, erscheint Validierungsfehler
- [ ] Ein Feld kann nicht gleichzeitig Required und Optional sein
- [ ] `minimum_amount` > `maximum_amount` erzeugt Validierungsfehler
- [ ] Methoden mit `participant_selectable: false` (Institution backoffice, External provider) sind nicht im Participant-Portal sichtbar
- [ ] Nach Save: Badge-Status (*Enabled*/*Disabled*) aktualisiert sich sofort
- [ ] Operating Summary zeigt korrekte Anzahl aktiver Methoden

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Letzte aktive Methode deaktivieren | Validierungsfehler: "At least one payment method must be enabled" |
| External provider aktiviert ohne Provider-Bindung | Validierungsfehler: "External provider routes must bind an enabled provider_key" |
| Provider-Key referenziert deaktivierten Provider | Validierungsfehler: "Payment settings reference disabled or unknown providers" |
| `minimum_amount` > `maximum_amount` | Validierungsfehler: "Minimum amount cannot exceed maximum amount for method '...'" |
| `participant_can_select_method` aktiv, aber keine selectable Methode aktiv | Validierungsfehler: "Participant payout-method selection requires at least one enabled participant-selectable method" |
| Keine Berechtigung | ForbiddenError |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /admin/settings/payments | Lädt alle Methoden-Konfigurationen |
| PUT | /admin/settings/payments | Speichert aktualisierte payment_methods |
| GET | /financial/providers/available | Lädt verfügbare aktive Provider für Bound provider-Dropdown |

## Offene Fragen

- Kann eine neue Methode mit Custom `method`-Key angelegt werden, oder nur die 5 vordefinierten?
- Wird bei Deaktivierung einer Methode, die Participants bereits ausgewählt haben, eine Warnung angezeigt?
- Welche `recipient_source`-Optionen sind in der UI sichtbar (`on_site` fehlt in den Screenshots)?

## Notizen

- Standardmäßig ist nur `bank_transfer` aktiviert; alle anderen Methoden sind `disabled`
- `institution_backoffice` und `external_provider` haben `participant_selectable: false` – sie tauchen nie im Participant-Portal auf
- Ein Feld in `optional_recipient_fields` wird automatisch entfernt, wenn es auch in `required_recipient_fields` ist (Backend-Normalisierung)
