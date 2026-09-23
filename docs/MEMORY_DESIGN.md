# Memory design

Hospira AI uses three bounded context levels within an anonymous browser session.

## Recent conversation context

The backend loads at most eight recent messages for the active conversation, supporting same-conversation references such as “does it have a bathtub?” without sending unlimited history.

## Conversation summary

After each chat turn, `summarize_context` stores a bounded summary containing detected topics, recent user context, and the latest room. It is passed to Groq on later turns and is not a raw transcript dump.

## Session memory

When a validated response identifies a supported room, the backend stores a `room_interest` memory with the anonymous session scope, stable room ID/name, source conversation, confidence, timestamps, and active state. Existing active memories are updated instead of duplicated. Memory retrieval is limited to the current `X-Anonymous-Session` value, and deletion is a soft deactivation.

## Limitations

A browser-local session ID is not an authenticated identity. Clearing local storage, changing browser profiles, or using another device starts a new scope. Anyone using the same browser profile can access its demo history. Sensitive information should not be stored.
