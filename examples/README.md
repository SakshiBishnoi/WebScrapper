# Web Scraper CLI Usage Examples

This directory contains examples for using the Web Scraper CLI tool. The CLI interface allows you to scrape websites without using the GUI, which will be implemented in Phase 3.

## Basic Usage

### Interactive Mode

The easiest way to use the scraper is in interactive mode, which will prompt you for all required information:

```bash
python main.py --interactive
```

### Command Line Arguments

You can also provide all parameters directly via command line:

```bash
python main.py -u https://example.com -s "{\"title\": \"h1\", \"paragraphs\": \"p\"}" -f json
```

### Using a Selectors File

For more complex scraping tasks, you can define your selectors in a JSON file (see `selectors.json` in this directory):

```bash
python main.py -u https://example.com -s examples/selectors.json -o results -f csv
```

## Available Options

- `-u, --url`: URL to scrape
- `-s, --selectors`: JSON string or path to JSON file with CSS selectors
- `-o, --output`: Output file path (without extension)
- `-f, --format`: Output format (csv or json, default: json)
- `-d, --dynamic`: Use dynamic scraper for JavaScript-heavy sites
- `-c, --config`: Path to custom configuration file
- `--interactive`: Run in interactive mode

## Selector Format

Selectors should be provided as a JSON object where:
- Keys are the names you want to give to the extracted data
- Values are CSS selectors to locate elements on the page

Example:
```json
{
    "title": "h1",
    "meta_description": "meta[name='description']",
    "paragraphs": "p"
}
```

## Output

The scraper will export data to the specified format and display a preview of the extracted data in the console.