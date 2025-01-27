from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# Configuración de Swagger
api = Api(
    app,
    version='1.0',
    title='Motorcycle Shop API',
    description='API para gestión de clientes y motocicletas',
    doc='/docs'
)

# Namespaces
ns_branches = api.namespace('branches', description='Operaciones con sucursales')
ns_motorcycles = api.namespace('motorcycles', description='Operaciones con motocicletas')
ns_clients = api.namespace('clients', description='Operaciones con clientes')
ns_recommend = api.namespace('recommend', description='Recomendaciones de sucursales')

# Models de Base de Datos (los mismos que ya tenías)
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    street = db.Column(db.String(100), nullable=False)
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
    id = db.Column(db.Integer, primary_key=True)
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

# Modelos Swagger
branch_model = api.model('Branch', {
    'id': fields.Integer(readonly=True, description='ID único de la sucursal'),
    'name': fields.String(required=True, description='Nombre de la sucursal'),
    'brand': fields.String(required=True, description='Marca (KTM o YAMAHA)'),
    'address': fields.String(readonly=True, description='Dirección completa')
})

motorcycle_model = api.model('Motorcycle', {
    'id': fields.Integer(readonly=True, description='ID único de la motocicleta'),
    'brand': fields.String(required=True, description='Marca de la motocicleta'),
    'model': fields.String(required=True, description='Modelo de la motocicleta'),
    'year': fields.Integer(required=True, description='Año del modelo'),
    'branch': fields.String(description='Nombre de la sucursal')
})

client_input_model = api.model('ClientInput', {
    'first_name': fields.String(required=True, description='Nombre'),
    'last_name_1': fields.String(required=True, description='Primer apellido'),
    'last_name_2': fields.String(description='Segundo apellido'),
    'email': fields.String(required=True, description='Correo electrónico'),
    'phone': fields.String(required=True, description='Teléfono'),
    'birth_date': fields.Date(required=True, description='Fecha de nacimiento'),
    'street': fields.String(required=True, description='Calle'),
    'number': fields.String(required=True, description='Número'),
    'district': fields.String(required=True, description='Colonia'),
    'city': fields.String(required=True, description='Ciudad'),
    'state': fields.String(required=True, description='Estado'),
    'motorcycle_ids': fields.List(fields.Integer, description='IDs de motocicletas de interés')
})

address_input_model = api.model('AddressInput', {
    'street': fields.String(required=True, description='Calle'),
    'number': fields.String(required=True, description='Número'),
    'district': fields.String(required=True, description='Colonia'),
    'city': fields.String(required=True, description='Ciudad'),
    'state': fields.String(required=True, description='Estado')
})

# Funciones auxiliares (las mismas que ya tenías)
def get_coordinates(address):
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "MotorcycleShopApp/1.0"
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
    from math import radians, sin, cos, sqrt, atan2
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    R = 6371
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

# Endpoints
@ns_branches.route('/')
class BranchList(Resource):
    @ns_branches.doc('list_branches')
    @ns_branches.marshal_list_with(branch_model)
    def get(self):
        """Lista todas las sucursales"""
        branches = Branch.query.all()
        return [{
            'id': b.id,
            'name': b.name,
            'brand': b.brand,
            'address': b.full_address
        } for b in branches]

@ns_motorcycles.route('/')
class MotorcycleList(Resource):
    @ns_motorcycles.doc('list_motorcycles')
    @ns_motorcycles.marshal_list_with(motorcycle_model)
    def get(self):
        """Lista todas las motocicletas"""
        motorcycles = Motorcycle.query.all()
        return [{
            'id': m.id,
            'brand': m.brand,
            'model': m.model,
            'year': m.year,
            'branch': m.branch.name
        } for m in motorcycles]

@ns_motorcycles.route('/<int:branch_id>')
class BranchMotorcycles(Resource):
    @ns_motorcycles.doc('get_branch_motorcycles')
    @ns_motorcycles.marshal_list_with(motorcycle_model)
    def get(self, branch_id):
        """Lista las motocicletas de una sucursal específica"""
        motorcycles = Motorcycle.query.filter_by(branch_id=branch_id).all()
        return [{
            'id': m.id,
            'brand': m.brand,
            'model': m.model,
            'year': m.year
        } for m in motorcycles]

@ns_clients.route('/')
class ClientAPI(Resource):
    @ns_clients.doc('create_client')
    @ns_clients.expect(client_input_model)
    def post(self):
        """Crea un nuevo cliente"""
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

            client_coords = get_coordinates(client.full_address)
            if client_coords:
                branches = Branch.query.all()
                nearest_branch = None
                min_distance = float('inf')

                for branch in branches:
                    branch_coords = get_coordinates(branch.full_address)
                    if branch_coords:
                        distance = calculate_distance(client_coords, branch_coords)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_branch = branch

                if nearest_branch:
                    return {
                        'message': 'Client created successfully',
                        'client_id': client.id,
                        'nearest_branch': {
                            'id': nearest_branch.id,
                            'name': nearest_branch.name,
                            'address': nearest_branch.full_address,
                            'distance_km': round(min_distance, 2)
                        }
                    }

        except Exception as e:
            db.session.rollback()
            api.abort(400, str(e))

@ns_recommend.route('/branch')
class RecommendBranch(Resource):
    @ns_recommend.doc('recommend_branch')
    @ns_recommend.expect(address_input_model)
    def post(self):
        """Recomienda la sucursal más cercana basada en una dirección"""
        data = request.json
        try:
            client_address = f"{data['street']} {data['number']}, {data['district']}, {data['city']}, {data['state']}"
            client_coords = get_coordinates(client_address)

            if not client_coords:
                api.abort(400, 'No se pudieron obtener las coordenadas del domicilio')

            branches = Branch.query.all()
            nearest_branch = None
            min_distance = float('inf')

            for branch in branches:
                branch_coords = get_coordinates(branch.full_address)
                if branch_coords:
                    distance = calculate_distance(client_coords, branch_coords)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_branch = {
                            'branch': branch,
                            'lat': branch_coords[0],
                            'lng': branch_coords[1]
                        }

            if nearest_branch:
                return {
                    'nearest_branch': {
                        'id': nearest_branch['branch'].id,
                        'name': nearest_branch['branch'].name,
                        'address': nearest_branch['branch'].full_address,
                        'distance_km': round(min_distance, 2),
                        'location': {
                            'lat': nearest_branch['lat'],
                            'lng': nearest_branch['lng']
                        }
                    }
                }
            else:
                api.abort(404, 'No se encontró una sucursal cercana')

        except Exception as e:
            api.abort(400, str(e))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4200)