from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from datetime import datetime
import random
import os

app = Flask(__name__)

app.secret_key = 'wxyz'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=180)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_EMAIL_DOMAINS'] = [
    d.strip().lower() for d in os.environ.get('ADMIN_EMAIL_DOMAINS', '@zeonskills.com').split(',') if d.strip()
]

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False, default=300)  # ⏱ seconds (e.g., 300 = 5 min)
    questions = db.relationship('Question', backref='skill', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")
    user_answers = db.relationship('UserAnswer', backref='question', lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    
class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)

class UserSkillAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # prevent duplicate attempts per skill/user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', name='unique_user_skill_attempt'),
    )

# Category model
class Category(db.Model):
    _tablename_ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)


with app.app_context():
    db.create_all()

# --- AUTH & USER ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['username'] = user.name
            session['email'] = user.email
            session['role'] = user.role
            session['user_id'] = user.id
            session.permanent = True
            flash(f"Welcome back, {user.name}!", "success")
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))

        flash("Invalid email or password", "danger")
        return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        admin_domains = app.config.get('ADMIN_EMAIL_DOMAINS', ['@zeonskills.com'])
        role = 'admin' if any(email.strip().lower().endswith(d) for d in admin_domains) else 'user'
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('registration'))
        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Successfully Registered!", "success")
        return redirect(url_for('login'))
    return render_template("registration.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template("home.html", header=True, footer=True)

@app.route('/popularquiz')
def popularquiz():
    all_skills = Skill.query.all()
    skills_by_category = {}
    for skill in all_skills:
        if skill.category not in skills_by_category:
            skills_by_category[skill.category] = []
        skills_by_category[skill.category].append(skill)
    return render_template("popularquiz.html", skills_by_category=skills_by_category, categories=skills_by_category.keys(), header=True, footer=True)

@app.route('/testqn/<int:skill_id>', methods=['GET'])
def testqn(skill_id):
    if 'username' not in session:
        flash("Please log in to start a quiz.", "warning")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    skill = Skill.query.get_or_404(skill_id)

    # 🚫 Check if user already attempted this skill
    if UserSkillAttempt.query.filter_by(user_id=user_id, skill_id=skill.id).first():
        flash("⚠️ You have already attempted this quiz. Only one attempt is allowed.", "danger")
        return redirect(url_for('viewresult'))

    # Store quiz start time in session
    if session.get('quiz_start_time') is None or session.get('quiz_skill_id') != skill.id:
        session['quiz_start_time'] = datetime.now().isoformat()
        session['quiz_skill_id'] = skill.id

    # Calculate remaining seconds
    start_time = datetime.fromisoformat(session['quiz_start_time'])
    remaining_seconds = max(skill.time_limit - int((datetime.now() - start_time).total_seconds()), 0)

    return render_template(
        "testqn.html",
        skill=skill,
        footer=True,
        remaining_seconds=remaining_seconds
    )

# --- TAKE TEST & SAVE RESULTS ---
@app.route('/test/<int:skill_id>', methods=['POST'])
def test(skill_id):
    if 'username' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    skill = Skill.query.get_or_404(skill_id)

    # 🚫 Block if already attempted
    if UserSkillAttempt.query.filter_by(user_id=user_id, skill_id=skill.id).first():
        flash("⚠️ You have already attempted this quiz. Only one attempt is allowed.", "danger")
        return redirect(url_for('viewresult'))

    start_time_str = session.get('quiz_start_time')
    skill_in_session = session.get('quiz_skill_id')

    if not start_time_str or skill_in_session != skill.id:
        flash("Quiz session invalid or expired.", "danger")
        return redirect(url_for('popularquiz'))

    start_time = datetime.fromisoformat(start_time_str)
    elapsed = (datetime.now() - start_time).total_seconds()
    time_up = elapsed > skill.time_limit

    score = 0
    total = len(skill.questions)
    results = []

    for question in skill.questions:
        ans_id = request.form.get(f'question_{question.id}')
        selected_answer = Answer.query.get(int(ans_id)) if ans_id else None

        if ans_id:
            user_answer = UserAnswer(user_id=user_id, question_id=question.id, answer_id=int(ans_id))
            db.session.add(user_answer)

        correct_answer = next((a for a in question.answers if a.is_correct), None)
        is_correct = selected_answer and selected_answer.is_correct

        if is_correct:
            score += 1

        results.append({
            "question": question.question_text,
            "your_answer": selected_answer.answer_text if selected_answer else "Not answered",
            "correct_answer": correct_answer.answer_text if correct_answer else "N/A",
            "is_correct": is_correct
        })

    # ✅ Mark that user attempted this skill
    attempt = UserSkillAttempt(user_id=user_id, skill_id=skill.id)
    db.session.add(attempt)

    db.session.commit()
    session.pop('quiz_start_time', None)
    session.pop('quiz_skill_id', None)

    if time_up:
        flash("⏰ Time up! Your quiz was submitted automatically.", "danger")

    return render_template(
        "testresult.html",
        skill=skill,
        score=score,
        total=total,
        results=results,
        footer=True
    )

@app.route('/quizview')
def quizview():
    return render_template("quizview.html", footer=True)

# --- VIEW RESULT FOR SPECIFIC SKILL (BY QUERY PARAM) ---
@app.route('/testresult')
def testresult():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    skill_id = request.args.get('skill_id', type=int)

    if not skill_id:
        flash("No skill selected for result.", "warning")
        return redirect(url_for('viewresult'))

    skill = Skill.query.get_or_404(skill_id)

    user_answers = (
        UserAnswer.query.filter_by(user_id=user_id)
        .join(Question)
        .filter(Question.skill_id == skill.id)
        .all()
    )

    if not user_answers:
        flash("No result found for this skill.", "info")
        return redirect(url_for('viewresult'))

    total = len(skill.questions)
    score = 0
    results = []

    for question in skill.questions:
        ua = next((ua for ua in user_answers if ua.question_id == question.id), None)
        selected_answer = Answer.query.get(ua.answer_id) if ua else None
        correct_answer = next((a for a in question.answers if a.is_correct), None)
        is_correct = selected_answer and selected_answer.is_correct

        if is_correct:
            score += 1

        results.append({
            "question": question.question_text,
            "your_answer": selected_answer.answer_text if selected_answer else "Not answered",
            "correct_answer": correct_answer.answer_text if correct_answer else "N/A",
            "is_correct": is_correct
        })

    return render_template("testresult.html", skill=skill, score=score, total=total, results=results, footer=True)

# --- VIEW ALL RESULTS (USER DASHBOARD) ---
@app.route('/viewresult')
def viewresult():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    skills = db.session.query(Skill).join(Question).join(UserAnswer).filter(UserAnswer.user_id == user_id).all()

    user_results = []
    for skill in skills:
        answers = UserAnswer.query.filter_by(user_id=user_id).join(Question).filter(Question.skill_id == skill.id).all()
        total = len(skill.questions)
        correct = 0
        for ua in answers:
            ans = Answer.query.get(ua.answer_id)
            if ans and ans.is_correct:
                correct += 1
        status = "Passed" if correct >= total/2 else "Failed"
        user_results.append({
            "skill": skill,
            "score": correct,
            "total": total,
            "status": status
        })

    return render_template("viewresult.html", results=user_results, footer=True)


# --- ADMIN ROUTES ---
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    # Get total counts from the database
    total_categories = db.session.query(Category).count()
    total_skills = db.session.query(Skill).count()
    total_users = db.session.query(User).count()
    
    # Get total attempted skills (distinct skills with at least one user answer)
    attempted_skills_count = db.session.query(db.func.count(db.func.distinct(Question.skill_id))).join(UserAnswer).scalar()

    # Get recent skills opened by the admin from the session
    recent_skills_data = session.get('recent_admin_skills', [])

    # Pass the dynamic data to the template
    return render_template(
        "admin_dashboard.html",
        username=session.get('username'),
        total_categories=total_categories,
        total_skills=total_skills,
        total_users=total_users,
        attempted_skills=attempted_skills_count,
        recent_skills_data=recent_skills_data,
        footer=True,
        sidebar=True,
        header=True,
        current_year=datetime.now().year
    )


@app.route('/admin_createskill', methods=['GET', 'POST'])
def admin_createskill():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        skill_name = request.form.get('skill_name')
        description = request.form.get('description')
        category = request.form.get('category')
        level = request.form.get('level')
        new_skill = Skill(name=skill_name, description=description, category=category, level=level)
        db.session.add(new_skill)
        db.session.flush()
        question_index = 0
        while f"questions[{question_index}][text]" in request.form:
            q_text = request.form.get(f"questions[{question_index}][text]")
            correct_idx = request.form.get(f"questions[{question_index}][correct_answer]")
            if not q_text:
                question_index += 1
                continue
            new_question = Question(question_text=q_text, skill=new_skill)
            db.session.add(new_question)
            db.session.flush()
            answers = request.form.getlist(f"questions[{question_index}][answers][]")
            for i, ans_text in enumerate(answers):
                if not ans_text.strip():
                    continue
                is_correct = (str(i) == correct_idx)
                new_answer = Answer(answer_text=ans_text.strip(), is_correct=is_correct, question=new_question)
                db.session.add(new_answer)
            question_index += 1
        db.session.commit()
        flash('New skill with questions added successfully!', 'success')
        return redirect(url_for('admin_allskill'))
    return render_template("admin_createskill.html", footer=True, sidebar=True, header=True)

@app.route('/admin_allskill')
def admin_allskill():
    all_skills = Skill.query.all()
    return render_template("admin_allskill.html", skills=all_skills, footer=True, sidebar=True, header=True)

@app.route('/admin_deleteskill/<int:skill_id>', methods=['POST'])
def admin_deleteskill(skill_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    skill_to_delete = Skill.query.get_or_404(skill_id)
    db.session.delete(skill_to_delete)
    db.session.commit()
    flash(f'Skill "{skill_to_delete.name}" has been deleted.', 'success')
    return redirect(url_for('admin_allskill'))

@app.route("/add_category", methods=["POST"])
def add_category():
    data = request.get_json()
    category_name = data.get("name")
    if category_name:
        new_category = Category(name=category_name)
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/admin_categories')
def admin_categories():
    categories = Category.query.all()
    return render_template(
        "admin_categories.html",
        categories=categories,
        footer=True,
        sidebar=True,
        header=True
    )

# --- UPDATED EDIT SKILL ROUTE (LOGS SKILL TO SESSION) ---
@app.route('/admin_editskill/<int:skill_id>', methods=['GET', 'POST'])
def admin_editskill(skill_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    skill = Skill.query.get_or_404(skill_id)

    # Logic to log the recently opened skill in the session
    if 'recent_admin_skills' not in session:
        session['recent_admin_skills'] = []
    
    recent_skills = session['recent_admin_skills']
    
    # Create a dictionary for the current skill
    current_skill_data = {
        'id': skill.id,
        'name': skill.name,
        'category': skill.category
    }

    # Remove the skill if it's already in the list to move it to the front
    recent_skills = [s for s in recent_skills if s['id'] != skill.id]
    
    # Add the current skill to the beginning of the list
    recent_skills.insert(0, current_skill_data)
    
    # Keep the list size to a reasonable limit (e.g., 5)
    session['recent_admin_skills'] = recent_skills[:5]
    
    if request.method == 'POST':
        skill.name = request.form.get('skill_name')
        skill.description = request.form.get('description')
        skill.category = request.form.get('category')
        skill.level = request.form.get('level')
        db.session.commit()
        flash('Skill details updated successfully!', 'success')
        return redirect(url_for('admin_editskill', skill_id=skill.id))
    return render_template("admin_editskill.html", skill=skill, footer=True, sidebar=True, header=True)

# --- NEW ROUTE TO ADD A QUESTION ---
@app.route('/admin_add_question/<int:skill_id>', methods=['POST'])
def admin_add_question(skill_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    skill = Skill.query.get_or_404(skill_id)
    q_text = request.form.get('new_question_text')
    answers = request.form.getlist('new_answers[]')
    correct_answer_index = request.form.get('new_correct_answer')

    if q_text and len(answers) == 4 and correct_answer_index is not None:
        new_question = Question(question_text=q_text, skill=skill)
        db.session.add(new_question)
        db.session.flush() # Flush to get the new_question.id
        for i, ans_text in enumerate(answers):
            is_correct = (str(i) == correct_answer_index)
            new_answer = Answer(answer_text=ans_text, is_correct=is_correct, question_id=new_question.id)
            db.session.add(new_answer)
        db.session.commit()
        flash('New question added successfully!', 'success')
    else:
        flash('Failed to add new question. Please fill out all fields.', 'danger')
    return redirect(url_for('admin_editskill', skill_id=skill.id))

# --- NEW ROUTE TO UPDATE A QUESTION ---
@app.route('/admin_update_question/<int:question_id>', methods=['POST'])
def admin_update_question(question_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    question = Question.query.get_or_404(question_id)
    question.question_text = request.form.get('question_text')
    
    correct_answer_id = request.form.get('correct_answer')

    for answer in question.answers:
        answer.answer_text = request.form.get(f'answer_text_{answer.id}')
        answer.is_correct = (str(answer.id) == correct_answer_id)
    
    db.session.commit()
    flash(f'Question "{question.question_text[:30]}..." updated!', 'success')
    return redirect(url_for('admin_editskill', skill_id=question.skill_id))

# --- NEW ROUTE TO DELETE A QUESTION ---
@app.route('/admin_delete_question/<int:question_id>', methods=['POST'])
def admin_delete_question(question_id):
    if session.get('role') != 'admin':
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)
    skill_id = question.skill_id
    
    db.session.delete(question)
    db.session.commit()

    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_editskill', skill_id=skill_id))


@app.route('/admin_skillresults')
def admin_skillresults():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    results = []
    skills = Skill.query.all()
    for skill in skills:
        user_ids = db.session.query(UserAnswer.user_id).join(Question).filter(
            Question.skill_id == skill.id
        ).distinct().all()

        for (user_id,) in user_ids:
            user = User.query.get(user_id)
            total = len(skill.questions)
            score = 0
            for q in skill.questions:
                correct_answer = next((a for a in q.answers if a.is_correct), None)
                if correct_answer:
                    attempted = UserAnswer.query.filter_by(
                        user_id=user_id, question_id=q.id, answer_id=correct_answer.id
                    ).first()
                    if attempted:
                        score += 1
            percentage = (score / total * 100) if total > 0 else 0
            results.append({
                "user": user,
                "skill": skill,
                "score": score,
                "total": total,
                "percentage": percentage
            })

    return render_template("admin_skillresults.html", results=results, footer=True, sidebar=True, header=True)

@app.route('/admin_viewresults')
def admin_viewresults():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    user_id = request.args.get("user_id")
    skill_id = request.args.get("skill_id")

    user = User.query.get_or_404(user_id)
    skill = Skill.query.get_or_404(skill_id)

    detailed_results = []
    for q in skill.questions:
        user_answer = UserAnswer.query.filter_by(user_id=user.id, question_id=q.id).first()
        correct_answer = next((a for a in q.answers if a.is_correct), None)

        detailed_results.append({
            "question": q,
            "user_answer": Answer.query.get(user_answer.answer_id) if user_answer else None,
            "correct_answer": correct_answer
        })

    return render_template(
        "admin_viewresults.html",
        user=user,
        skill=skill,
        detailed_results=detailed_results,
        now=datetime.now(),
        footer=True,
        sidebar=True,
        header=True
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)