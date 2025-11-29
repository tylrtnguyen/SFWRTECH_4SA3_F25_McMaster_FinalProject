-- Migration 019: Add status column to credit_transactions table
-- Tracks the status of each credit transaction: pending, success, failed, cancelled

-- Create enum type for transaction status
CREATE TYPE transaction_status AS ENUM ('pending', 'success', 'failed', 'cancelled');

-- Add status column with default 'pending'
ALTER TABLE credit_transactions
ADD COLUMN status transaction_status DEFAULT 'pending';

-- Update existing records based on context (all current ones are pending)
UPDATE credit_transactions SET status = 'pending' WHERE status IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN credit_transactions.status IS 'Transaction status: pending (awaiting payment), success (payment completed), failed (payment failed), cancelled (user cancelled)';

