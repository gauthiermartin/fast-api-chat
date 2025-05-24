#!/usr/bin/env python3
"""
Script to import insurance_claims.csv data into PostgreSQL database.
This script should be run after the database has been initialized with init.sql.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from pathlib import Path
import sys
import os
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CSVDataImporter:
    """Import CSV data into PostgreSQL database."""

    def __init__(self, csv_path: Path, db_config: dict):
        self.csv_path = csv_path
        self.db_config = db_config
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.df: Optional[pd.DataFrame] = None

    def connect_to_database(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            logger.info("Connecting to PostgreSQL database...")
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False
            logger.info("Successfully connected to database")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect_from_database(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def load_csv_data(self) -> None:
        """Load and validate CSV data."""
        try:
            logger.info(f"Loading CSV data from {self.csv_path}")
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} rows with {len(self.df.columns)} columns")

            # Validate required columns
            required_columns = [
                'policy_id', 'claim_id', 'customer_age', 'customer_gender',
                'customer_state', 'vehicle_make', 'vehicle_model', 'vehicle_year',
                'claim_date', 'claim_type', 'claim_amount', 'deductible',
                'claim_status', 'annual_premium', 'is_fraud'
            ]

            missing_columns = set(required_columns) - set(self.df.columns)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            logger.info("CSV data validation passed")

        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise

    def prepare_data_for_import(self) -> list:
        """Prepare CSV data for database import."""
        try:
            logger.info("Preparing data for database import...")

            if self.df is None:
                raise ValueError("DataFrame is not loaded")

            # Convert data types
            self.df['customer_age'] = pd.to_numeric(self.df['customer_age'], errors='coerce')
            self.df['vehicle_year'] = pd.to_numeric(self.df['vehicle_year'], errors='coerce')
            self.df['claim_amount'] = pd.to_numeric(self.df['claim_amount'], errors='coerce')
            self.df['deductible'] = pd.to_numeric(self.df['deductible'], errors='coerce')
            self.df['annual_premium'] = pd.to_numeric(self.df['annual_premium'], errors='coerce')

            # Convert claim_date to proper datetime format
            self.df['claim_date'] = pd.to_datetime(self.df['claim_date'])

            # Convert boolean column
            self.df['is_fraud'] = self.df['is_fraud'].astype(bool)

            # Check for any null values that shouldn't be there
            null_counts = self.df.isnull().sum()
            if null_counts.any():
                logger.warning("Found null values in data:")
                for col, count in null_counts[null_counts > 0].items():
                    logger.warning(f"  {col}: {count} null values")

            # Prepare data as list of tuples for insertion
            data_tuples = []
            for _, row in self.df.iterrows():
                data_tuples.append((
                    row['policy_id'],
                    row['claim_id'],
                    row['customer_age'],
                    row['customer_gender'],
                    row['customer_state'],
                    row['vehicle_make'],
                    row['vehicle_model'],
                    row['vehicle_year'],
                    row['claim_date'],
                    row['claim_type'],
                    row['claim_amount'],
                    row['deductible'],
                    row['claim_status'],
                    row['annual_premium'],
                    row['is_fraud']
                ))

            logger.info(f"Prepared {len(data_tuples)} records for import")
            return data_tuples

        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise

    def check_table_exists(self) -> bool:
        """Check if the insurance_claims table exists."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'insurance_claims'
                );
            """)
            exists = cursor.fetchone()[0]
            cursor.close()
            return exists

        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            raise

    def get_record_count(self) -> int:
        """Get current number of records in the table."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM insurance_claims;")
            count = cursor.fetchone()[0]
            cursor.close()
            return count

        except Exception as e:
            logger.error(f"Error getting record count: {e}")
            return 0

    def clear_existing_data(self) -> None:
        """Clear existing data from the table."""
        try:
            logger.info("Clearing existing data from insurance_claims table...")
            cursor = self.connection.cursor()
            cursor.execute("TRUNCATE TABLE insurance_claims RESTART IDENTITY CASCADE;")
            self.connection.commit()
            cursor.close()
            logger.info("Successfully cleared existing data")

        except Exception as e:
            logger.error(f"Error clearing existing data: {e}")
            self.connection.rollback()
            raise

    def import_data(self, data_tuples: list, batch_size: int = 100) -> None:
        """Import data into the database using batch processing."""
        try:
            cursor = self.connection.cursor()

            insert_query = """
                INSERT INTO insurance_claims (
                    policy_id, claim_id, customer_age, customer_gender, customer_state,
                    vehicle_make, vehicle_model, vehicle_year, claim_date, claim_type,
                    claim_amount, deductible, claim_status, annual_premium, is_fraud
                ) VALUES %s
                ON CONFLICT (policy_id) DO UPDATE SET
                    claim_amount = EXCLUDED.claim_amount,
                    claim_status = EXCLUDED.claim_status,
                    annual_premium = EXCLUDED.annual_premium,
                    is_fraud = EXCLUDED.is_fraud;
            """

            # Import data in batches
            total_records = len(data_tuples)
            imported_count = 0

            for i in range(0, total_records, batch_size):
                batch = data_tuples[i:i + batch_size]
                execute_values(
                    cursor,
                    insert_query,
                    batch,
                    template=None,
                    page_size=batch_size
                )
                imported_count += len(batch)
                logger.info(f"Imported {imported_count}/{total_records} records")

            self.connection.commit()
            cursor.close()

            logger.info(f"Successfully imported {total_records} records")

        except Exception as e:
            logger.error(f"Error importing data: {e}")
            self.connection.rollback()
            raise

    def validate_import(self) -> None:
        """Validate the imported data."""
        try:
            cursor = self.connection.cursor()

            # Check record count
            cursor.execute("SELECT COUNT(*) FROM insurance_claims;")
            db_count = cursor.fetchone()[0]
            csv_count = len(self.df)

            logger.info(f"Records in database: {db_count}")
            logger.info(f"Records in CSV: {csv_count}")

            if db_count != csv_count:
                logger.warning(f"Record count mismatch! DB: {db_count}, CSV: {csv_count}")
            else:
                logger.info("✅ Record count validation passed")

            # Check for any obvious data issues
            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN claim_amount <= 0 THEN 1 END) as invalid_amounts,
                    COUNT(CASE WHEN customer_age < 18 OR customer_age > 100 THEN 1 END) as invalid_ages,
                    COUNT(CASE WHEN vehicle_year < 2000 OR vehicle_year > 2024 THEN 1 END) as invalid_years
                FROM insurance_claims;
            """)

            validation_result = cursor.fetchone()
            logger.info("Data validation results:")
            logger.info(f"  Total records: {validation_result[0]}")
            logger.info(f"  Invalid amounts: {validation_result[1]}")
            logger.info(f"  Invalid ages: {validation_result[2]}")
            logger.info(f"  Invalid years: {validation_result[3]}")

            cursor.close()

        except Exception as e:
            logger.error(f"Error validating import: {e}")

    def run_import(self, clear_existing: bool = False) -> None:
        """Main method to run the complete import process."""
        try:
            # Load and prepare data
            self.load_csv_data()
            data_tuples = self.prepare_data_for_import()

            # Connect to database
            self.connect_to_database()

            # Check if table exists
            if not self.check_table_exists():
                raise Exception("insurance_claims table does not exist. Please run init.sql first.")

            # Clear existing data if requested
            if clear_existing:
                existing_count = self.get_record_count()
                if existing_count > 0:
                    logger.info(f"Found {existing_count} existing records")
                    self.clear_existing_data()

            # Import data
            logger.info("Starting data import...")
            self.import_data(data_tuples)

            # Validate import
            self.validate_import()

            logger.info("🎉 Data import completed successfully!")

        except Exception as e:
            logger.error(f"Data import failed: {e}")
            raise
        finally:
            self.disconnect_from_database()


def get_database_config() -> dict:
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'insurance_claims'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }


def main(clear_existing_data_flag: bool = False, called_from_app: bool = False):
    """Main function to run the data import."""
    # Set up paths
    project_root = Path(__file__).parent.parent
    csv_path = project_root / "data" / "insurance_claims.csv"

    # Validate input file exists
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    # Get database configuration
    db_config = get_database_config()

    # Import data
    importer = CSVDataImporter(csv_path, db_config)

    try:
        # Ask user if they want to clear existing data, unless called from app
        should_clear = clear_existing_data_flag
        if not called_from_app and not clear_existing_data_flag:
            clear_input = input("Clear existing data before import? (y/N): ").lower()
            if clear_input.startswith('y'):
                should_clear = True
            elif clear_input and not clear_input.startswith('n'):
                logger.warning("Invalid input. Defaulting to not clearing data.")
                should_clear = False


        importer.run_import(clear_existing=should_clear)

        logger.info("\\\\n✅ Successfully imported insurance claims data!")
        logger.info(f"📁 Source file: {csv_path}")
        logger.info(f"🗄️ Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        if not called_from_app:
            print("\\\\n🚀 Next steps:")
            print("1. Verify data using your FastAPI application")
            print("2. Run queries against the imported data")
            print("3. Use the generated views for data analysis")

    except Exception as e:
        logger.error(f"Import process failed: {e}")
        if not called_from_app:
            sys.exit(1)
        else:
            raise # Re-raise for the application to handle

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import insurance claims data.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before import without prompting."
    )
    args = parser.parse_args()
    main(clear_existing_data_flag=args.clear)
