import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import DatabaseError
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer
from .services import (
    get_company_info_twelve,
    get_market_data_twelve,
    SymbolNotFoundException,
)

logger = logging.getLogger(__name__)


class CompanyPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 45


@swagger_auto_schema(
    method="get",
    operation_description="Validates the provided token.",
    responses={200: openapi.Response("Token is valid")},
)
@api_view(["GET"])
def validate_token(request):
    return Response({"detail": "Token is valid."}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_summary="List or search companies",
    operation_description="Retrieve a list of companies, with filtering, pagination, and sorting capabilities.",
    responses={200: CompanySerializer(many=True)},
)
@swagger_auto_schema(
    method="post",
    operation_summary="Create a new company",
    operation_description="Create a new company by specifying its name, description, and symbol. Validates the symbol with an external service.",
    request_body=CompanySerializer,
    responses={201: CompanySerializer},
)
@api_view(["GET", "POST"])
def company_list_create(request):

    if request.method == "GET":
        valid_search_fields = [
            "in_all",
            "in_name",
            "in_symbol",
            "in_description",
            "by_symbol",
        ]
        valid_sort_fields = ["name", "symbol"]
        valid_sort_directions = ["asc", "desc"]

        search_field = request.query_params.get("search_field", None)
        search = request.query_params.get("search", None)
        sort_by = request.query_params.get("sort_by", "name")
        sort_direction = request.query_params.get("sort_direction", "asc")
        per_page = request.query_params.get("per_page", 9)

        filters = Q()
        if search_field == "in_all" and search:
            filters |= (
                Q(name__icontains=search)
                | Q(symbol__icontains=search)
                | Q(description__icontains=search)
            )
        elif search_field == "in_name" and search:
            filters &= Q(name__icontains=search)
        elif search_field == "in_symbol" and search:
            filters &= Q(symbol__icontains=search)
        elif search_field == "in_description" and search:
            filters &= Q(description__icontains=search)
        elif search_field == "by_symbol" and search:
            filters &= Q(symbol__exact=search)

        if sort_by not in valid_sort_fields:
            sort_by = "name"

        if sort_direction not in valid_sort_directions:
            sort_direction = "asc"

        if sort_direction == "desc":
            sort_by = f"-{sort_by}"

        companies = Company.objects.filter(filters).order_by(sort_by)

        paginator = CompanyPagination()
        paginator.page_size = per_page
        result_page = paginator.paginate_queryset(companies, request)
        serializer = CompanySerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    elif request.method == "POST":
        symbol = request.data.get("symbol", None)

        if not symbol:
            return Response(
                {"detail": "Symbol is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Company.objects.filter(symbol=symbol).exists():
            return Response(
                {
                    "detail": f"A company with symbol '{symbol}' already exists.",
                    "error": "duplicated",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            get_company_info_twelve(symbol)
        except SymbolNotFoundException as e:
            logger.error(f"Symbol '{symbol}' is not valid: {e}")
            return Response(
                {"detail": f"The symbol '{symbol}' is not valid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CompanySerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except DatabaseError as e:
            logger.error(f"Error saving company: {e}")
            return Response(
                {"detail": "Error saving to the database."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@swagger_auto_schema(
    method="get",
    operation_summary="Retrieve company details",
    operation_description="Fetch a company’s details by ID. Optionally, include market data from Twelve Data by adding 'market' to query params.",
    responses={200: CompanySerializer},
)
@swagger_auto_schema(
    method="put",
    operation_summary="Update a company",
    operation_description="Update the details of a company with the given ID. Allows partial updates.",
    request_body=CompanySerializer,
    responses={200: CompanySerializer},
)
@swagger_auto_schema(
    method="delete",
    operation_summary="Delete a company",
    operation_description="Delete a company by its ID.",
    responses={204: "Company deleted successfully"},
)
@api_view(["GET", "PUT", "DELETE"])
def company_detail(request, pk):
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        logger.error(f"Company with id {pk} not found.")
        return Response(
            {"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND
        )
    except DatabaseError as e:
        logger.error(f"Error fetching the company: {e}")
        return Response(
            {"detail": "Error accessing the database."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if request.method == "GET":
        serializer = CompanySerializer(company)
        response_data = serializer.data

        if "market" in request.query_params:
            try:
                market_data = get_market_data_twelve(company.symbol)
                response_data["market_data"] = market_data
            except SymbolNotFoundException as e:
                logger.error(f"Symbol {company.symbol} not found in Twelve Data: {e}")
                return Response(
                    {"detail": f"Symbol '{company.symbol}' not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                logger.error(f"Error fetching market data from Twelve Data: {e}")
                return Response(
                    {"detail": "Error fetching market data."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if not serializer.is_valid():
            logger.error(f"Validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DatabaseError as e:
            logger.error(f"Error updating the company: {e}")
            return Response(
                {"detail": "Error updating the company."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "DELETE":
        try:
            company.delete()
            logger.info(f"Company with id {pk} deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            logger.error(f"Error deleting the company: {e}")
            return Response(
                {"detail": "Error deleting the company."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@swagger_auto_schema(
    method="get",
    operation_summary="Get external company info by symbol",
    operation_description="Fetches company information from the Twelve Data API based on a stock symbol.",
    responses={200: "External company info"},
)
@api_view(["GET"])
def get_company_info(request, symbol):
    try:
        company_info = get_company_info_twelve(symbol)
        return Response(company_info, status=status.HTTP_200_OK)
    except SymbolNotFoundException as e:
        logger.error(f"Symbol {symbol} not found: {e}")
        return Response(
            {"detail": f"Symbol '{symbol}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Error fetching data from Twelve Data: {e}")
        return Response(
            {"detail": "Error fetching data from Twelve Data."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
