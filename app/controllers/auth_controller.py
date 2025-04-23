from flask import Blueprint, request, render_template, redirect, url_for, session
from app.services.auth_service import check_login, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        next_page, error = check_login(username, password)

        if error:
            return render_template("login.html", error=error)
        else:
            return redirect(next_page or url_for("auth.home"))
        
    return render_template("login.html")

@auth_bp.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("auth.login"))

@auth_bp.route('/')
@login_required
def home():
    return render_template("index.html") 