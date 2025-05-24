import csv
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

class CSVDataImporter:
    def __init__(self, csv_file: str, db_connection):
        self.csv_file = csv_file
        self.connection = db_connection

    def load_csv_data(self) -> None:
        """Load data from the CSV file into memory."""
        try:
            with open(self.csv_file, 'r') as file:
                reader = csv.reader(file)
                # Skip header row
                next(reader)
                self.data = [row for row in reader]
            logger.info(f"Loaded {len(self.data)} records from {self.csv_file}")
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise

    def prepare_data_for_import(self) -> List[dict]:
        """Prepare and return data for import into the database."""
        try:
            data_records = []
            for row in self.data:
                record = {
                    'policy_id': row[0],  # Keep as string
                    'claim_id': row[1],   # Keep as string
                    'customer_age': int(row[2]),
                    'customer_gender': row[3],
                    'customer_state': row[4],
                    'vehicle_make': row[5],
                    'vehicle_model': row[6],
                    'vehicle_year': int(row[7]),
                    'claim_date': datetime.strptime(row[8], '%Y-%m-%d %H:%M:%S.%f'),  # Include time
                    'claim_type': row[9],
                    'claim_amount': float(row[10]),
                    'deductible': int(row[11]),  # Convert to int as per model
                    'claim_status': row[12],
                    'annual_premium': float(row[13]),
                    'is_fraud': row[14].lower() == 'true'  # Better boolean conversion
                }
                data_records.append(record)
            logger.info(f"Prepared {len(data_records)} records for import")
            return data_records
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise

    def get_record_count(self) -> int:
        """Return the number of records in the insurance_claims table."""
        try:
            from sqlmodel import Session, select
            from app.models.database import InsuranceClaim

            with Session(self.connection) as session:
                result = session.exec(select(InsuranceClaim)).all()
                count = len(result)
                logger.info(f"Current record count: {count}")
                return count
        except Exception as e:
            logger.error(f"Error getting record count: {e}")
            raise

    def import_data(self, data_records: list, batch_size: int = 100) -> None:
        """Import data into the database using SQLAlchemy."""
        try:
            from sqlmodel import Session
            from app.models.database import InsuranceClaim

            with Session(self.connection) as session:
                for i in range(0, len(data_records), batch_size):
                    batch = data_records[i:i + batch_size]

                    for record in batch:
                        # Create InsuranceClaim object
                        claim = InsuranceClaim(**record)

                        # Use merge to handle conflicts (update if exists, insert if not)
                        session.merge(claim)

                    session.commit()
                    logger.info(f"Imported batch {i // batch_size + 1} ({len(batch)} records)")

            logger.info("Data import completed successfully")
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            raise

    def run_import(self, clear_existing: bool = False) -> None:
        """Main method to run the complete import process."""
        try:
            # Load and prepare data
            self.load_csv_data()
            data_records = self.prepare_data_for_import()

            # Clear existing data if requested
            if clear_existing:
                logger.info("Clearing existing data from the database")
                from sqlmodel import Session
                from app.models.database import InsuranceClaim

                with Session(self.connection) as session:
                    # Delete all existing records
                    session.query(InsuranceClaim).delete()
                    session.commit()

            # Import new data
            self.import_data(data_records)

            logger.info("Data import completed successfully")
        except Exception as e:
            logger.error(f"Error during import process: {e}")
            raise

