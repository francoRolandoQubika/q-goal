---
document_type: service
summary: >-
  `@q-goal/ui` is a shared React component library that provides the design
  system and reusable UI components for the web frontend. It exports
  shadcn/ui-based ...
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - service
  - typescript
  - library
service_id: ui
---
# UI Library

## Purpose

`@q-goal/ui` is a shared React component library that provides the design system and reusable UI components for the web frontend. It exports shadcn/ui-based primitives, Base UI components, icon wrappers (lucide-react), and utility functions for Tailwind CSS styling. The library ensures a single source of truth for visual consistency across [[web]].

## Public API / Surface

- **Components**: React primitives built on shadcn/ui and Radix UI (Button, Form components, and others); stored in `src/components/{name}.tsx`
- **Utilities**: `cn()` — class variance authority function for conditional Tailwind CSS class merging; utility helpers in `src/lib/utils.ts`
- **Icons**: Re-exported lucide-react icons for consistent iconography
- **Custom hooks**: (not determined by analysis)

All exports are consumed via `@q-goal/ui` barrel imports in [[web]] and other workspace packages.

## Internal Architecture

The library is organized into two tiers:

1. **Component layer** (`src/components/`) — Copy-paste React components based on shadcn/ui, built on Base UI / Radix UI primitives, styled with Tailwind CSS
2. **Utility layer** (`src/lib/utils.ts`) — Helper functions (especially the `cn()` class-merge utility) and custom hooks

Styling is purely className-based via Tailwind CSS (no CSS-in-JS runtime). The `cn()` utility is a frequent dependency point (high bridge coupling score: 0.00109), indicating it is central to conditional styling across the application.

## Request Lifecycle

(Not applicable — this is a library package, not a service with request handlers.)

## Data Layer

(Not applicable — UI library does not own persistent data.)

## Configuration

(No environment variables consumed.)

## Integrations

- **[[web]]** — Primary consumer via `@q-goal/ui` imports
- **React 19** — Peer dependency; all components are functional React components
- **Tailwind CSS** — Single source of styling; processed at build time
- **@base-ui/react** — Headless component primitives (Radix UI compatible)
- **lucide-react** — Icon library, re-exported for consistent usage

## Service-Specific Patterns

**shadcn/ui copy-paste model**: Components are not published as independent npm modules but copied and customized within the library. This allows the team to own implementation details without external release dependencies.

**Class merging via `cn()`**: Conditional Tailwind CSS class composition through a utility function; widely used across component variants and conditional styling.

**Component-first API**: All public exports are React components or styling utilities; no data models, services, or business logic resides in this package.
