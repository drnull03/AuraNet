// virtual-patches/rules.js

const PATCH_MAP = {
    "sql_injection": "block-sql-injection.yaml",
    "path_traversal": "block-path-traversal.yaml",
    "privilege_escalation": "strict-rbac-jail.yaml",
    "network_anomaly": "default-quarantine.yaml", // Neural AI hits
    "unknown_anomaly": "default-quarantine.yaml"  // Fallback
};

function determineVirtualPatch(threatSignatures) {
    if (!threatSignatures || threatSignatures.length === 0) {
        return PATCH_MAP["unknown_anomaly"];
    }

    // Grab the first matched threat and return its corresponding patch
    for (const threat of threatSignatures) {
        if (PATCH_MAP[threat]) {
            return PATCH_MAP[threat];
        }
    }

    return PATCH_MAP["unknown_anomaly"];
}

module.exports = {
    determineVirtualPatch
};