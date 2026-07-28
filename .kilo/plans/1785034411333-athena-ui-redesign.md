# Athena UI/UX Redesign — Implementation Plan

## Design System

| Token | Value |
|-------|-------|
| **Style** | Minimalism + Swiss Style (clean, high contrast, spacious) |
| **Primary (Olive/Sage)** | `#7C8A5A` (600), `#5E6B45` (800), `#96A874` (400) |
| **Gold accent** | `#D4A853` (CTA, active, highlights) |
| **Ivory white** | `#FFFAF5` (background), `#FFF8F0` (cards) |
| **Warm gray** | `#5C4F3C` (text), `#8B7D6B` (muted), `#D4C5B2` (borders) |
| **Heading font** | Cinzel (serif, 400-700) — Google Fonts |
| **Body font** | Josefin Sans (sans-serif, 300-600) — Google Fonts |
| **Icons** | Lucide React (no emoji icons) |

## Target Repo

`/home/dysthemix/projects/realty-ai-v1/` (the V1 rebuild)

---

## Phase 1: Foundation — Design Token Overhaul

### 1.1 Tailwind Config + globals.css
- Extend `tailwind.config.ts`:
  - `colors.olive` scale: 50-900 from sage green palette
  - `colors.gold` scale: 50-900 from gold/amber palette
  - `colors.ivory` scale: warm white tones
  - `fontFamily.cinzel`: `['Cinzel', 'serif']`
  - `fontFamily.josefin`: `['Josefin Sans', 'sans-serif']`
  - `animation`: fade-in, slide-up, subtle-pulse (for owl), shimmer
  - `keyframes`: matching keyframe definitions
- Update `globals.css`:
  - Google Fonts import (Cinzel + Josefin Sans)
  - CSS custom properties for theme colors
  - `body` uses `font-family: 'Josefin Sans'`, `bg-ivory`, `text-warm-900`
  - Scrollbar styling (thin, olive-toned)
  - Remove old `--foreground`/`--background` vars

### 1.2 Auth Pages (Login + Signup)
- Replace blue gradient with ivory background + olive accent border
- Cinzel heading "RealtyAI", Josefin Sans form labels
- Inputs: `border-warm-200`, `focus:border-olive-500`, `focus:ring-olive-200`
- CTA button: `bg-gold-500` → `hover:bg-gold-600`, text `warm-900`
- Signup link: `text-olive-600`
- Add subtle olive-branch SVG divider between form and footer

### 1.3 Dashboard Layout
- Sidebar: `bg-ivory border-r border-warm-200`
- Header: `bg-ivory border-b border-warm-200`, avatar circle `bg-olive-600`
- Main content: `bg-ivory-50`
- Replace all `gray-*` references across the dashboard layout shell

---

## Phase 2: Expandable Chat Panel (Sidebar)

### 2.1 Create `ChatPanel` Component
File: `frontend/src/components/chat/chat-panel.tsx`
- Collapsed state (default): compact `48px` bar with "Ask Athena..." input + owl icon button
- Clicking the bar or owl button expands the panel
- Expanded state: `320px` tall, scrollable, contains:
  - Message list (last 15 messages, auto-scroll)
  - Textarea input + send button at bottom
  - Collapse button (chevron-up) in top-right
  - Owl SVG animates subtly while Athena is thinking
- Height animates via `max-height` transition with `overflow-hidden`
- Nav items below the panel shift down smoothly using `translate-y` on the nav container

### 2.2 Chat Panel State Management
- Extract chat state from `/dashboard/chat/page.tsx` into a shared hook: `frontend/src/hooks/use-chat.ts`
  - `messages`, `convId`, `sending`, `handleSend`
- `ChatPanel` and `/dashboard/chat/page.tsx` both consume the same hook
- Chat panel in sidebar shares conversation with full chat page (same `convId` in state)

### 2.3 Sidebar Layout Restructuring
- Move `ChatPanel` to top of sidebar, above nav
- Nav container gets `mt-0 transition-transform duration-300` — shifts down when chat expands
- Sidebar height: `h-screen` with `flex flex-col`
- Nav section: `flex-1 overflow-y-auto`
- Logout stays at bottom

### 2.4 Typing Indicator → Animated Owl
- Create SVG owl component: `frontend/src/components/chat/athena-owl.tsx`
  - Owl silhouette (simple, elegant, geometric)
  - CSS animation: subtle head tilt + eye blink (3s cycle)
  - While Athena is "thinking": owl's eyes glow gold, gentle wing flutter
  - SVG inline, no external assets
- Replace bouncing dots in chat with owl animation

---

## Phase 3: Chat Response Formatting

### 3.1 Enhanced Markdown Rendering
- Create `frontend/src/components/chat/markdown-renderer.tsx`
- Wraps `ReactMarkdown` with custom components:
  - Tables: `rounded-lg border border-warm-200 overflow-hidden`
  - Code blocks: `bg-warm-50 border border-warm-200 rounded-lg` (no inline code styling for real estate data)
  - Links: `text-olive-600 hover:text-olive-700 underline`
  - Lists: styled with gold `::marker` bullets
  - Blockquotes: left `border-olive-400`, `bg-olive-50`, italic for legal disclaimers
  - Images: `rounded-lg max-w-full shadow-sm` for property photos in chat
- Add `remark-gfm` for tables, strikethrough, task lists (already in package.json)

### 3.2 Structured Data Cards in Chat
- When Athena returns listings, detect property data and render as styled cards inline
- Match property addresses to DB records, show thumbnail + price + link to detail page
- Property card inline component: small thumbnail, price, beds/baths, "View Details →" link

### 3.3 Chat Bubble Styling
- User bubble: `bg-olive-600 text-white rounded-2xl rounded-br-md`
- Assistant bubble: `bg-white text-warm-900 rounded-2xl rounded-bl-md shadow-sm border border-warm-100`
- Bot avatar: gradient circle with owl SVG (small, 32px)
- User avatar: `bg-gold-500` circle with first letter

---

## Phase 4: SVG Animations + Graphics

### 4.1 Athena Owl Logo Component
- `frontend/src/components/shared/athena-owl-logo.tsx`
- Full owl SVG: geometric shapes, gold/olive colors
- States:
  - `idle`: gentle breathing animation (scale 1→1.02→1 over 4s)
  - `loading/thinking`: eyes glow gold, slight head tilt, pulse
  - `success`: brief celebratory wing spread (1.5s, plays once)
- Used in: chat typing indicator, sidebar header, empty states, favicon

### 4.2 Olive Branch Background Pattern
- `frontend/src/components/shared/olive-pattern.tsx`
- Subtle repeating SVG pattern: olive branch motifs, Greek key meander border
- Used as `background-image` on: empty states, briefing cards, dashboard hero section
- Very low opacity (5-10%) so it doesn't compete with content

### 4.3 Stat Card Entrance Animations
- Dashboard stat cards get staggered `fade-in-up` animation on load
- Each card: `opacity-0 translate-y-4` → `opacity-100 translate-y-0` with staggered delay (0ms, 100ms, 200ms)
- Card hover: subtle gold border glow + 2px lift
- SVG decorative element in top-right corner of each card: small geometric Greek key motif in `text-olive-200`

### 4.4 Page Transition Animations
- All dashboard page transitions: `fade-in` (150ms) with `slide-up` (100ms)
- Use CSS `@keyframes` defined in tailwind config, applied via utility classes
- No layout shift during transitions

---

## Phase 5: Scraping Fix — Better Parsing + Zillow Links

### 5.1 Backend: Fix `listing_service.py` scrape_zillow
File: `backend/app/services/listing_service.py`

Current issues:
1. Only extracts one image URL per listing (regex searches ENTIRE text, not per-block)
2. No Zillow URL extraction
3. Address parsing is fragile (uses `lines[0]`)

Fixes:
- Extract all image URLs within each property block, not globally
- Generate Zillow search URL from address: `https://www.zillow.com/homes/{address_slug}_rb/`
- Better address parsing: use the first line that looks like an address (contains numbers + street name)
- Extract MLS ID if present in the data
- Store multiple images as array, not single-element
- Add `zillow_url` field to each property before import

### 5.2 Frontend: Listing Card Redesign
File: `frontend/src/app/dashboard/listings/page.tsx`

- Card: `bg-white rounded-xl shadow-sm border border-warm-200 hover:shadow-md hover:border-gold-300 transition-all duration-200`
- Image: `h-48 w-full object-cover rounded-t-xl`
- Multiple images: show first as hero, tiny thumbnails below for rest (2-3 small squares)
- Price: `text-gold-600 font-bold text-lg` (Cinzel)
- Address: `text-warm-900 font-medium` (Josefin Sans)
- Details row: beds | baths | sqft in `text-warm-500 text-sm`
- "View on Zillow →" link below details: `text-olive-600 text-xs hover:underline`
- Status badge: `bg-olive-100 text-olive-700` (active), `bg-gold-100 text-gold-800` (pending)
- Grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`

### 5.3 Frontend: Listing Detail Page Redesign
File: `frontend/src/app/dashboard/listings/[id]/page.tsx`

- Hero image gallery: horizontal scroll with all images, click to lightbox
- Price in large Cinzel heading, gold color
- Address + "View on Zillow" external link button
- Key details as icon-grid: beds | baths | sqft | year | lot size, each in a card with olive icon
- Description in prose with Josefin Sans
- Back button with `← Back to listings`

---

## Phase 6: Global Component Restyle

### 6.1 All Cards, Buttons, Inputs
- Cards: `bg-white rounded-xl shadow-sm border border-warm-200`
- Primary button: `bg-gold-500 hover:bg-gold-600 text-warm-900 font-medium`
- Secondary button: `border border-olive-300 text-olive-700 hover:bg-olive-50`
- Danger button: `text-red-600 hover:bg-red-50 border border-red-200`
- Inputs: `border-warm-200 focus:border-olive-500 focus:ring-1 focus:ring-olive-300`
- Selects: same input styling

### 6.2 Sidebar Navigation
- Nav items: `text-warm-600 hover:bg-olive-50 hover:text-olive-700`
- Active nav item: `bg-olive-100 text-olive-800 font-medium border-l-2 border-gold-500`
- Icons: 20x20, consistent sizing
- Collapse/expand toggle: gold owl icon button

### 6.3 Header
- Background: `bg-ivory/90 backdrop-blur-sm border-b border-warm-200`
- User avatar: `bg-olive-600 text-white font-cinzel`
- Notification bell (future): gold outline icon

### 6.4 Empty States, Error States, Loading
- EmptyState component: olive branch pattern background, Cinzel heading
- ErrorState: `border-red-200 bg-red-50`, gold retry button
- Loading: `Skeleton` components with `bg-warm-200 animate-pulse`
- Toast notifications: `bg-gold-50 border-gold-200 text-warm-800` (success), `bg-red-50 border-red-200` (error)

---

## Phase 7: Page-Specific Polish

### 7.1 Dashboard Overview
- Greeting in Cinzel: "Welcome back, {name}"
- Stat cards: olive-branch SVG pattern in corner, staggered entrance animation
- AI Briefing card: `bg-gradient-to-br from-olive-50 to-gold-50 border border-warm-200`
- Quick actions: icon + label cards with hover gold border

### 7.2 Clients Page
- Client cards: hover gold border, pre-approved = gold checkmark
- Search bar: `rounded-full` (pill shape), gold magnifying glass icon
- Add Client modal: olive-tinted backdrop, Cinzel heading

### 7.3 Tasks Page
- Kanban columns: `bg-ivory border-t-4` (olive, gold, olive-dark for each column)
- Task cards: `bg-white shadow-sm`, priority dot instead of badge
- New task form: inline, gold buttons

### 7.4 Memory Page, Messages Page, Settings Page
- Apply consistent card/input/button styling
- Memory cards: category badge in olive, semantic search scores in gold

---

## Validation Plan

After each phase:
1. `cd /home/dysthemix/projects/realty-ai-v1/frontend && npx tsc --noEmit` — zero TS errors
2. `cd /home/dysthemix/projects/realty-ai-v1 && docker compose up -d` — backend + frontend healthy
3. `curl http://localhost:8000/api/v1/health` — backend ok
4. `curl http://localhost:3000/` — frontend serves 200
5. Visual check: `/login`, `/signup`, `/dashboard`, sidebar chat panel

## File Manifest

### Files to Create
- `frontend/src/components/chat/chat-panel.tsx`
- `frontend/src/components/chat/athena-owl.tsx`
- `frontend/src/components/chat/markdown-renderer.tsx`
- `frontend/src/components/shared/athena-owl-logo.tsx`
- `frontend/src/components/shared/olive-pattern.tsx`
- `frontend/src/hooks/use-chat.ts`

### Files to Modify
- `frontend/tailwind.config.ts` — add olive/gold/ivory colors, fonts, animations
- `frontend/src/app/globals.css` — Google Fonts import, theme variables
- `frontend/src/app/layout.tsx` — font class application
- `frontend/src/components/layout/sidebar.tsx` — add ChatPanel, restyle nav
- `frontend/src/components/layout/header.tsx` — olive/ivory restyle
- `frontend/src/components/shared/skeleton.tsx` — warm gray tones
- `frontend/src/components/shared/empty-state.tsx` — olive branch pattern
- `frontend/src/components/shared/error-state.tsx` — gold retry button
- `frontend/src/components/shared/toast.tsx` — gold/olive colors
- `frontend/src/components/clients/client-card.tsx` — new card design
- `frontend/src/components/clients/client-form-modal.tsx` — olive backdrop
- `frontend/src/app/dashboard/layout.tsx` — ivory background
- `frontend/src/app/dashboard/page.tsx` — greeting + stat card animations
- `frontend/src/app/dashboard/chat/page.tsx` — use shared hook
- `frontend/src/app/dashboard/clients/page.tsx` — search bar + card grid
- `frontend/src/app/dashboard/clients/[id]/page.tsx` — detail page
- `frontend/src/app/dashboard/listings/page.tsx` — cards + Zillow links
- `frontend/src/app/dashboard/listings/[id]/page.tsx` — gallery + detail
- `frontend/src/app/dashboard/tasks/page.tsx` — kanban colors
- `frontend/src/app/dashboard/memory/page.tsx` — search + cards
- `frontend/src/app/dashboard/messages/page.tsx` — inbox
- `frontend/src/app/dashboard/settings/page.tsx` — integrations
- `frontend/src/app/dashboard/briefing/page.tsx` — gold/olive cards
- `frontend/src/app/login/page.tsx` — olive branch + gold CTA
- `frontend/src/app/signup/page.tsx` — olive branch + gold CTA
- `frontend/src/lib/api.ts` — add Zillow URL to Property type
- `backend/app/services/listing_service.py` — fix image extraction + Zillow links
