# XchangeFinder CLI — Polyglot Tools

Same analysis interface implemented in **Bash**, **C**, **C++**, and **Go**.

All tools read CSV exports of the SQLite database (`cli/data/`).

## Quick run

```bash
cd cli

# Bash (no compile)
chmod +x bash/xfinder.sh
./bash/xfinder.sh all

# Build all compiled tools
make all

# Run summary from each language
make run
```

## Commands (same for every language)

| Command   | Description                          |
|-----------|--------------------------------------|
| `summary` | Counts of stores, users, rates, etc. |
| `stores`  | List exchange shops                  |
| `rates`   | Sample user & store rate submissions |
| `safety`  | Safety ratings + averages            |
| `all`     | Everything (default)                 |

## Per language

### Bash
```bash
./bash/xfinder.sh [summary|stores|rates|safety|all]
```

### C
```bash
gcc -O2 -o bin/xfinder_c c/xfinder.c
./bin/xfinder_c all
# or from c/: ../bin/xfinder_c summary
```

### C++
```bash
g++ -std=c++17 -O2 -o bin/xfinder_cpp cpp/xfinder.cpp
./bin/xfinder_cpp all
```

### Go
```bash
cd go && go build -o ../bin/xfinder_go .
../bin/xfinder_go all
# or: go run . safety
```

## Data

CSV files under `cli/data/` are exported from `db/XchangeFinder.db`:

- `stores.csv`
- `users.csv`
- `userRateSubmissions.csv`
- `storeRateSubmissions.csv`
- `safetyRatings.csv`

Re-export (from project root):

```bash
python3 -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('db/XchangeFinder.db')
for t in ['stores','users','userRateSubmissions','storeRateSubmissions','safetyRatings']:
    pd.read_sql(f'SELECT * FROM {t}', conn).to_csv(f'cli/data/{t}.csv', index=False)
conn.close()
"
```
