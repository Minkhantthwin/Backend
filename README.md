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

### Setup and Installation

1. **Clone the repository and open the project:**
   ```bash
   git clone <your-repo-url>
   cd Backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the project:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000` by default.

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
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Create a pull request

### License
This project is licensed under the MIT License.

### Contact
For questions or support, please open an issue or contact the maintainer.