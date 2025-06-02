"""
Custom Plugin Example for DumpSleuth

This example shows how to create a custom plugin to extend DumpSleuth's capabilities.
"""

from typing import Dict, Any
from dumpsleuth import DumpAnalyzer, AnalyzerPlugin, DumpData


class EmailExtractorPlugin(AnalyzerPlugin):
    """Custom plugin to extract email addresses from memory dumps."""
    
    def get_name(self) -> str:
        return "email_extractor"
        
    def get_description(self) -> str:
        return "Extracts email addresses from memory dumps"
        
    def analyze(self, dump_data: DumpData) -> Dict[str, Any]:
        """Extract email addresses from the dump."""
        import re
        
        print("Extracting email addresses...")
        
        # Email regex pattern
        email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        emails = set()
        
        # Read dump in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        offset = 0
        file_size = dump_data.metadata.get('file_size', 0)
        
        while offset < file_size:
            # Read chunk
            chunk = dump_data.read(offset, chunk_size)
            if not chunk:
                break
                
            # Find emails in chunk
            text = chunk.decode('utf-8', errors='ignore')
            found_emails = email_pattern.findall(text)
            emails.update(found_emails)
            
            offset += chunk_size
            
        # Create results
        email_list = sorted(list(emails))
        
        return {
            'emails': [
                {'address': email, 'domain': email.split('@')[1]}
                for email in email_list
            ],
            'summary': {
                'total_emails': len(email_list),
                'unique_domains': len(set(email.split('@')[1] for email in email_list))
            }
        }


def main():
    # Create analyzer
    dump_file = "path/to/your/dump.dmp"
    analyzer = DumpAnalyzer(dump_file)
    
    # Add our custom plugin
    email_plugin = EmailExtractorPlugin()
    analyzer.add_plugin(email_plugin)
    
    # Run analysis
    print("Running analysis with custom plugin...")
    results = analyzer.analyze()
    
    # Check email results
    email_results = results.results.get('email_extractor', {})
    if email_results:
        print(f"\nFound {email_results['summary']['total_emails']} email addresses")
        print(f"From {email_results['summary']['unique_domains']} unique domains")
        
        # Show first 10 emails
        print("\nFirst 10 emails found:")
        for email_info in email_results['emails'][:10]:
            print(f"  - {email_info['address']}")
    
    # Save report
    results.save("custom_analysis_report.html")
    print("\nReport saved!")


if __name__ == "__main__":
    main() 