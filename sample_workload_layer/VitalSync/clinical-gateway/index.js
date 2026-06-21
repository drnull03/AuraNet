const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8080;

// Internal backend URLs (Defaults to localhost for local testing)
const RECORDS_SERVICE_URL = process.env.RECORDS_SERVICE_URL || 'http://localhost:5000';
const IMAGING_SERVICE_URL = process.env.IMAGING_SERVICE_URL || 'http://localhost:8081';

// Allow the Clinical Portal UI to connect
app.use(cors());

// Log every request for SOC visibility
app.use((req, res, next) => {
    console.log(`[Clinical Gateway] Routing ${req.method} ${req.originalUrl}`);
    next();
});

// Route 1: Radiology Imaging Service (Target for the LFI Attack)
app.use('/api/images', createProxyMiddleware({ 
    target: IMAGING_SERVICE_URL, 
    changeOrigin: true 
}));

// Route 2: Patient Records Service (Target for the Command Injection Attack)
app.use('/api/reports', createProxyMiddleware({ 
    target: RECORDS_SERVICE_URL, 
    changeOrigin: true 
}));

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'VitalSync Clinical Gateway Online', secure: true });
});

app.listen(PORT, () => {
    console.log(`🏥 VitalSync Clinical Gateway listening on port ${PORT}`);
});
