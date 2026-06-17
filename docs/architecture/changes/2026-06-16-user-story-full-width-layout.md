# User Story Full Width Layout

## Context

The generated user-story review page used the same Docusaurus document content
container as prose documentation. On wide screens this left the interactive
story list and detail view constrained to a documentation-style content width
instead of using the available workspace width.

## Change

Archdoc review pages that render through `.endpointTableWrapper` now opt out of
the default Docusaurus max-width on desktop. The container uses the full
available width with page padding, and the user-story view has an explicit
responsive grid:

- fixed-width story list column
- fluid detail column
- single-column layout on smaller screens

## Verification

- CSS-only scoped change under `site/src/css/custom.css`
- verified the user-story layout classes are nested under the existing Archdoc
  wrapper used by generated review pages
