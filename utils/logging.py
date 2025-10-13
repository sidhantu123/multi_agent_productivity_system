"""Logging configuration for the Gmail agent"""

import os
import logging
from datetime import datetime


def setup_logging():
    """Setup comprehensive logging for debugging memory issues"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/langgraph_memory_debug_{timestamp}.log"
    
    # Configure logging (file only; no console output)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file)
        ]
    )
    
    # Create specific loggers
    logger = logging.getLogger('langgraph_memory')
    logger.setLevel(logging.DEBUG)
    
    # Log startup note to file only
    logger.info(f"Debug logging enabled - Log file: {log_file}")
    return logger


def get_logger():
    """Get the langgraph memory logger"""
    return logging.getLogger('langgraph_memory')

