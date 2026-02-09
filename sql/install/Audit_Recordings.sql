CREATE TABLE IF NOT EXISTS audit_recordings (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    recording_id BIGINT,
    action ENUM('INSERT','UPDATE','DELETE'),
    action_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(100),
    notes TEXT
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

