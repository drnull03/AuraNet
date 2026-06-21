package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	// Create a dummy image directory and file so normal requests succeed
	os.MkdirAll("./images", 0755)
	os.WriteFile("./images/chest_xray_001.png", []byte("[BINARY_DATA] Valid Chest X-Ray Loaded. Lungs appear clear."), 0644)

	http.HandleFunc("/api/images", lfiHandler)
	http.HandleFunc("/health", healthHandler)

	port := getEnv("PORT", "8081")
	fmt.Printf("🏥 VitalSync Imaging Service listening on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

// 🚨 INTENTIONAL VULNERABILITY: Local File Inclusion (LFI) / Path Traversal 🚨
// An attacker can pass "?file=../../../../etc/passwd" to escape the images folder.
func lfiHandler(w http.ResponseWriter, r *http.Request) {
	fileName := r.URL.Query().Get("file")
	if fileName == "" {
		http.Error(w, "Missing file parameter", http.StatusBadRequest)
		return
	}

	// DANGEROUS: Concatenating user input directly into the file path without sanitization
	basePath := "./images/"
	targetPath := basePath + fileName

	fmt.Printf("[Imaging Service] Attempting to read file: %s\n", targetPath)

	data, err := os.ReadFile(targetPath)
	if err != nil {
		http.Error(w, fmt.Sprintf("File not found or access denied: %v", err), http.StatusNotFound)
		return
	}

	// Setting to text/plain so the UI terminal easily displays the /etc/passwd contents
	w.Header().Set("Content-Type", "text/plain")
	w.Write(data)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "Imaging Service Online", "secure": true}`))
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}
