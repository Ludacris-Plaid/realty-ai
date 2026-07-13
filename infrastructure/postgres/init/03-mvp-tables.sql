-- RealtyAI MVP Tables
-- Creates all tables needed for the MVP features:
-- 1. AI Lead Assistant
-- 2. AI Listing Marketing Generator
-- 3. AI Document Intelligence

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Organizations (brokerage or company)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'starter',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (agents, admins, etc.)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(50) DEFAULT 'agent',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent profiles
CREATE TABLE IF NOT EXISTS agent_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    brokerage VARCHAR(255),
    phone VARCHAR(50),
    license_number VARCHAR(100),
    bio TEXT,
    profile_image_url VARCHAR(500),
    gmail_connected BOOLEAN DEFAULT FALSE,
    google_calendar_connected BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead sources enum
DO $$ BEGIN
    CREATE TYPE lead_source AS ENUM (
        'zillow', 'realtor_com', 'redfin', 'website', 'referral',
        'social_media', 'open_house', 'call_in', 'email', 'other'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Lead statuses
DO $$ BEGIN
    CREATE TYPE lead_status AS ENUM (
        'new', 'qualifying', 'qualified', 'contacted',
        'appointment_set', 'closed_won', 'closed_lost', 'dormant'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES users(id) NOT NULL,
    brokerage_id UUID REFERENCES organizations(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    source lead_source DEFAULT 'other',
    status lead_status DEFAULT 'new',
    budget NUMERIC(12,2),
    location_interest VARCHAR(255),
    property_type_interest VARCHAR(100),
    timeline VARCHAR(100),
    pre_approved BOOLEAN,
    ai_score FLOAT DEFAULT 0,
    ai_score_reason TEXT,
    ai_score_updated_at TIMESTAMPTZ,
    last_contacted_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Property types and statuses
DO $$ BEGIN
    CREATE TYPE property_type AS ENUM (
        'single_family', 'condo', 'townhouse', 'multi_family', 'land', 'commercial'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE property_status AS ENUM (
        'draft', 'active', 'pending', 'sold', 'expired', 'withdrawn'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Properties / Listings
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES users(id) NOT NULL,
    brokerage_id UUID REFERENCES organizations(id),
    client_id UUID,
    address_street VARCHAR(255) NOT NULL,
    address_city VARCHAR(100) NOT NULL,
    address_state VARCHAR(50) NOT NULL,
    address_zip VARCHAR(20) NOT NULL,
    address_unit VARCHAR(50),
    property_type property_type DEFAULT 'single_family',
    status property_status DEFAULT 'draft',
    beds INTEGER,
    baths FLOAT,
    sqft FLOAT,
    lot_size FLOAT,
    year_built INTEGER,
    garage_spaces INTEGER,
    list_price NUMERIC(14,2),
    hoa_dues NUMERIC(10,2),
    description TEXT,
    features JSONB DEFAULT '[]',
    images JSONB DEFAULT '[]',
    mls_number VARCHAR(50),
    listed_at TIMESTAMPTZ,
    sold_at TIMESTAMPTZ,
    sold_price NUMERIC(14,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clients (buyers/sellers linked to agent)
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES users(id) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    type VARCHAR(50) DEFAULT 'buyer',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document categories
DO $$ BEGIN
    CREATE TYPE doc_category AS ENUM (
        'contract', 'disclosure', 'inspection', 'appraisal',
        'agreement', 'marketing', 'other'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES users(id) NOT NULL,
    property_id UUID REFERENCES properties(id),
    client_id UUID REFERENCES clients(id),
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes INTEGER,
    content_type VARCHAR(100),
    category doc_category DEFAULT 'other',
    title VARCHAR(500),
    description TEXT,
    extracted_text TEXT,
    vector_embedding_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document chunks for RAG
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    client_id UUID REFERENCES clients(id),
    title VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages in conversations
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Memory (org-level, agent-level, client-level)
CREATE TABLE IF NOT EXISTS ai_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    client_id UUID REFERENCES clients(id),
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity feed
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    agent_name VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    intent VARCHAR(100) DEFAULT 'general',
    model_used VARCHAR(100),
    status VARCHAR(50) DEFAULT 'success',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Approval requests
CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    agent_name VARCHAR(100),
    action_type VARCHAR(100) NOT NULL,
    summary TEXT,
    details JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost NUMERIC(10,6) DEFAULT 0,
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_agent ON leads(agent_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(ai_score DESC);
CREATE INDEX IF NOT EXISTS idx_properties_agent ON properties(agent_id);
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
CREATE INDEX IF NOT EXISTS idx_documents_agent ON documents(agent_id);
CREATE INDEX IF NOT EXISTS idx_documents_property ON documents(property_id);
CREATE INDEX IF NOT EXISTS idx_activities_org ON activities(organization_id);
CREATE INDEX IF NOT EXISTS idx_activities_created ON activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approvals_org ON approvals(organization_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_ai_memories_org ON ai_memories(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_memories_user ON ai_memories(user_id);
