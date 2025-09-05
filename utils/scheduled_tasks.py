import logging
import threading
from typing import Dict, Optional
from core.rss_processor import JiraRSSProcessor

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """
    Manages background tasks for the application.
    Ensures only one instance of each task is running.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackgroundTaskManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._tasks = {}
        self._rss_processor = None
        logger.info("Background Task Manager initialized")
    
    def start_rss_sync(self, db_path: str = "activity_metrics.db") -> bool:
        """
        Start the RSS synchronization background task.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            if 'rss_sync' in self._tasks and self._tasks['rss_sync'].is_running:
                logger.warning("RSS sync already running")
                return False
                
            try:
                self._rss_processor = JiraRSSProcessor(db_path=db_path)
                self._rss_processor.start_background_sync()
                self._tasks['rss_sync'] = self._rss_processor
                logger.info("RSS sync started successfully")
                return True
            except Exception as e:
                logger.exception(f"Failed to start RSS sync: {str(e)}")
                return False
    
    def stop_rss_sync(self) -> bool:
        """
        Stop the RSS synchronization background task.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        with self._lock:
            if 'rss_sync' not in self._tasks or not self._tasks['rss_sync']:
                logger.warning("RSS sync not running")
                return False
                
            try:
                self._rss_processor.stop_background_sync()
                self._tasks.pop('rss_sync')
                logger.info("RSS sync stopped successfully")
                return True
            except Exception as e:
                logger.exception(f"Failed to stop RSS sync: {str(e)}")
                return False
    
    def get_rss_processor(self) -> Optional[JiraRSSProcessor]:
        """
        Get the RSS processor instance.
        
        Returns:
            JiraRSSProcessor instance or None if not running
        """
        return self._rss_processor
    
    def shutdown(self):
        """Stop all background tasks"""
        with self._lock:
            for task_name, task in list(self._tasks.items()):
                try:
                    if hasattr(task, 'stop_background_sync'):
                        task.stop_background_sync()
                    logger.info(f"Stopped {task_name}")
                except Exception as e:
                    logger.error(f"Error stopping {task_name}: {str(e)}")
            
            self._tasks.clear()
            logger.info("All background tasks stopped")


# Singleton instance
task_manager = BackgroundTaskManager()
