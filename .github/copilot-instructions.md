# Project

# 1.Initialization
1. Create the proper python environment using python 3.13
2. Initialize the project using uv
3. Add FastAPI as dependency of the project
4. Create a basic Fast API endpoint with a health endpoint. Please leverage a router for this endpoint.
5. Add a test for the health endpoint using pytest
6. Create a dockerfile for the project make sure to leverage the same python version and use uv to install the dependencies
7. Create a docker-compose file to run the project and make sure to expose the port 8000

# 2.Database
1. Create a database using PostgreSQL database must be deployed using docker-compose
2. Add the database as a dependency of the project
3. Download the dataset from the following link: https://www.kaggle.com/datasets/litvinenko630/insurance-claims/data
4. Inspect the dataset by using pandas and create a table in the database that matches the dataset structure using SQL model (https://sqlmodel.tiangolo.com/)
