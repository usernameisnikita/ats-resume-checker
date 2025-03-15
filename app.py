from flask import Flask, render_template, request
import os
import docx
import pdfplumber
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Expected Sections in a Good Resume
EXPECTED_SECTIONS = ["experience", "education", "skills", "projects", "certifications"]

# Keywords for ATS matching (Example: Tech Jobs)
KEYWORDS = ["python", "java", "html", "css", "javascript", "machine learning", "sql", "data analysis"]

def extract_text(file_path):
    """Extracts text from PDF or DOCX"""
    text = ""
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text.lower()

def calculate_ats_score(text):
    """Calculates ATS score based on keyword matching and formatting"""
    score = 0
    total_criteria = 5
    matched_keywords = sum(1 for word in KEYWORDS if word in text)
    
    # Keyword Matching Score (40%)
    keyword_score = (matched_keywords / len(KEYWORDS)) * 40

    # Section Matching Score (20%)
    section_score = (sum(1 for section in EXPECTED_SECTIONS if section in text) / len(EXPECTED_SECTIONS)) * 20

    # Formatting Check (20%)
    formatting_penalty = 0
    if len(re.findall(r"\t", text)) > 5:  # Too many tabs (bad formatting)
        formatting_penalty = 10
    formatting_score = max(0, 20 - formatting_penalty)

    # Bullet Points Usage (10%)
    bullet_score = 10 if "-" in text or "•" in text else 0

    # File Type Score (10%)
    file_score = 10 if ".docx" in text else 5  # DOCX preferred over PDF

    # Final ATS Score Calculation
    score = keyword_score + section_score + formatting_score + bullet_score + file_score
    return round(score, 2)  # Rounded to 2 decimal places

@app.route("/", methods=["GET", "POST"])
def index():
    score = None
    if request.method == "POST":
        if "resume" not in request.files:
            return "No file part", 400
        file = request.files["resume"]
        if file.filename == "":
            return "No selected file", 400
        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            text = extract_text(file_path)
            score = calculate_ats_score(text)
    return render_template("index.html", score=score)

if __name__ == "__main__":
    app.run(debug=True)
