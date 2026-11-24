/*
 * XchangeFinder CLI — C++
 * Compile: g++ -std=c++17 -O2 -o xfinder xfinder.cpp
 * Usage:   ./xfinder [summary|stores|rates|safety|all]
 */

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::string data_dir = "../data";

std::vector<std::string> split_csv(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;
    bool in_quotes = false;
    for (char c : line) {
        if (c == '"') {
            in_quotes = !in_quotes;
        } else if (c == ',' && !in_quotes) {
            out.push_back(cur);
            cur.clear();
        } else if (c != '\n' && c != '\r') {
            cur.push_back(c);
        }
    }
    out.push_back(cur);
    return out;
}

std::string strip_q(std::string s) {
    if (!s.empty() && s.front() == '"') s.erase(0, 1);
    if (!s.empty() && s.back() == '"') s.pop_back();
    return s;
}

int count_rows(const std::string& file) {
    std::ifstream in(data_dir + "/" + file);
    if (!in) return -1;
    int n = 0;
    std::string line;
    while (std::getline(in, line)) ++n;
    return n > 0 ? n - 1 : 0;
}

void cmd_summary() {
    std::cout << "\n=== XchangeFinder Summary (C++) ===\n";
    std::cout << "  Stores          : " << count_rows("stores.csv") << "\n";
    std::cout << "  Users           : " << count_rows("users.csv") << "\n";
    std::cout << "  User rates      : " << count_rows("userRateSubmissions.csv") << "\n";
    std::cout << "  Store rates     : " << count_rows("storeRateSubmissions.csv") << "\n";
    std::cout << "  Safety ratings  : " << count_rows("safetyRatings.csv") << "\n";
}

void cmd_stores() {
    std::ifstream in(data_dir + "/stores.csv");
    if (!in) {
        std::cerr << "Cannot open stores.csv\n";
        return;
    }
    std::cout << "\n=== Stores ===\n";
    std::cout << std::left
              << std::setw(6) << "UUID"
              << std::setw(16) << "Name"
              << std::setw(12) << "Latitude"
              << std::setw(12) << "Longitude"
              << std::setw(14) << "Hours" << "\n";
    std::cout << std::string(60, '-') << "\n";

    std::string line;
    std::getline(in, line); // header
    while (std::getline(in, line)) {
        auto cols = split_csv(line);
        if (cols.size() < 8) continue;
        std::cout << std::left
                  << std::setw(6) << cols[0]
                  << std::setw(16) << strip_q(cols[3])
                  << std::setw(12) << cols[1]
                  << std::setw(12) << cols[2]
                  << std::setw(14) << strip_q(cols[7]) << "\n";
    }
}

void cmd_rates() {
    {
        std::ifstream in(data_dir + "/userRateSubmissions.csv");
        if (!in) return;
        std::cout << "\n=== User Rate Submissions (first 15) ===\n";
        std::cout << std::left
                  << std::setw(12) << "User"
                  << std::setw(8) << "Store"
                  << std::setw(6) << "From"
                  << std::setw(6) << "To"
                  << std::setw(8) << "Rate" << "\n";
        std::cout << std::string(46, '-') << "\n";
        std::string line;
        std::getline(in, line);
        int shown = 0;
        while (std::getline(in, line) && shown < 15) {
            auto cols = split_csv(line);
            if (cols.size() < 6) continue;
            std::cout << std::left
                      << std::setw(12) << strip_q(cols[0])
                      << std::setw(8) << cols[1]
                      << std::setw(6) << strip_q(cols[3])
                      << std::setw(6) << strip_q(cols[4])
                      << std::setw(8) << cols[5] << "\n";
            ++shown;
        }
    }
    {
        std::ifstream in(data_dir + "/storeRateSubmissions.csv");
        if (!in) return;
        std::cout << "\n=== Store Rate Submissions (first 15) ===\n";
        std::cout << std::left
                  << std::setw(8) << "Store"
                  << std::setw(6) << "From"
                  << std::setw(6) << "To"
                  << std::setw(8) << "Rate" << "\n";
        std::cout << std::string(32, '-') << "\n";
        std::string line;
        std::getline(in, line);
        int shown = 0;
        while (std::getline(in, line) && shown < 15) {
            auto cols = split_csv(line);
            if (cols.size() < 5) continue;
            std::cout << std::left
                      << std::setw(8) << cols[0]
                      << std::setw(6) << strip_q(cols[2])
                      << std::setw(6) << strip_q(cols[3])
                      << std::setw(8) << cols[4] << "\n";
            ++shown;
        }
    }
}

void cmd_safety() {
    // Load store names
    std::map<std::string, std::string> names;
    {
        std::ifstream in(data_dir + "/stores.csv");
        std::string line;
        std::getline(in, line);
        while (std::getline(in, line)) {
            auto cols = split_csv(line);
            if (cols.size() >= 4)
                names[cols[0]] = strip_q(cols[3]);
        }
    }

    std::map<std::string, std::pair<double, int>> agg; // uuid -> (sum, count)

    std::ifstream in(data_dir + "/safetyRatings.csv");
    if (!in) return;

    std::cout << "\n=== Safety Ratings ===\n";
    std::cout << std::left
              << std::setw(12) << "User"
              << std::setw(8) << "Store"
              << std::setw(8) << "Rating" << "\n";
    std::cout << std::string(30, '-') << "\n";

    std::string line;
    std::getline(in, line);
    while (std::getline(in, line)) {
        auto cols = split_csv(line);
        if (cols.size() < 3) continue;
        std::cout << std::left
                  << std::setw(12) << strip_q(cols[0])
                  << std::setw(8) << cols[2]
                  << std::setw(8) << cols[1] << "\n";
        double r = std::stod(cols[1]);
        agg[cols[2]].first += r;
        agg[cols[2]].second += 1;
    }

    std::cout << "\n=== Average Safety by Store ===\n";
    std::cout << std::left
              << std::setw(16) << "Store"
              << std::setw(10) << "Avg"
              << std::setw(8) << "Votes" << "\n";
    std::cout << std::string(36, '-') << "\n";
    for (const auto& [uuid, sc] : agg) {
        std::string n = names.count(uuid) ? names[uuid] : uuid;
        double avg = sc.second ? sc.first / sc.second : 0.0;
        std::cout << std::left
                  << std::setw(16) << n
                  << std::setw(10) << std::fixed << std::setprecision(2) << avg
                  << std::setw(8) << sc.second << "\n";
    }
}

void cmd_all() {
    cmd_summary();
    cmd_stores();
    cmd_rates();
    cmd_safety();
}

} // namespace

int main(int argc, char** argv) {
    // try alternate data paths
    if (!std::ifstream(data_dir + "/stores.csv")) {
        if (std::ifstream("cli/data/stores.csv"))
            data_dir = "cli/data";
        else if (std::ifstream("../../cli/data/stores.csv"))
            data_dir = "../../cli/data";
    }

    std::string cmd = argc > 1 ? argv[1] : "all";
    if (cmd == "summary") cmd_summary();
    else if (cmd == "stores") cmd_stores();
    else if (cmd == "rates") cmd_rates();
    else if (cmd == "safety") cmd_safety();
    else if (cmd == "all") cmd_all();
    else {
        std::cerr << "Usage: " << argv[0] << " [summary|stores|rates|safety|all]\n";
        return 1;
    }
    std::cout << "\nDone (C++ CLI).\n";
    return 0;
}
