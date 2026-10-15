import csv
import statistics

ESG_MIN = 7.0       # minimum weighted ESG score (D3)
PILLAR_MIN = 3      # every pillar must be at least 3 (section 5)
Z_MIN = 1.0         # at least 1 standard deviation above the industry average (D1)


def ask_number(question, low, high):
    while True:
        answer = input(question)
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f"Please type a whole number between {low} and {high}.")


def ask_yes_no(question):
    while True:
        answer = input(question + " (yes/no): ").strip().lower()
        if answer in ("yes", "no"):
            return answer == "yes"
        print("Please type yes or no.")


def load_stocks(path):
    stocks = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            stocks.append({
                "id": row["ID"],
                "performance": float(row["Performance"]),
                "industry": row["Industry"],
                "year": int(row["FoundationYear"]),
                "environment": int(row["Environment"]),
                "social": int(row["Social"]),
                "governance": int(row["Governance"]),
            })
    return stocks


def industry_cutoffs(stocks):
    """Cut-off per industry = average return + Z_MIN x standard deviation (D1)."""
    returns = {}
    for s in stocks:
        returns.setdefault(s["industry"], []).append(s["performance"])
    cutoffs = {}
    for industry, values in returns.items():
        average = statistics.mean(values)
        deviation = statistics.pstdev(values)   # 0 if all returns are equal -> all pass
        cutoffs[industry] = average + Z_MIN * deviation
    return cutoffs


def merge_sort(items, key):
    """Sort a list with merge sort (low to high by key) and return a new sorted list."""
    if len(items) <= 1:                      # 0 or 1 item: already sorted
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)   # sort the left half
    right = merge_sort(items[middle:], key)  # sort the right half
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):  # merge: always take the smaller front item
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])                  # add what is left of either half
    merged.extend(right[j:])
    return merged


def main():
    stocks = load_stocks("stocks.csv")

    # Part 1 - ask the user (D6, D9)
    n = ask_number("How many stocks do you want (1-100)? ", 1, 100)
    use_industry = ask_yes_no("Only the highest performers in their industry?")
    use_year = ask_yes_no("Only well-established companies?")
    max_year = ask_number("Founded in or before which year (1800-2020)? ", 1800, 2020) if use_year else None
    use_esg = ask_yes_no("Only companies with a high ESG score?")
    w_env, w_soc, w_gov = 1, 1, 1                       # equal weights by default (D3)
    if use_esg:
        w_env = ask_number("Weight for Environment (1-5)? ", 1, 5)
        w_soc = ask_number("Weight for Social (1-5)? ", 1, 5)
        w_gov = ask_number("Weight for Governance (1-5)? ", 1, 5)
    w_total = w_env + w_soc + w_gov

    # Part 2 - cut-off per industry, only when that filter is on (D10)
    cutoffs = industry_cutoffs(stocks) if use_industry else {}

    # Part 3 - check every stock
    matches, others = [], []
    for s in stocks:
        s["esg"] = (w_env * s["environment"] + w_soc * s["social"] + w_gov * s["governance"]) / w_total
        lowest_pillar = min(s["environment"], s["social"], s["governance"])
        s["misses"] = []
        if use_industry and s["performance"] < cutoffs[s["industry"]]:
            s["misses"].append("industry")
        if use_esg and (s["esg"] < ESG_MIN or lowest_pillar < PILLAR_MIN):
            s["misses"].append("ESG")
        if use_year and s["year"] > max_year:
            s["misses"].append("year")
        (others if s["misses"] else matches).append(s)
    matches = merge_sort(matches, key=lambda s: (-s["performance"], -s["esg"], s["id"]))   # D7

    # Part 4 - build the final list (D4, D5)
    result = matches[:n]
    if len(matches) < n:
        print(f"\nOnly {len(matches)} stocks pass all your filters. You asked for {n}.")
        if ask_yes_no("Fill up the list with the closest other stocks?"):
            others = merge_sort(others, key=lambda s: (len(s["misses"]), -s["performance"], s["id"]))
            result = result + others[:n - len(result)]

    # Part 5 - show the result (D8)
    if not result:
        print("No stocks to show.")
        return
    print(f"\n=========== iTrade: your top {len(result)} stocks ===========")
    print(f"{'#':<4}{'ID':<6}{'Industry':<15}{'Return':>8}{'ESG':>6}   Reason")
    for rank, s in enumerate(result, start=1):
        if s["misses"]:
            reason = "added by filling up, misses: " + ", ".join(s["misses"])
        else:
            reason = "passes all active filters"
        print(f"{rank:<4}{s['id']:<6}{s['industry']:<15}{s['performance']:>7.2f}%{s['esg']:>6.1f}   {reason}")
        if s["performance"] < 0:
            print("    Warning: this stock has a negative return.")
    print("=" * 52)


if __name__ == "__main__":
    main()
