package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	_ "github.com/lib/pq"
)

// Default to localhost for K8s environment variable compatibility
var accountServiceURL = getEnv("ACCOUNT_SERVICE_URL", "http://localhost:5000")
var db *sql.DB

type Loan struct {
	ID        string  `json:"id"`
	AccountID int     `json:"account_id"`
	Amount    float64 `json:"amount"`
	Status    string  `json:"status"`
}

func main() {
	initDB()
	defer db.Close()

	http.HandleFunc("/api/loans", getLoansHandler)
	http.HandleFunc("/api/loans/scrape", ssrfScrapeHandler) // 🚨 THE VULNERABILITY 🚨
	http.HandleFunc("/health", healthHandler)

	port := getEnv("PORT", "8081")
	fmt.Printf("🚀 OmniFinance Loan Service listening on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

// Initialize the real PostgreSQL connection
func initDB() {
	host := getEnv("DB_HOST", "localhost")
	user := getEnv("DB_USER", "postgres")
	pass := getEnv("DB_PASSWORD", "supersecret")
	dbname := getEnv("DB_NAME", "omnifinance")

	connStr := fmt.Sprintf("host=%s user=%s password=%s dbname=%s sslmode=disable", host, user, pass, dbname)
	
	var err error
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Fatal error opening DB connection: %v", err)
	}

	err = db.Ping()
	if err != nil {
		log.Printf("Warning: Could not ping database at startup: %v", err)
	} else {
		fmt.Println("✅ Successfully connected to Finance DB")
	}
}

// Normal Business Logic: Now querying the real database
func getLoansHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT id, account_id, amount, status FROM loans")
	if err != nil {
		http.Error(w, "Database query failed", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var loans []Loan
	for rows.Next() {
		var l Loan
		if err := rows.Scan(&l.ID, &l.AccountID, &l.Amount, &l.Status); err != nil {
			log.Printf("Error scanning row: %v", err)
			continue
		}
		loans = append(loans, l)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(loans)
}

// 🚨 INTENTIONAL VULNERABILITY: Lateral Movement / SSRF 🚨
// A hacker hits this endpoint to force the Loan Service to secretly 
// query the Account Service directly, bypassing the API Gateway!
func ssrfScrapeHandler(w http.ResponseWriter, r *http.Request) {
	accountID := r.URL.Query().Get("id")
	if accountID == "" {
		http.Error(w, "Missing account ID to scrape", http.StatusBadRequest)
		return
	}

	targetURL := fmt.Sprintf("%s/api/accounts?id=%s", accountServiceURL, accountID)
	fmt.Printf("[Lateral Movement Attempt] Scraping %s\n", targetURL)

	// Make the unauthorized internal request
	resp, err := http.Get(targetURL)
	if err != nil {
		http.Error(w, fmt.Sprintf("Lateral movement failed: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, "Failed to read response", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(body)
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