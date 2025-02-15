1. Overview
Product Name: jobs-applier
Primary Goal: Automatically apply to job postings on LinkedIn (via LinkedIn Easy Apply), optionally generating a customized cover letter when required, using an LLM for content generation.
1.1 Purpose
Job seekers often spend a significant amount of time manually searching for jobs, filtering results, and filling out repetitive information for each application. “jobs-applier” aims to streamline this workflow by:
Taking in high-level job search parameters (keywords, location, remote filters, etc.).
Automating LinkedIn Easy Apply submission flows.
Generating on-demand cover letters (only if needed) through an LLM.
1.2 Scope
The scope of “jobs-applier” is limited to LinkedIn Easy Apply jobs to avoid complex multi-website integrations. Future expansions might include other job sites or advanced flows, but the initial MVP focuses on:
Searching LinkedIn for jobs given some set of filters.
Iterating over the search results.
Automatically clicking “Easy Apply” and completing all required form fields, including uploading user assets (CV, resume, personal details).
If a cover letter is required, calling an LLM to generate one in real-time, then inserting it in the application form.
2. User Personas & Use Cases
2.1 User Personas
Frequent Job Seeker (“Alex”)
Searching for multiple roles at once across various locations or with “Remote” filter.
Wants to send out large volume of applications quickly.
May require an on-the-fly generated cover letter for certain roles.
Passive Job Seeker (“Jordan”)
Occasionally looks for new opportunities but doesn’t want to spend hours applying.
Wants a quick method to shoot applications to roles that meet basic criteria.
High-volume Recruiter / Agency Staff
Might need to apply to multiple roles on behalf of clients.
Possibly less common but still valuable scenario.
2.2 Use Cases
Basic Easy Apply
User enters keywords (e.g., “Software Engineer”, “Data Scientist”), location (e.g., “Remote”), job type filters, and the application automatically:
Loads LinkedIn search results matching the criteria.
Iterates through postings with “Easy Apply” available.
Fills out user’s stored personal information.
Submits application.
Cover Letter Generation
Certain “Easy Apply” flows optionally ask for a cover letter. The system:
Scrapes the job title, job description, and relevant company details.
Sends these details + the user’s profile to an LLM prompt.
Receives the tailored cover letter text and inserts it into the application.
Resume / CV Upload
The system must handle uploading a standard user resume/CV file, or possibly multiple versions based on the job category.
Multi-Session / Multi-Profile
Optionally handle multiple user accounts or personal info sets. (Future extension.)
3. Functional Requirements
Search & Filter
Accept text-based search terms (e.g., “Machine Learning Engineer”).
Accept location (e.g., “Remote”, “Honolulu”, “San Francisco”).
Accept additional LinkedIn filters (e.g., “Full-time”, “Entry level/Mid level/Senior level”, “Company size”, “Posted date”).
Automated Browser Control
Use a library such as Playwright, Puppeteer, or Selenium to open LinkedIn, log in as the user, and navigate to job search results.
The tool should robustly handle dynamic page load, scrolling, and pagination.
Application Flow
Detect “Easy Apply” button on job postings.
Click it and fill out all required fields from the user’s saved profile data.
If a prompt for a cover letter appears, generate it using an LLM.
Upload resumes, references, or any other documents as required by the job posting’s flow.
Submit the application.
Log result (success/failure, job title, company name, date/time).
Resume & Profile Handling
Store user’s basic details (name, email, phone, location, etc.) in a configurable file or secure settings.
Allow uploading a CV/resume in PDF or DOCX format.
LLM Integration for Cover Letters
Connect to an LLM API (e.g., OpenAI’s GPT, Anthropic Claude, or similar) with a configurable endpoint/key.
Input:
Job Title, Company Name, Job Description text from the posting.
(Optional) user’s personal summary or unique achievements.
Output:
A short customized cover letter text.
Insert the result into the relevant field in the Easy Apply form.
Logging & Error Handling
Maintain logs of each job posting’s success or failure.
In case of an error (e.g., mandatory question not answered, application flow changes), log the error reason and skip to the next job.
Rate Limiting / Throttling
Include a mechanism to avoid applying too quickly (risk of LinkedIn detection or account flags).
Configurable intervals between applications (e.g., 10-30 seconds random wait).
Configuration
A config file (YAML, JSON, or environment variables) to store:
LinkedIn credentials (could also be in a secure store).
LLM API keys.
Rate-limit/timeouts.
Default user info (address, phone, etc.).
Searching parameters (filters, location, etc.).
CLI or GUI
MVP: Command-line Interface for easy usage.
Potential future extension: Simple web-based UI for less technical users.
4. Non-Functional Requirements
Reliability
Should handle LinkedIn’s typical daily usage patterns without crashing or skipping steps.
Recover gracefully if the page fails to load or if LinkedIn’s layout changes slightly.
Performance
The system should be able to apply to a large number of jobs without noticeable slowdowns.
However, do not exceed typical daily usage limits to avoid having the account locked or flagged.
Security
Credentials and sensitive data (resumes, personal details, LLM API keys) must be stored securely.
Provide instructions or examples for safely storing environment variables or encryption.
Maintainability
Code should be modular, with well-documented methods for browser automation, LLM integration, and config management.
Clear error logs and debug logs to help with troubleshooting.
Extensibility
The system design should allow adding new filters or data points easily.
Possibly allow plug-and-play with different LLMs or different job boards.
Open Source Compliance
Use MIT, Apache, or similar permissive license.
Properly attribute any libraries or third-party code used.
5. Proposed Technical Approach
5.1 Architecture
Core Modules
Browser Automation Module
Manages all interaction with LinkedIn (search, pagination, form filling).
Data Storage / Config Module
Manages user credentials, resume files, filters, and LLM settings.
LLM Module
Connects to an LLM endpoint with a well-structured prompt.
Receives the generated text for the cover letter.
Application Orchestrator
High-level logic controlling the flow: read config -> open LinkedIn -> apply to jobs -> log results.
Logging Module
Writes to console, file, or remote logging service for success/failure events.
Workflow Example
Initialize
Read user configuration (LinkedIn credentials, search keywords, location, filters).
Launch headless or non-headless browser with user session or credentials.
Login & Search
Navigate to LinkedIn, perform login, wait for completion.
Perform job search with specified keywords, filters.
Iterate Job Postings
For each job in the search results:
Check if “Easy Apply” is available.
If yes, open the job posting detail, click “Easy Apply.”
Fill in all required fields from the user’s data.
If a cover letter is required, use LLM integration to generate text.
Submit.
Log success/failure.
Wait a random time interval (e.g., 10–30 seconds) before moving to the next job.
Cover Letter Generation
Query the job title, company name, and job description.
Prompt the LLM with “Generate a short cover letter for {job title at company} referencing these job requirements: {job description} and my background: {user summary}.”
Wait for LLM response; insert text.
Exit or Repeat
Once no more job postings match the criteria or user stops the process, log out or close the browser session.
5.2 Technologies & Tools
Language: Python, Node.js, or similar (Python + Playwright or Node.js + Puppeteer are popular combos).
Browser Automation:
Playwright (Python or Node.js).
Alternatively, Puppeteer or Selenium.
LLM Integration:
OpenAI GPT / Anthropics Claude / etc.
Using official SDK or REST API calls.
Configuration Management:
dotenv files or YAML/JSON config for storing secrets and user data.
Logging:
Basic logging to console + optional text file.
Potential use of libraries like winston (Node.js) or logging (Python).
6. Detailed Feature Specifications
6.1 Command-line Interface (CLI)
Commands:
jobs-applier config — Launches interactive config to set LinkedIn username, password, LLM API key, personal details, etc.
jobs-applier run — Executes the automated job apply flow using the stored config.
jobs-applier logs — Displays recent logs for applications.
Options:
--keywords: Comma-separated job titles or skills (e.g., “Software Engineer, Machine Learning”).
--location: Location (e.g., “Remote”, “Honolulu, HI”).
--max-applications: Limit the number of applications in a session (e.g., 50).
--llm-cover-letters: Boolean flag to enable/disable cover letter generation.
--wait-range: Min and max seconds to wait between applications (default 10–30).
6.2 Browser Automation
Logging In:
Use LinkedIn credentials from config.
Implement error handling for 2FA or unusual login flows.
Search:
Use the LinkedIn job search URL with query parameters (keyword, location, filters).
Scroll or paginate through results.
Easy Apply:
Identify the DOM element for “Easy Apply” or “Apply Now.”
Follow the multi-step form if it spans multiple pop-up windows or modals.
Fill details with user data (phone, email, etc.).
Upload resume from a pre-configured path.
Cover Letter:
If required, fetch job description from the DOM.
Call the LLM with relevant details.
Paste the result into the text field.
6.3 LLM Cover Letter Module
Prompt Template:
css
Copy
You are a professional resume writer. 
Please write a short, concise, and tailored cover letter for the position:
{job_title} at {company_name}.
The job description is: {job_description}.
My personal background is: {user_background}.
API:
Provide endpoint + API key in config.
Keep the request short to avoid large token usage.
Provide text-based or JSON structured response.
Insertion:
Insert the text into the relevant “Cover Letter” or “Additional Info” field.
6.4 Error Handling
If the tool encounters a “no Easy Apply” job, skip it.
If the required fields change, attempt to fill them if possible. If it can’t locate an element, log the job post link and error message.
If the LLM times out or fails, skip that job or try again up to a configured max retry.
6.5 Logging & Reporting
Application Logs:
Time, job title, company, success/failure reason, link.
Export:
Optionally export to CSV or JSON so the user can track or revisit.
7. Timeline & Milestones
MVP (2–3 weeks)
Implement basic browser automation (login, search, easy apply form filling).
Basic LLM integration for cover letter.
Logging to console or a text file.
Simple CLI with minimal config.
Beta Release (1–2 weeks after MVP)
Enhanced error handling (UI changes on LinkedIn).
Config file for user data and LLM credentials.
Throttling and random wait intervals.
Basic logging improvements.
Stable v1.0 (2–3 weeks after Beta)
Documentation + Examples.
Additional advanced filters.
Unit tests for core logic.
Possibly basic GUI or improved CLI UX.
8. Risks & Mitigations
LinkedIn Policy & Anti-Bot Measures
Risk: Account suspension or CAPTCHAs if applying too quickly or too frequently.
Mitigation: Throttling, random time intervals, headless vs. non-headless usage, possibility of manual input for CAPTCHAs.
LinkedIn UI Changes
Risk: LinkedIn regularly updates their DOM elements or flows.
Mitigation: Frequent updates, open-source contributions to keep up with changes.
LLM Costs
Risk: Generating many cover letters might be expensive if the user applies to hundreds of jobs.
Mitigation: Option to disable cover letters or limit them to certain roles. Possibly store short letter templates.
Sensitive Data Exposure
Risk: Storing user credentials, personal info, and resumes in plain text.
Mitigation: Encourage environment variables or a local encryption solution. Provide disclaimers in docs.
Quality of Cover Letters
Risk: LLM output might not be perfect or could contain repetition or irrelevant info.
Mitigation: Provide user with partial control or a review process for the cover letter. Possibly allow quick editing prior to final submission.
9. Acceptance Criteria
Basic: The user can run jobs-applier with their LinkedIn credentials, set search parameters, and watch the system apply to jobs automatically that have “Easy Apply.”
Cover Letter: If a role requires a cover letter, the system successfully generates one via the LLM and inserts it.
Config: All sensitive data and search parameters are loaded from a config file or environment variables.
Logs: Successful or failed job applications are recorded with relevant details.
Final Notes
“jobs-applier” will be an open source project, so clarity, maintainability, and ease of use are paramount. By focusing on LinkedIn Easy Apply in the MVP, we keep the scope tight while delivering a valuable automation tool for job seekers. The system is designed to be modular, enabling future expansions (multi-job-board support, advanced AI matching, analytics, etc.).
This PRD and technical spec provides a foundation for building out the “jobs-applier” project. The next step is to create a repository, set up the basic scaffolding (license, README, code structure), and start implementing the MVP features.