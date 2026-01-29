# Example Usage Scenarios

## Scenario 1: Automatic Priority Detection

When a user sends a message containing priority keywords, the bot automatically detects and tags it:

**User message:**
```
"This is an urgent issue with the production server!"
```

**Bot action:**
- Detects keyword "urgent" → CRITICAL priority
- Adds 🔴 (red_circle) reaction to the message
- Logs: "Auto-detected CRITICAL priority for message"

---

## Scenario 2: Manual Priority Assignment

**Step 1:** User sends a message
```
"We need to update the documentation before the release"
```

**Step 2:** User types `/prioritize` in the same channel

**Step 3:** Bot responds with interactive buttons (ephemeral message visible only to user):
```
Set Message Priority:
[🔴 Critical] [🟠 High] [🟡 Medium] [🟢 Low]
```

**Step 4:** User clicks "🟠 High" button

**Step 5:** Bot actions:
- Finds user's most recent message
- Adds 🟠 (orange_circle) reaction
- Confirms: "🟠 Message prioritized as high!"

---

## Scenario 3: Priority Keywords Reference

**User types:** `/priority-keywords`

**Bot responds (ephemeral):**
```
Priority Detection Keywords:

🔴 CRITICAL: urgent, emergency, critical, asap, immediately
🟠 HIGH: important, priority, deadline, blocker
🟡 MEDIUM: soon, needed, required
🟢 LOW: fyi, info, update

Messages containing these keywords will be automatically tagged with the 
corresponding priority level.
```

---

## Scenario 4: App Home Dashboard

**User clicks on the app name in Slack sidebar**

**Bot displays:**
```
📊 Message Priority Dashboard

Welcome to the Slack Message Prioritization App!

This app helps you manage and prioritize your messages effectively.

─────────────────────────────────────

How it works:

• 🤖 Automatic Detection: Messages with priority keywords are automatically tagged
• 🔘 Manual Tagging: Use /prioritize to manually set message priority
• 📝 View Keywords: Use /priority-keywords to see the priority detection keywords
• 🎨 Visual Indicators: Priority levels are shown with colored emoji reactions

─────────────────────────────────────

Priority Levels:

🔴 Critical - Urgent issues requiring immediate attention
🟠 High - Important tasks with deadlines
🟡 Medium - Standard priority items
🟢 Low - Informational updates and FYIs

─────────────────────────────────────

Commands:

/prioritize - Manually prioritize your last message
/priority-keywords - View priority detection keywords
```

---

## Scenario 5: Multiple Keywords (Highest Priority Wins)

**User message:**
```
"FYI: This is an urgent security issue that needs immediate attention"
```

**Bot action:**
- Detects "fyi" (LOW), "urgent" (CRITICAL), "immediate" (CRITICAL)
- Applies highest priority: CRITICAL
- Adds 🔴 (red_circle) reaction

**Note:** The priority detection algorithm checks keywords in order from highest to lowest priority, returning the first match found.

---

## Scenario 6: Word Boundary Detection

The app uses word boundary matching to avoid false positives:

**Message 1:** `"This is important information"`
- Detects "important" as a complete word → 🟠 HIGH priority

**Message 2:** `"We are reformatting the document"`
- Contains "info" as substring but NOT as a word → ⚪ No priority

**Message 3:** `"The deadline is tomorrow"`
- Detects "deadline" as a complete word → 🟠 HIGH priority

---

## Scenario 7: Changing Priority

**Initial state:**
- User message has 🟢 (low priority) reaction

**User action:**
- Types `/prioritize`
- Clicks "🔴 Critical" button

**Bot action:**
- Removes existing 🟢 reaction
- Adds new 🔴 reaction
- Confirms: "🔴 Message prioritized as critical!"

---

## Scenario 8: Threaded Messages

**User sends a threaded reply:**
```
Thread: "Original message"
  └─ Reply: "This is urgent - we need to fix this ASAP!"
```

**Bot action:**
- Detects "urgent" and "asap" in the thread reply
- Adds 🔴 reaction to the threaded message
- Both the thread and channel see the priority indicator

---

## Configuration Examples

### Custom Keywords

Edit `.env` to customize priority keywords for your team:

```env
# Sales team example
CRITICAL_KEYWORDS=urgent,emergency,critical,deal-breaker,client-escalation
HIGH_KEYWORDS=important,priority,deadline,hot-lead,proposal-due
MEDIUM_KEYWORDS=soon,needed,follow-up,reminder
LOW_KEYWORDS=fyi,info,update,heads-up,note

# Development team example
CRITICAL_KEYWORDS=urgent,emergency,critical,production-down,security-breach
HIGH_KEYWORDS=important,priority,deadline,blocker,regression
MEDIUM_KEYWORDS=soon,needed,required,tech-debt
LOW_KEYWORDS=fyi,info,update,refactor,nice-to-have

# Support team example
CRITICAL_KEYWORDS=urgent,emergency,critical,p0,sev1
HIGH_KEYWORDS=important,priority,p1,sev2,customer-impact
MEDIUM_KEYWORDS=soon,needed,p2,sev3
LOW_KEYWORDS=fyi,info,update,p3,sev4
```

---

## Benefits

### For Individual Users
- 🎯 Never miss critical messages
- 📌 Quick visual identification of priority
- ⚡ Fast manual tagging with simple commands
- 🔍 Easy filtering by emoji reactions

### For Teams
- 📊 Shared understanding of priorities
- 🤝 Better communication efficiency
- ⏱️ Reduced response times for urgent issues
- 📈 Improved team productivity

### For Managers
- 👀 Visibility into team priorities
- 📝 Historical priority patterns
- 🎛️ Customizable to team workflows
- 📐 Scalable across channels

---

## Technical Details

### Message Processing Flow
```
Incoming Message
    ↓
Check if bot/app message? → Yes → Ignore
    ↓ No
Check for ignored subtypes? → Yes → Ignore
    ↓ No
Extract message text
    ↓
Run priority detection (word boundary regex)
    ↓
Priority found? → Yes → Add emoji reaction
    ↓ No
Continue (no action needed)
```

### Priority Detection Algorithm
```javascript
1. Convert message to lowercase
2. For each priority level (CRITICAL → HIGH → MEDIUM → LOW):
   a. For each keyword in that level:
      - Create regex with word boundaries: \bkeyword\b
      - Test against message text
   b. If any keyword matches:
      - Return that priority level
3. If no matches found, return null (no priority)
```

### Reaction Management
```
Manual Prioritization Flow:
1. User invokes /prioritize
2. Bot fetches last 50 messages in channel
3. Find user's most recent message
4. Check for existing priority reactions
5. Remove old priority reaction (if exists)
6. Add new priority reaction
7. Confirm to user
```
