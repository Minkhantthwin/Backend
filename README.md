## University Application & Recommendation System

### Overview
This backend service provides a robust API for university application and recommendation management. It helps users find suitable universities and programs based on their qualifications and interests, and supports CRUD operations for applications, users, and related entities.

### Features
- University and program recommendation
- User profile and qualification management
- Application tracking
- RESTful API with clear response formats
- Error handling and logging

### API Response Format

#### ✅ Success Response
```json
{
  "error": 0,
  "timestamp": "Date & Time",
  "message": "success response message",
  "data": { ... }
}
```

#### 🚩 Failure Response
```json
{
  "detail": {
    "error": 404,
    "timestamp": "Date & Time",
    "message": "fail response message",
    "data": null
  }
}
```

### Error Codes
- `0`: No Error
- `404`: Not Found
- `400`: Bad Request
- `422`: Request Format Error
- `500`: Internal Server Error

### Database Architecture

This application uses a **dual-database architecture**:

#### MySQL (Primary Database)
- Stores all application data (users, universities, programs, applications)
- Handles CRUD operations and data integrity
- Provides ACID compliance for transactional operations

#### Neo4j (Recommendation Engine)
- Stores user profiles and relationships for recommendations
- Enables graph-based queries for program matching
- Provides fast recommendation algorithms based on user interests, qualifications, and preferences

### Key Features

#### User Management
- **User Registration**: Creates user profiles in both MySQL and Neo4j
- **Profile Updates**: Synchronizes changes across both databases
- **Recommendations**: Leverages Neo4j graph relationships for personalized program suggestions

#### Recommendation System
- **Graph-Based Matching**: Uses Neo4j to find connections between users and programs
- **Multi-Factor Scoring**: Considers qualifications, interests, and test scores
- **Real-Time Updates**: User changes automatically update recommendation data

### Setup and Installation

1. **Prerequisites:**
   - Python 3.8+
   - MySQL 5.7+
   - Neo4j 4.0+

2. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Backend
   ```

3. **Environment Setup:**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Database Configuration:**
   - Configure MySQL and Neo4j connection details in `.env` file
   - Make sure both databases are running

5. **Initialize Databases:**
   ```bash
   # This will create MySQL tables and test connections
   python -m app.main
   
   # Optional: Populate Neo4j with sample data
   python populate_neo4j.py
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`

### API Endpoints

#### User Management
- `POST /users` - Create new user (saves to both MySQL and Neo4j)
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user (updates both databases)
- `DELETE /users/{user_id}` - Delete user (removes from both databases)
- `GET /users/{user_id}/recommendations` - Get personalized recommendations

#### User Interest Management
- `POST /users/{user_id}/interests` - Create user interest (saves to both MySQL and Neo4j)
- `GET /users/{user_id}/interests` - Get user interests from MySQL
- `GET /users/{user_id}/interests/neo4j` - Get user interests from Neo4j
- `GET /interests/{interest_id}` - Get specific interest
- `PUT /interests/{interest_id}` - Update interest (updates both databases)
- `DELETE /interests/{interest_id}` - Delete interest (removes from both databases)

#### Program Management
- `POST /programs` - Create new program (saves to both MySQL and Neo4j)
- `GET /programs/{program_id}` - Get program details
- `GET /programs` - List all programs
- `DELETE /programs/{program_id}` - Soft delete program
- `GET /programs/recommendations/field/{field_of_study}` - Get program recommendations by field

#### University Management
- `POST /universities` - Create new university (saves to both MySQL and Neo4j)
- `GET /universities/{university_id}` - Get university details
- `GET /universities` - List all universities
- `PUT /universities/{university_id}` - Update university (updates both databases)
- `DELETE /universities/{university_id}` - Delete university (removes from both databases)
- `GET /regions/{region_id}/universities` - Get universities by region from Neo4j

#### Region Management
- `POST /regions` - Create new region (saves to both MySQL and Neo4j)
- `GET /regions/{region_id}` - Get region details
- `GET /regions` - List all regions
- `PUT /regions/{region_id}` - Update region (updates both databases)
- `DELETE /regions/{region_id}` - Delete region (removes from both databases)

#### Qualification Management
- `POST /users/{user_id}/qualifications/check/{program_id}` - Check user qualification for specific program (saves to both MySQL and Neo4j)
- `GET /users/{user_id}/qualifications/summary` - Get user's qualification summary for all programs
- `POST /users/{user_id}/qualifications/check-all` - Check user qualification against all programs
- `GET /users/{user_id}/qualifications/recommendations` - Get program recommendations based on qualification status (from Neo4j)
- `GET /users/{user_id}/qualifications/neo4j-status` - Get user qualification status from Neo4j
- `POST /users/{user_id}/qualifications/sync-neo4j` - Sync qualification status to Neo4j
- `GET /programs/{program_id}/qualified-users` - Get users qualified for a specific program

### Usage
- Use an API client (e.g., Postman, curl) to interact with endpoints under `/app`.
- Refer to the API documentation or code for available routes and request/response formats.

### Logging
Log files are stored in the `logs/` directory:
- `app.log`: General application logs
- `error.log`: Error logs
- `debug.log`: Debug logs

### Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feat/YourFeature`)
3. Commit your changes (`git commit -m '#Issue Number | feat/fix/update: YourCode'`)
4. Push to the branch (`git push origin feat/YourFeature`)
5. Create a pull request

### License
This project is licensed under the MIT License.

### Contact
For questions or support, please open an issue or contact the maintainer.