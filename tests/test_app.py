import unittest
from unittest.mock import patch, MagicMock
from api.app import app, db, Branch, Motorcycle, Client
import json
from datetime import datetime

class TestMotorcycleAPI(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_get_branches_empty(self):
        response = self.client.get('/branches')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

    def test_get_branches_with_data(self):
        with app.app_context():
            branch = Branch(
                name='Test Branch',
                brand='HONDA',  # Changed to a valid enum value
                street='Test Street',
                number='123',
                district='Test District',
                city='Test City',
                state='Test State'
            )
            db.session.add(branch)
            db.session.commit()

            response = self.client.get('/branches')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'Test Branch')

    @patch('api.app.get_coordinates')
    @patch('api.app.calculate_distance')
    def test_create_client(self, mock_calculate_distance, mock_get_coordinates):
        # Mock coordinate responses
        mock_get_coordinates.return_value = (19.4326, -99.1332)
        mock_calculate_distance.return_value = 5.0

        # Create test branch with valid brand
        with app.app_context():
            branch = Branch(
                name='Test Branch',
                brand='HONDA',  # Changed to a valid enum value
                street='Test Street',
                number='123',
                district='Test District',
                city='Test City',
                state='Test State'
            )
            db.session.add(branch)
            db.session.commit()

            # Test client creation
            client_data = {
                'first_name': 'John',
                'last_name_1': 'Doe',
                'last_name_2': 'Smith',
                'email': 'john@example.com',
                'phone': '1234567890',
                'birth_date': '1990-01-01',
                'street': 'Client Street',
                'number': '456',
                'district': 'Client District',
                'city': 'Client City',
                'state': 'Client State'
            }

            response = self.client.post('/client',
                                      json=client_data,
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('client_id', data)
            self.assertIn('nearest_branch', data)

    def test_get_motorcycles(self):
        with app.app_context():
            # Create test branch with valid brand
            branch = Branch(
                name='Test Branch',
                brand='HONDA',  # Changed to a valid enum value
                street='Test Street',
                number='123',
                district='Test District',
                city='Test City',
                state='Test State'
            )
            db.session.add(branch)
            db.session.commit()

            # Create test motorcycle with valid brand
            motorcycle = Motorcycle(
                brand='HONDA',  # Changed to a valid enum value
                model='Test Model',
                year=2023,
                branch_id=branch.id
            )
            db.session.add(motorcycle)
            db.session.commit()

            response = self.client.get('/motorcycles')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['brand'], 'HONDA')
            self.assertEqual(data[0]['model'], 'Test Model')

if __name__ == '__main__':
    unittest.main()