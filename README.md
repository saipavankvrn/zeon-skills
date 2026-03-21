# Veda-X 

Veda-X (formerly Zeon Skill) is a robust **Skill Assessment and Learning Management System (LMS)** built with Python and Flask. This platform allows administrators to create interactive, timed multiple-choice quizzes, while users can take those tests to evaluate their knowledge across various subjects.

---

## 🚀 Key Features

### For Students / Candidates
* **Browse Quizzes:** Explore a library of available skills and topics categorized by domain (e.g., Programming, Marketing).
* **Timed Testing Environment:** Test your knowledge against a live countdown timer.
* **Instant Auto-Grading:** See your results instantly upon submitting the quiz or when the timer expires.
* **Detailed Results Review:** View your final score and review which questions you got right or wrong.

### For Administrators / Instructors
* **Admin Dashboard:** Access a centralized control panel to monitor platform statistics, total test attempts, and total registered users.
* **Content Management:** Create, Read, Update, and Delete categories and customized skill quizzes.
* **Question Editor:** Add and edit customized multiple-choice questions for any quiz.
* **User Analytics:** Track student progress. Drill down into specific user attempts to see exactly which questions a user struggled with. *(Accounts registered with `@veda-x.com` automatically gain Admin rights).*

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask Framework
* **Database:** SQLite managed via Flask-SQLAlchemy (ORM)
* **Frontend:** HTML, CSS, JavaScript (Jinja2 Templating)

---

## 💻 Running the Project Locally

### Prerequisites
* Python 3.8+ installed
* Pip (Python package manager)

### Installation Steps

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/saipavankvrn/Veda-X.git
   cd Veda-X
   ```

2. **Set up a Virtual Environment**:
   * **Windows:**
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **macOS/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   *(You may need to manually install standard Flask dependencies if a `requirements.txt` is not present).*
   ```bash
   pip install flask flask_sqlalchemy
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   *The SQLite database (`users.db`) will be created automatically in the `instance` folder when the app runs for the first time.*

5. **Access the Platform**:
   Open your browser and navigate to: `http://127.0.0.1:5000/`

---

## 📄 License & Rights
© 2025 Veda-X. All Rights Reserved.
