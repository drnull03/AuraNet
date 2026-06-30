// virtual-patches/rules.js
const fs = require('fs');
const path = require('path');
const { getThreatMatrix } = require('./threat-parser');
// The mapping now includes a 'severity' score (1-100)


//now we are only picking the highest severity to apply a patch too 

//we are gonna add more of these 
//when using the LLM approach 
//or cloud flare method we use the full context of the array







function determineVirtualPatch(threatSignatures) {
    const THREAT_MATRIX = getThreatMatrix();
    
    // Default fallback values
    const fallbackPatch = "unknown_anomaly_patch.yaml";
    
    //  Fallback if no specific signatures are provided
    if (!threatSignatures || threatSignatures.length === 0) {
        return fallbackPatch;
    }

    let highestSeverity = -1;
    let selectedThreat = "unknown_anomaly";

    //  Loop through threats to find the highest severity
    for (const threat of threatSignatures) {
        const severity = THREAT_MATRIX[threat] || THREAT_MATRIX["unknown_anomaly"];
        
        if (severity > highestSeverity) {
            highestSeverity = severity;
            selectedThreat = threat;
        }
    }

    //  Construct filename and verify existence
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
    determineVirtualPatch
};