# jobs-applier

An open-source Python tool that automates LinkedIn Easy Apply job applications and optionally generates custom cover letters via LLM.

## Features
- Automated browser control (Playwright)
- Fetches LinkedIn job postings based on search criteria
- Applies using LinkedIn Easy Apply
- (Optional) LLM-powered cover letter generation
- Logging of application success/failure

## Installation

1. Install `uv` if you haven't already:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/your-username/jobs-applier.git
   cd jobs-applier
   ```

3. Create virtual environment and install dependencies using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   
   uv pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Configuration

You'll need to set up your configuration before running. Copy the example config and modify it:

```bash
cp config.example.yaml config.yaml
```

Then edit `config.yaml` with your settings:

```yaml
linkedin:
  email: "your.email@example.com"    # Your LinkedIn email
  password: "your_password"          # Your LinkedIn password

search:
  keywords: "Software Engineer"      # Your job search keywords
  location: "Remote"                # Or your preferred location
  max_applications: 10              # Start small for testing
  experience_levels:
    - "ENTRY_LEVEL"
    - "ASSOCIATE"
  job_types:
    - "FULL_TIME"
  date_posted: "Past Week"

llm:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"      # Will be read from .env file
  enabled: true                      # Set false to skip cover letters

user_profile:
  full_name: "Your Name"
  phone: "Your Phone"
  resume_path: "./data/resume.pdf"   # Path to your resume
  summary: "Your professional summary..."
```

## Usage

1. Make sure your virtual environment is activated:
   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

2. Run the application:
   ```bash
   python -m jobs_applier.main
   ```

## Project Structure
```
jobs-applier/
├── jobs_applier/          # Main package
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration handling
│   ├── browser_automation.py
│   ├── llm_integration.py
│   ├── logs.py
│   ├── utils.py
│   └── constants.py
├── tests/                # Test suite
├── data/                 # Store your resume here
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── config.yaml
```

## Development

To set up for development:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Run tests:
```bash
pytest
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
