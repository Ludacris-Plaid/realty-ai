# Email System Overhaul Plan

## Problem
Two disconnected email data pipelines causing confusion:
- **Email tab** (`/dashboard/email`): Uses `gmailApi` (Gmail sync → EmailMessage table)
- **Daily Briefing Inbox widget**: Uses `messages.listConversations()` (webhook pipeline → Conversation table)
- Links point to `/dashboard/messages` which shows webhook data, not real Gmail emails

## Solution
Unify everything on the Gmail pipeline. Webhook messages remain as a separate inbound channel for SMS/webhook test data.

---

## Phase 1: Auto-Process Emails on Sync
**File**: `backend/app/api/gmail.py`

When user clicks Sync:
1. Fetch emails from Gmail via `gmailApi.sync()`
2. Auto-run AI classification on new emails (`EmailAIService.process_email`)
3. AI extracts: classification, lead info, suggested action
4. Auto-generate draft replies for `buyer_lead`, `seller_lead`, `follow_up_required`
5. Return sync + processed count

**Key function**: Rewrite `POST /gmail/sync` to chain `sync_emails()` → `process_all()` automatically when `process=true` (default).

---

## Phase 2: Unify Daily Briefing Inbox
**File**: `frontend/src/app/dashboard/page.tsx`

**Changes:**
1. Replace `messages.listConversations()` with `gmailApi.list(10)` for the email widget
2. All inbox links: `/dashboard/messages` → `/dashboard/email`
3. Show real email subjects, senders, AI classifications in the briefing widget
4. Show unread count from Gmail emails

---

## Phase 3: Standardize Email Page Flow
**File**: `frontend/src/app/dashboard/email/page.tsx`

**Changes:**
1. Sync button triggers auto-processing (Phase 1 covers this)
2. Show processing results (X emails classified, Y drafts created)
3. Tabs: Inbox | Drafts | Sent
4. Drafts panel auto-refreshes after sync

---

## Phase 4: Sidebar Link Fix
**File**: `frontend/src/components/layout/sidebar.tsx`

**Change**: Keep Email tab as `/dashboard/email` (already correct). Optionally remove standalone `/dashboard/messages` as its own tab since it's now combined under Email.

---

## Files to Modify
1. `backend/app/api/gmail.py` — add auto-processing after sync
2. `frontend/src/app/dashboard/page.tsx` — fix inbox widget data source + links
3. `frontend/src/app/dashboard/email/page.tsx` — show processing results after sync
4. `frontend/src/lib/api.ts` — ensure gmailApi.list() returns the right data

## Expected User Flow After Fix
1. User clicks **Sync** in Email tab
2. Gmail emails fetched → AI classifies → drafts generated
3. User sees inbox populated with classified emails
4. User clicks email → sees AI suggestion → clicks Reply
5. Compose opens with Athena draft assistant (already built)
6. User asks Athena to draft → clicks Import Draft → edits → Send

## Daily Briefing Email Widget
Shows:
- Latest 3 synced Gmail emails (subject, sender, AI classification badge)
- Unread count
- Link to `/dashboard/email`
