
const { determineVirtualPatch } = require("./rules");

describe("AuraNet AutoHeal: Severity Engine", () => {
    
    -

    test("1. Should return the highest severity patch when multiple threats are present", () => {
        // network_anomaly (20) vs sql_injection (100)
        const threats = ["network_anomaly", "sql_injection"];
        expect(determineVirtualPatch(threats)).toBe("block-sql-injection.yaml");
    });

    test("2. Should return the exact match for a single valid threat", () => {
        const threats = ["privilege_escalation"];
        expect(determineVirtualPatch(threats)).toBe("strict-rbac-jail.yaml");
    });

    test("3. Should evaluate correctly regardless of array order (Highest threat first)", () => {
        const threats = ["sql_injection", "path_traversal", "network_anomaly"];
        expect(determineVirtualPatch(threats)).toBe("block-sql-injection.yaml");
    });

    test("4. Should evaluate correctly regardless of array order (Highest threat last)", () => {
        const threats = ["network_anomaly", "path_traversal", "privilege_escalation"];
        // privilege_escalation (90) is the highest here
        expect(determineVirtualPatch(threats)).toBe("strict-rbac-jail.yaml");
    });

    test("5. Should handle duplicate threat signatures without crashing or overwriting", () => {
        // If the ZTC accidentally sends duplicates due to a rapid-fire attack
        const threats = ["path_traversal", "path_traversal", "network_anomaly"];
        expect(determineVirtualPatch(threats)).toBe("block-path-traversal.yaml");
    });

    

    test("6. Should fallback to default quarantine if the threat array is empty or undefined", () => {
        expect(determineVirtualPatch([])).toBe("default-quarantine.yaml");
        expect(determineVirtualPatch(undefined)).toBe("default-quarantine.yaml");
    });

    test("7. Should safely ignore unknown threat strings and still evaluate the known ones", () => {
        // Simulating a hallucination from the AI or a broken sensor name
        const threats = ["some_made_up_threat", "path_traversal", "hacker_typing_fast"];
        // It should ignore the garbage data and catch the path_traversal (80)
        expect(determineVirtualPatch(threats)).toBe("block-path-traversal.yaml");
    });

    test("8. Should fallback to default quarantine if given an array of entirely garbage strings", () => {
        const threats = ["undefined_error_123", "null", "broken_sensor_data"];
        expect(determineVirtualPatch(threats)).toBe("default-quarantine.yaml");
    });
});