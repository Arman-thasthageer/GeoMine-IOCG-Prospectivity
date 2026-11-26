
import csv
import json
import os
import re
import requests

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(PROJECT_DIR, "eval")

QUESTIONS_FILE = os.path.join(EVAL_DIR, "groundedness_questions.json")
API_URL = "http://127.0.0.1:8081/api/ask"

# Expected evidence based on verified project outputs.
EXPECTED = {
    "Q01": ["R2", "0.8256", "0.9652", "92.00", "23", "Known deposit cells: 0"],
    "Q02": ["R1", "0.9273", "2492.00", "15"],
    "Q03": ["11", "refined target polygons"],
    "Q04": ["15 known deposit cells in total", "R1: 15", "R2: 0"],
    "Q05": [
        "Grid cell 2",
        "0.9758",
        "99.8743",
        "Sources 64.2205",
        "Energy 48.6725",
        "Pathways 66.2254",
        "Deposition 2.6327",
        "P2a",
        "D2a",
        "P1"
    ],
    "Q06": ["R11", "0.5896"],
    "Q07": [
        "1. R1: 0.9273",
        "2. R2: 0.8256",
        "3. R3: 0.8029",
        "4. R4: 0.7981",
        "5. R5: 0.7533",
        "6. R6: 0.7389",
        "7. R7: 0.7241",
        "8. R8: 0.7125",
        "9. R9: 0.6904",
        "10. R10: 0.6899",
        "11. R11: 0.5896"
    ],
    "Q08": ["R2", "Known deposit cells: 0"],
    "Q09": ["R2", "92.00 km²"],
}

UNSUPPORTED_TERMS = [
    "does not contain",
    "not available",
    "not provided",
    "cannot determine",
    "cannot provide",
    "no copper grade"
]


def evaluate_response(test, data, http_success=True):
    question_id = test["id"]
    answer = str(data.get("answer", ""))
    lower_answer = answer.lower()

    checks = {
        "answer_present": bool(answer.strip()),
        "grounded_true": data.get("grounded") is True,
        "source_present": bool(data.get("sources")),
        "question_specific": False
    }

    if question_id in EXPECTED:
        checks["question_specific"] = all(
            term.lower() in lower_answer
            for term in EXPECTED[question_id]
        )

    elif question_id == "Q10":
        checks["question_specific"] = any(
            term in lower_answer for term in UNSUPPORTED_TERMS
        )

    passed = http_success and all(checks.values())

    return {
        "test_id": question_id,
        "question": test["question"],
        "answer": answer,
        "grounded": data.get("grounded", False),
        "http_success": http_success,
        "automatic_check": "PASS" if passed else "FAIL",
        "failed_checks": "; ".join(
            name for name, result in checks.items() if not result
        ),
        "manual_review_required": True,
        "sources": "; ".join(data.get("sources", []))
    }


def main():
    print("=" * 60)
    print("GEOMINE GROUNDEDNESS EVALUATION")
    print("=" * 60)

    if not os.path.exists(QUESTIONS_FILE):
        raise FileNotFoundError(QUESTIONS_FILE)

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        evaluation = json.load(file)

    results = []

    for test in evaluation["tests"]:
        print(f"\nTesting {test['id']}: {test['question']}")

        try:
            response = requests.post(
                API_URL,
                json={"question": test["question"]},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            result = evaluate_response(test, data)
        except (requests.RequestException, ValueError) as error:
            result = evaluate_response(
                test,
                {
                    "answer": f"API or response error: {error}",
                    "grounded": False,
                    "sources": []
                },
                http_success=False
            )

        results.append(result)

        print("Answer:", result["answer"])
        print("Grounded:", result["grounded"])
        print("Automatic check:", result["automatic_check"])

        if result["failed_checks"]:
            print("Failed checks:", result["failed_checks"])

    csv_path = os.path.join(EVAL_DIR, "groundedness_results.csv")
    json_path = os.path.join(EVAL_DIR, "groundedness_transcripts.json")

    fields = [
        "test_id",
        "question",
        "answer",
        "grounded",
        "http_success",
        "automatic_check",
        "failed_checks",
        "manual_review_required",
        "sources"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    passed = sum(r["automatic_check"] == "PASS" for r in results)
    failed = len(results) - passed

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print("Total questions:", len(results))
    print("Passed:", passed)
    print("Failed:", failed)
    print("Manual review required:", len(results))
    print("CSV:", csv_path)
    print("Transcripts:", json_path)

    if failed:
        print("\nSome checks failed. Review the failed checks above.")
    else:
        print("\nAll automatic checks passed.")


if __name__ == "__main__":
    main()
