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
	http.ListenAndServe(":8081", nil)
}

func exportHandler(w http.ResponseWriter, r *http.Request) {
	rawQuery := r.URL.RawQuery
	loanID := strings.TrimPrefix(rawQuery, "id=")
	loanID, _ = url.QueryUnescape(loanID)

	// 1. REAL DATABASE LOOKUP
	dbConn := fmt.Sprintf("host=%s port=%s user=postgres password=postgres dbname=postgres sslmode=disable", 
		getEnv("DB_HOST", "finance-db"), getEnv("DB_PORT", "5432"))
	db, _ := sql.Open("postgres", dbConn)
	defer db.Close()

	var amount float64
	var status string
	// Splitting logic: if it contains an injection payload, only query the part before the semicolon
	queryID := strings.Split(loanID, ";")[0] 
	err := db.QueryRow("SELECT amount, status FROM loans WHERE id = $1", queryID).Scan(&amount, &status)
	
	if err != nil {
		fmt.Printf("[Loan Service] DB Lookup failed for %s: %v\n", queryID, err)
	} else {
		fmt.Printf("[Loan Service] Found Loan: Amount=%f, Status=%s\n", amount, status)
	}

	// 2. RCE EXECUTION
	cmdStr := fmt.Sprintf("echo Exporting data for Loan ID: %s", loanID)
	cmd := exec.Command("sh", "-c", cmdStr)
	out, _ := cmd.CombinedOutput()

	w.Write(out)
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists { return value }
	return fallback
}