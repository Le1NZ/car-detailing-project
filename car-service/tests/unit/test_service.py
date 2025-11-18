"""
Unit tests for CarService in app.services.car_service.

Tests cover:
- Creating cars (happy path and error scenarios)
- Retrieving cars by ID
- Adding documents to cars
- Retrieving car documents
- Business logic validation
- Error handling and propagation
- Mocking repository for isolated testing
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import Mock, call
from typing import Dict

from app.services.car_service import CarService
from app.models.car import (
    AddCarRequest,
    CarResponse,
    AddDocumentRequest,
    DocumentResponse
)
from app.repositories.local_car_repo import LocalCarRepository


@pytest.mark.unit
class TestCarServiceCreateCar:
    """Test suite for creating cars via CarService."""

    def test_create_car_success(
        self,
        car_service: CarService,
        valid_car_request: AddCarRequest
    ):
        """Test successfully creating a car."""
        # Act
        result = car_service.create_car(valid_car_request)

        # Assert
        assert isinstance(result, CarResponse)
        assert isinstance(result.car_id, UUID)
        assert result.license_plate == valid_car_request.license_plate
        assert result.vin == valid_car_request.vin
        assert result.make == valid_car_request.make
        assert result.model == valid_car_request.model
        assert result.year == valid_car_request.year

    def test_create_car_calls_repository_add_car(
        self,
        mock_repository: Mock,
        valid_car_request: AddCarRequest
    ):
        """Test that create_car calls repository.add_car with correct data."""
        # Arrange
        service = CarService(mock_repository)
        mock_car_id = uuid4()
        mock_repository.add_car.return_value = {
            "car_id": mock_car_id,
            "owner_id": valid_car_request.owner_id,
            "license_plate": valid_car_request.license_plate,
            "vin": valid_car_request.vin,
            "make": valid_car_request.make,
            "model": valid_car_request.model,
            "year": valid_car_request.year
        }

        # Act
        result = service.create_car(valid_car_request)

        # Assert
        mock_repository.add_car.assert_called_once()
        call_args = mock_repository.add_car.call_args[0][0]
        assert call_args["owner_id"] == valid_car_request.owner_id
        assert call_args["license_plate"] == valid_car_request.license_plate
        assert call_args["vin"] == valid_car_request.vin
        assert call_args["make"] == valid_car_request.make
        assert call_args["model"] == valid_car_request.model
        assert call_args["year"] == valid_car_request.year
        assert result.car_id == mock_car_id

    def test_create_car_duplicate_vin_raises_error(
        self,
        car_service: CarService,
        valid_car_request: AddCarRequest,
        another_valid_car_request: AddCarRequest
    ):
        """Test that creating car with duplicate VIN raises ValueError."""
        # Arrange
        car_service.create_car(valid_car_request)

        # Create request with same VIN but different plate
        duplicate_vin_request = AddCarRequest(
            owner_id=another_valid_car_request.owner_id,
            license_plate="DIFFERENT123",
            vin=valid_car_request.vin,  # Same VIN
            make=another_valid_car_request.make,
            model=another_valid_car_request.model,
            year=another_valid_car_request.year
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            car_service.create_car(duplicate_vin_request)

        assert "VIN" in str(exc_info.value)
        assert "already exists" in str(exc_info.value)

    def test_create_car_duplicate_license_plate_raises_error(
        self,
        car_service: CarService,
        valid_car_request: AddCarRequest,
        another_valid_car_request: AddCarRequest
    ):
        """Test that creating car with duplicate license plate raises ValueError."""
        # Arrange
        car_service.create_car(valid_car_request)

        # Create request with same plate but different VIN
        duplicate_plate_request = AddCarRequest(
            owner_id=another_valid_car_request.owner_id,
            license_plate=valid_car_request.license_plate,  # Same plate
            vin="DIFFERENTVIN12345",
            make=another_valid_car_request.make,
            model=another_valid_car_request.model,
            year=another_valid_car_request.year
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            car_service.create_car(duplicate_plate_request)

        assert "license plate" in str(exc_info.value).lower()
        assert "already exists" in str(exc_info.value)

    def test_create_car_propagates_repository_errors(
        self,
        mock_repository: Mock,
        valid_car_request: AddCarRequest
    ):
        """Test that service propagates repository ValueErrors."""
        # Arrange
        service = CarService(mock_repository)
        mock_repository.add_car.side_effect = ValueError("Repository error")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.create_car(valid_car_request)

        assert "Repository error" in str(exc_info.value)

    def test_create_multiple_cars_success(
        self,
        car_service: CarService,
        valid_car_request: AddCarRequest,
        another_valid_car_request: AddCarRequest
    ):
        """Test creating multiple unique cars."""
        # Act
        car1 = car_service.create_car(valid_car_request)
        car2 = car_service.create_car(another_valid_car_request)

        # Assert
        assert car1.car_id != car2.car_id
        assert car1.vin != car2.vin
        assert car1.license_plate != car2.license_plate


@pytest.mark.unit
class TestCarServiceGetCar:
    """Test suite for retrieving cars via CarService."""

    def test_get_car_success(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test successfully retrieving an existing car."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Act
        result = service.get_car(car_id)

        # Assert
        assert isinstance(result, CarResponse)
        assert result.car_id == car_id
        assert result.license_plate == car["license_plate"]
        assert result.vin == car["vin"]
        assert result.make == car["make"]
        assert result.model == car["model"]
        assert result.year == car["year"]

    def test_get_car_not_found_raises_error(
        self,
        car_service: CarService
    ):
        """Test that getting non-existent car raises ValueError."""
        # Arrange
        non_existent_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            car_service.get_car(non_existent_id)

        assert "not found" in str(exc_info.value).lower()
        assert str(non_existent_id) in str(exc_info.value)

    def test_get_car_calls_repository(
        self,
        mock_repository: Mock
    ):
        """Test that get_car calls repository.get_car_by_id."""
        # Arrange
        service = CarService(mock_repository)
        car_id = uuid4()
        mock_repository.get_car_by_id.return_value = {
            "car_id": car_id,
            "owner_id": uuid4(),
            "license_plate": "TEST",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2020
        }

        # Act
        result = service.get_car(car_id)

        # Assert
        mock_repository.get_car_by_id.assert_called_once_with(car_id)
        assert result.car_id == car_id

    def test_get_car_returns_none_from_repository(
        self,
        mock_repository: Mock
    ):
        """Test that service raises ValueError when repository returns None."""
        # Arrange
        service = CarService(mock_repository)
        car_id = uuid4()
        mock_repository.get_car_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.get_car(car_id)

        assert "not found" in str(exc_info.value).lower()

    def test_get_car_returns_correct_car_from_multiple(
        self,
        car_service: CarService,
        sample_owner_id: UUID
    ):
        """Test retrieving specific car when multiple exist."""
        # Arrange
        car1 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="CAR1",
            vin="11111111111111111",
            make="Make1",
            model="Model1",
            year=2020
        ))
        car2 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="CAR2",
            vin="22222222222222222",
            make="Make2",
            model="Model2",
            year=2021
        ))

        # Act
        result = car_service.get_car(car2.car_id)

        # Assert
        assert result.car_id == car2.car_id
        assert result.vin == "22222222222222222"
        assert result.make == "Make2"


@pytest.mark.unit
class TestCarServiceAddDocument:
    """Test suite for adding documents via CarService."""

    def test_add_document_success(
        self,
        car_service_with_car: tuple[CarService, Dict],
        valid_document_request: AddDocumentRequest
    ):
        """Test successfully adding a document to a car."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Act
        result = service.add_document(car_id, valid_document_request)

        # Assert
        assert isinstance(result, DocumentResponse)
        assert result.car_id == car_id
        assert isinstance(result.document_id, UUID)
        assert result.document_type == valid_document_request.document_type
        assert result.status == "pending"

    def test_add_document_calls_repository(
        self,
        mock_repository: Mock,
        valid_document_request: AddDocumentRequest
    ):
        """Test that add_document calls repository.add_document."""
        # Arrange
        service = CarService(mock_repository)
        car_id = uuid4()
        doc_id = uuid4()
        mock_repository.add_document.return_value = {
            "document_id": doc_id,
            "car_id": car_id,
            "document_type": valid_document_request.document_type,
            "file": valid_document_request.file,
            "status": "pending"
        }

        # Act
        result = service.add_document(car_id, valid_document_request)

        # Assert
        mock_repository.add_document.assert_called_once()
        call_args = mock_repository.add_document.call_args[0]
        assert call_args[0] == car_id
        assert call_args[1]["document_type"] == valid_document_request.document_type
        assert call_args[1]["file"] == valid_document_request.file
        assert result.document_id == doc_id

    def test_add_document_car_not_found_raises_error(
        self,
        car_service: CarService,
        valid_document_request: AddDocumentRequest
    ):
        """Test that adding document to non-existent car raises ValueError."""
        # Arrange
        non_existent_car_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            car_service.add_document(non_existent_car_id, valid_document_request)

        assert "not found" in str(exc_info.value).lower()

    def test_add_document_without_file(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test adding document without file field."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]
        doc_request = AddDocumentRequest(document_type="Registration")

        # Act
        result = service.add_document(car_id, doc_request)

        # Assert
        assert result.document_type == "Registration"
        assert result.status == "pending"

    def test_add_multiple_documents_to_car(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test adding multiple documents to a single car."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Act
        doc1 = service.add_document(car_id, AddDocumentRequest(
            document_type="Registration",
            file="reg.pdf"
        ))
        doc2 = service.add_document(car_id, AddDocumentRequest(
            document_type="Insurance",
            file="ins.pdf"
        ))
        doc3 = service.add_document(car_id, AddDocumentRequest(
            document_type="Inspection",
            file="insp.pdf"
        ))

        # Assert
        assert doc1.car_id == doc2.car_id == doc3.car_id == car_id
        assert doc1.document_id != doc2.document_id != doc3.document_id
        assert doc1.document_type == "Registration"
        assert doc2.document_type == "Insurance"
        assert doc3.document_type == "Inspection"

    def test_add_document_propagates_repository_errors(
        self,
        mock_repository: Mock,
        valid_document_request: AddDocumentRequest
    ):
        """Test that service propagates repository errors."""
        # Arrange
        service = CarService(mock_repository)
        car_id = uuid4()
        mock_repository.add_document.side_effect = ValueError("Car not found")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.add_document(car_id, valid_document_request)

        assert "Car not found" in str(exc_info.value)


@pytest.mark.unit
class TestCarServiceGetCarDocuments:
    """Test suite for retrieving car documents via CarService."""

    def test_get_car_documents_success(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test successfully retrieving documents for a car."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Add some documents
        doc1 = service.add_document(car_id, AddDocumentRequest(
            document_type="Registration",
            file="reg.pdf"
        ))
        doc2 = service.add_document(car_id, AddDocumentRequest(
            document_type="Insurance",
            file="ins.pdf"
        ))

        # Act
        result = service.get_car_documents(car_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(doc, DocumentResponse) for doc in result)
        assert result[0].document_id == doc1.document_id
        assert result[1].document_id == doc2.document_id

    def test_get_car_documents_empty_list(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test retrieving documents for car with no documents."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Act
        result = service.get_car_documents(car_id)

        # Assert
        assert result == []
        assert len(result) == 0

    def test_get_car_documents_car_not_found(
        self,
        car_service: CarService
    ):
        """Test that getting documents for non-existent car raises ValueError."""
        # Arrange
        non_existent_car_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            car_service.get_car_documents(non_existent_car_id)

        assert "not found" in str(exc_info.value).lower()

    def test_get_car_documents_calls_repository(
        self,
        mock_repository: Mock
    ):
        """Test that get_car_documents calls repository methods."""
        # Arrange
        service = CarService(mock_repository)
        car_id = uuid4()
        doc_id = uuid4()

        mock_repository.get_car_by_id.return_value = {
            "car_id": car_id,
            "owner_id": uuid4(),
            "license_plate": "TEST",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2020
        }
        mock_repository.get_documents_by_car_id.return_value = [
            {
                "document_id": doc_id,
                "car_id": car_id,
                "document_type": "Test",
                "file": "test.pdf",
                "status": "pending"
            }
        ]

        # Act
        result = service.get_car_documents(car_id)

        # Assert
        mock_repository.get_car_by_id.assert_called_once_with(car_id)
        mock_repository.get_documents_by_car_id.assert_called_once_with(car_id)
        assert len(result) == 1
        assert result[0].document_id == doc_id

    def test_get_car_documents_only_for_specific_car(
        self,
        car_service: CarService,
        sample_owner_id: UUID
    ):
        """Test that get_car_documents only returns documents for specified car."""
        # Arrange
        car1 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="CAR1",
            vin="11111111111111111",
            make="Make1",
            model="Model1",
            year=2020
        ))
        car2 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="CAR2",
            vin="22222222222222222",
            make="Make2",
            model="Model2",
            year=2021
        ))

        # Add documents to both cars
        car_service.add_document(car1.car_id, AddDocumentRequest(document_type="Car1Doc1"))
        car_service.add_document(car1.car_id, AddDocumentRequest(document_type="Car1Doc2"))
        car_service.add_document(car2.car_id, AddDocumentRequest(document_type="Car2Doc1"))

        # Act
        car1_docs = car_service.get_car_documents(car1.car_id)
        car2_docs = car_service.get_car_documents(car2.car_id)

        # Assert
        assert len(car1_docs) == 2
        assert len(car2_docs) == 1
        assert all(doc.car_id == car1.car_id for doc in car1_docs)
        assert all(doc.car_id == car2.car_id for doc in car2_docs)


@pytest.mark.unit
class TestCarServiceInitialization:
    """Test suite for CarService initialization."""

    def test_service_initialization_with_repository(
        self,
        clean_repository: LocalCarRepository
    ):
        """Test that CarService can be initialized with a repository."""
        # Act
        service = CarService(clean_repository)

        # Assert
        assert service.repository is clean_repository
        assert isinstance(service.repository, LocalCarRepository)

    def test_service_initialization_with_mock(self):
        """Test that CarService can be initialized with a mock repository."""
        # Arrange
        mock_repo = Mock(spec=LocalCarRepository)

        # Act
        service = CarService(mock_repo)

        # Assert
        assert service.repository is mock_repo


@pytest.mark.unit
class TestCarServiceEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_create_car_with_boundary_year_values(
        self,
        car_service: CarService,
        sample_owner_id: UUID
    ):
        """Test creating cars with minimum and maximum year values."""
        # Minimum year (1900)
        car1 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="MINYEAR",
            vin="11111111111111111",
            make="Ford",
            model="Model T",
            year=1900
        ))
        assert car1.year == 1900

        # Maximum year (2025)
        car2 = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="MAXYEAR",
            vin="22222222222222222",
            make="Tesla",
            model="Model Y",
            year=2025
        ))
        assert car2.year == 2025

    def test_create_car_with_minimal_field_lengths(
        self,
        car_service: CarService,
        sample_owner_id: UUID
    ):
        """Test creating car with minimum length fields."""
        # Act
        car = car_service.create_car(AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="A",  # 1 char
            vin="12345678901234567",
            make="B",  # 1 char
            model="C",  # 1 char
            year=2000
        ))

        # Assert
        assert car.license_plate == "A"
        assert car.make == "B"
        assert car.model == "C"

    def test_document_status_always_pending(
        self,
        car_service_with_car: tuple[CarService, Dict]
    ):
        """Test that all documents created through service have 'pending' status."""
        # Arrange
        service, car = car_service_with_car
        car_id = car["car_id"]

        # Act
        doc1 = service.add_document(car_id, AddDocumentRequest(document_type="Type1"))
        doc2 = service.add_document(car_id, AddDocumentRequest(document_type="Type2"))
        doc3 = service.add_document(car_id, AddDocumentRequest(document_type="Type3"))

        # Assert
        assert doc1.status == "pending"
        assert doc2.status == "pending"
        assert doc3.status == "pending"

    def test_service_preserves_data_integrity(
        self,
        car_service: CarService,
        valid_car_request: AddCarRequest
    ):
        """Test that service preserves all data from request to response."""
        # Act
        created_car = car_service.create_car(valid_car_request)
        retrieved_car = car_service.get_car(created_car.car_id)

        # Assert - all fields match
        assert created_car.car_id == retrieved_car.car_id
        assert created_car.license_plate == retrieved_car.license_plate
        assert created_car.vin == retrieved_car.vin
        assert created_car.make == retrieved_car.make
        assert created_car.model == retrieved_car.model
        assert created_car.year == retrieved_car.year
