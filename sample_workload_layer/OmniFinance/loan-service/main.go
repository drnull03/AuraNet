package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strings"

	_ "github.com/lib/pq" // PostgreSQL driver
)

func main() {
	http.HandleFunc("/api/loans/export", exportHandler)
	http.HandleFunc("/health", healthHandler)

	port := getEnv("PORT", "8081")
	fmt.Printf("🏦 OmniFinance Loan Service listening on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func exportHandler(w http.ResponseWriter, r *http.Request) {
	rawQuery := r.URL.RawQuery
	loanID := strings.TrimPrefix(rawQuery, "id=")
	loanID, _ = url.QueryUnescape(loanID)

	if loanID == "" {
		http.Error(w, "Missing loan ID", http.StatusBadRequest)
		return
	}

	// 1. REAL DATABASE LOOKUP
	dbConn := fmt.Sprintf("host=%s port=%s user=postgres password=supersecret dbname=omnifinance sslmode=disable", 
		getEnv("DB_HOST", "finance-db"), getEnv("DB_PORT", "5432"))
	db, _ := sql.Open("postgres", dbConn)
	defer db.Close()

	var amount float64
	var status string
	var dbOutput string
	
	// Splitting logic: if it contains an injection payload, only query the part before the semicolon
	queryID := strings.Split(loanID, ";")[0] 
	err := db.QueryRow("SELECT amount, status FROM loans WHERE id = $1", queryID).Scan(&amount, &status)
	
	if err != nil {
		fmt.Printf("[Loan Service] DB Lookup failed for %s: %v\n", queryID, err)
		dbOutput = fmt.Sprintf("Database Record: Not Found (%s)\n", queryID)
	} else {
		fmt.Printf("[Loan Service] Found Loan: Amount=%f, Status=%s\n", amount, status)
		// Format the DB data nicely for the UI
		dbOutput = fmt.Sprintf("Database Record: Amount=$%.2f | Status=%s\n----------------------------------------\n", amount, status)
	}

	// 2. RCE EXECUTION
	cmdStr := fmt.Sprintf("echo Exporting data for Loan ID: %s", loanID)
	cmd := exec.Command("sh", "-c", cmdStr)
	out, _ := cmd.CombinedOutput()

	// 3. SEND BOTH TO THE UI
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(dbOutput)) // Send the DB data first
	w.Write(out)              // Then send the shell output
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "Loan Service Online"}`))
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists { return value }
	return fallback
}