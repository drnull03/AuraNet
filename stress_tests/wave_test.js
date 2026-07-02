import http from 'k6/http';
import { sleep, check } from 'k6';

// Execution Configuration 
export const options = {
    stages: [
        { duration: '10s', target: 25 }, // Crest 1: Sudden morning peak traffic
        { duration: '15s', target: 5 },  // Trough 1: Midday drop (Testing recovery/scale-down)
        { duration: '10s', target: 25 }, // Crest 2: Afternoon rush peak
        { duration: '15s', target: 0 },  // Trough 2: End of cycle full drain
    ],
    thresholds: {
        // The system must bounce back and maintain sub-10 second p95 latency across the entire wave
        http_req_duration: ['p(95)<10000'],
        'checks': ['rate>0.80'],
    },
};

export default function () {
    const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:10000';
    
    // Shifting attack profile: 10% malicious requests during the waves
    const isMalicious = Math.random() < 0.10;
    
    let url = `${GATEWAY_URL}/api/loans/export?id=123`;
    if (isMalicious) {
        url = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/passwd`;
    }

    const res = http.get(url);
    
    if (!isMalicious) {
        check(res, {
            'System adapts to traffic wave (200 OK)': (r) => r.status === 200,
        });
    }

    sleep(0.8);
}
