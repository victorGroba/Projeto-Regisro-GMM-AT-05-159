from app import create_app
from flask_talisman import Talisman

app = create_app()
Talisman(app, content_security_policy=None) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)

