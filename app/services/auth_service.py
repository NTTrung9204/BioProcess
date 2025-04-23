from functools import wraps
import hashlib
from flask import redirect, request, session, url_for
from app.config import UserConfig
from app.services.hash_service import hash256

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_login(username, password):
    error, next_page = None, None

    name = username

    username, password = hash256(username), hash256(password)
    
    if username in UserConfig.UserDBInstance and UserConfig.UserDBInstance[username] == password:
        session['username'] = name
        session.permanent = True

        next_page = request.args.get('next')
    else:
        error = "Login failure!"

    return next_page, error 