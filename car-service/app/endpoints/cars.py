"""API endpoints for car-service."""

from uuid import UUID
from typing import List
import logging

from fastapi import APIRouter, HTTPException, status, Depends

from app.models.car import (
    AddCarRequest,
    CarResponse,
    AddDocumentRequest,
    DocumentResponse
)
from app.services.car_service import CarService
from app.repositories.local_car_repo import get_repository, LocalCarRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cars", tags=["cars"])


def get_car_service(repository = Depends(get_repository)) -> CarService:
    """
    Dependency injection for CarService.

    Args:
        repository: LocalCarRepository instance (injected)

    Returns:
        CarService instance
    """
    return CarService(repository)


@router.post(
    "",
    response_model=CarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new car",
    description="Register a new car in the system with owner and vehicle details"
)
def add_car(
    request: AddCarRequest,
    car_service: CarService = Depends(get_car_service)
) -> CarResponse:
    """
    Add a new car to the system.

    Args:
        request: AddCarRequest with car details
        car_service: CarService instance (injected)

    Returns:
        CarResponse with created car information

    Raises:
        HTTPException 409: If VIN or license_plate already exists
        HTTPException 422: If validation fails
    """
    try:
        logger.info(f"POST /api/cars - Adding car with VIN: {request.vin}")
        car = car_service.create_car(request)
        logger.info(f"Car created successfully: car_id={car.car_id}")
        return car
    except ValueError as e:
        logger.error(f"Conflict error when adding car: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error when adding car: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{car_id}",
    response_model=CarResponse,
    status_code=status.HTTP_200_OK,
    summary="Get car information",
    description="Retrieve detailed information about a specific car by its ID"
)
def get_car(
    car_id: UUID,
    car_service: CarService = Depends(get_car_service)
) -> CarResponse:
    """
    Get car information by ID.

    This endpoint is critical for order-service integration.

    Args:
        car_id: UUID of the car
        car_service: CarService instance (injected)

    Returns:
        CarResponse with car information

    Raises:
        HTTPException 404: If car not found
    """
    try:
        logger.info(f"GET /api/cars/{car_id} - Retrieving car")
        car = car_service.get_car(car_id)
        logger.info(f"Car retrieved successfully: car_id={car_id}")
        return car
    except ValueError as e:
        logger.warning(f"Car not found: car_id={car_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error when retrieving car: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{car_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Add document to car",
    description="Add a new document (registration, insurance, etc.) to a specific car"
)
def add_car_document(
    car_id: UUID,
    request: AddDocumentRequest,
    car_service: CarService = Depends(get_car_service)
) -> DocumentResponse:
    """
    Add a document to a car.

    Args:
        car_id: UUID of the car
        request: AddDocumentRequest with document details
        car_service: CarService instance (injected)

    Returns:
        DocumentResponse with created document information

    Raises:
        HTTPException 404: If car not found
        HTTPException 422: If validation fails
    """
    try:
        logger.info(f"POST /api/cars/{car_id}/documents - Adding document type: {request.document_type}")
        document = car_service.add_document(car_id, request)
        logger.info(f"Document added successfully: document_id={document.document_id}")
        return document
    except ValueError as e:
        logger.warning(f"Car not found when adding document: car_id={car_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error when adding document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
