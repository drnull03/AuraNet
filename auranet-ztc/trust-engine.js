// config 
const CONTEXT_WINDOW_MS = 5 * 60 * 1000; // 5 minutes 
const QUARANTINE_THRESHOLD = 10;         
const MAX_TRUST = 100;

// THE THREAT MATRIX 
const { getThreatMatrix } = require('./threat-parser');
const THREAT_MATRIX = getThreatMatrix();

// THE MEMORY 
const workloadHistory = new Map();
const healingLocks = new Set(); 

function calculateDeduction(data) {
    const threatName = data.threat || "unknown_anomaly";
    return THREAT_MATRIX[threatName] || THREAT_MATRIX["unknown_anomaly"] || 30;
}

function evaluateBatch(batchedAlerts) {
    const now = Date.now();
    const workloadsToQuarantine = new Map(); 
    
    const ZTC_DEDUPE_WINDOW_MS = 5000; 
    const uniqueAlerts = new Map();

    for (const alert of batchedAlerts) {
        const subjectParts = alert.subject.split('.');
        if (subjectParts.length < 4) continue; 

        const workload = subjectParts[3]; 
        const threat = alert.data.threat || "unknown_anomaly";
        const deduction = calculateDeduction(alert.data);

        if (deduction === 0) continue; 

        const dedupeKey = `${workload}:${threat}`;

        let recentlyPenalized = false;
        if (workloadHistory.has(workload)) {
            const history = workloadHistory.get(workload);
            recentlyPenalized = history.some(a => 
                a.threat === threat && (now - a.timestamp) < ZTC_DEDUPE_WINDOW_MS
            );
        }

        if (!recentlyPenalized && !uniqueAlerts.has(dedupeKey)) {
            uniqueAlerts.set(dedupeKey, {
                workload: workload,
                threat: threat,
                deduction: deduction,
                subject: alert.subject
            });
        }
    }

    for (const alert of uniqueAlerts.values()) {
        if (!workloadHistory.has(alert.workload)) {
            workloadHistory.set(alert.workload, []);
        }

        workloadHistory.get(alert.workload).push({
            timestamp: now,
            deduction: alert.deduction,
            threat: alert.threat,
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
            // NEW: Only fire if we haven't already locked this workload for healing
            if (!healingLocks.has(workload)) {
                console.log(`🚨 [Trust Engine] THRESHOLD BREACHED: ${workload} dropped to ${currentScore}! Marking for auto-healing.`);
                
                // Lock it so we don't spam NATS
                healingLocks.add(workload);

                workloadsToQuarantine.set(workload, {
                    workload: workload,
                    finalScore: currentScore,
                    reasons: activeAlerts.map(a => a.threat)
                });
            } else {
                // Optional: You can comment this out if it clutters the terminal, 
                // but it helps visualize the lock working.
                console.log(`[Trust Engine] ⏳ ${workload} is currently healing. Suppressing duplicate quarantine order.`);
            }
        }
    }

    return Array.from(workloadsToQuarantine.values());
}

function resetWorkload(workload) {
    console.log(`[Trust Engine] 🟢 Wiping threat history and restoring trust for [${workload}].`);
    workloadHistory.delete(workload);
    // NEW: Release the lock so the workload can be quarantined again if a new attack occurs
    healingLocks.delete(workload);
}

module.exports = {
    evaluateBatch,
    resetWorkload
};