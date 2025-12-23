CREATE OR REPLACE FUNCTION log_alpha_event(
    p_user_id UUID,
    p_event_type VARCHAR(100),
    p_event_data JSONB DEFAULT '{}'::JSONB,
    p_session_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO alpha_observation_logs (
        user_id,
        event_type,
        event_data,
        session_id,
        metadata
    ) VALUES (
        p_user_id,
        p_event_type,
        p_event_data,
        p_session_id,
        jsonb_build_object(
            'logged_at', NOW(),
            'alpha_mode', true
        )
    ) RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;
