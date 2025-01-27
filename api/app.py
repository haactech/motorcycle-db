from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# Models
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    street  = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    motorcycles = db.relationship('Motorcycle', backref='branch', lazy=True)

    @property
    def full_address(self):
        return f"{self.street} {self.number}, {self.district}, {self.city}, {self.state}"

class Motorcycle(db.Model):
    __tablename__ = 'motorcycles'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True )
    first_name = db.Column(db.String(100), nullable=False)
    last_name_1 = db.Column(db.String(100), nullable=False)
    last_name_2 = db.Column(db.String(100))
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    street = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    interests = db.relationship('Motorcycle', secondary='client_interests')

    @property
    def full_address(self):
        return f"{self.street} {self.number}, {self.district}, {self.city}, {self.state}"


client_interests = db.Table('client_interests',
    db.Column('client_id', db.Integer, db.ForeignKey('clients.id'), primary_key=True),
    db.Column('motorcycle_id', db.Integer, db.ForeignKey('motorcycles.id'), primary_key=True)
)

def get_coordinates(address):
    "Get coordinates using OpenStreetMap Nominatim API"
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format":"json",
            "limit":1
        }
        headers = {
            "User-Agent":"MotorcycleShopApp/1.0"
        }

        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()

        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None 
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2 

    lat1, lon1 = coord1
    lat2, lon2 = coord2 

    R = 6371

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1 

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R*c

    return distance

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

@app.route('/client', methods=['POST'])
def create_client():
    data = request.json
    try:
        client = Client(
            first_name=data['first_name'],
            last_name_1=data['last_name_1'],
            last_name_2=data.get('last_name_2'),
            email=data['email'],
            phone=data['phone'],
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
            street=data['street'],
            number=data['number'],
            district=data['district'],
            city=data['city'],
            state=data['state']
        )

        if 'motorcycle_ids' in data:
            motorcycles = Motorcycle.query.filter(Motorcycle.id.in_(data['motorcycle_ids'])).all()
            client.interests.extend(motorcycles)

        db.session.add(client)
        db.session.commit()

        #Find nereast branch
        client_coords = get_coordinates(client.full_address)
        if client_coords:
            branches = Branch.query.all()
            nearest_branch = None
            min_distance = float('inf')

            for branch in branches:
                branch_coords = get_coordinates(branch.full_address)
                if branch_coords:
                    distance = calculate_distance(client_coords,branch_coords)
                    if(distance < min_distance):
                        min_distance = distance
                        nearest_branch = branch
            
            if nearest_branch:
                return jsonify({
                    'message': 'Client created successfully',
                    'client_id': client.id,
                    'nearest_branch': {
                        'id': nearest_branch.id,
                        'name': nearest_branch.name,
                        'address': nearest_branch.full_address,
                        'distance_km': round(min_distance, 2)
                    }
                })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 
    
@app.route('/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': c.id,
        'first_name': c.first_name,
        'last_name_1': c.last_name_1,
        'last_name_2': c.last_name_2,
        'email': c.email,
        'interests': [{
            'id': m.id,
            'brand': m.brand,
            'model': m.model
        } for m in c.interests]
    } for c in clients])

@app.route('health',methods=['GET'])
def health():
    return jsonify({'helath':'it´s working'}), 200

@app.route('/recommend-branch', methods=['POST'])
def recommend_branch():
    data = request.json
    try:
        # Obtener las coordenadas del domicilio del cliente
        client_address = f"{data['street']} {data['number']}, {data['district']}, {data['city']}, {data['state']}"
        client_coords = get_coordinates(client_address)

        if not client_coords:
            return jsonify({'error': 'No se pudieron obtener las coordenadas del domicilio'}), 400

        # Obtener todas las sucursales
        branches = Branch.query.all()
        nearest_branch = None
        min_distance = float('inf')

        # Calcular la sucursal más cercana
        for branch in branches:
            branch_coords = get_coordinates(branch.full_address)
            if branch_coords:
                distance = calculate_distance(client_coords, branch_coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_branch = {
                        'branch':branch,
                        'lat': branch_coords[0],
                        'lng': branch_coords[1]
                    }

        if nearest_branch:
            return jsonify({
                'nearest_branch': {
                    'id': nearest_branch["branch"].id,
                    'name': nearest_branch["branch"].name,
                    'address': nearest_branch["branch"].full_address,
                    'distance_km': round(min_distance, 2),
                    'location': {
                        'lat': nearest_branch['lat'],
                        'lng': nearest_branch['lng']
                    }
                }
            })
        else:
            return jsonify({'error': 'No se encontró una sucursal cercana'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4200)
