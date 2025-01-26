from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# Models
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    motorcycles = db.relationship('Motorcycle', backref='branch', lazy=True)

class Motorcycle(db.Model):
    __tablename__ = 'motorcycles'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))

# Routes
@app.route('/branches', methods=['GET'])
def get_branches():
    branches = Branch.query.all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'brand': b.brand
    } for b in branches])

@app.route('/motorcycles', methods=['GET'])
def get_motorcycles():
    motorcycles = Motorcycle.query.all()
    return jsonify([{
        'id': m.id,
        'brand': m.brand,
        'model': m.model,
        'year': m.year,
        'branch': m.branch.name
    } for m in motorcycles])

@app.route('/motorcycles/<int:branch_id>', methods=['GET'])
def get_branch_motorcycles(branch_id):
    motorcycles = Motorcycle.query.filter_by(branch_id=branch_id).all()
    return jsonify([{
        'id': m.id,
        'brand': m.brand,
        'model': m.model,
        'year': m.year
    } for m in motorcycles])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4200)
