// virtual-patches/rules.js

// The mapping now includes a 'severity' score (1-100)


//now we are only picking the highest severity to apply a patch too 

//we are gonna add more of these 
//when using the LLM approach 
//or cloud flare method we use the full context of the array
const RULE_ENGINE = {
    "sql_injection": { patch: "block-sql-injection.yaml", severity: 100 },
    "privilege_escalation": { patch: "strict-rbac-jail.yaml", severity: 90 },
    "path_traversal": { patch: "block-path-traversal.yaml", severity: 80 },
    "network_anomaly": { patch: "default-quarantine.yaml", severity: 20 },
    "unknown_anomaly": { patch: "default-quarantine.yaml", severity: 10 }
};

function determineVirtualPatch(threatSignatures) {
    if (!threatSignatures || threatSignatures.length === 0) {
        return RULE_ENGINE["unknown_anomaly"].patch;
    }

    let highestSeverity = -1;
    let selectedPatch = RULE_ENGINE["unknown_anomaly"].patch;

    // Loop through ALL threats to find the highest severity
    for (const threat of threatSignatures) {
        const rule = RULE_ENGINE[threat];
        
        if (rule && rule.severity > highestSeverity) {
            highestSeverity = rule.severity;
            selectedPatch = rule.patch;
        }
    }

    return selectedPatch;
}

module.exports = {
    determineVirtualPatch
};