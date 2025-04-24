import os
import logging
import shutil
from pathlib import Path

logger = logging.getLogger("web-analysis-framework.utils")

def ensure_directories():
    """Create all necessary directories for the application"""
    try:
        # Create all the required directories
        dirs = [
            "app/static",
            "app/static/code",
            "app/static/test_cases",
            "app/static/pyvis_libs",
            "app/static/pyvis_libs/lib",
            "app/static/pyvis_libs/lib/bindings",
            "app/static/pyvis_libs/lib/network"
        ]
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created or verified: {directory}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {str(e)}", exc_info=True)
        return False

def copy_pyvis_assets():
    """Try to copy pyvis assets to our static directory"""
    try:
        import pyvis
        pyvis_dir = os.path.dirname(pyvis.__file__)
        
        # Check if the pyvis static directory exists
        pyvis_static = os.path.join(pyvis_dir, "static")
        if os.path.exists(pyvis_static):
            # Copy the needed files
            for subdir in ["lib/bindings", "lib/network"]:
                src_dir = os.path.join(pyvis_static, subdir)
                dst_dir = os.path.join("app/static/pyvis_libs", subdir)
                
                if os.path.exists(src_dir):
                    # Copy all files from the directory
                    for file in os.listdir(src_dir):
                        src_file = os.path.join(src_dir, file)
                        dst_file = os.path.join(dst_dir, file)
                        
                        if os.path.isfile(src_file):
                            shutil.copy2(src_file, dst_file)
                            logger.info(f"Copied pyvis asset: {dst_file}")
            
            logger.info("Successfully copied pyvis assets")
            return True
        else:
            logger.warning(f"Pyvis static directory not found at {pyvis_static}")
            return False
    except Exception as e:
        logger.error(f"Error copying pyvis assets: {str(e)}", exc_info=True)
        return False

def setup():
    """Main setup function"""
    logger.info("Starting directory setup")
    dirs_created = ensure_directories()
    
    if dirs_created:
        assets_copied = copy_pyvis_assets()
        if not assets_copied:
            logger.warning("Could not copy pyvis assets, will use CDN fallback")
    
    logger.info("Directory setup complete")
    return dirs_created 