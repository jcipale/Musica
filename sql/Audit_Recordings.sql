CREATE TABLE audit_recordings (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    recording_id INT,
    action ENUM('INSERT','UPDATE','DELETE'),
    action_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(100),
    notes TEXT
);

