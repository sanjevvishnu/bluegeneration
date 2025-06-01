-- =============================================
-- AI Interview Practice Platform - Database Schema with Users
-- Includes Clerk authentication integration
-- =============================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- USERS TABLE
-- =============================================
CREATE TYPE experience_level AS ENUM ('entry', 'junior', 'mid', 'senior', 'staff', 'principal');
CREATE TYPE subscription_tier AS ENUM ('free', 'premium', 'enterprise');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    experience_level experience_level DEFAULT 'entry',
    target_companies TEXT[], -- ['amazon', 'google', 'microsoft', 'meta', 'apple']
    subscription_tier subscription_tier DEFAULT 'free',
    interviews_used_this_month INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);

-- =============================================
-- CONVERSATIONS TABLE (Updated with user_id)
-- =============================================
CREATE TYPE conversation_status AS ENUM ('active', 'completed', 'abandoned');
CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard');

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    mode VARCHAR(100) NOT NULL, -- 'amazon_interviewer', 'technical_screening', etc.
    status conversation_status DEFAULT 'active',
    title VARCHAR(255),
    duration INTEGER, -- duration in seconds
    performance_score DECIMAL(3,2), -- 0.00 to 10.00
    difficulty_level difficulty_level DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- =============================================
-- TRANSCRIPTS TABLE (Updated with user_id)
-- =============================================
CREATE TYPE speaker_type AS ENUM ('user', 'assistant');

CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    sequence_number INTEGER,
    speaker speaker_type NOT NULL,
    text TEXT NOT NULL,
    provider VARCHAR(50), -- 'gemini_speech', 'gemini_text', 'user_input'
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_transcripts_conversation_id ON transcripts(conversation_id);
CREATE INDEX idx_transcripts_user_id ON transcripts(user_id);
CREATE INDEX idx_transcripts_session_id ON transcripts(session_id);
CREATE INDEX idx_transcripts_sequence ON transcripts(conversation_id, sequence_number);

-- =============================================
-- INTERVIEW FEEDBACK TABLE (New)
-- =============================================
CREATE TABLE interview_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    technical_score DECIMAL(3,2), -- 0.00 to 10.00
    communication_score DECIMAL(3,2), -- 0.00 to 10.00
    problem_solving_score DECIMAL(3,2), -- 0.00 to 10.00
    overall_feedback TEXT,
    strengths TEXT[],
    improvement_areas TEXT[],
    recommended_topics TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_interview_feedback_conversation_id ON interview_feedback(conversation_id);
CREATE INDEX idx_interview_feedback_user_id ON interview_feedback(user_id);

-- =============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_feedback ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (clerk_user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (clerk_user_id = auth.jwt() ->> 'sub');

-- Conversations policies
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

-- Transcripts policies
CREATE POLICY "Users can view own transcripts" ON transcripts
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

CREATE POLICY "Users can insert own transcripts" ON transcripts
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

-- Interview feedback policies
CREATE POLICY "Users can view own feedback" ON interview_feedback
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

CREATE POLICY "Users can insert own feedback" ON interview_feedback
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));

-- =============================================
-- FUNCTIONS AND TRIGGERS
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-increment sequence_number for transcripts
CREATE OR REPLACE FUNCTION set_transcript_sequence_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sequence_number IS NULL THEN
        NEW.sequence_number := COALESCE(
            (SELECT MAX(sequence_number) FROM transcripts WHERE conversation_id = NEW.conversation_id),
            0
        ) + 1;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_transcript_sequence BEFORE INSERT ON transcripts
    FOR EACH ROW EXECUTE FUNCTION set_transcript_sequence_number();

-- =============================================
-- SAMPLE DATA (for testing)
-- =============================================

-- Sample user (for testing)
INSERT INTO users (clerk_user_id, email, full_name, experience_level, target_companies, subscription_tier) VALUES
('user_test123', 'test@example.com', 'Test User', 'mid', ARRAY['amazon', 'google'], 'premium');

-- Sample conversation
INSERT INTO conversations (user_id, session_id, mode, status, title, duration, performance_score, difficulty_level) VALUES
((SELECT id FROM users WHERE email = 'test@example.com'), 'test-session-123', 'amazon_interviewer', 'completed', 'Amazon Technical Interview Practice', 1200, 8.5, 'medium');

-- Sample transcripts
INSERT INTO transcripts (conversation_id, user_id, session_id, speaker, text, provider) VALUES
((SELECT id FROM conversations WHERE session_id = 'test-session-123'), (SELECT id FROM users WHERE email = 'test@example.com'), 'test-session-123', 'assistant', 'Hello! Welcome to your Amazon interview practice. Can you start by telling me about yourself?', 'gemini_speech'),
((SELECT id FROM conversations WHERE session_id = 'test-session-123'), (SELECT id FROM users WHERE email = 'test@example.com'), 'test-session-123', 'user', 'Hi! I''m a software engineer with 3 years of experience. I specialize in full-stack development.', 'user_input');

-- =============================================
-- VIEWS FOR ANALYTICS
-- =============================================

-- User interview statistics
CREATE VIEW user_interview_stats AS
SELECT 
    u.id,
    u.email,
    u.full_name,
    u.subscription_tier,
    COUNT(c.id) as total_interviews,
    COUNT(CASE WHEN c.status = 'completed' THEN 1 END) as completed_interviews,
    AVG(c.performance_score) as avg_score,
    MAX(c.created_at) as last_interview_date
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
GROUP BY u.id, u.email, u.full_name, u.subscription_tier;

-- Monthly interview usage
CREATE VIEW monthly_interview_usage AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_tier,
    DATE_TRUNC('month', c.created_at) as month,
    COUNT(c.id) as interviews_count
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
WHERE c.created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY u.id, u.email, u.subscription_tier, DATE_TRUNC('month', c.created_at);

-- Performance trends
CREATE VIEW performance_trends AS
SELECT 
    u.id as user_id,
    c.mode,
    c.difficulty_level,
    c.performance_score,
    c.created_at,
    LAG(c.performance_score) OVER (PARTITION BY u.id, c.mode ORDER BY c.created_at) as previous_score
FROM users u
JOIN conversations c ON u.id = c.user_id
WHERE c.status = 'completed' AND c.performance_score IS NOT NULL
ORDER BY u.id, c.created_at;

-- =============================================
-- COMMENTS
-- =============================================

COMMENT ON TABLE users IS 'User profiles with Clerk authentication integration';
COMMENT ON TABLE conversations IS 'Interview sessions linked to users';
COMMENT ON TABLE transcripts IS 'Real-time conversation transcripts with user association';
COMMENT ON TABLE interview_feedback IS 'Detailed feedback and scoring for completed interviews';

COMMENT ON COLUMN users.clerk_user_id IS 'Unique identifier from Clerk authentication service';
COMMENT ON COLUMN users.target_companies IS 'Array of companies the user is preparing for';
COMMENT ON COLUMN users.interviews_used_this_month IS 'Track usage for subscription limits';
COMMENT ON COLUMN conversations.performance_score IS 'Overall interview performance score (0-10)';
COMMENT ON COLUMN transcripts.sequence_number IS 'Order of messages in conversation';
COMMENT ON COLUMN interview_feedback.strengths IS 'Array of user strengths identified during interview';
COMMENT ON COLUMN interview_feedback.improvement_areas IS 'Array of areas needing improvement'; 