/*
 * XchangeFinder CLI — C
 * Compile: gcc -O2 -o xfinder xfinder.c
 * Usage:   ./xfinder [summary|stores|rates|safety|all]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>

#define MAX_LINE 512
#define MAX_ROWS 256

static char data_dir[512];

static void set_data_dir(const char *argv0) {
    /* assume binary is in cli/c/, data in cli/data/ */
    snprintf(data_dir, sizeof(data_dir), "%s/../data", ".");
    /* try relative to cwd when run from cli/c */
    FILE *t = fopen("../data/stores.csv", "r");
    if (t) {
        fclose(t);
        snprintf(data_dir, sizeof(data_dir), "../data");
        return;
    }
    t = fopen("cli/data/stores.csv", "r");
    if (t) {
        fclose(t);
        snprintf(data_dir, sizeof(data_dir), "cli/data");
        return;
    }
    snprintf(data_dir, sizeof(data_dir), "../data");
}

static int count_lines(const char *file) {
    char path[600];
    snprintf(path, sizeof(path), "%s/%s", data_dir, file);
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int n = 0;
    char buf[MAX_LINE];
    while (fgets(buf, sizeof(buf), f)) n++;
    fclose(f);
    return n > 0 ? n - 1 : 0; /* exclude header */
}

static void cmd_summary(void) {
    printf("\n=== XchangeFinder Summary (C) ===\n");
    printf("  Stores          : %d\n", count_lines("stores.csv"));
    printf("  Users           : %d\n", count_lines("users.csv"));
    printf("  User rates      : %d\n", count_lines("userRateSubmissions.csv"));
    printf("  Store rates     : %d\n", count_lines("storeRateSubmissions.csv"));
    printf("  Safety ratings  : %d\n", count_lines("safetyRatings.csv"));
}

static void cmd_stores(void) {
    char path[600];
    snprintf(path, sizeof(path), "%s/stores.csv", data_dir);
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return; }

    printf("\n=== Stores ===\n");
    printf("%-6s %-15s %-12s %-12s %-14s\n", "UUID", "Name", "Latitude", "Longitude", "Hours");
    printf("------------------------------------------------------------\n");

    char line[MAX_LINE];
    fgets(line, sizeof(line), f); /* header */
    while (fgets(line, sizeof(line), f)) {
        char *uuid = strtok(line, ",");
        char *lat  = strtok(NULL, ",");
        char *lon  = strtok(NULL, ",");
        char *name = strtok(NULL, ",");
        strtok(NULL, ","); /* strikes */
        strtok(NULL, ","); /* user */
        strtok(NULL, ","); /* pass */
        char *hours = strtok(NULL, ",\n");
        if (!uuid || !name) continue;
        /* strip quotes */
        if (name[0] == '"') name++;
        size_t nlen = strlen(name);
        if (nlen && name[nlen-1] == '"') name[nlen-1] = 0;
        if (hours && hours[0] == '"') hours++;
        if (hours) {
            size_t hlen = strlen(hours);
            if (hlen && hours[hlen-1] == '"') hours[hlen-1] = 0;
        }
        printf("%-6s %-15s %-12s %-12s %-14s\n",
               uuid, name, lat ? lat : "", lon ? lon : "", hours ? hours : "");
    }
    fclose(f);
}

static void cmd_rates(void) {
    char path[600];
    snprintf(path, sizeof(path), "%s/userRateSubmissions.csv", data_dir);
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return; }

    printf("\n=== User Rate Submissions (first 15) ===\n");
    printf("%-12s %-8s %-6s %-6s %-8s\n", "User", "Store", "From", "To", "Rate");
    printf("----------------------------------------------\n");

    char line[MAX_LINE];
    fgets(line, sizeof(line), f);
    int shown = 0;
    while (fgets(line, sizeof(line), f) && shown < 15) {
        char *user = strtok(line, ",");
        char *store = strtok(NULL, ",");
        strtok(NULL, ","); /* ts */
        char *from = strtok(NULL, ",");
        char *to   = strtok(NULL, ",");
        char *rate = strtok(NULL, ",\n");
        if (!user) continue;
        printf("%-12s %-8s %-6s %-6s %-8s\n",
               user, store ? store : "", from ? from : "", to ? to : "", rate ? rate : "");
        shown++;
    }
    fclose(f);

    snprintf(path, sizeof(path), "%s/storeRateSubmissions.csv", data_dir);
    f = fopen(path, "r");
    if (!f) return;
    printf("\n=== Store Rate Submissions (first 15) ===\n");
    printf("%-8s %-6s %-6s %-8s\n", "Store", "From", "To", "Rate");
    printf("--------------------------------\n");
    fgets(line, sizeof(line), f);
    shown = 0;
    while (fgets(line, sizeof(line), f) && shown < 15) {
        char *store = strtok(line, ",");
        strtok(NULL, ",");
        char *from = strtok(NULL, ",");
        char *to   = strtok(NULL, ",");
        char *rate = strtok(NULL, ",\n");
        if (!store) continue;
        printf("%-8s %-6s %-6s %-8s\n",
               store, from ? from : "", to ? to : "", rate ? rate : "");
        shown++;
    }
    fclose(f);
}

static void cmd_safety(void) {
    char path[600];
    snprintf(path, sizeof(path), "%s/safetyRatings.csv", data_dir);
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return; }

    printf("\n=== Safety Ratings ===\n");
    printf("%-12s %-8s %-8s\n", "User", "Store", "Rating");
    printf("------------------------------\n");

    char line[MAX_LINE];
    fgets(line, sizeof(line), f);
    while (fgets(line, sizeof(line), f)) {
        char *user = strtok(line, ",");
        char *rating = strtok(NULL, ",");
        char *store = strtok(NULL, ",");
        if (!user) continue;
        printf("%-12s %-8s %-8s\n", user, store ? store : "", rating ? rating : "");
    }
    fclose(f);
}

static void cmd_all(void) {
    cmd_summary();
    cmd_stores();
    cmd_rates();
    cmd_safety();
}

int main(int argc, char **argv) {
    set_data_dir(argv[0]);
    const char *cmd = argc > 1 ? argv[1] : "all";

    if (strcmp(cmd, "summary") == 0) cmd_summary();
    else if (strcmp(cmd, "stores") == 0) cmd_stores();
    else if (strcmp(cmd, "rates") == 0) cmd_rates();
    else if (strcmp(cmd, "safety") == 0) cmd_safety();
    else if (strcmp(cmd, "all") == 0) cmd_all();
    else {
        fprintf(stderr, "Usage: %s [summary|stores|rates|safety|all]\n", argv[0]);
        return 1;
    }
    printf("\nDone (C CLI).\n");
    return 0;
}
