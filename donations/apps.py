from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donations'
    
    def ready(self):
        """
        Called when Django is ready - auto-initialize recorder if needed
        """
        try:
            # Import here to avoid circular imports
            from .models import AutoRecordingSettings
            from cognizanttrust.crypto_utils import credential_manager
            from web3_integration.auto_recorder import auto_recorder
            
            # Check if auto mode is enabled and credentials exist
            try:
                settings = AutoRecordingSettings.get_settings()
                
                if (settings.is_automatic_mode and 
                    settings.credentials_configured and 
                    credential_manager.credentials_exist()):
                    
                    logger.info("🚀 Auto-initializing blockchain recorder on startup...")
                    
                    # Try to auto-initialize the recorder using cached session password
                    if auto_recorder.auto_initialize():
                        logger.info("✅ Auto-recorder successfully initialized from cached session!")
                    else:
                        logger.info("ℹ️ Auto-initialization requires user to toggle auto mode first")
                        logger.info("💡 Session will persist across Django restarts once toggled")
                        
                else:
                    if not settings.is_automatic_mode:
                        logger.info("ℹ️ Auto-mode disabled - skipping auto-initialization")
                    elif not settings.credentials_configured:
                        logger.info("ℹ️ No credentials configured - skipping auto-initialization")
                    elif not credential_manager.credentials_exist():
                        logger.info("ℹ️ Credentials file missing - skipping auto-initialization")
                    
            except Exception as db_error:
                # Database might not be migrated yet
                logger.info(f"ℹ️ Skipping auto-initialization: {db_error}")
                
        except ImportError as e:
            logger.warning(f"⚠️ Could not auto-initialize recorder: {e}")
        except Exception as e:
            logger.error(f"❌ Error during auto-initialization: {e}")
        
        # Start comprehensive background processor (3 threads) - only if auto mode enabled
        try:
            from .background_processor import start_background_processor
            from .models import AutoRecordingSettings
            
            # Only start if auto mode is properly configured
            settings = AutoRecordingSettings.get_settings()
            if settings.is_automatic_mode:
                start_background_processor()
                logger.info("🚀 Background processor (3 threads) started - auto mode enabled")
            else:
                logger.info("⏸️ Background processor not started - auto mode disabled")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not start background processor: {e}")