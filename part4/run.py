from app import create_app
from config import DevelopmentConfig
from extention import db

app = create_app(DevelopmentConfig)
@app.errorhandler(ValueError)
def handle_value_error(error):
    return {"error": str(error)}, 400

if __name__ == '__main__':
    with app.app_context():  # Needed for DB operations
        db.create_all()
    app.run(debug=True)
