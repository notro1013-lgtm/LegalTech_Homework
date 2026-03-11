import os
import csv

CHECKLIST_PATH = "data/contract_checklist.csv"
CONTRACTS_DIR  = "data/contracts_txt"
ISSUES_PATH    = "reports/contract_issues.csv"
SUMMARY_PATH   = "reports/contract_summary.txt"


# ШАГ 1: Читаем правила из чек-листа

def load_rules(path):
    rules = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rules.append(row)
    return rules


# ШАГ 2: Читаем текст договора

def load_contract(path):
    with open(path, encoding="utf-8") as f:
        return f.read().lower()  


# ШАГ 3: Проверяем один договор по всем правилам

def check_contract(filename, text, rules):
    results = []
    for rule in rules:
        pattern   = rule["pattern"].lower()
        rule_type = rule["rule_type"]

        found = pattern in text  # True если слово/фраза найдена в тексте

        # Определяем статус в зависимости от типа правила
        if rule_type == "required":
            status = "FOUND" if found else "MISSING"
        elif rule_type == "risk":
            status = "FOUND_RISK" if found else "NOT_FOUND"
        else:
            status = "UNKNOWN"

        results.append({
            "contract_file": filename,
            "rule_id":       rule["rule_id"],
            "rule_type":     rule_type,
            "severity":      rule["severity"],
            "pattern":       rule["pattern"],
            "status":        status,
            "comment":       rule["comment"],
        })
    return results


# ШАГ 4: Сохраняем детальный отчёт contract_issues.csv

def save_issues(all_results):
    os.makedirs("reports", exist_ok=True)
    fieldnames = ["contract_file", "rule_id", "rule_type", "severity", "pattern", "status", "comment"]
    with open(ISSUES_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(all_results)
    print(f"  Детальный отчёт сохранён: {ISSUES_PATH}")


# ШАГ 5: Сохраняем краткое резюме contract_summary.txt

def save_summary(all_results):
    # Собираем список уникальных договоров
    contracts = sorted(set(r["contract_file"] for r in all_results))
    total_critical = sum(
        1 for r in all_results
        if r["severity"] == "Критично" and r["status"] in ("MISSING", "FOUND_RISK")
    )

    lines = []
    lines.append("=" * 60)
    lines.append("РЕЗЮМЕ ПРОВЕРКИ ДОГОВОРОВ")
    lines.append("=" * 60)
    lines.append(f"Проверено договоров : {len(contracts)}")
    lines.append(f"Критичных замечаний : {total_critical}")
    lines.append("")

    for contract in contracts:
        # Берём только результаты для этого договора
        c_results = [r for r in all_results if r["contract_file"] == contract]

        # Ключевые выводы: критичные MISSING и все FOUND_RISK
        key_issues = [
            r for r in c_results
            if (r["status"] == "MISSING" and r["severity"] == "Критично")
            or r["status"] == "FOUND_RISK"
        ]

        lines.append(f"Договор: {contract}")
        lines.append("-" * 40)

        if not key_issues:
            lines.append("  Критичных замечаний не обнаружено.")
        else:
            for r in key_issues[:5]:  # не более 5 выводов на договор
                lines.append(f"  [{r['status']}] {r['rule_id']} | {r['severity']} | {r['comment']}")

        lines.append("")

    lines.append("=" * 60)

    os.makedirs("reports", exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Резюме сохранено      : {SUMMARY_PATH}")


# ГЛАВНАЯ ФУНКЦИЯ — запускает всё по порядку

def main():
    print("Загружаем правила из чек-листа...")
    rules = load_rules(CHECKLIST_PATH)
    print(f"  Загружено правил: {len(rules)}")

    print("Обрабатываем договоры...")
    all_results = []

    for filename in os.listdir(CONTRACTS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(CONTRACTS_DIR, filename)
            text = load_contract(filepath)
            results = check_contract(filename, text, rules)
            all_results.extend(results)
            print(f"  Проверен: {filename}")

    print("Сохраняем отчёты...")
    save_issues(all_results)
    save_summary(all_results)

    print("\nГотово! Отчёты находятся в папке reports/")

# Точка входа — скрипт запускается отсюда
if __name__ == "__main__":
    main()