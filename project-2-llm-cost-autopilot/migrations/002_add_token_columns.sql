-- migration 002: token counts for exact baseline cost math
ALTER TABLE requests ADD COLUMN input_tokens INTEGER;
ALTER TABLE requests ADD COLUMN output_tokens INTEGER;
