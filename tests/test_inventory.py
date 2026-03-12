import pytest
import requests
import json

API_URL = "http://localhost:3000"


class TestInventoryAPI:
    
    def test_get_movies_empty(self):
        """Test getting movies when database is empty"""
        response = requests.get(f"{API_URL}/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert "movies" in data
    
    def test_create_movie(self):
        """Test creating a new movie"""
        movie_data = {
            "title": "Test Movie",
            "description": "A test movie description"
        }
        response = requests.post(
            f"{API_URL}/api/movies",
            json=movie_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_movies_with_data(self):
        """Test getting movies after creating one"""
        response = requests.get(f"{API_URL}/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert "movies" in data
        assert len(data["movies"]) > 0
    
    def test_search_movies_by_title(self):
        """Test searching movies by title"""
        response = requests.get(f"{API_URL}/api/movies?title=Test")
        assert response.status_code == 200
        data = response.json()
        assert "movies" in data
    
    def test_create_movie_invalid_json(self):
        """Test creating movie with invalid JSON"""
        response = requests.post(
            f"{API_URL}/api/movies",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
