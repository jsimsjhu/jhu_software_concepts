import json
import os
from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

# Path to the JSON data file
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "projects.json")

def load_projects():
    """Load project data from JSON file."""
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

@bp.route("/")
def home():
    return render_template("pages/index.html", active="home")

@bp.route("/about")
def about():
    return render_template("pages/about.html", active="about")

@bp.route("/contact")
def contact():
    return render_template("pages/contact.html", active="contact")

@bp.route("/projects")
def projects():
    projects_data = load_projects()
    return render_template("pages/projects.html", projects=projects_data, active="projects")