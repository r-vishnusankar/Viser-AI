require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const connectDB = require('./config/database');
const buildsRouter = require('./routes/builds');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors({ origin: true }));
app.use(express.json());
app.use('/api/builds', buildsRouter);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'BuildShield 360' });
});

// Serve ZAP HTML report so it can be viewed in BuildShield UI
app.get('/api/zap/report', (req, res) => {
  const reportPath = path.resolve(process.cwd(), 'zap_scanner', 'zap_report.html');
  if (!fs.existsSync(reportPath)) {
    return res.status(404).json({ error: 'ZAP report not found. Run a scan first.' });
  }
  res.sendFile(reportPath);
});

(async () => {
  await connectDB();
  app.listen(PORT, () => {
    console.log(`BuildShield 360 API running on http://localhost:${PORT}`);
  });
})();
