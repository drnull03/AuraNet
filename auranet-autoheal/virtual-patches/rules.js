const fs = require('fs');
const path = require('path');
const { matrixState } = require('./threat-parser');

/**
 * Dynamically checks if a threat signature belongs to the Runtime branch
 * based on its prefix. Network/AI threats always start with 'l7_', 
 * 'symbolic_', or 'network_'.
 * 
 * @param {string[]} threatSignatures Array of detected threat signatures.
 * @returns {boolean} True if a runtime threat is detected.
 */
function isRuntimeThreat(threatSignatures) {
    if (!threatSignatures || threatSignatures.length === 0) return false;
    
    return threatSignatures.some(threat => {
        const isNetwork = threat.startsWith('l7_') || 
                          threat.startsWith('symbolic_') || 
                          threat.startsWith('network_') ||
                          threat === 'unknown_anomaly'; // Default fallback is network
        return !isNetwork;
    });
}

/**
 * Determines the virtual patch to apply for a detected attack.
 *
 * @param {string[]} threatSignatures Array of detected threat signatures.
 * @returns {string} Name of the virtual patch YAML file to deploy.
 */
function determineVirtualPatch(threatSignatures) {
    const THREAT_MATRIX = matrixState.current;
    const fallbackPatch = "unknown_anomaly_patch.yaml";
    
    if (!threatSignatures || threatSignatures.length === 0) {
        return fallbackPatch;
    }

    let highestSeverity = -1;
    let selectedThreat = "unknown_anomaly";

    for (const threat of threatSignatures) {
        const severity = THREAT_MATRIX[threat] || THREAT_MATRIX["unknown_anomaly"];
        
        if (severity > highestSeverity) {
            highestSeverity = severity;
            selectedThreat = threat;
        }
    }

    const patchFileName = `${selectedThreat}_patch.yaml`;
    const patchPath = path.join(__dirname, patchFileName);

    if (!fs.existsSync(patchPath)) {
        console.warn(`[Rules Engine] ⚠️ Patch file for '${selectedThreat}' (${patchFileName}) not found. Defaulting to fallback.`);
        return fallbackPatch;
    }

    console.log(`[Rules Engine] Analyzed threats. Selected highest severity (${highestSeverity}): ${patchFileName}`);
    return patchFileName;
}

module.exports = {
    determineVirtualPatch,
    isRuntimeThreat
};