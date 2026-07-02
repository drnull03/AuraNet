import http from 'k6/http';
import { sleep, check } from 'k6';

//  Execution Configuration 
export const options = {
    stages: [
        { duration: '15s', target: 10 }, // Step 1: Low load
        { duration: '15s', target: 20 }, // Step 2: Medium load
        { duration: '15s', target: 40 }, // Step 3: High load (System straining)
        { duration: '15s', target: 60 }, // Step 4: Break-point target (Looking for collapse)
        { duration: '10s', target: 0 },  // Cool down
    ],
    thresholds: {
        // We omit strict latency thresholds here because our goal is to find where the system breaks,
        // but we track data failure rates to map the breaking threshold.
        'http_req_failed': ['rate<0.50'], // Test aborts if failure rate exceeds 50%
    },
};

export default function () {
    const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:10000';
    
    // Low malicious ratio (2%) to isolate architectural load failure from pure security policy drops
    const isMalicious = Math.random() < 0.02;
    
    let url = `${GATEWAY_URL}/api/loans/export?id=123`;
    if (isMalicious) {
        url = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/passwd`;
    }

    const res = http.get(url);
    
    if (!isMalicious) {
        check(res, {
            'Connection sustained successfully': (r) => r.status === 200,
        });
    }

    sleep(1);
}
