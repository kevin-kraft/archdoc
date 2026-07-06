---
id: US-ADMIN-002
title: List users
area: admin
status: draft
owner: Architecture Demo
endpoints:
  - method: GET
    path: /users
    purpose: Loads the user list for administration workflows.
roles:
  - admin
---

# US-ADMIN-002 - List users

## User Story

Als **Admin** moechte ich **alle Nutzer in einer Liste sehen**,
damit **ich Benutzerkonten schnell pruefen und verwalten kann**.

## Kontext

Diese Story dient als zweite Demo-Story, damit die User-Story-Ansicht zwischen
mehreren Eintraegen wechseln kann.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf die User-Verwaltung
- [ ] Es existieren Nutzer im System

## Ablauf

1. Admin oeffnet die User-Verwaltung.
2. System laedt die User-Liste.
3. Admin sucht oder filtert nach einem User.
4. System zeigt passende Ergebnisse.

## Akzeptanzkriterien

- [ ] User-Liste wird geladen
- [ ] Berechtigungen werden geprueft
- [ ] Leere Ergebnislisten werden verstaendlich angezeigt
- [ ] Fehler beim Laden werden sichtbar gemacht

## Fehlerfaelle

| Fall | Erwartetes Verhalten |
|---|---|
| Keine Berechtigung | Zugriff verweigern |
| Keine Nutzer gefunden | Leeren Zustand anzeigen |
| Serverfehler | Fehlermeldung anzeigen |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /users | Laedt die User-Liste |

## Offene Fragen

- Welche Filter und Suchfelder gehoeren fachlich zur ersten Version?
