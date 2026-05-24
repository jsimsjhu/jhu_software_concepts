from board import pages
from board import create_app

app = create_app()
print(app.url_map)