from assistant.adapters.local_rule_based_adapter import LocalRuleBasedAdapter


def test_resume_adapter_extracts_fields_and_answers():
    text = """Praneeth Reddy
Data Scientist
praneeth@example.com | +91 6309122909 | github.com/example
SUMMARY
Data Scientist with 3+ years at IIT Madras specialising in evaluation framework design and LLM quality assessment.
TECHNICAL SKILLS
Python, PyTorch, Hugging Face, pandas, NumPy, SQL, AWS
PROFESSIONAL EXPERIENCE
Project Associate — AI4Bharat
EDUCATION
B.E., Electrical Engineering | CGPA: 7.5
CERTIFICATIONS
Google Cybersecurity
"""
    output = LocalRuleBasedAdapter().predict({"text": text, "request": "summarize this resume"})
    assert output["fields"]["candidate_name"] == "Praneeth Reddy"
    assert "Python" in output["fields"]["skills"]
    assert "not enough evidence" not in output["answer"].lower()
