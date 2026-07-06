---
id: US-FIN-002
title: Neuen Zahlungsanbieter hinzufügen
area: finance
status: draft
priority: high
owner: Pieric Brast
endpoints:
  - method: GET
    path: /available
  - method: GET
    path: routers.payment_providers.get.list-providers
roles:
  - admin
tables:
  - payment_providers
---

# US-FIN-002 - Neuen Zahlungsanbieter hinzufügen

## User Story

Als **Admin** möchte ich einen neuen Zahlungsanbieter konfigurieren,
damit das System Auszahlungen über diesen Anbieter durchführen kann.

## Kontext

Über den "+ Anbieter hinzufügen"-Button öffnet sich ein Dialog, in dem ein neuer Zahlungsanbieter aus einer Liste verfügbarer Adapter ausgewählt und konfiguriert werden kann.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Es gibt noch nicht konfigurierte Anbieter (sonst ist der Button deaktiviert)

## Ablauf

1. Benutzer öffnet die Seite Finanzen → Zahlungsanbieter
2. Benutzer klickt auf "+ Anbieter hinzufügen"
3. Ein Dialog öffnet sich
4. Benutzer wählt einen Anbieter aus der Dropdown-Liste aus
5. Benutzer gibt einen Anzeigenamen ein
6. Benutzer gibt optional Zugangsdaten (JSON) ein
7. Benutzer gibt optional Konfiguration (JSON) ein
8. Benutzer wählt ob der Anbieter sofort aktiviert werden soll
9. Benutzer klickt auf "Anbieter hinzufügen"
10. System speichert den neuen Anbieter
11. System zeigt Erfolgsmeldung und aktualisiert die Liste

## Akzeptanzkriterien

- [ ] Dialog öffnet sich beim Klick
- [ ] Alle verfügbaren Anbieter sind in der Dropdown-Liste aufgeführt
- [ ] Anzeigename wird automatisch befüllt wenn ein Anbieter gewählt wird
- [ ] Pflichtfelder (Anbieter, Name) werden validiert
- [ ] Stub-Anbieter zeigen eine Warnmeldung
- [ ] Nach Erfolg schließt sich der Dialog und die Liste wird aktualisiert
- [ ] Button ist deaktiviert wenn alle verfügbaren Anbieter bereits konfiguriert sind

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Pflichtfeld fehlt | Button bleibt deaktiviert |
| Ungültiges JSON in Credentials | Fehlermeldung anzeigen |
| Serverfehler | Fehlermeldung "Anbieter konnte nicht hinzugefügt werden" |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /api/payment-providers/available | Lädt verfügbare Anbieter-Typen |
| POST | /api/payment-providers | Erstellt neuen Anbieter |

## Offene Fragen

- Welche JSON-Felder werden für die einzelnen Anbieter benötigt?

## Notizen

- Button ist deaktiviert wenn `unconfiguredProviders.length === 0`
- Stub-Anbieter (z.B. PayPal) zeigen Badge "Demnächst verfügbar"
