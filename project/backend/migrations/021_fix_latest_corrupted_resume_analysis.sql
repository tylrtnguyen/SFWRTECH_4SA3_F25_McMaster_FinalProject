-- Fix the latest corrupted resume analysis record
-- Extract match_score and tips from the JSON structure wrapped in markdown code blocks

DO $$
DECLARE
    record_id UUID;
    raw_tips TEXT;
    match_score_str TEXT;
    tips_str TEXT;
    extracted_match_score FLOAT;
    extracted_tips TEXT;
BEGIN
    -- Find the corrupted record (starts with ```json)
    SELECT id, recommended_tips INTO record_id, raw_tips
    FROM resume_analyses
    WHERE recommended_tips LIKE '```json%'
    ORDER BY created_at DESC
    LIMIT 1;

    IF record_id IS NOT NULL THEN
        RAISE NOTICE 'Found corrupted record ID: %', record_id;

        -- Extract match_score using regex: "match_score": (\d+)
        SELECT substring(raw_tips from '"match_score":\s*([0-9]+)') INTO match_score_str;
        IF match_score_str IS NOT NULL THEN
            extracted_match_score := match_score_str::FLOAT;
        END IF;

        -- Extract tips using regex: "tips": "(.+)" but handle the multiline content
        -- Find the position after "tips": "
        DECLARE
            tips_start INTEGER;
            tips_content TEXT;
        BEGIN
            tips_start := position('"tips": "' in raw_tips);
            IF tips_start > 0 THEN
                -- Get everything after "tips": " until the last "
                tips_content := substring(raw_tips from tips_start + 9);
                -- Remove the trailing " and any content after it
                DECLARE
                    last_quote_pos INTEGER;
                BEGIN
                    -- Find the last " that comes before ```
                    last_quote_pos := position('"' in reverse(tips_content));
                    IF last_quote_pos > 0 THEN
                        tips_content := substring(tips_content from 1 for length(tips_content) - last_quote_pos);
                    END IF;
                END;
                extracted_tips := tips_content;
            END IF;
        END;

        RAISE NOTICE 'Extracted match_score: %, tips preview: %', extracted_match_score, left(extracted_tips, 100);

        -- Update the record with the extracted values
        UPDATE resume_analyses
        SET
            match_score = extracted_match_score,
            recommended_tips = extracted_tips,
            updated_at = NOW()
        WHERE id = record_id;

        RAISE NOTICE 'Successfully fixed corrupted resume analysis record ID: %', record_id;
    ELSE
        RAISE NOTICE 'No corrupted resume analysis records found';
    END IF;
END $$;
