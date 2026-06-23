---
document_type: service
summary: >-
  The **ui** package is a shared React component library providing reusable,
  accessible UI components built on Base UI primitives and Tailwind CSS. It is
  consu...
last_updated: '2026-06-23T22:59:00.000Z'
tags:
  - service
  - typescript
  - library
  - react
  - base-ui
service_id: ui
---
# UI Component Library

## Purpose

The **ui** package is a shared React component library providing reusable, accessible UI components built on Base UI primitives and Tailwind CSS. It is consumed by [[web]] and other client applications throughout the monorepo, ensuring visual consistency and reducing duplication.

## Public API / Surface

The library exports React components from `src/components/` (e.g., Button, Dialog) and utility functions from `src/lib/utils.ts` (e.g., `cn` for className composition). Components are built with the CVA (Class Variance Authority) pattern for type-safe variant selection and compose Base UI unstyled primitives. `dialog.tsx` exports `Dialog`, `DialogTrigger`, `DialogPortal`, `DialogBackdrop`, `DialogPopup`, `DialogTitle`, `DialogDescription`, `DialogClose`, `DialogFooter`, and a generic `ConfirmDialog` molecule (controlled, with `title`/`description`/`confirmLabel`/`cancelLabel`/`destructive` props).

## Internal Architecture

The library follows a component-driven structure:

- **components/** — Reusable React components wrapping Base UI unstyled primitives. Each component is styled via Tailwind CSS and uses CVA for variant management.
- **lib/utils.ts** — Utility functions for common tasks (e.g., `cn` for merging Tailwind classes with clsx and tailwind-merge).

Components apply variant logic via CVA and render Base UI nodes to the DOM. Styling is scoped via Tailwind's `data-slot` attribute targeting and arbitrary CSS modifiers.

## Request Lifecycle

Not applicable—ui is a component library with no request/response cycle. Components are imported by consuming applications and rendered in JSX.

## Data Layer

(no data layer)

## Configuration

(no environment variables consumed)

## Integrations

**External Dependencies:**
- React 19.2.6
- Base UI 1.0.0 (headless component primitives)
- lucide-react (icon library)
- next-themes (theme switching support)
- TailwindCSS v4
- Class Variance Authority (CVA)
- clsx + tailwind-merge (className utilities)

**Consumed By:**
- [[web]] (React SPA frontend)
- External projects via npm workspaces (@q-goal/ui)

## Service-Specific Patterns

**CVA (Class Variance Authority):** Components use CVA to define type-safe, composable variant combinations. Each component exposes a `variants` object mapping variant names (e.g., `variant`, `size`) to Tailwind class strings, enabling consumers to select styles declaratively.

**Base UI Wrapping:** All components wrap unstyled Base UI primitives (e.g., ButtonPrimitive), delegating accessibility and DOM semantics to Base UI while applying Tailwind styling on top.

**TailwindCSS v4 Arbitrary Modifiers:** The library leverages Tailwind v4 arbitrary modifiers (e.g., `[a]:hover:`, `[&_svg]:`) for context-dependent styling within components without additional CSS.

**data-slot Attributes:** Components use `data-slot` attributes (e.g., `data-slot='button'`) as semantic selectors, replacing fragile class-name-based targeting.
