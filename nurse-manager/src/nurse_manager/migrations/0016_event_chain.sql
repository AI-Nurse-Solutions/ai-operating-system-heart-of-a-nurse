-- Existing events remain unchained; do not manufacture historical hashes.
ALTER TABLE event_log ADD COLUMN previous_sha256 TEXT;
ALTER TABLE event_log ADD COLUMN event_sha256 TEXT;

CREATE TABLE audit_chain_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    legacy_through INTEGER NOT NULL CHECK (legacy_through >= 0),
    legacy_count INTEGER NOT NULL CHECK (legacy_count >= 0),
    head_seq INTEGER NOT NULL CHECK (head_seq >= legacy_through),
    head_sha256 TEXT NOT NULL CHECK (length(head_sha256) = 64 AND head_sha256 NOT GLOB '*[^0-9a-f]*')
);
INSERT INTO audit_chain_state
SELECT 1, coalesce(max(seq), 0), count(*), coalesce(max(seq), 0),
       '0000000000000000000000000000000000000000000000000000000000000000'
FROM event_log;

CREATE TRIGGER event_log_no_update BEFORE UPDATE ON event_log
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;
CREATE TRIGGER event_log_no_delete BEFORE DELETE ON event_log
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;
CREATE TRIGGER event_log_link_required BEFORE INSERT ON event_log
BEGIN
    SELECT CASE WHEN NEW.event_sha256 IS NULL OR length(NEW.event_sha256) != 64
        OR NEW.event_sha256 GLOB '*[^0-9a-f]*'
        OR NEW.previous_sha256 IS NULL
        OR NOT EXISTS (SELECT 1 FROM audit_chain_state WHERE singleton = 1
            AND NEW.previous_sha256 = head_sha256 AND NEW.seq > head_seq)
        THEN RAISE(ABORT, 'audit event needs the current chain link') END;
    SELECT CASE WHEN NEW.event_sha256 != audit_event_sha256(NEW.seq, NEW.at,
        NEW.actor, NEW.kind, NEW.record_type, NEW.record_id, NEW.previous_sha256)
        THEN RAISE(ABORT, 'audit event hash does not match') END;
END;
CREATE TRIGGER event_log_advance_head AFTER INSERT ON event_log
BEGIN
    UPDATE audit_chain_state SET head_seq = NEW.seq, head_sha256 = NEW.event_sha256
    WHERE singleton = 1;
END;
