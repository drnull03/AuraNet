package main

import (
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strings"
)

func main() {
	http.HandleFunc("/api/loans/export", exportHandler)
	http.HandleFunc("/health", healthHandler)

	port := getEnv("PORT", "8081")
	fmt.Printf("🏦 OmniFinance Loan Service listening on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func exportHandler(w http.ResponseWriter, r *http.Request) {
	// FIX: Go 1.17+ strictly blocks unescaped semicolons in URL.Query().
	// we bypass the parser, grab the raw URL string, and slice it manually!
	rawQuery := r.URL.RawQuery
	loanID := strings.TrimPrefix(rawQuery, "id=")
	loanID, _ = url.QueryUnescape(loanID)

	if loanID == "" {
		http.Error(w, "Missing loan ID", http.StatusBadRequest)
		return
	}

	// DANGEROUS: Passing user input directly into a system shell command!
	// If a user inputs "123; cat /etc/passwd", the shell will execute both commands.
	cmdStr := fmt.Sprintf("echo Exporting loan data for ID: %s", loanID)
	cmd := exec.Command("sh", "-c", cmdStr)

	fmt.Printf("[Loan Service] Executing Shell Command: %s\n", cmdStr)

	out, _ := cmd.CombinedOutput()

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write(out)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "Loan Service Online"}`))
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}