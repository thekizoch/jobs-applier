# jobs-applier

An open-source Python tool that automates LinkedIn Easy Apply job applications and optionally generates custom cover letters via LLM.

## Features
- Automated browser control (Playwright)
- Fetches LinkedIn job postings based on search criteria
- Applies using LinkedIn Easy Apply
- (Optional) LLM-powered cover letter generation
- Logging of application success/failure

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/jobs-applier.git
   ```

2. Install dependencies:
   ```bash
   cd jobs-applier
   pip install -r requirements.txt
   ```

3. Install Playwright drivers:
   ```bash
   playwright install
   ```

## Usage
1. Configure your settings:
   - Copy `config.yaml.example` to `config.yaml` and update with your preferences
   - Or use environment variables (see Configuration section)

2. Run:
   ```bash
   python -m jobs_applier.main
   ```

## Configuration
You can configure the application using either a `config.yaml` file or environment variables.

### Using config.yaml
```yaml
credentials:
  linkedin:
    email: your.email@example.com
    password: your_password
  openai:
    api_key: your_openai_key  # Optional, for cover letter generation

search_criteria:
  keywords: ["Software Engineer", "Python Developer"]
  location: "Remote"
  job_types: ["Full-time"]
  experience_level: ["Entry level", "Mid-Senior level"]
  date_posted: "Past Week"

application_settings:
  max_applications_per_run: 50
  wait_time_between_apps: [10, 30]  # Random wait between 10-30 seconds
  generate_cover_letters: true
```

### Using Environment Variables
Create a `.env` file in the root directory:
```env
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # Optional, for cover letter generation
```

## Project Structure
```
jobs-applier/
├── jobs_applier/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── browser_automation.py
│   ├── llm_integration.py
│   ├── logs.py
│   ├── utils.py
│   └── constants.py
├── tests/
│   ├── test_basic.py
│   ├── test_browser_flow.py
│   └── test_llm_integration.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── config.yaml
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
