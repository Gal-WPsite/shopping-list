---
name: shopping-list
description: Turn a pasted shopping list into a fast, minimal, mobile Hebrew (RTL) page grouped by store category, with a tap-to-mark "bought" checkbox, a "חסר" (out of stock) button per item, marks synced live between every phone that opens the link, a WhatsApp export of the list with each item's status, and a public link for the phone. Use when the user pastes a grocery list or asks "תסדר לי רשימת קניות", "רשימת קניות", "אני בסופר", or "shopping list".
---

# Shopping List

The user is often already in the supermarket. Speed beats polish: no questions and no design iteration, and hand over a working page within a couple of minutes.

Paths below are relative to this skill's directory.

## Steps

1. Parse the list into `[quantity, name, note]` items. The quantity is a leading number or weight ("2", "800 ג׳"), or `""` when there is none. Put qualifiers in the note, not the name: who an item is for, "אם יש", "לא קלויים", and anything the user emphasized (for example `*לא מתוקה*` becomes the note "לא מתוקה!"). Keep the user's wording, and never drop or merge items.
2. Group the items into categories in store-walking order, and skip empty ones. Default set: `🥬 ירקות`, `🍎 פירות`, `🍞 לחם ומאפים`, `🧀 מקרר וחלב` (dairy and eggs), `🥩 בשר ודגים`, `🥐 קפואים`, `🌾 אפייה ויבשים` (flour, nuts, chocolate, salt, spices, cans), `🥤 שתייה`, `🧽 ניקיון`, `🧴 טואלטיקה`. Add a category only when an item fits none of these. See `examples/list.json`.
3. Write the data as JSON to a temp file and render the page:
   `python3 scripts/build.py /tmp/shopping-list/data.json /tmp/shopping-list`
4. Get the page onto the phone. If the environment already has its own preview or share-link tool, use that. Otherwise run:
   `scripts/share.sh start /tmp/shopping-list`
   This serves the page and its shared-state API (`scripts/server.py`) on `127.0.0.1:8765` and opens a Cloudflare Quick Tunnel: a random public `trycloudflare.com` URL that needs no account. It stays open until `scripts/share.sh stop`, a reboot, or sleep; pass a fourth argument in seconds only if the user wants it to close itself. The page contains only the list. Tell the user the link is public to anyone who has it, and that sharing it (for example with a partner) gives a live shared list. If the environment used its own share tool instead of `share.sh`, it must serve through `scripts/server.py`, not a plain static server, or sync is lost.
5. Hand over the link only after `status=200`. Keep the reply short and in the user's language: the link on its own line, that it is shared live with anyone who opens it, and one line on how the categories came out. `scripts/share.sh stop` closes it.

## Page behavior (`assets/template.html`)

- Ticking an item strikes it through and moves it to the bottom of its category. "חסר" marks the item red, and a second tap clears it. The header shows how many items are done out of the total, plus the missing count. "📤 וואטסאפ" opens WhatsApp (`wa.me/?text=`) with the whole list and a ✅/❌/⬜ status per item and, when served over http(s), the page link at the end, so the user can pick a chat and send it. "איפוס" clears every mark.
- Marks are shared: every open page polls `/state` once a second, so a mark on one phone shows on the others within about a second. Each change is sent as a single item update, so two people marking different items never overwrite each other; on the same item, the last tap wins. The server keeps the state in `state.json` next to the page, and `build.py` clears it for a new list.
- Each phone also keeps a localStorage copy under a key stamped with the build time. The page then still works when opened as a plain file with no server, only without sync.
- To change an open list, edit the built `index.html` in place. The user refreshes the same link, and the marks survive as long as the storage key and item names stay the same. After any JS edit, extract the script and run `node --check` on it, because a syntax error blanks the page while the user is in the store.
