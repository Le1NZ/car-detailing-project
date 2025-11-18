"""In-memory repository for car data storage."""

from uuid import UUID, uuid4
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class LocalCarRepository:
    """In-memory storage for cars and documents."""

    def __init__(self):
        """Initialize empty storage lists."""
        self.cars: List[Dict] = []
        self.documents: List[Dict] = []
        logger.info("LocalCarRepository initialized with in-memory storage")

    def add_car(self, car_data: Dict) -> Dict:
        """
        Add a new car to storage.

        Args:
            car_data: Dictionary with car information

        Returns:
            Dictionary with car data including generated car_id

        Raises:
            ValueError: If VIN or license_plate already exists
        """
        # Check for duplicate VIN
        if any(car['vin'] == car_data['vin'] for car in self.cars):
            logger.warning(f"Attempt to add car with duplicate VIN: {car_data['vin']}")
            raise ValueError(f"Car with VIN {car_data['vin']} already exists")

        # Check for duplicate license plate
        if any(car['license_plate'] == car_data['license_plate'] for car in self.cars):
            logger.warning(f"Attempt to add car with duplicate license plate: {car_data['license_plate']}")
            raise ValueError(f"Car with license plate {car_data['license_plate']} already exists")

        # Generate new car ID
        car_id = uuid4()
        car = {
            'car_id': car_id,
            'owner_id': car_data['owner_id'],
            'license_plate': car_data['license_plate'],
            'vin': car_data['vin'],
            'make': car_data['make'],
            'model': car_data['model'],
            'year': car_data['year']
        }

        self.cars.append(car)
        logger.info(f"Car added successfully: car_id={car_id}, VIN={car_data['vin']}")
        return car

    def get_car_by_id(self, car_id: UUID) -> Optional[Dict]:
        """
        Retrieve a car by its ID.

        Args:
            car_id: UUID of the car

        Returns:
            Car dictionary if found, None otherwise
        """
        for car in self.cars:
            if car['car_id'] == car_id:
                logger.debug(f"Car found: car_id={car_id}")
                return car

        logger.debug(f"Car not found: car_id={car_id}")
        return None

    def add_document(self, car_id: UUID, document_data: Dict) -> Dict:
        """
        Add a document for a specific car.

        Args:
            car_id: UUID of the car
            document_data: Dictionary with document information

        Returns:
            Dictionary with document data including generated document_id

        Raises:
            ValueError: If car_id does not exist
        """
        # Verify car exists
        car = self.get_car_by_id(car_id)
        if car is None:
            logger.warning(f"Attempt to add document for non-existent car: car_id={car_id}")
            raise ValueError(f"Car with ID {car_id} not found")

        # Generate new document ID
        document_id = uuid4()
        document = {
            'document_id': document_id,
            'car_id': car_id,
            'document_type': document_data['document_type'],
            'file': document_data.get('file'),
            'status': 'pending'  # Default status for new documents
        }

        self.documents.append(document)
        logger.info(f"Document added successfully: document_id={document_id}, car_id={car_id}, type={document_data['document_type']}")
        return document

    def get_documents_by_car_id(self, car_id: UUID) -> List[Dict]:
        """
        Retrieve all documents for a specific car.

        Args:
            car_id: UUID of the car

        Returns:
            List of document dictionaries
        """
        docs = [doc for doc in self.documents if doc['car_id'] == car_id]
        logger.debug(f"Found {len(docs)} documents for car_id={car_id}")
        return docs

    def get_all_cars(self) -> List[Dict]:
        """
        Retrieve all cars from storage.

        Returns:
            List of all car dictionaries
        """
        logger.debug(f"Retrieving all cars: total={len(self.cars)}")
        return self.cars.copy()

    def clear(self):
        """Clear all data from storage (useful for testing)."""
        self.cars.clear()
        self.documents.clear()
        logger.info("Repository cleared")


# Singleton instance
_repository_instance: Optional[LocalCarRepository] = None


def get_repository() -> LocalCarRepository:
    """
    Get the singleton repository instance.

    Returns:
        LocalCarRepository instance
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = LocalCarRepository()
    return _repository_instance
