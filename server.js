import express from 'express';
import fs from 'fs';
import path from 'path';

const app = express();
const PORT = 5000;

// Function to safely read JSON files
const readJsonFile = (filePath) => {
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    } catch (error) {
        console.error(`Error reading ${filePath}:`, error);
        return null;
    }
};

// Corrected paths to JSON files
const softwareAlertsPath = path.resolve('backend/software_alerts_history.json');
const hardwareAlertsPath = path.resolve('backend/hardware_alerts_history.json');

// API to fetch both Software & Hardware alerts
app.get('/alerts', (req, res) => {
    const softwareAlerts = readJsonFile(softwareAlertsPath) || {};
    const hardwareAlerts = readJsonFile(hardwareAlertsPath) || {};

    console.log(" Fetched Software Alerts:", softwareAlerts);
    console.log(" Fetched Hardware Alerts:", hardwareAlerts);

    res.json({ software_alerts: softwareAlerts, hardware_alerts: hardwareAlerts });
});

// Start the server
app.listen(PORT, () => {
    console.log(` Server running at http://localhost:${PORT}`);
});
