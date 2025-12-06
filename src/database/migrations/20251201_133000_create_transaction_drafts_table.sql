-- 创建交易草稿表
CREATE TABLE IF NOT EXISTS transaction_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    target_account_id INTEGER,
    category_id INTEGER,
    type TEXT NOT NULL CHECK(type IN ('income', 'expense', 'transfer')),
    amount REAL NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_transaction_drafts_account ON transaction_drafts(account_id);
CREATE INDEX IF NOT EXISTS idx_transaction_drafts_date ON transaction_drafts(date);
CREATE INDEX IF NOT EXISTS idx_transaction_drafts_type ON transaction_drafts(type);