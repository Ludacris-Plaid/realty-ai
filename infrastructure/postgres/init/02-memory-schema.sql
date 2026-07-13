-- RealtyAI — AI Memory Schema
-- Long-term and short-term memory for the AI assistant.

-- Short-term memory: conversation history
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    agent_id UUID NOT NULL REFERENCES users(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB DEFAULT '[]',
    tool_results JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conv_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_conv_messages_agent ON conversation_messages(agent_id);
CREATE INDEX idx_conv_messages_created ON conversation_messages(created_at DESC);

-- Long-term memory: AI remembers facts about agents, clients, preferences
CREATE TABLE IF NOT EXISTS ai_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES users(id),
    memory_type TEXT NOT NULL CHECK (memory_type IN ('fact', 'preference', 'interaction', 'insight', 'document')),
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    source TEXT,
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_memories_agent ON ai_memories(agent_id);
CREATE INDEX idx_ai_memories_type ON ai_memories(memory_type);
CREATE INDEX idx_ai_memories_key ON ai_memories(key);

-- Tool usage tracking
CREATE TABLE IF NOT EXISTS tool_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES users(id),
    tool_name TEXT NOT NULL,
    input JSONB,
    output_summary TEXT,
    duration_ms INT,
    model_used TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tool_usage_agent ON tool_usage(agent_id);
CREATE INDEX idx_tool_usage_tool ON tool_usage(tool_name);
CREATE INDEX idx_tool_usage_created ON tool_usage(created_at DESC);
