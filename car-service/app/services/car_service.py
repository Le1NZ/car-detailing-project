"""Business logic layer for car-service."""

from uuid import UUID
from typing import List
import logging

from app.models.car import (
    AddCarRequest,
    CarResponse,
    AddDocumentRequest,
    DocumentResponse
)
from app.repositories.local_car_repo import LocalCarRepository

logger = logging.getLogger(__name__)


class CarService:
    """Service layer for car business logic."""

    def __init__(self, repository: LocalCarRepository):
        """
        Initialize car service with repository.

        Args:
            repository: LocalCarRepository instance
        """
        self.repository = repository
        logger.info("CarService initialized")

    def create_car(self, request: AddCarRequest) -> CarResponse:
        """
        Create a new car record.

        Args:
            request: AddCarRequest with car details

        Returns:
            CarResponse with created car information

        Raises:
            ValueError: If VIN or license_plate already exists
        """
        logger.info(f"Creating new car: VIN={request.vin}, license_plate={request.license_plate}")

        car_data = {
            'owner_id': request.owner_id,
            'license_plate': request.license_plate,
            'vin': request.vin,
            'make': request.make,
            'model': request.model,
            'year': request.year
        }

        # Repository will raise ValueError for duplicates
        car = self.repository.add_car(car_data)

        return CarResponse(
            car_id=car['car_id'],
            license_plate=car['license_plate'],
            vin=car['vin'],
            make=car['make'],
            model=car['model'],
            year=car['year']
        )

    def get_car(self, car_id: UUID) -> CarResponse:
        """
        Retrieve car information by ID.

        Args:
            car_id: UUID of the car

        Returns:
            CarResponse with car information

        Raises:
            ValueError: If car not found
        """
        logger.info(f"Retrieving car: car_id={car_id}")

        car = self.repository.get_car_by_id(car_id)
        if car is None:
            logger.warning(f"Car not found: car_id={car_id}")
            raise ValueError(f"Car with ID {car_id} not found")

        return CarResponse(
            car_id=car['car_id'],
            license_plate=car['license_plate'],
            vin=car['vin'],
            make=car['make'],
            model=car['model'],
            year=car['year']
        )

    def add_document(self, car_id: UUID, request: AddDocumentRequest) -> DocumentResponse:
        """
        Add a document to a car.

        Args:
            car_id: UUID of the car
            request: AddDocumentRequest with document details

        Returns:
            DocumentResponse with created document information

        Raises:
            ValueError: If car not found
        """
        logger.info(f"Adding document to car: car_id={car_id}, type={request.document_type}")

        document_data = {
            'document_type': request.document_type,
            'file': request.file
        }

        # Repository will raise ValueError if car not found
        document = self.repository.add_document(car_id, document_data)

        return DocumentResponse(
            car_id=document['car_id'],
            document_id=document['document_id'],
            document_type=document['document_type'],
            status=document['status']
        )

    def get_car_documents(self, car_id: UUID) -> List[DocumentResponse]:
        """
        Retrieve all documents for a car.

        Args:
            car_id: UUID of the car

        Returns:
            List of DocumentResponse objects

        Raises:
            ValueError: If car not found
        """
        logger.info(f"Retrieving documents for car: car_id={car_id}")

        # First verify car exists
        car = self.repository.get_car_by_id(car_id)
        if car is None:
            logger.warning(f"Car not found when retrieving documents: car_id={car_id}")
            raise ValueError(f"Car with ID {car_id} not found")

        documents = self.repository.get_documents_by_car_id(car_id)

        return [
            DocumentResponse(
                car_id=doc['car_id'],
                document_id=doc['document_id'],
                document_type=doc['document_type'],
                status=doc['status']
            )
            for doc in documents
        ]
