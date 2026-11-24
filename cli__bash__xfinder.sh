#!/bin/bash
# XchangeFinder CLI — Bash
# Usage: ./xfinder.sh [summary|stores|rates|safety|all]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${SCRIPT_DIR}/../data"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

header() { echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}"; }

cmd_summary() {
  header "XchangeFinder Summary (Bash)"
  stores=$(tail -n +2 "$DATA/stores.csv" | wc -l)
  users=$(tail -n +2 "$DATA/users.csv" | wc -l)
  urates=$(tail -n +2 "$DATA/userRateSubmissions.csv" | wc -l)
  srates=$(tail -n +2 "$DATA/storeRateSubmissions.csv" | wc -l)
  safety=$(tail -n +2 "$DATA/safetyRatings.csv" | wc -l)
  printf "  Stores          : %s\n" "$stores"
  printf "  Users           : %s\n" "$users"
  printf "  User rates      : %s\n" "$urates"
  printf "  Store rates     : %s\n" "$srates"
  printf "  Safety ratings  : %s\n" "$safety"
}

cmd_stores() {
  header "Stores"
  printf "%-6s %-15s %-12s %-12s %-14s\n" "UUID" "Name" "Latitude" "Longitude" "Hours"
  printf "%s\n" "------------------------------------------------------------"
  tail -n +2 "$DATA/stores.csv" | while IFS=',' read -r uuid lat lon name strikes user pass hours pic; do
    # strip quotes if any
    name="${name//\"/}"
    hours="${hours//\"/}"
    printf "%-6s %-15s %-12s %-12s %-14s\n" "$uuid" "$name" "$lat" "$lon" "$hours"
  done
}

cmd_rates() {
  header "User Rate Submissions (sample)"
  printf "%-12s %-8s %-6s %-6s %-8s\n" "User" "Store" "From" "To" "Rate"
  printf "%s\n" "----------------------------------------------"
  tail -n +2 "$DATA/userRateSubmissions.csv" | head -15 | while IFS=',' read -r user store ts from to rate; do
    user="${user//\"/}"; from="${from//\"/}"; to="${to//\"/}"
    printf "%-12s %-8s %-6s %-6s %-8s\n" "$user" "$store" "$from" "$to" "$rate"
  done

  header "Store Rate Submissions (sample)"
  printf "%-8s %-6s %-6s %-8s\n" "Store" "From" "To" "Rate"
  printf "%s\n" "--------------------------------"
  tail -n +2 "$DATA/storeRateSubmissions.csv" | head -15 | while IFS=',' read -r store ts from to rate; do
    from="${from//\"/}"; to="${to//\"/}"
    printf "%-8s %-6s %-6s %-8s\n" "$store" "$from" "$to" "$rate"
  done
}

cmd_safety() {
  header "Safety Ratings"
  printf "%-12s %-8s %-8s\n" "User" "Store" "Rating"
  printf "%s\n" "------------------------------"
  tail -n +2 "$DATA/safetyRatings.csv" | while IFS=',' read -r user rating store ts; do
    user="${user//\"/}"
    printf "%-12s %-8s %-8s\n" "$user" "$store" "$rating"
  done

  header "Average Safety by Store (awk)"
  # join store names
  awk -F',' '
    NR==FNR { if(NR>1) name[$1]=$4; next }
    FNR>1 { sum[$3]+=$2; cnt[$3]++ }
    END {
      printf "%-15s %-10s %-8s\n", "Store", "Avg", "Votes"
      printf "------------------------------------\n"
      for (s in sum) {
        n = (s in name) ? name[s] : s
        gsub(/"/, "", n)
        printf "%-15s %-10.2f %-8d\n", n, sum[s]/cnt[s], cnt[s]
      }
    }
  ' "$DATA/stores.csv" "$DATA/safetyRatings.csv"
}

cmd_all() {
  cmd_summary
  cmd_stores
  cmd_rates
  cmd_safety
}

case "${1:-all}" in
  summary) cmd_summary ;;
  stores)  cmd_stores ;;
  rates)   cmd_rates ;;
  safety)  cmd_safety ;;
  all)     cmd_all ;;
  *)
    echo "Usage: $0 [summary|stores|rates|safety|all]"
    exit 1
    ;;
esac

echo -e "\n${GREEN}Done (Bash CLI).${NC}"
