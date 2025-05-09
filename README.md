# Web Analysis and Test Automation Framework

A framework for analyzing websites, generating site maps, creating natural language test cases, and converting them to Selenium Python test scripts.

## Features

- **Website Analysis**: Scrapes website pages and generates a visual graph of the site structure using BSoup and NetworkX
- **Site Categorization**: Automatically determines the type of website based on content
- **Test Case Generation**: Creates natural language test cases tailored to the website type
- **Code Generation**: Converts test cases to executable Selenium Python scripts
- **Modern UI**: User-friendly interface with three main steps: Analysis, Test Generation, and Code Generation

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Follow the three steps in the UI:
   - Enter a website URL to analyze
   - Generate test cases based on the analysis
   - Convert test cases to Selenium Python code

## Project Structure

```
.
├── app
│   ├── api
│   │   └── routes.py         # API endpoints
│   ├── core
│   │   ├── web_analyzer.py   # Website scraping and analysis
│   │   ├── test_generator.py # Test case generation
│   │   └── code_generator.py # Selenium code generation
│   ├── static                # Static files
│   │   ├── code/             # Generated Python code
│   │   └── test_cases/       # Generated test cases
│   ├── templates             # HTML templates
│   │   └── index.html        # Main UI template
│   └── main.py               # FastAPI application
└── requirements.txt          # Project dependencies
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Beautiful Soup 4
- NetworkX
- Selenium
- Pyvis
- Matplotlib

## License

This project is licensed under the MIT License - see the LICENSE file for details. 