/**
 * @file threat-parser.js
 * @brief Loads the AuraNet threat severity matrix.
 *
 * Reads the configured threat matrix from disk and converts it into
 * an in-memory lookup table used by the virtual patch rules engine.
 */

const fs = require('fs');
const path = require('path');

const CONFIG_PATH = process.env.THREAT_MATRIX_PATH || "/etc/auranet/config/threat_matrix.conf";

/**
 * Loads the threat severity matrix from the configured file.
 *
 * The matrix maps threat signatures to numerical severity scores.
 * If the configuration cannot be loaded, a default fallback entry
 * is created to ensure the system remains operational.
 *
 * @returns {Object.<string, number>} Mapping of threat names to severity scores.
 */
function getThreatMatrix() {
    const matrix = {};
    try {
        const data = fs.readFileSync(CONFIG_PATH, 'utf8');
        const lines = data.split('\n');
        
        for (const line of lines) {
            const trimmed = line.trim();
            // Ignore empty lines and comments
            if (!trimmed || trimmed.startsWith('#')) continue;
            
            const [threat, score] = trimmed.split('=');
            if (threat && score) {
                matrix[threat.trim()] = parseInt(score.trim(), 10);
            }
        }
    } catch (err) {
        console.error(`[Config] ⚠️ Failed to load threat matrix from ${CONFIG_PATH}. Using fallback. Error:`, err.message);
        matrix["unknown_anomaly"] = 30;
    }
    
    return matrix;
}

module.exports = {
    getThreatMatrix
};