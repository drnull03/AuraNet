//config 
const CONTEXT_WINDOW_MS = 5 * 60 * 1000; // 5 minutes 
const QUARANTINE_THRESHOLD = 10;         
const MAX_TRUST = 100;

// THE THREAT MATRIX 
//these will change soon
const RUNTIME_PENALTIES = {
    "nc_execution": 70,
    "unauthorized_file_read": 60,
    "privilege_escalation": 90,         // Instant quarantine basically
    "unexpected_outbound_traffic": 50,
    "unknown_anomaly": 30               // Fallback penalty
};

//  THE MEMORY 
// Key: workload name (e.g., 'payment-api')
// Value: Array of alert objects { timestamp, deduction, threat }
const workloadHistory = new Map();

function calculateDeduction(subject, data) {
    //  If it's an AI Alert: Check if Symbolic or Neural won
    if (subject.includes('.ai.')) {
        const probability = data.probability || 0;
        
        if (probability === 0) {
            // Symbolic AI won: Treat it like a hard runtime alert
            const threatName = data.threat;
            return RUNTIME_PENALTIES[threatName] || RUNTIME_PENALTIES["unknown_anomaly"];
        } else {
            // Neural AI won: Scale deduction based on the model's confidence/probability
            return Math.round(probability * 100); 
        }
    }
    
    //  If it is a Runtime Alert: Look up the hardcoded penalty in the matrix
    if (subject.includes('.runtime.')) {
        const threatName = data.threat;
        return RUNTIME_PENALTIES[threatName] || RUNTIME_PENALTIES["unknown_anomaly"];
    }

    return 0; // Failsafe
}

function evaluateBatch(batchedAlerts) {
    const now = Date.now();
    const workloadsToQuarantine = new Map(); 

    for (const alert of batchedAlerts) {
        
        // Extract routing metadata directly from the NATS subject
        // Example: "auranet.events.runtime.payment-api" -> ["auranet", "events", "runtime", "payment-api"]
        const subjectParts = alert.subject.split('.');
        if (subjectParts.length < 4) continue; // Malformed subject, ignore and move on

        const source = subjectParts[2];   // 'ai' or 'runtime'
        const workload = subjectParts[3]; // e.g., 'payment-api'
        
        let threat = "unknown_anomaly";
        
        // Determine threat name based on source and Neurosymbolic logic
        if (source === 'runtime') {
            threat = alert.data.threat || "unknown_anomaly";
        } else if (source === 'ai') {
            const probability = alert.data.probability || 0;
            if (probability === 0) {
                // Symbolic AI triggered explicitly
                threat = alert.data.threat || "unknown_anomaly";
            } else {
                // Neural AI triggered a probability-based anomaly
                threat = "network_anomaly";
            }
        }
        
        // DECOUPLED SCORING: Calculate here, don't read from payload
        const deduction = calculateDeduction(alert.subject, alert.data);

        if (deduction === 0) continue; // Ignore empty or invalid alerts

        if (!workloadHistory.has(workload)) {
            workloadHistory.set(workload, []);
        }

        // Pod tracking removed. Workload-level quarantine only.
        workloadHistory.get(workload).push({
            timestamp: now,
            deduction: deduction,
            threat: threat,
            source: alert.subject
        });
    }

    // Slide the Window & Calculate Scores
    for (const [workload, alerts] of workloadHistory.entries()) {
        
        const activeAlerts = alerts.filter(a => (now - a.timestamp) <= CONTEXT_WINDOW_MS);
        
        if (activeAlerts.length === 0) {
            workloadHistory.delete(workload); 
            continue;
        } else {
            workloadHistory.set(workload, activeAlerts);
        }

        const totalDeductions = activeAlerts.reduce((sum, a) => sum + a.deduction, 0);
        const currentScore = MAX_TRUST - totalDeductions;

        console.log(`[Trust Engine] ${workload} | Current Score: ${currentScore} | Active Alerts: ${activeAlerts.length}`);

        // Check against Quarantine Threshold
        if (currentScore < QUARANTINE_THRESHOLD) {
            console.log(`[Trust Engine] 🚨 THRESHOLD BREACHED: ${workload} dropped to ${currentScore}! Marking for auto-healing.`);

            workloadsToQuarantine.set(workload, {
                workload: workload,
                finalScore: currentScore,
                reasons: activeAlerts.map(a => a.threat)
            });
        }
    }

    return Array.from(workloadsToQuarantine.values());
}

module.exports = {
    evaluateBatch
};