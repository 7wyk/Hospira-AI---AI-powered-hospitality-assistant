# Memory design

Recent messages are limited to the current conversation. Conversation summaries are kept on the conversation record. Persistent memories are user-owned records with a type, structured JSON value, source conversation, confidence, active flag, and timestamps. Room interests are saved only when the grounded resolver has a supported room reference. A new chat can resolve a single recent room memory; multiple plausible memories require clarification. Deletion is a soft delete and inactive memories are excluded from retrieval.
