require('dotenv').config();
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
app.use(express.json());

// SQLite DB setup
const dbPath = path.join(__dirname, 'db.sqlite');
const db = new sqlite3.Database(dbPath);
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);
});

// Simple health check
app.get('/', (req, res) => {
  res.send('Backoffice API is running!');
});
// User info endpoint for dashboard
app.get('/api/user/me', (req, res) => {
  res.json({
    name: process.env.ADMIN_USERNAME || 'RIZZO',
    level: 'Starter',
    referrals: [],
    benefits: [
      'Full access to your back office',
      'Referral earnings paid daily',
      'Ad credits for Facebook/TikTok/Instagram/YouTube',
      'Cloud hosting (Empire package)',
      'Custom email (upgrade)',
      'Lifetime earnings'
    ]
  });
});

// Example: Add user
app.post('/user', (req, res) => {
  const { email } = req.body;
  if (!email) return res.status(400).json({ error: 'Email required' });
  db.run('INSERT INTO users (email) VALUES (?)', [email], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ id: this.lastID, email });
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Backoffice server running on port ${PORT}`);
});
