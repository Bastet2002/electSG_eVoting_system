CREATE INDEX idx_district_id_stealth_address ON myapp_votingcurrency(district_id, stealth_address);
CREATE INDEX idx_district_id_key_image ON myapp_voterecords (district_id, key_image);
CREATE INDEX idx_stealth_address ON myapp_voterecords ((transaction_record->>'stealth_address'));
CREATE INDEX idx_rg ON myapp_voterecords ((transaction_record->>'rG'));
CREATE INDEX idx_output_commitment ON myapp_voterecords ((transaction_record->'commitment'->>'output_commitment'));
CREATE INDEX idx_amount_mask ON myapp_voterecords ((transaction_record->'commitment'->>'amount_mask'));