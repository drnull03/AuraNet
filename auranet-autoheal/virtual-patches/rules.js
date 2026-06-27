// virtual-patches/rules.js
const { getThreatMatrix } = require('./threat-parser');

// The mapping now includes a 'severity' score (1-100)


//now we are only picking the highest severity to apply a patch too 

//we are gonna add more of these 
//when using the LLM approach 
//or cloud flare method we use the full context of the array


function determineVirtualPatch(threatSignatures) {
    const THREAT_MATRIX = getThreatMatrix();
    
    // Fallback if no specific signatures are provided
    if (!threatSignatures || threatSignatures.length === 0) {
        return "unknown_anomaly_patch.yaml";
    }

    let highestSeverity = -1;
    let selectedThreat = "unknown_anomaly";

    // Loop through ALL threats to find the one with the highest numerical penalty
    for (const threat of threatSignatures) {
        const severity = THREAT_MATRIX[threat] || THREAT_MATRIX["unknown_anomaly"];
        
        if (severity > highestSeverity) {
            highestSeverity = severity;
            selectedThreat = threat;
        }
    }

    // Enforce strict naming convention: <threat_name>_patch.yaml
    const patchFileName = `${selectedThreat}_patch.yaml`;
    console.log(`[Rules Engine] Analyzed threats. Selected highest severity (${highestSeverity}): ${patchFileName}`);
    
    return patchFileName;
}

module.exports = {
    determineVirtualPatch
};