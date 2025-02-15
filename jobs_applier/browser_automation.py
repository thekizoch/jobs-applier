# browser_automation.py

import asyncio
import time
import random
import logging

from playwright.sync_api import sync_playwright, TimeoutError
from .config import Config
from .logs import get_logger
from .llm_integration import generate_cover_letter
from .utils import random_wait

logger = get_logger(__name__)

def apply_to_jobs(config: Config):
    """
    Main orchestrator for searching and applying to LinkedIn jobs.
    """
    linkedin_email = config.get_nested("linkedin", "email")
    linkedin_password = config.get_nested("linkedin", "password")
    keywords = config.get_nested("search", "keywords", default="")
    location = config.get_nested("search", "location", default="Remote")
    max_applications = config.get_nested("search", "max_applications", default=10)

    with sync_playwright() as p:
        # If you get flagged by LinkedIn, try headless=True or slow_mo=50
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        login_linkedin(page, linkedin_email, linkedin_password)

        # 2. Perform job search with advanced filters
        perform_job_search(page, keywords, location, config)

        # 3. Paginate through results, collecting & applying to jobs
        total_applied = 0
        while total_applied < max_applications:
            jobs_on_page = collect_easy_apply_jobs(page)
            for job in jobs_on_page:
                if total_applied >= max_applications:
                    break
                try:
                    apply_single_job(page, job, config)
                    total_applied += 1
                    logger.info(f"[{total_applied}] Applied to {job['title']} @ {job['company']}")
                    # Rate-limit
                    random_wait(min_sec=10, max_sec=30)
                except Exception as e:
                    logger.error(f"Failed to apply to {job['title']} at {job['company']}: {e}")
            
            # Attempt to go to the next page
            has_next_page = go_to_next_page(page)
            if not has_next_page:
                break

        logger.info(f"Finished. Total applications submitted this run: {total_applied}")
        browser.close()

def login_linkedin(page, email: str, password: str):
    """Automate LinkedIn login."""
    page.goto("https://www.linkedin.com/login")
    page.fill("input#username", email)
    page.fill("input#password", password)
    page.click("button[type='submit']")
    # Wait for page to load or redirect
    page.wait_for_load_state("networkidle")
    logger.info("Logged into LinkedIn successfully.")

def perform_job_search(page, keywords: str, location: str, config: Config):
    """
    Navigate to LinkedIn Jobs search, fill advanced filters, handle location.
    """
    page.goto("https://www.linkedin.com/jobs/")
    page.wait_for_load_state("networkidle")

    # Fill keywords
    page.fill("input[placeholder='Search jobs']", keywords)
    # Fill location
    page.fill("input[placeholder='Search location']", location)
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")

    # Optional: apply advanced filters (experience level, job type, date posted)
    experience_levels = config.get_nested("search", "experience_levels", default=[])
    job_types = config.get_nested("search", "job_types", default=[])
    date_posted = config.get_nested("search", "date_posted", default="Any time")

    # The actual DOM structure for these filters changes frequently on LinkedIn;
    # you might need to adapt to the current UI. Here's a simplified approach:
    logger.info(f"Applying advanced filters - Experience: {experience_levels}, Job Type: {job_types}, Date Posted: {date_posted}")
    # Example flow: open filter menus, click appropriate checkboxes or items.

    # Because LinkedIn's DOM is dynamic, you should locate the relevant elements
    # and click them. E.g.:
    # filter_button = page.query_selector("button.jobs-search-dropdown__trigger") # etc.

    logger.info(f"Searching for jobs: '{keywords}' in '{location}'")

def collect_easy_apply_jobs(page) -> list:
    """
    Collect visible job postings with "Easy Apply" in the current results list.
    """
    job_cards = page.query_selector_all("ul.jobs-search-results__list li")
    easy_apply_jobs = []
    for card in job_cards:
        easy_apply_button = card.query_selector("button:has-text('Easy Apply')")
        title_elem = card.query_selector("h3")
        company_elem = card.query_selector("h4")

        if easy_apply_button and title_elem and company_elem:
            easy_apply_jobs.append({
                "element": card,
                "title": title_elem.inner_text().strip(),
                "company": company_elem.inner_text().strip(),
            })
    logger.info(f"Found {len(easy_apply_jobs)} Easy Apply jobs on this page.")
    return easy_apply_jobs

def apply_single_job(page, job: dict, config: Config):
    """
    Execute the Easy Apply flow for a single job, including multi-step forms.
    """
    elem = job["element"]
    elem.click()
    time.sleep(2)  # wait for side panel or job detail to load

    # In the side panel, look for "Easy Apply" button
    easy_apply_button = page.query_selector("button:has-text('Easy Apply')")
    if not easy_apply_button:
        raise RuntimeError("No Easy Apply button found in job detail.")
    
    easy_apply_button.click()

    # Wait for the application modal
    try:
        page.wait_for_selector("div#artdeco-modal-outlet", timeout=8000)
    except TimeoutError:
        raise RuntimeError("Application modal did not appear.")

    fill_application_form(page, config, job)

    # If the final "Submit application" or "Send application" button is present, click it
    submit_button = page.query_selector("button:has-text('Submit')") or page.query_selector("button:has-text('Send')")
    if submit_button:
        submit_button.click()
        # Wait for network or some confirmation
        page.wait_for_load_state("networkidle", timeout=10000)
        logger.info(f"Submitted application for {job['title']} at {job['company']}")
    else:
        raise RuntimeError("Submit/Send button not found")

def fill_application_form(page, config: Config, job: dict):
    """
    Fill out all required fields. Some applications have multiple steps.
    """
    user_profile = config.get("user_profile", {})
    phone = user_profile.get("phone", "")
    resume_path = user_profile.get("resume_path", "")

    # Step 1: Possibly fill phone number
    phone_input = page.query_selector("input#phoneNumber") or page.query_selector("input[aria-label='Phone']")
    if phone_input:
        phone_input.fill(phone)

    # Step 2: Upload resume if required
    if resume_path:
        file_input = page.query_selector("input[type='file']")
        if file_input:
            file_input.set_input_files(resume_path)

    # Step 3: If a cover letter is required, look for a relevant text area
    if config.get_nested("llm", "enabled", default=False):
        text_area = page.query_selector("textarea[name*='coverLetter']") or page.query_selector("textarea[aria-label*='cover letter']")
        if text_area:
            job_desc = fetch_job_description(page)
            cover_letter_text = generate_cover_letter(
                job_title=job["title"],
                company_name=job["company"],
                job_description=job_desc,
                user_background=user_profile.get("summary", "")
            )
            text_area.fill(cover_letter_text)

    # Step 4: Some Easy Apply forms have multiple “Next” steps
    proceed_through_steps(page)

def proceed_through_steps(page):
    """
    Click any "Next" buttons until we either reach "Review" or "Submit".
    """
    while True:
        next_button = page.query_selector("button:has-text('Next')")
        if not next_button:
            break
        next_button.click()
        time.sleep(1)
        # If additional questions appear, you’d fill them in here, then proceed.

def fetch_job_description(page) -> str:
    """
    Attempt to extract job description text from the side panel or job detail area.
    """
    desc_elem = page.query_selector("div#job-details") or page.query_selector("div.description")
    if desc_elem:
        return desc_elem.inner_text().strip()
    return ""

def go_to_next_page(page) -> bool:
    """
    Click the pagination button "Next" if available, return True if succeeded,
    False if no more pages.
    """
    next_page_btn = page.query_selector("button[aria-label='Next']")  # or label changes
    if next_page_btn and "disabled" not in next_page_btn.get_attribute("class", ""):
        next_page_btn.click()
        page.wait_for_load_state("networkidle")
        return True
    return False
