#! /usr/bin/env python

from flask import Flask, request, jsonify
from models.user import User
from database import db
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from dotenv import load_dotenv
from os import environ

load_dotenv()
DATA_BASE_CONNECTION_STRING = environ.get("DATA_BASE_CONNECTION_STRING")

assert DATA_BASE_CONNECTION_STRING is not None, "Verifique seu `.env`!"

print(f"{DATA_BASE_CONNECTION_STRING=}")

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = DATA_BASE_CONNECTION_STRING

print(f"{app.config.get('SQLALCHEMY_DATABASE_URI')=}")

login_manager = LoginManager()

db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

@app.route("/user", methods=["POST"])
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Credenciais inválidas"}), 400
    
    existent_user = User.query.filter_by(username=username).first()

    if existent_user:
        return jsonify({"message": "Usuário já existe"}), 422

    new_user = User(username=username, password=password, role="user")
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Usuário criado com sucesso",
        "user": {
            "id": new_user.id,
            "username": new_user.username
        }
    }), 201

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Credenciais inválidas"}), 400
    
    user = User.query.filter_by(username=username).first()

    if not user or not user.password == password:
        return jsonify({"message": "Credenciais inválidas"}), 400
    
    login_user(user)
    return jsonify({"message": "Autenticação realizada com sucesso"})

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout realizado com sucesso"})

@app.route("/user/<int:user_id>", methods=["GET"])
@login_required
def read_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    return jsonify({"id": user.id, "username": user.username})

@app.route("/user/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({"message": "Operação não permitida."}), 403
    
    data = request.json
    password = data.get("password")

    if not password:
        return jsonify({"message": "Credenciais inválidas"}), 422
    
    user.password = password
    db.session.commit()

    return jsonify({
        "message": "Usuário atualizado com sucesso",
        "user": {
            "id": user.id,
            "username": user.username
        }
    })

@app.route("/user/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({"message": "Operação não permitida"}), 403

    if user_id == current_user.id:
        return jsonify({"message": "O usuário logado não pode ser deletado"})

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"Usuário {user_id} deletado com sucesso."})

@app.route("/", methods=["GET"])
def hello_world():
    return jsonify({"hello": "word"})

if __name__ == "__main__":
    app.run(debug=True)
