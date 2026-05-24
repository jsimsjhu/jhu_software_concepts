from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
def home():
    return render_template("pages/index.html")

@bp.route("/about")
def about():
    return render_template("pages/about.html")

@bp.route("/contact")
def contact():
    return render_template("pages/contact.html")

@bp.route("/projects")
def projects():
    return render_template("pages/projects.html")