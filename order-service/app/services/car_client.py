"""HTTP client for car-service communication"""
import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class CarServiceClient:
    """Client for interacting with car-service"""

    def __init__(self):
        self.base_url = settings.CAR_SERVICE_URL
        self.timeout = 10.0

    async def verify_car_exists(self, car_id: str) -> bool:
        """
        Verify that a car exists in car-service

        Args:
            car_id: UUID of the car to verify

        Returns:
            True if car exists (200 response), False otherwise
        """
        url = f"{self.base_url}/api/cars/{car_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Verifying car existence: {url}")
                response = await client.get(url)

                if response.status_code == 200:
                    logger.info(f"Car {car_id} exists")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"Car {car_id} not found")
                    return False
                else:
                    logger.error(f"Unexpected status code {response.status_code} from car-service")
                    return False

        except httpx.TimeoutException:
            logger.error(f"Timeout while connecting to car-service: {url}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Error connecting to car-service: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while verifying car: {e}")
            return False

    async def get_car_details(self, car_id: str) -> Optional[dict]:
        """
        Get detailed information about a car

        Args:
            car_id: UUID of the car

        Returns:
            Car details as dict if found, None otherwise
        """
        url = f"{self.base_url}/api/cars/{car_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Fetching car details: {url}")
                response = await client.get(url)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to fetch car details: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching car details: {e}")
            return None


# Singleton instance
car_client = CarServiceClient()
