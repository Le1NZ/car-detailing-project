"""Unit tests for CarServiceClient"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
import httpx

from app.services.car_client import CarServiceClient


class TestCarServiceClientVerifyCarExists:
    """Tests for verify_car_exists method"""

    @pytest.mark.asyncio
    async def test_verify_car_exists_success(self, test_car_id):
        """Test successful car verification when car exists"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is True
            mock_client.get.assert_called_once_with(
                f"{client.base_url}/api/cars/{test_car_id}"
            )

    @pytest.mark.asyncio
    async def test_verify_car_exists_not_found(self, test_car_id):
        """Test car verification when car does not exist (404)"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_server_error(self, test_car_id):
        """Test car verification when car-service returns 500"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_timeout(self, test_car_id):
        """Test car verification handles timeout gracefully"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_connection_error(self, test_car_id):
        """Test car verification handles connection errors"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_generic_request_error(self, test_car_id):
        """Test car verification handles generic request errors"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_unexpected_exception(self, test_car_id):
        """Test car verification handles unexpected exceptions"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.verify_car_exists(str(test_car_id))

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_car_exists_uses_correct_url(self, test_car_id):
        """Test that verify_car_exists constructs correct URL"""
        client = CarServiceClient()
        client.base_url = "http://test-car-service:8002"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await client.verify_car_exists(str(test_car_id))

            expected_url = f"http://test-car-service:8002/api/cars/{test_car_id}"
            mock_client.get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    async def test_verify_car_exists_uses_correct_timeout(self, test_car_id):
        """Test that verify_car_exists uses configured timeout"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await client.verify_car_exists(str(test_car_id))

            # Verify timeout was passed to AsyncClient
            mock_client_class.assert_called_once_with(timeout=client.timeout)


class TestCarServiceClientGetCarDetails:
    """Tests for get_car_details method"""

    @pytest.mark.asyncio
    async def test_get_car_details_success(self, test_car_id):
        """Test successful retrieval of car details"""
        client = CarServiceClient()
        expected_data = {
            "car_id": str(test_car_id),
            "make": "Toyota",
            "model": "Camry",
            "year": 2020
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.get_car_details(str(test_car_id))

            assert result == expected_data
            mock_client.get.assert_called_once_with(
                f"{client.base_url}/api/cars/{test_car_id}"
            )

    @pytest.mark.asyncio
    async def test_get_car_details_not_found(self, test_car_id):
        """Test get_car_details returns None when car not found"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.get_car_details(str(test_car_id))

            assert result is None

    @pytest.mark.asyncio
    async def test_get_car_details_server_error(self, test_car_id):
        """Test get_car_details returns None on server error"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.get_car_details(str(test_car_id))

            assert result is None

    @pytest.mark.asyncio
    async def test_get_car_details_exception(self, test_car_id):
        """Test get_car_details handles exceptions gracefully"""
        client = CarServiceClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=Exception("Network error")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.get_car_details(str(test_car_id))

            assert result is None


class TestCarServiceClientConfiguration:
    """Tests for CarServiceClient configuration"""

    def test_client_initialization(self):
        """Test CarServiceClient initializes with correct defaults"""
        client = CarServiceClient()

        assert client.base_url is not None
        assert client.timeout == 10.0

    def test_client_uses_settings_url(self):
        """Test CarServiceClient uses URL from settings"""
        from app.config import settings

        client = CarServiceClient()

        assert client.base_url == settings.CAR_SERVICE_URL
