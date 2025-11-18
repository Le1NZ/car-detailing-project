"""
Unit tests for LocalCarRepository in app.repositories.local_car_repo.

Tests cover:
- Adding cars (happy path and duplicate detection)
- Retrieving cars by ID
- Adding documents to cars
- Retrieving documents by car ID
- Repository clearing
- Edge cases and error scenarios
"""

import pytest
from uuid import UUID, uuid4
from typing import Dict

from app.repositories.local_car_repo import LocalCarRepository, get_repository


@pytest.mark.unit
class TestLocalCarRepositoryAddCar:
    """Test suite for adding cars to the repository."""

    def test_add_car_success(self, clean_repository: LocalCarRepository, valid_car_data: Dict):
        """Test successfully adding a car to empty repository."""
        # Arrange
        repo = clean_repository

        # Act
        result = repo.add_car(valid_car_data)

        # Assert
        assert result is not None
        assert "car_id" in result
        assert isinstance(result["car_id"], UUID)
        assert result["owner_id"] == valid_car_data["owner_id"]
        assert result["license_plate"] == valid_car_data["license_plate"]
        assert result["vin"] == valid_car_data["vin"]
        assert result["make"] == valid_car_data["make"]
        assert result["model"] == valid_car_data["model"]
        assert result["year"] == valid_car_data["year"]

    def test_add_car_generates_unique_id(
        self,
        clean_repository: LocalCarRepository,
        valid_car_data: Dict
    ):
        """Test that each added car gets a unique UUID."""
        # Arrange
        repo = clean_repository
        car_data_2 = {**valid_car_data, "vin": "DIFFERENT123456789", "license_plate": "XYZ999"}

        # Act
        car1 = repo.add_car(valid_car_data)
        car2 = repo.add_car(car_data_2)

        # Assert
        assert car1["car_id"] != car2["car_id"]
        assert isinstance(car1["car_id"], UUID)
        assert isinstance(car2["car_id"], UUID)

    def test_add_car_duplicate_vin_raises_error(
        self,
        clean_repository: LocalCarRepository,
        valid_car_data: Dict
    ):
        """Test that adding a car with duplicate VIN raises ValueError."""
        # Arrange
        repo = clean_repository
        repo.add_car(valid_car_data)

        # Create new car data with same VIN but different plate
        duplicate_vin_data = {
            **valid_car_data,
            "license_plate": "DIFFERENT123"
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repo.add_car(duplicate_vin_data)

        assert "VIN" in str(exc_info.value)
        assert valid_car_data["vin"] in str(exc_info.value)
        assert "already exists" in str(exc_info.value)

    def test_add_car_duplicate_license_plate_raises_error(
        self,
        clean_repository: LocalCarRepository,
        valid_car_data: Dict
    ):
        """Test that adding a car with duplicate license plate raises ValueError."""
        # Arrange
        repo = clean_repository
        repo.add_car(valid_car_data)

        # Create new car data with same plate but different VIN
        duplicate_plate_data = {
            **valid_car_data,
            "vin": "DIFFERENTVIN123456"
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repo.add_car(duplicate_plate_data)

        assert "license plate" in str(exc_info.value).lower()
        assert valid_car_data["license_plate"] in str(exc_info.value)
        assert "already exists" in str(exc_info.value)

    def test_add_multiple_unique_cars(self, clean_repository: LocalCarRepository):
        """Test adding multiple cars with unique VIN and plates."""
        # Arrange
        repo = clean_repository
        car1_data = {
            "owner_id": uuid4(),
            "license_plate": "CAR001",
            "vin": "11111111111111111",
            "make": "Toyota",
            "model": "Camry",
            "year": 2020
        }
        car2_data = {
            "owner_id": uuid4(),
            "license_plate": "CAR002",
            "vin": "22222222222222222",
            "make": "Honda",
            "model": "Accord",
            "year": 2021
        }
        car3_data = {
            "owner_id": uuid4(),
            "license_plate": "CAR003",
            "vin": "33333333333333333",
            "make": "Ford",
            "model": "Focus",
            "year": 2019
        }

        # Act
        result1 = repo.add_car(car1_data)
        result2 = repo.add_car(car2_data)
        result3 = repo.add_car(car3_data)

        # Assert
        assert len(repo.cars) == 3
        assert result1["car_id"] != result2["car_id"] != result3["car_id"]
        assert result1["vin"] == "11111111111111111"
        assert result2["vin"] == "22222222222222222"
        assert result3["vin"] == "33333333333333333"

    def test_add_car_preserves_all_fields(
        self,
        clean_repository: LocalCarRepository,
        sample_owner_id: UUID
    ):
        """Test that all car data fields are preserved exactly."""
        # Arrange
        repo = clean_repository
        car_data = {
            "owner_id": sample_owner_id,
            "license_plate": "PRESERVE",
            "vin": "TESTVIN1234567890",
            "make": "Test Make",
            "model": "Test Model",
            "year": 2015
        }

        # Act
        result = repo.add_car(car_data)

        # Assert
        assert result["owner_id"] == sample_owner_id
        assert result["license_plate"] == "PRESERVE"
        assert result["vin"] == "TESTVIN1234567890"
        assert result["make"] == "Test Make"
        assert result["model"] == "Test Model"
        assert result["year"] == 2015


@pytest.mark.unit
class TestLocalCarRepositoryGetCar:
    """Test suite for retrieving cars from the repository."""

    def test_get_car_by_id_success(
        self,
        clean_repository: LocalCarRepository,
        valid_car_data: Dict
    ):
        """Test successfully retrieving a car by its ID."""
        # Arrange
        repo = clean_repository
        added_car = repo.add_car(valid_car_data)
        car_id = added_car["car_id"]

        # Act
        result = repo.get_car_by_id(car_id)

        # Assert
        assert result is not None
        assert result["car_id"] == car_id
        assert result["vin"] == valid_car_data["vin"]
        assert result["license_plate"] == valid_car_data["license_plate"]

    def test_get_car_by_id_not_found(self, clean_repository: LocalCarRepository):
        """Test that getting non-existent car returns None."""
        # Arrange
        repo = clean_repository
        non_existent_id = uuid4()

        # Act
        result = repo.get_car_by_id(non_existent_id)

        # Assert
        assert result is None

    def test_get_car_by_id_from_multiple_cars(
        self,
        clean_repository: LocalCarRepository
    ):
        """Test retrieving specific car when multiple cars exist."""
        # Arrange
        repo = clean_repository
        car1 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR001",
            "vin": "11111111111111111",
            "make": "Make1",
            "model": "Model1",
            "year": 2020
        })
        car2 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR002",
            "vin": "22222222222222222",
            "make": "Make2",
            "model": "Model2",
            "year": 2021
        })
        car3 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR003",
            "vin": "33333333333333333",
            "make": "Make3",
            "model": "Model3",
            "year": 2022
        })

        # Act
        result = repo.get_car_by_id(car2["car_id"])

        # Assert
        assert result is not None
        assert result["car_id"] == car2["car_id"]
        assert result["vin"] == "22222222222222222"
        assert result["make"] == "Make2"


@pytest.mark.unit
class TestLocalCarRepositoryDocuments:
    """Test suite for document operations in the repository."""

    def test_add_document_success(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict],
        valid_document_data: Dict
    ):
        """Test successfully adding a document to a car."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]

        # Act
        result = repo.add_document(car_id, valid_document_data)

        # Assert
        assert result is not None
        assert "document_id" in result
        assert isinstance(result["document_id"], UUID)
        assert result["car_id"] == car_id
        assert result["document_type"] == valid_document_data["document_type"]
        assert result["file"] == valid_document_data["file"]
        assert result["status"] == "pending"

    def test_add_document_generates_unique_id(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict],
        valid_document_data: Dict
    ):
        """Test that each document gets a unique UUID."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]
        doc_data_2 = {"document_type": "Insurance", "file": "insurance.pdf"}

        # Act
        doc1 = repo.add_document(car_id, valid_document_data)
        doc2 = repo.add_document(car_id, doc_data_2)

        # Assert
        assert doc1["document_id"] != doc2["document_id"]
        assert isinstance(doc1["document_id"], UUID)
        assert isinstance(doc2["document_id"], UUID)

    def test_add_document_car_not_found(
        self,
        clean_repository: LocalCarRepository,
        valid_document_data: Dict
    ):
        """Test that adding document to non-existent car raises ValueError."""
        # Arrange
        repo = clean_repository
        non_existent_car_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repo.add_document(non_existent_car_id, valid_document_data)

        assert "not found" in str(exc_info.value).lower()
        assert str(non_existent_car_id) in str(exc_info.value)

    def test_add_document_without_file(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict]
    ):
        """Test adding a document without file field (None)."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]
        doc_data = {"document_type": "Registration"}

        # Act
        result = repo.add_document(car_id, doc_data)

        # Assert
        assert result["file"] is None
        assert result["document_type"] == "Registration"
        assert result["status"] == "pending"

    def test_add_multiple_documents_to_one_car(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict]
    ):
        """Test adding multiple documents to a single car."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]

        # Act
        doc1 = repo.add_document(car_id, {"document_type": "Registration", "file": "reg.pdf"})
        doc2 = repo.add_document(car_id, {"document_type": "Insurance", "file": "ins.pdf"})
        doc3 = repo.add_document(car_id, {"document_type": "Inspection", "file": "insp.pdf"})

        # Assert
        assert len(repo.documents) == 3
        assert doc1["car_id"] == doc2["car_id"] == doc3["car_id"] == car_id
        assert doc1["document_type"] == "Registration"
        assert doc2["document_type"] == "Insurance"
        assert doc3["document_type"] == "Inspection"

    def test_get_documents_by_car_id_success(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict]
    ):
        """Test retrieving all documents for a specific car."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]
        doc1 = repo.add_document(car_id, {"document_type": "Doc1", "file": "file1.pdf"})
        doc2 = repo.add_document(car_id, {"document_type": "Doc2", "file": "file2.pdf"})

        # Act
        result = repo.get_documents_by_car_id(car_id)

        # Assert
        assert len(result) == 2
        assert result[0]["document_id"] == doc1["document_id"]
        assert result[1]["document_id"] == doc2["document_id"]
        assert all(doc["car_id"] == car_id for doc in result)

    def test_get_documents_by_car_id_no_documents(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict]
    ):
        """Test retrieving documents for car with no documents."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]

        # Act
        result = repo.get_documents_by_car_id(car_id)

        # Assert
        assert result == []
        assert len(result) == 0

    def test_get_documents_by_car_id_multiple_cars(
        self,
        clean_repository: LocalCarRepository
    ):
        """Test that get_documents_by_car_id only returns documents for specified car."""
        # Arrange
        repo = clean_repository
        car1 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR1",
            "vin": "11111111111111111",
            "make": "Make1",
            "model": "Model1",
            "year": 2020
        })
        car2 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR2",
            "vin": "22222222222222222",
            "make": "Make2",
            "model": "Model2",
            "year": 2021
        })

        # Add documents to both cars
        doc1_car1 = repo.add_document(car1["car_id"], {"document_type": "Car1Doc1"})
        doc2_car1 = repo.add_document(car1["car_id"], {"document_type": "Car1Doc2"})
        doc1_car2 = repo.add_document(car2["car_id"], {"document_type": "Car2Doc1"})

        # Act
        car1_docs = repo.get_documents_by_car_id(car1["car_id"])
        car2_docs = repo.get_documents_by_car_id(car2["car_id"])

        # Assert
        assert len(car1_docs) == 2
        assert len(car2_docs) == 1
        assert all(doc["car_id"] == car1["car_id"] for doc in car1_docs)
        assert all(doc["car_id"] == car2["car_id"] for doc in car2_docs)
        assert car1_docs[0]["document_type"] == "Car1Doc1"
        assert car2_docs[0]["document_type"] == "Car2Doc1"


@pytest.mark.unit
class TestLocalCarRepositoryUtilityMethods:
    """Test suite for utility methods in the repository."""

    def test_get_all_cars_empty_repository(self, clean_repository: LocalCarRepository):
        """Test get_all_cars on empty repository."""
        # Arrange
        repo = clean_repository

        # Act
        result = repo.get_all_cars()

        # Assert
        assert result == []
        assert len(result) == 0

    def test_get_all_cars_with_multiple_cars(self, clean_repository: LocalCarRepository):
        """Test get_all_cars returns all cars."""
        # Arrange
        repo = clean_repository
        car1 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR1",
            "vin": "11111111111111111",
            "make": "Make1",
            "model": "Model1",
            "year": 2020
        })
        car2 = repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR2",
            "vin": "22222222222222222",
            "make": "Make2",
            "model": "Model2",
            "year": 2021
        })

        # Act
        result = repo.get_all_cars()

        # Assert
        assert len(result) == 2
        assert car1 in result
        assert car2 in result

    def test_get_all_cars_returns_copy(self, clean_repository: LocalCarRepository):
        """Test that get_all_cars returns a copy, not the original list."""
        # Arrange
        repo = clean_repository
        repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "TEST",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2020
        })

        # Act
        result = repo.get_all_cars()
        result.append({"fake": "car"})  # Modify the returned list

        # Assert
        assert len(repo.get_all_cars()) == 1  # Original list unchanged

    def test_clear_removes_all_cars(self, clean_repository: LocalCarRepository):
        """Test that clear() removes all cars."""
        # Arrange
        repo = clean_repository
        repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR1",
            "vin": "11111111111111111",
            "make": "Make1",
            "model": "Model1",
            "year": 2020
        })
        repo.add_car({
            "owner_id": uuid4(),
            "license_plate": "CAR2",
            "vin": "22222222222222222",
            "make": "Make2",
            "model": "Model2",
            "year": 2021
        })

        # Act
        repo.clear()

        # Assert
        assert len(repo.cars) == 0
        assert len(repo.get_all_cars()) == 0

    def test_clear_removes_all_documents(self, repository_with_car: tuple[LocalCarRepository, Dict]):
        """Test that clear() removes all documents."""
        # Arrange
        repo, car = repository_with_car
        repo.add_document(car["car_id"], {"document_type": "Doc1"})
        repo.add_document(car["car_id"], {"document_type": "Doc2"})

        # Act
        repo.clear()

        # Assert
        assert len(repo.documents) == 0

    def test_clear_on_empty_repository(self, clean_repository: LocalCarRepository):
        """Test that clear() works on already empty repository."""
        # Arrange
        repo = clean_repository

        # Act
        repo.clear()

        # Assert
        assert len(repo.cars) == 0
        assert len(repo.documents) == 0


@pytest.mark.unit
class TestRepositorySingleton:
    """Test suite for the singleton pattern implementation."""

    def test_get_repository_returns_same_instance(self):
        """Test that get_repository() returns the same instance on multiple calls."""
        # Act
        repo1 = get_repository()
        repo2 = get_repository()
        repo3 = get_repository()

        # Assert
        assert repo1 is repo2
        assert repo2 is repo3
        assert id(repo1) == id(repo2) == id(repo3)

    def test_get_repository_returns_local_car_repository(self):
        """Test that get_repository() returns LocalCarRepository instance."""
        # Act
        repo = get_repository()

        # Assert
        assert isinstance(repo, LocalCarRepository)

    def test_singleton_state_persists(self):
        """Test that state persists across get_repository() calls."""
        # Arrange
        repo1 = get_repository()
        repo1.clear()  # Start clean
        car_data = {
            "owner_id": uuid4(),
            "license_plate": "PERSIST",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2020
        }

        # Act
        added_car = repo1.add_car(car_data)
        repo2 = get_repository()
        retrieved_car = repo2.get_car_by_id(added_car["car_id"])

        # Assert
        assert retrieved_car is not None
        assert retrieved_car["car_id"] == added_car["car_id"]
        assert len(repo2.cars) == 1

        # Cleanup
        repo1.clear()


@pytest.mark.unit
class TestRepositoryEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_add_car_with_uuid_as_owner_id(self, clean_repository: LocalCarRepository):
        """Test adding car with UUID object vs UUID string."""
        # Arrange
        repo = clean_repository
        owner_uuid = uuid4()

        # Act - with UUID object
        car = repo.add_car({
            "owner_id": owner_uuid,
            "license_plate": "TEST",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2020
        })

        # Assert
        assert car["owner_id"] == owner_uuid

    def test_case_sensitive_duplicate_detection(self, clean_repository: LocalCarRepository):
        """Test that duplicate detection is case-sensitive for VIN and plate."""
        # Arrange
        repo = clean_repository
        car1_data = {
            "owner_id": uuid4(),
            "license_plate": "ABC123",
            "vin": "UPPERCASE123456789",
            "make": "Test",
            "model": "Car",
            "year": 2020
        }
        repo.add_car(car1_data)

        # Different case VIN - should be allowed (case-sensitive)
        car2_data = {
            "owner_id": uuid4(),
            "license_plate": "XYZ789",
            "vin": "uppercase123456789",  # lowercase version
            "make": "Test",
            "model": "Car",
            "year": 2020
        }

        # Act & Assert - this should succeed since VIN is case-sensitive
        car2 = repo.add_car(car2_data)
        assert car2["vin"] == "uppercase123456789"

    def test_document_status_always_pending_on_creation(
        self,
        repository_with_car: tuple[LocalCarRepository, Dict]
    ):
        """Test that all new documents have status 'pending' regardless of input."""
        # Arrange
        repo, car = repository_with_car
        car_id = car["car_id"]

        # Act - try to set different status (should be overridden)
        doc = repo.add_document(car_id, {"document_type": "Test", "status": "approved"})

        # Assert
        assert doc["status"] == "pending"
