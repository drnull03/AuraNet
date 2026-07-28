const assert = require('assert');
const trustEngine = require('../trust-engine');

console.log("Starting Trust Engine Unit Tests...\n");

try {
   
    // TEST 1: The Zero-Probability Failsafe
    // proves that a nural network reporting a threat propablity of zero is completly safe
   
    const failsafeBatch = [{
        subject: "auranet.events.ai.safe-workload",
        data: { probability: 0 }
    }];
    
    let result = trustEngine.evaluateBatch(failsafeBatch);
    assert.strictEqual(result.length, 0, "Test 1 Failed: Safe workload was quarantined!");
    console.log("✅ Test 1 Passed: Safe Neural (0 prob) is properly ignored.");

    
    // TEST 2: The Multi-Stage Accumulation (Sliding Window Math)
    // proves the ZTC adds scores together correctly but doesn't strike early.
    
    const accumulationBatch = [
        {
            subject: "auranet.events.ai.suspicious-api",
            data: { probability: 0.50 } // -50 points
        },
        {
            subject: "auranet.events.runtime.suspicious-api",
            data: { threat: "unknown_anomaly" } // -30 points from Matrix
        }
    ];
    
    // Total deduction = 80. Score = 20. Threshold is 10. Should NOT quarantine yet.
    result = trustEngine.evaluateBatch(accumulationBatch);
    assert.strictEqual(result.length, 0, "Test 2 Failed: ZTC triggered quarantine too early!");
    console.log("✅ Test 2 Passed: Multi-stage accumulation calculated correctly (No early strike).");

    
    // TEST 3: The Symbolic AI Override
    // proves  custom `-1` logic forces a hard threat matrix lookup.
    
    const symbolicBatch = [{
        subject: "auranet.events.ai.symbolic-target",
        data: { probability: -1, threat: "privilege_escalation" } // Matrix says 90 points
    }];
    
    // Deduction = 90. Score = 10. Threshold is < 10. 
    // It's right on the line, but shouldn't trigger!
    result = trustEngine.evaluateBatch(symbolicBatch);
    assert.strictEqual(result.length, 0, "Test 3 Failed: Score of 10 triggered quarantine (Threshold is < 10).");
    console.log("✅ Test 3 Passed: Symbolic logic correctly mapped to matrix (Score hit 10, held the line).");

    
    // TEST 4: The Threshold Breach (The Kill Shot)
    // Proves that breaking the threshold actually outputs the execution order.
    
    const breachBatch = [
        {
            subject: "auranet.events.runtime.doomed-api",
            data: { threat: "nc_execution" } // -70 points
        },
        {
            subject: "auranet.events.runtime.doomed-api",
            data: { threat: "unauthorized_file_read" } // -60 points
        }
    ];
    
    // Total deduction = 130. Score = -30. Threshold breached!
    result = trustEngine.evaluateBatch(breachBatch);
    
    assert.strictEqual(result.length, 1, "Test 4 Failed: Expected 1 workload to be quarantined.");
    assert.strictEqual(result[0].workload, "doomed-api", "Test 4 Failed: Wrong workload targeted.");
    assert.strictEqual(result[0].finalScore, -30, "Test 4 Failed: Math is incorrect on breach.");
    assert.deepStrictEqual(result[0].reasons, ["nc_execution", "unauthorized_file_read"], "Test 4 Failed: Threat signatures missing.");
    
    console.log("✅ Test 4 Passed: Threshold breach successfully generated execution order.");

    console.log("\n🚀 ALL TRUST ENGINE UNIT TESTS PASSED SUCCESSFULLY.");

} catch (error) {
    console.error(`\n❌ UNIT TEST FAILED: ${error.message}`);
    process.exit(1);
}