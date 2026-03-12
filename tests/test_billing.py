import pytest
import requests
import time

API_URL = "http://localhost:3000"


class TestBillingAPI:
    
    def test_send_order_to_queue(self):
        """Test sending order to billing queue"""
        order_data = {
            "user_id": 123,
            "number_of_items": 2,
            "total_amount": 29.99
        }
        response = requests.post(
            f"{API_URL}/api/billing/",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_send_order_invalid_json(self):
        """Test sending order with invalid JSON"""
        response = requests.post(
            f"{API_URL}/api/billing/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    
    def test_multiple_orders(self):
        """Test sending multiple orders"""
        orders = [
            {"user_id": 1, "number_of_items": 1, "total_amount": 9.99},
            {"user_id": 2, "number_of_items": 3, "total_amount": 39.99},
            {"user_id": 3, "number_of_items": 2, "total_amount": 19.99}
        ]
        
        for order in orders:
            response = requests.post(
                f"{API_URL}/api/billing/",
                json=order,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200
