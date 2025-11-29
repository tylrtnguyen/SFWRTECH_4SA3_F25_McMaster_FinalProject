-- Migration 018: Fix corrupted resume_analyses records
-- Some records have raw JSON stored in recommended_tips instead of the parsed tips field
-- This migration extracts the proper values from the JSON using regex and substring

UPDATE resume_analyses
SET 
    match_score = (regexp_match(recommended_tips, '"match_score":\s*(\d+)'))[1]::float,
    recommended_tips = regexp_replace(
        regexp_replace(
            regexp_replace(
                -- Extract everything between "tips": " and the closing pattern
                substring(
                    recommended_tips 
                    from position('"tips": "' in recommended_tips) + 9
                    for length(recommended_tips) - position('"tips": "' in recommended_tips) - 15
                ),
                '\\n', E'\n', 'g'  -- Convert \n to actual newlines
            ),
            '\\"', '"', 'g'  -- Convert \" to actual quotes
        ),
        '\\\\', '\', 'g'  -- Convert \\ to single backslash
    )
WHERE recommended_tips LIKE '```json%' 
  AND recommended_tips LIKE '%"match_score"%' 
  AND recommended_tips LIKE '%"tips"%';

-- Add comment for documentation
COMMENT ON TABLE resume_analyses IS 'Stores individual resume analysis results from Gemini AI. Migration 018 fixed corrupted records with raw JSON.';

