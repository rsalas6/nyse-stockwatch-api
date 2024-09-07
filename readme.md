# NYSE StockWatch Backend

The `nyse-stockwatch-backend` is a Django REST API project developed as part of a technical assessment for **Webull-MX**. The API manages company information and integrates external stock market data from Alpha Vantage and Twelve Data. It provides CRUD operations for companies and allows users to retrieve real-time and historical market data.

## Features
- CRUD operations for managing company records.
- Validation of stock symbols using Alpha Vantage API.
- Fetch market data and historical stock prices via Twelve Data API.
- Pagination and filtering for efficient data retrieval.
- Swagger and ReDoc for API documentation.

## Prerequisites
To run this project, make sure you have **Docker**, **docker-compose**, and optionally **Taskfile CLI** installed.

### Required Environment Variables
Ensure you create a `.env` file in the root directory with the following variables:

```plaintext
POSTGRES_DB=postgres_db
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
ALPHA_VINTAGE_API_KEY=your_alpha_vantage_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key
```

## Getting Started

### Project Initialization (with Taskfile)

To initialize the project, use the `task init` command:

```bash
task init
```

This command will:
- Build the Docker services.
- Start the services in detached mode.
- Run database migrations.

You can also view all available commands and their descriptions by inspecting the **[Taskfile.yml](./taskfile.yml)**.

### Accessing the API

Once the server is running, you can interact with the API at:

- **Swagger UI**: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- **ReDoc**: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

These provide interactive documentation to explore the API.

### Key Endpoints

- **GET /api/v1/companies/**: List companies with filtering and pagination.
- **POST /api/v1/companies/**: Add a new company.
- **GET /api/v1/companies/{id}/**: Get company details by UUID.
- **PUT /api/v1/companies/{id}/**: Update a company.
- **DELETE /api/v1/companies/{id}/**: Delete a company.
- **GET /api/v1/companies/external/{symbol}/**: Fetch company info from Alpha Vantage.
- **GET /api/v1/companies/{id}/?market=true**: Fetch company details with market data for the last 7 days.

## Testing
You can run unit tests with:

```bash
python manage.py test
```

### Code Formatting and Linting

The project is configured to use **Black** for code formatting and **Ruff** for linting and static code analysis. These tools ensure the codebase follows Python style guidelines and is free of common issues.

You can run the following commands to format and lint the code:

- **Format with Black**:
  ```bash
  task black:fix
  ```

- **Check code with Ruff**:
  ```bash
  task ruff:check
  ```

Refer to the **[Taskfile.yml](./taskfile.yml)** for more commands.