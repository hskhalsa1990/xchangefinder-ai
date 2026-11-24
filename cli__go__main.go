/*
 * XchangeFinder CLI — Go
 * Run:   go run . [summary|stores|rates|safety|all]
 * Build: go build -o xfinder .
 */
package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func dataDir() string {
	candidates := []string{
		filepath.Join("..", "data"),
		filepath.Join("cli", "data"),
		filepath.Join("..", "..", "cli", "data"),
		"data",
	}
	for _, d := range candidates {
		if _, err := os.Stat(filepath.Join(d, "stores.csv")); err == nil {
			return d
		}
	}
	return filepath.Join("..", "data")
}

func readCSV(name string) ([][]string, error) {
	f, err := os.Open(filepath.Join(dataDir(), name))
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	return r.ReadAll()
}

func cmdSummary() {
	fmt.Println("\n=== XchangeFinder Summary (Go) ===")
	files := []struct {
		label, file string
	}{
		{"Stores", "stores.csv"},
		{"Users", "users.csv"},
		{"User rates", "userRateSubmissions.csv"},
		{"Store rates", "storeRateSubmissions.csv"},
		{"Safety ratings", "safetyRatings.csv"},
	}
	for _, it := range files {
		rows, err := readCSV(it.file)
		n := 0
		if err == nil && len(rows) > 0 {
			n = len(rows) - 1
		}
		fmt.Printf("  %-16s: %d\n", it.label, n)
	}
}

func cmdStores() {
	rows, err := readCSV("stores.csv")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Println("\n=== Stores ===")
	fmt.Printf("%-6s %-15s %-12s %-12s %-14s\n", "UUID", "Name", "Latitude", "Longitude", "Hours")
	fmt.Println(strings.Repeat("-", 60))
	for i, row := range rows {
		if i == 0 || len(row) < 8 {
			continue
		}
		fmt.Printf("%-6s %-15s %-12s %-12s %-14s\n",
			row[0], row[3], row[1], row[2], row[7])
	}
}

func cmdRates() {
	rows, err := readCSV("userRateSubmissions.csv")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Println("\n=== User Rate Submissions (first 15) ===")
	fmt.Printf("%-12s %-8s %-6s %-6s %-8s\n", "User", "Store", "From", "To", "Rate")
	fmt.Println(strings.Repeat("-", 46))
	shown := 0
	for i, row := range rows {
		if i == 0 || len(row) < 6 {
			continue
		}
		fmt.Printf("%-12s %-8s %-6s %-6s %-8s\n",
			row[0], row[1], row[3], row[4], row[5])
		shown++
		if shown >= 15 {
			break
		}
	}

	rows, err = readCSV("storeRateSubmissions.csv")
	if err != nil {
		return
	}
	fmt.Println("\n=== Store Rate Submissions (first 15) ===")
	fmt.Printf("%-8s %-6s %-6s %-8s\n", "Store", "From", "To", "Rate")
	fmt.Println(strings.Repeat("-", 32))
	shown = 0
	for i, row := range rows {
		if i == 0 || len(row) < 5 {
			continue
		}
		fmt.Printf("%-8s %-6s %-6s %-8s\n", row[0], row[2], row[3], row[4])
		shown++
		if shown >= 15 {
			break
		}
	}
}

func cmdSafety() {
	// store names
	names := map[string]string{}
	if rows, err := readCSV("stores.csv"); err == nil {
		for i, row := range rows {
			if i == 0 || len(row) < 4 {
				continue
			}
			names[row[0]] = row[3]
		}
	}

	type agg struct {
		sum float64
		n   int
	}
	avgs := map[string]*agg{}

	rows, err := readCSV("safetyRatings.csv")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Println("\n=== Safety Ratings ===")
	fmt.Printf("%-12s %-8s %-8s\n", "User", "Store", "Rating")
	fmt.Println(strings.Repeat("-", 30))
	for i, row := range rows {
		if i == 0 || len(row) < 3 {
			continue
		}
		fmt.Printf("%-12s %-8s %-8s\n", row[0], row[2], row[1])
		r, _ := strconv.ParseFloat(row[1], 64)
		if avgs[row[2]] == nil {
			avgs[row[2]] = &agg{}
		}
		avgs[row[2]].sum += r
		avgs[row[2]].n++
	}

	fmt.Println("\n=== Average Safety by Store ===")
	fmt.Printf("%-16s %-10s %-8s\n", "Store", "Avg", "Votes")
	fmt.Println(strings.Repeat("-", 36))
	for uuid, a := range avgs {
		name := names[uuid]
		if name == "" {
			name = uuid
		}
		avg := 0.0
		if a.n > 0 {
			avg = a.sum / float64(a.n)
		}
		fmt.Printf("%-16s %-10.2f %-8d\n", name, avg, a.n)
	}
}

func cmdAll() {
	cmdSummary()
	cmdStores()
	cmdRates()
	cmdSafety()
}

func main() {
	cmd := "all"
	if len(os.Args) > 1 {
		cmd = os.Args[1]
	}
	switch cmd {
	case "summary":
		cmdSummary()
	case "stores":
		cmdStores()
	case "rates":
		cmdRates()
	case "safety":
		cmdSafety()
	case "all":
		cmdAll()
	default:
		fmt.Fprintf(os.Stderr, "Usage: %s [summary|stores|rates|safety|all]\n", os.Args[0])
		os.Exit(1)
	}
	fmt.Println("\nDone (Go CLI).")
}
