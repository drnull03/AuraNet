import http from 'k6/http';
import { sleep, check } from 'k6';

// Execution Configuration 
export const options = {
    stages: [
        { duration: '5s', target: 30 },  // FAST Ramp up to 30 concurrent users
        { duration: '15s', target: 30 }, // Hold the massive spike
        { duration: '10s', target: 0 },  // Cooldown
    ],
    thresholds: {
        // We expect major latency during a spike, but it shouldn't completely lock up (10s max)
        http_req_duration: ['p(95)<10000'], 
        // We accept up to a 20% drop rate because the gateway is going to be cycling rapidly
        'checks': ['rate>0.80'], 
    },
};

export default function () {
    const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:10000';
    
    // Only 5% malicious. At 30 VUs, this is still enough to constantly trigger the sensors
    const isMalicious = Math.random() < 0.05;
    
    let url = `${GATEWAY_URL}/api/loans/export?id=123`;
    if (isMalicious) {
        url = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/passwd`;
    }

    const res = http.get(url);
    
    if (!isMalicious) {
        check(res, {
            'Benign traffic survives the spike (200 OK)': (r) => r.status === 200,
        });
    }

    // Faster sleep to simulate aggressive bot traffic
    sleep(0.5); 
}