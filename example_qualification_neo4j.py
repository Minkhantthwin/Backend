#!/usr/bin/env python3
"""
Sample usage example for qualification Neo4j integration
"""

import requests
import json

# Base URL for your API
BASE_URL = "http://localhost:8000"

def example_qualification_neo4j_usage():
    """Example usage of qualification Neo4j features"""
    
    print("=== Qualification Neo4j Integration Examples ===\n")
    
    # Example 1: Check user qualification for a specific program
    print("1. Checking user qualification for specific program...")
    print("   This will save qualification status to both MySQL and Neo4j")
    print("   POST /users/1/qualifications/check/1")
    print("   Response: Detailed qualification analysis with status saved to Neo4j\n")
    
    # Example 2: Get program recommendations based on qualification
    print("2. Getting program recommendations based on qualification status...")
    print("   This retrieves recommendations from Neo4j based on qualification scores")
    print("   GET /users/1/qualifications/recommendations?limit=10")
    print("   Response: List of programs with high qualification match\n")
    
    # Example 3: Get qualification status from Neo4j
    print("3. Getting qualification status from Neo4j...")
    print("   This retrieves qualification data directly from Neo4j graph")
    print("   GET /users/1/qualifications/neo4j-status")
    print("   Response: Qualification statuses stored in Neo4j\n")
    
    # Example 4: Check user against all programs
    print("4. Checking user against all programs...")
    print("   This will create qualification relationships for all programs in Neo4j")
    print("   POST /users/1/qualifications/check-all")
    print("   Response: Comprehensive qualification analysis for all programs\n")
    
    # Example 5: Sync qualification status to Neo4j
    print("5. Syncing qualification status to Neo4j...")
    print("   This migrates existing MySQL qualification data to Neo4j")
    print("   POST /users/1/qualifications/sync-neo4j")
    print("   Response: Sync status and results\n")
    
    # Example Neo4j Cypher queries that would be generated
    print("=== Neo4j Relationships Created ===")
    print("User -> QUALIFIED_FOR -> Program")
    print("Properties: is_qualified, qualification_score, requirements_met, etc.")
    print()
    
    print("=== Sample Cypher Queries ===")
    print("1. Find programs user is qualified for:")
    print("   MATCH (u:User {user_id: 1})-[r:QUALIFIED_FOR]->(p:Program)")
    print("   WHERE r.is_qualified = true")
    print("   RETURN p, r.qualification_score")
    print()
    
    print("2. Find users qualified for a specific program:")
    print("   MATCH (u:User)-[r:QUALIFIED_FOR]->(p:Program {program_id: 1})")
    print("   WHERE r.is_qualified = true")
    print("   RETURN u, r.qualification_score")
    print()
    
    print("3. Get qualification recommendations:")
    print("   MATCH (u:User {user_id: 1})-[r:QUALIFIED_FOR]->(p:Program)")
    print("   WHERE r.qualification_score >= 80")
    print("   RETURN p, r.qualification_score ORDER BY r.qualification_score DESC")
    print()

def example_api_calls():
    """Example API calls for qualification Neo4j features"""
    
    print("=== Example API Calls ===\n")
    
    # Note: These are example calls - make sure your server is running
    try:
        # Example 1: Check qualification
        print("1. Checking qualification (saves to Neo4j):")
        # response = requests.post(f"{BASE_URL}/users/1/qualifications/check/1")
        print("   curl -X POST http://localhost:8000/users/1/qualifications/check/1")
        print("   -> Creates/updates QUALIFIED_FOR relationship in Neo4j\n")
        
        # Example 2: Get recommendations
        print("2. Getting recommendations from Neo4j:")
        # response = requests.get(f"{BASE_URL}/users/1/qualifications/recommendations")
        print("   curl -X GET http://localhost:8000/users/1/qualifications/recommendations")
        print("   -> Returns programs with high qualification scores from Neo4j\n")
        
        # Example 3: Get Neo4j status
        print("3. Getting qualification status from Neo4j:")
        # response = requests.get(f"{BASE_URL}/users/1/qualifications/neo4j-status")
        print("   curl -X GET http://localhost:8000/users/1/qualifications/neo4j-status")
        print("   -> Returns qualification relationships from Neo4j graph\n")
        
        # Example 4: Sync to Neo4j
        print("4. Syncing qualification data to Neo4j:")
        # response = requests.post(f"{BASE_URL}/users/1/qualifications/sync-neo4j")
        print("   curl -X POST http://localhost:8000/users/1/qualifications/sync-neo4j")
        print("   -> Migrates MySQL qualification data to Neo4j\n")
        
    except Exception as e:
        print(f"Note: Server needs to be running for actual API calls. Error: {e}")

if __name__ == "__main__":
    example_qualification_neo4j_usage()
    print("\n" + "="*50 + "\n")
    example_api_calls()
