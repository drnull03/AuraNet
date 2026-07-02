import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
    stages: [
        { duration: '10s', target: 5 },  // Ramp up to 5 users
        { duration: '2m', target: 5 },   // SOAK: Hold steady for a full 2 minutes
        { duration: '10s', target: 0 },  // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<10000'],
    },
};

export default function () {
    const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:10000';
    
    // The Soak Test throws EVERYTHING at the system to test the ZTC's multi-sensor logic over time
    const diceRoll = Math.random();
    
    let url = `${GATEWAY_URL}/api/loans/export?id=123`; // 80% Benign
    
    if (diceRoll > 0.8 && diceRoll <= 0.9) {
        // 10% L7 AI SQLi Attack
        url = `${GATEWAY_URL}/api/accounts?id=1%20UNION%20SELECT%20*%20FROM%20users`;
    } else if (diceRoll > 0.9) {
        // 10% L4 Command Injection Attack
        url = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/shadow`;
    }

    const res = http.get(url);
    
    if (diceRoll <= 0.8) {
        check(res, {
            'System remains stable over time (200 OK)': (r) => r.status === 200,
        });
    }

    sleep(1);
}