from django.db import connections
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)

def check_db_connection():
    try:
        db_conn = connections['default']
        db_conn.cursor()
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def get_connection_info():
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            
            return {
                "status": "connected",
                "version": version,
                "database": db_name
            }
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }