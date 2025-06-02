#!/usr/bin/env python3
"""
Test script to verify encoding works properly
"""

import sys
import os

def test_console_output():
    """Test various output formats"""
    
    print("Testing console output formats...")
    print("=" * 60)
    
    # Test ASCII banner
    print("ASCII Banner:")
    banner = """
================================================================
                     DUMP SLEUTH
                Memory Dump Analysis
================================================================
    """
    print(banner)
    
    # Test section headers
    print(">> Section Headers:")
    print("  >> Basic File Information")
    print("  >> Memory Structure Analysis") 
    print("  >> Extracting Strings")
    print("  >> Pattern Recognition")
    print("  >> Generating Report")
    
    # Test status messages
    print("\n>> Status Messages:")
    print("  >> Found 234 unique strings")
    print("  >> Analysis Complete!")
    print("  >> Results saved in: reports")
    print("  >> Check the generated report for detailed findings!")
    
    # Test error messages
    print("\n>> Error Messages:")
    print("  ERROR: No .dmp files found in current directory!")
    print("  TIP: Make sure your dump file is in the same folder as this script.")
    print("  ERROR: Invalid selection!")
    
    print("\n" + "=" * 60)
    print("Encoding test completed successfully!")
    print("If you can see this message properly, the encoding fix worked!")

if __name__ == "__main__":
    test_console_output() 