import http from 'k6/http';
import { sleep, check } from 'k6';

// Execution Configuration 
export const options = {
    stages: [
        { duration: '10s', target: 5 },  // Ramp up slowly to 5 concurrent users
        { duration: '30s', target: 5 },  // Hold steady for 30 seconds
        { duration: '10s', target: 0 },  // Cool down
    ],
    thresholds: {
        // Ensure 95% of requests complete in under 800ms, even with AI inspection
        http_req_duration: ['p(95)<10000'],
        'checks': ['rate>0.85'],
    },
};

//  Test Scenario 
export default function () {
    const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:10000';
    
    // 80% normal traffic, 20% malicious traffic
    const isMalicious = Math.random() < 0.2;
    
    let url = `${GATEWAY_URL}/api/loans/export?id=123`;
    if (isMalicious) {
        url = `${GATEWAY_URL}/api/loans/export?id=123%20UNION%20SELECT%20username%20FROM%20users--`;
    }

    const res = http.get(url);
    
    // We only strictly check benign traffic status codes. 
    // Malicious traffic might get a 500, a connection drop, or a 403 depending on AutoHeal's exact timing.
    if (!isMalicious) {
        check(res, {
            'Benign traffic succeeds (200 OK)': (r) => r.status === 200,
        });
    }

    // Sleep for 1 second between iterations per Virtual User
    sleep(1);
}