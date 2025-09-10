# Environment Configuration Guide

This document provides detailed information about configuring the environment variables for the University Recommendation System.

## Required Environment Variables

### Application Settings
```env
APP_NAME="University Recommendation System"
APP_VERSION="1.0.0"
APP_DESCRIPTION="AI-powered university recommendation and application system"
DEBUG=false
ENVIRONMENT=development
API_V1_STR="v1"
HOST="localhost"
PORT=8000
RELOAD=true
```

### MySQL Database Configuration
```env
MYSQL_HOST="localhost"
MYSQL_PORT=3306
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE="university_recommendation_db"
MYSQL_CHARSET="utf8mb4"
MYSQL_POOL_SIZE=10
MYSQL_MAX_OVERFLOW=20
MYSQL_POOL_TIMEOUT=30
MYSQL_POOL_RECYCLE=3600
```

### Neo4j Database Configuration
```env
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE="neo4j"
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
```

## Database Setup Instructions

### MySQL Setup
1. Install MySQL 5.7 or higher
2. Create a new database:
   ```sql
   CREATE DATABASE university_recommendation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Create a user with appropriate permissions:
   ```sql
   CREATE USER 'your_mysql_username'@'localhost' IDENTIFIED BY 'your_mysql_password';
   GRANT ALL PRIVILEGES ON university_recommendation_db.* TO 'your_mysql_username'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Neo4j Setup
1. Install Neo4j Desktop or Neo4j Community Server
2. Create a new database or use the default `neo4j` database
3. Set a password for the `neo4j` user
4. Ensure the Bolt protocol is enabled on port 7687

## Environment-Specific Configurations

### Development Environment
```env
DEBUG=true
ENVIRONMENT=development
RELOAD=true
```

### Production Environment
```env
DEBUG=false
ENVIRONMENT=production
RELOAD=false
HOST=0.0.0.0
```

### Testing Environment
```env
DEBUG=false
ENVIRONMENT=testing
MYSQL_DATABASE="university_recommendation_test_db"
NEO4J_DATABASE="test"
```

## Security Notes

1. **Never commit your `.env` file** to version control
2. **Use strong passwords** for database connections
3. **Restrict database user permissions** to only what's necessary
4. **Use environment-specific configurations** for different deployment stages
5. **Consider using secrets management** for production environments

## Configuration Validation

The application will validate all environment variables on startup. If any required variables are missing or invalid, the application will fail to start with detailed error messages.

## Troubleshooting

### Common Issues
1. **Database Connection Failed**: Check host, port, username, and password
2. **Neo4j Authentication Error**: Verify Neo4j credentials and ensure the service is running
3. **Missing Environment Variables**: Ensure all required variables are set in your `.env` file
4. **Port Already in Use**: Change the `PORT` variable to an available port

### Testing Database Connections
The application includes built-in database connection testing. Check the logs on startup to verify successful connections to both MySQL and Neo4j.
