const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8080;

// Internal backend URLs
const ACCOUNT_SERVICE_URL = process.env.ACCOUNT_SERVICE_URL || 'http://localhost:5000';
// We use 8081 for local testing so it doesn't clash with the Gateway's 8080
const LOAN_SERVICE_URL = process.env.LOAN_SERVICE_URL || 'http://localhost:8081'; 

// Allow the React UI to connect
app.use(cors());

// Log every request
app.use((req, res, next) => {
    console.log(`[API Gateway] Routing ${req.method} ${req.originalUrl}`);
    next();
});


app.use('/api/accounts', createProxyMiddleware({ 
    target: ACCOUNT_SERVICE_URL, 
    changeOrigin: true 
}));


app.use('/api/loans', createProxyMiddleware({ 
    target: LOAN_SERVICE_URL, 
    changeOrigin: true 
}));

app.get('/health', (req, res) => {
    res.status(200).json({ status: 'OmniFinance API Gateway Online' });
});

app.listen(PORT, () => {
    console.log(`🚀 OmniFinance API Gateway listening on port ${PORT}`);
});