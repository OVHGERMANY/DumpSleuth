"""
Interactive CLI for DumpSleuth
"""

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from pathlib import Path
import time
from typing import Optional, List


console = Console()


def show_banner():
    """Display the DumpSleuth banner"""
    banner = """
    ╔═══════════════════════════════════════════╗
    ║        DumpSleuth v2.0 - Memory Analysis  ║
    ║        Modern • Fast • Extensible         ║
    ╚═══════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold cyan"))


@click.group(invoke_without_command=True)
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
@click.pass_context
def cli(ctx, interactive):
    """DumpSleuth - Modern Memory Dump Analysis Toolkit"""
    if ctx.invoked_subcommand is None and interactive:
        interactive_mode()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def interactive_mode():
    """Run DumpSleuth in interactive mode"""
    show_banner()
    
    while True:
        console.print("\n[bold cyan]Main Menu[/bold cyan]")
        console.print("1. Analyze dump file")
        console.print("2. Batch analysis") 
        console.print("3. View reports")
        console.print("4. Configure settings")
        console.print("5. Plugin manager")
        console.print("6. Exit")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            analyze_interactive()
        elif choice == "2":
            batch_analysis_interactive()
        elif choice == "3":
            view_reports_interactive()
        elif choice == "4":
            configure_interactive()
        elif choice == "5":
            plugin_manager_interactive()
        elif choice == "6":
            if Confirm.ask("Are you sure you want to exit?"):
                console.print("[bold green]Thank you for using DumpSleuth![/bold green]")
                break


def analyze_interactive():
    """Interactive dump analysis"""
    console.print("\n[bold yellow]Dump Analysis[/bold yellow]")
    
    # File selection
    dump_file = Prompt.ask("Enter dump file path")
    if not Path(dump_file).exists():
        console.print("[red]File not found![/red]")
        return
    
    # Analysis options
    console.print("\n[bold]Analysis Options:[/bold]")
    extract_strings = Confirm.ask("Extract strings?", default=True)
    find_urls = Confirm.ask("Find URLs and network data?", default=True)
    registry_analysis = Confirm.ask("Analyze registry keys?", default=True)
    generate_timeline = Confirm.ask("Generate timeline?", default=False)
    
    # Output format
    console.print("\n[bold]Output Format:[/bold]")
    output_format = Prompt.ask(
        "Select format",
        choices=["html", "json", "markdown", "all"],
        default="html"
    )
    
    # Run analysis with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing dump file...", total=100)
        
        # Import analyzer
        from ..core.analyzer import DumpAnalyzer
        
        progress.update(task, advance=20, description="Loading file...")
        analyzer = DumpAnalyzer(dump_file)
        
        # Configure plugins based on options
        if extract_strings:
            analyzer.enable_plugin("string_extractor")
        if find_urls:
            analyzer.enable_plugin("network_analyzer") 
        if registry_analysis:
            analyzer.enable_plugin("registry_analyzer")
            
        progress.update(task, advance=20, description="Running analysis...")
        results = analyzer.analyze()
        
        progress.update(task, advance=20, description="Generating report...")
        report_path = results.save(format=output_format)
        
        progress.update(task, advance=40, description="Finalizing...")
    
    # Show results summary
    console.print("\n[bold green]Analysis Complete![/bold green]")
    
    results_table = Table(title="Analysis Summary")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="magenta")
    
    # Get actual results from analysis
    summary = results.get_summary()
    for key, value in summary.items():
        results_table.add_row(key, str(value))
    
    results_table.add_row("Report location", str(report_path))
    console.print(results_table)
    
    if Confirm.ask("\nView detailed report?"):
        # Show preview of report
        console.print("\n[bold]Report Preview:[/bold]")
        preview = results.get_preview()
        console.print(Markdown(preview))


@click.command()
@click.argument('dump_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output directory', default='reports')
@click.option('--format', '-f', type=click.Choice(['html', 'json', 'markdown', 'all']), default='html')
@click.option('--plugins', '-p', multiple=True, help='Plugins to use')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(dump_file, output, format, plugins, config, quiet, verbose):
    """Analyze a memory dump file"""
    if not quiet:
        show_banner()
        
    console.print(f"[bold green]Analyzing:[/bold green] {dump_file}")
    
    # Import and run analyzer
    from ..core.analyzer import DumpAnalyzer
    
    analyzer = DumpAnalyzer(dump_file, config=config)
    
    # Enable specified plugins
    for plugin in plugins:
        analyzer.enable_plugin(plugin)
        
    # Run analysis
    with console.status("Running analysis..."):
        results = analyzer.analyze()
        
    # Save results
    output_path = results.save(output_dir=output, format=format)
    
    if not quiet:
        console.print(f"[bold green]✓[/bold green] Analysis complete!")
        console.print(f"[bold]Report saved:[/bold] {output_path}")


@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.dmp', help='File pattern to match')
@click.option('--recursive', '-r', is_flag=True, help='Search recursively')
@click.option('--output', '-o', help='Output directory', default='batch_reports')
@click.option('--parallel', '-j', type=int, help='Number of parallel jobs')
def batch(directory, pattern, recursive, output, parallel):
    """Batch analyze multiple dump files"""
    console.print(f"[bold cyan]Batch Analysis[/bold cyan]")
    console.print(f"Directory: {directory}")
    console.print(f"Pattern: {pattern}")
    
    # Find files
    path = Path(directory)
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
        
    console.print(f"Found {len(files)} files to analyze")
    
    if not files:
        console.print("[yellow]No files found matching pattern[/yellow]")
        return
        
    # Import analyzer
    from ..core.analyzer import DumpAnalyzer
    from concurrent.futures import ProcessPoolExecutor, as_completed
    
    # Determine number of workers
    import multiprocessing
    workers = parallel or min(len(files), multiprocessing.cpu_count())
    
    # Analyze each file
    with Progress(console=console) as progress:
        task = progress.add_task("Analyzing dumps...", total=len(files))
        
        if workers > 1:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(analyze_file, file, output): file 
                    for file in files
                }
                
                for future in as_completed(futures):
                    file = futures[future]
                    try:
                        result = future.result()
                        progress.update(task, description=f"Completed {file.name}")
                    except Exception as e:
                        console.print(f"[red]Error analyzing {file}: {e}[/red]")
                    progress.advance(task)
        else:
            # Sequential processing
            for file in files:
                progress.update(task, description=f"Analyzing {file.name}")
                try:
                    analyze_file(file, output)
                except Exception as e:
                    console.print(f"[red]Error analyzing {file}: {e}[/red]")
                progress.advance(task)
            
    console.print("[bold green]✓[/bold green] Batch analysis complete!")


def analyze_file(file_path: Path, output_dir: str) -> str:
    """Analyze a single file (for batch processing)"""
    from ..core.analyzer import DumpAnalyzer
    
    analyzer = DumpAnalyzer(str(file_path))
    results = analyzer.analyze()
    return results.save(output_dir=output_dir)


def batch_analysis_interactive():
    """Interactive batch analysis"""
    console.print("\n[bold yellow]Batch Analysis[/bold yellow]")
    
    directory = Prompt.ask("Enter directory path")
    if not Path(directory).exists():
        console.print("[red]Directory not found![/red]")
        return
        
    pattern = Prompt.ask("File pattern", default="*.dmp")
    recursive = Confirm.ask("Search recursively?", default=True)
    
    # Find files
    path = Path(directory)
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
        
    console.print(f"\nFound {len(files)} files:")
    for i, file in enumerate(files[:10]):
        console.print(f"  {i+1}. {file.name}")
    if len(files) > 10:
        console.print(f"  ... and {len(files) - 10} more")
        
    if files and Confirm.ask("\nProceed with analysis?"):
        batch(directory, pattern, recursive, "batch_reports", None)


def view_reports_interactive():
    """Interactive report viewer"""
    console.print("\n[bold yellow]Report Viewer[/bold yellow]")
    
    reports_dir = Path("reports")
    if not reports_dir.exists():
        console.print("[yellow]No reports directory found[/yellow]")
        return
        
    # List available reports
    reports = list(reports_dir.glob("**/*.html")) + \
              list(reports_dir.glob("**/*.json")) + \
              list(reports_dir.glob("**/*.md"))
              
    if not reports:
        console.print("[yellow]No reports found[/yellow]")
        return
        
    console.print("\nAvailable reports:")
    for i, report in enumerate(reports[:20]):
        console.print(f"  {i+1}. {report.name}")
        
    if len(reports) > 20:
        console.print(f"  ... and {len(reports) - 20} more")
        
    try:
        choice = int(Prompt.ask("\nSelect report number")) - 1
        if 0 <= choice < len(reports):
            report_path = reports[choice]
            
            # Open report based on type
            import webbrowser
            import subprocess
            import platform
            
            if report_path.suffix == '.html':
                webbrowser.open(str(report_path))
            else:
                # Open with default application
                if platform.system() == 'Windows':
                    subprocess.run(['start', str(report_path)], shell=True)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', str(report_path)])
                else:
                    subprocess.run(['xdg-open', str(report_path)])
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")


def configure_interactive():
    """Interactive configuration"""
    console.print("\n[bold yellow]Configuration[/bold yellow]")
    
    from ..core.config import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    console.print("\nCurrent configuration:")
    console.print(f"  String min length: {config.analysis.string_min_length}")
    console.print(f"  Max file size: {config.analysis.max_file_size} MB")
    console.print(f"  Output directory: {config.output.output_dir}")
    console.print(f"  Output formats: {', '.join(config.output.formats)}")
    console.print(f"  Enabled plugins: {', '.join(config.plugins.enabled) or 'None'}")
    
    if Confirm.ask("\nModify configuration?"):
        # String settings
        config.analysis.string_min_length = int(
            Prompt.ask("String minimum length", default=str(config.analysis.string_min_length))
        )
        
        # Output settings  
        config.output.output_dir = Prompt.ask(
            "Output directory", default=config.output.output_dir
        )
        
        # Save configuration
        if Confirm.ask("\nSave configuration?"):
            config_manager.save_config()
            console.print("[green]Configuration saved![/green]")


def plugin_manager_interactive():
    """Interactive plugin manager"""
    console.print("\n[bold yellow]Plugin Manager[/bold yellow]")
    
    from ..core.plugin import PluginManager
    from ..core.config import ConfigManager
    
    plugin_mgr = PluginManager()
    config_mgr = ConfigManager()
    config = config_mgr.get_config()
    
    # Load plugins
    plugin_dir = Path(config.plugins.plugin_dir)
    if plugin_dir.exists():
        plugin_mgr.load_plugins_from_directory(plugin_dir)
    
    # Show installed plugins
    plugins_table = Table(title="Installed Plugins")
    plugins_table.add_column("Name", style="cyan")
    plugins_table.add_column("Version", style="magenta") 
    plugins_table.add_column("Status", style="green")
    plugins_table.add_column("Description")
    
    for name, plugin in plugin_mgr.plugins.items():
        metadata = plugin.get_metadata()
        status = "Enabled" if name in config.plugins.enabled else "Disabled"
        status_color = "green" if status == "Enabled" else "red"
        
        plugins_table.add_row(
            metadata.name,
            metadata.version,
            f"[{status_color}]{status}[/{status_color}]",
            metadata.description
        )
    
    console.print(plugins_table)
    
    # Plugin actions
    console.print("\n[bold]Actions:[/bold]")
    console.print("1. Enable/Disable plugin")
    console.print("2. View plugin details")
    console.print("3. Back to main menu")
    
    choice = Prompt.ask("Select action", choices=["1", "2", "3"])
    
    if choice == "1":
        plugin_name = Prompt.ask("Enter plugin name")
        if plugin_name in plugin_mgr.plugins:
            if plugin_name in config.plugins.enabled:
                config.plugins.enabled.remove(plugin_name)
                console.print(f"[yellow]Disabled {plugin_name}[/yellow]")
            else:
                config.plugins.enabled.append(plugin_name)
                console.print(f"[green]Enabled {plugin_name}[/green]")
                
            if Confirm.ask("Save configuration?"):
                config_mgr.save_config()
        else:
            console.print("[red]Plugin not found[/red]")
            
    elif choice == "2":
        plugin_name = Prompt.ask("Enter plugin name")
        if plugin_name in plugin_mgr.plugins:
            plugin = plugin_mgr.plugins[plugin_name]
            metadata = plugin.get_metadata()
            
            console.print(f"\n[bold]Plugin: {metadata.name}[/bold]")
            console.print(f"Version: {metadata.version}")
            console.print(f"Author: {metadata.author}")
            console.print(f"Description: {metadata.description}")
            console.print(f"Tags: {', '.join(metadata.tags)}")
            console.print(f"Supported formats: {', '.join(plugin.get_supported_formats())}")


# Add commands to CLI group
cli.add_command(analyze)
cli.add_command(batch)


if __name__ == '__main__':
    cli()