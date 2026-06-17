# User Story Workspace Layout

## Context

The user-story review page became cramped once the story list, story markdown,
trace flow, endpoint links, and the Docusaurus navigation all competed for
horizontal space.

## Change

The user-story page now behaves more like a review workspace:

- the story selection list can be collapsed from inside the page
- the detail pane expands to the full available width when the list is hidden
- story detail content is split into tabs:
  - Story
  - Trace
  - Endpoints
- the top filter row includes the story-list toggle next to area/status/linkage

This keeps the Docusaurus shell stable while giving the active review workflow
more horizontal room.

## Verification

- `node node_modules/typescript/bin/tsc`
- verified generated CSS contains the collapsed layout, tabs, and toggle rules
