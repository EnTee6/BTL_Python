#!/usr/bin/env python3
"""
Quick Start Guide - Player Analysis System
Execution script to run the complete pipeline
"""
import subprocess
import sys
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 {description}")
    logger.info(f"{'='*80}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Command failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def main():
    """Main execution flow"""
    
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*78 + "║")
    logger.info("║" + "  PREMIER LEAGUE 2024-2025 PLAYER ANALYSIS SYSTEM".center(78) + "║")
    logger.info("║" + "  Complete Data Pipeline Execution".center(78) + "║")
    logger.info("║" + " "*78 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    # Check prerequisites
    logger.info("\n📋 Checking prerequisites...")
    
    # Note: Using existing paths database instead of purely new
    if not os.path.exists('database'):
        os.makedirs('database')
        
    if not os.path.exists('output'):
        os.makedirs('output')
        
    if not os.path.exists('logs'):
        os.makedirs('logs')
        logger.info("  ✓ Directories ready")
    
    # Phase 1: Data Collection
    logger.info(f"\n{'─'*80}")
    logger.info("PHASE 1: WEB SCRAPING & DATA COLLECTION")
    logger.info(f"{'─'*80}")
    
    logger.info("\n📊 Step 1.1: Scraping fbref.com for player statistics...")
    logger.info("⚠️  This may take 10-20 minutes depending on internet speed")
    logger.info("   Implementing: Random delays, User-Agent rotation, retry logic")
    
    # Modified from 'src/' to use our existing directories
    fbref_ok = run_command(
        [sys.executable, 'scraper/fbref_scraper.py'],
        "Scraping fbref.com - Player Statistics"
    )
    
    if not fbref_ok:
        logger.warning("⚠️  fbref scraping failed. Check logs for details.")
        # Don't exit, continue with other phases
    
    logger.info("\n💶 Step 1.2: Scraping footballtransfers.com for market values...")
    logger.info("⚠️  This may take some time due to delays")
    logger.info("   Note: If site blocks you, check for CAPTCHA or increase delays in .env")
    
    transfer_ok = run_command(
        [sys.executable, 'scraper/transfer_scraper.py'],
        "Scraping footballtransfers.com - Transfer Values"
    )
    
    if not transfer_ok:
        logger.warning("⚠️  Transfer scraping failed. Check logs for details.")
    
    if not fbref_ok and not transfer_ok:
        logger.error("\n✗ Phase 1 completely failed. Proceeding with caution (using cached DB if any).")
    
    # Phase 2: Start API Server - Noticed user wants it to be manual step
    logger.info(f"\n{'─'*80}")
    logger.info("PHASE 2: API SERVER (Manual Step Required)")
    logger.info(f"{'─'*80}")
    
    logger.info("\n🌐 To start the API server, run in a NEW TERMINAL:")
    logger.info("   python api/app.py")
    
    # Phase 3: Statistical Analysis
    logger.info(f"\n{'─'*80}")
    logger.info("PHASE 3: STATISTICAL ANALYSIS")
    logger.info(f"{'─'*80}")
    
    stats_ok = run_command(
        [sys.executable, 'analysis/statistics.py'],
        "Calculating Per-Club Statistics"
    )
    
    if stats_ok:
        logger.info("✓ Statistics saved successfully.")
    
    # Phase 4: Player Valuation
    logger.info(f"\n{'─'*80}")
    logger.info("PHASE 4: PLAYER VALUATION METHOD")
    logger.info(f"{'─'*80}")
    
    valuation_ok = run_command(
        [sys.executable, 'analysis/valuation.py'],
        "Proposing Player Valuation Method"
    )
    
    if valuation_ok:
        logger.info("✓ Valuation report saved successfully.")
    
    # Phase 5: Clustering & PCA
    logger.info(f"\n{'─'*80}")
    logger.info("PHASE 5: CLUSTERING & DIMENSIONALITY REDUCTION")
    logger.info(f"{'─'*80}")
    
    clustering_ok = run_command(
        [sys.executable, 'analysis/clustering.py'],
        "K-means Clustering & PCA Analysis"
    )
    
    if clustering_ok:
        logger.info("✓ Clustering visualizations saved to output/")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("✓ EXECUTION COMPLETE")
    logger.info(f"{'='*80}")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
