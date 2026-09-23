# Memory design

Hospira AI uses three bounded context levels.

## Recent conversation context

The backend loads at most eight recent messages for the active conversation and orders them chronologically before sending them to the AI adapter. This supports same-conversation references such as “does it have a bathtub?” without sending unlimited history.

## Conversation summary

After each chat turn, `summarize_context` creates a bounded summary containing detected main topics, recent user context, and the latest room. The summary is stored on the conversation record and is passed to Groq on later turns. It is intentionally concise and is not a dump of all messages.

## Persistent user memory

When a validated response identifies a supported room, the backend stores a `room_interest` memory with user ID, stable room ID/name, source conversation, confidence, timestamps, and active state. Existing active memories are updated rather than duplicated. Memory retrieval is limited to the authenticated user and active records. Deletion is a soft deactivation, so deleted memory is excluded from future resolution.

## Cross-conversation resolution

A new conversation first considers its own active room and recent messages, then one unambiguous active room-interest memory. If multiple room memories are plausible, the assistant asks for clarification rather than guessing. This provides the Premium Room follow-up behavior while preserving cross-user isolation.
