// config 
const CONTEXT_WINDOW_MS = 5 * 60 * 1000; // 5 minutes 
const QUARANTINE_THRESHOLD = 10;         
const MAX_TRUST = 100;

// THE THREAT MATRIX 
const { getThreatMatrix } = require('./threat-parser');
const THREAT_MATRIX = getThreatMatrix();

// THE MEMORY 
const workloadHistory = new Map();

function calculateDeduction(data) {
    // We now treat AI and Runtime alerts identically for scoring.
    // The AI acts as the sensor; the Matrix dictates the exact penalty.
    const threatName = data.threat || "unknown_anomaly";
    return THREAT_MATRIX[threatName] || THREAT_MATRIX["unknown_anomaly"] || 30;
}

function evaluateBatch(batchedAlerts) {
    const now = Date.now();
    const workloadsToQuarantine = new Map(); 

    for (const alert of batchedAlerts) {
        const subjectParts = alert.subject.split('.');
        if (subjectParts.length < 4) continue; 

        const workload = subjectParts[3]; 
        const threat = alert.data.threat || "unknown_anomaly";
        
        // Directly fetch the severity from the matrix
        const deduction = calculateDeduction(alert.data);

        if (deduction === 0) continue; 

        if (!workloadHistory.has(workload)) {
            workloadHistory.set(workload, []);
        }

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
            console.log(`🚨 [Trust Engine] THRESHOLD BREACHED: ${workload} dropped to ${currentScore}! Marking for auto-healing.`);

            workloadsToQuarantine.set(workload, {
                workload: workload,
                finalScore: currentScore,
                reasons: activeAlerts.map(a => a.threat)
            });
            // We NO LONGER delete the history here. We wait for AutoHeal to explicitly 
            // tell us the pod has been cycled before clearing the slate.
        }
    }

    return Array.from(workloadsToQuarantine.values());
}

function resetWorkload(workload) {
    console.log(`[Trust Engine] 🟢 Wiping threat history and restoring trust for [${workload}].`);
    workloadHistory.delete(workload);
}

module.exports = {
    evaluateBatch,
    resetWorkload
};