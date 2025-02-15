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

    browser_options = {
        "headless": False,
        "slow_mo": 100,  # Slow down operations by 100ms
        "timeout": 60000,  # Increase default timeout to 60 seconds
    }

    logger.info(f"Starting job application process for keywords: {keywords} in {location}")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(**browser_options)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            # Enable detailed network logging
            page = context.new_page()
            page.set_default_timeout(60000)  # 60 second timeout for all operations
            
            # Add event listeners for debugging
            page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
            page.on("pageerror", lambda err: logger.error(f"Browser page error: {err}"))
            page.on("request", lambda request: logger.debug(f"Request: {request.method} {request.url}"))
            page.on("response", lambda response: logger.debug(f"Response: {response.status} {response.url}"))

            # 1. Login with enhanced error handling
            login_success = login_linkedin(page, linkedin_email, linkedin_password)
            if not login_success:
                raise Exception("LinkedIn login failed")

            # 2. Perform job search with retry logic
            search_success = perform_job_search(page, keywords, location, config)
            if not search_success:
                raise Exception("Job search failed")

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
            return True
        except Exception as e:
            logger.error(f"Job application process failed: {str(e)}")
            browser.close()
            return False

def login_linkedin(page, email: str, password: str) -> bool:
    """
    Automate LinkedIn login with enhanced error handling and debugging.
    Returns True if login successful, False otherwise.
    """
    try:
        logger.info("Attempting LinkedIn login...")
        page.goto("https://www.linkedin.com/login")
        
        # Wait for and verify login form presence
        logger.debug("Waiting for login form...")
        page.wait_for_selector("input#username", timeout=10000)
        page.wait_for_selector("input#password", timeout=10000)
        
        # Fill credentials with typing simulation
        logger.debug("Filling credentials...")
        page.fill("input#username", email, timeout=5000)
        random_wait(1, 2)
        page.fill("input#password", password, timeout=5000)
        random_wait(1, 2)
        
        # Click submit and wait for navigation
        logger.debug("Submitting login form...")
        page.click("button[type='submit']")
        
        # Wait for successful login indicators with multiple checks
        success = False
        try:
            # Check for multiple success indicators
            logger.debug("Checking login success...")
            for selector in [
                "input[placeholder='Search']",  # Search bar
                ".global-nav__me-photo",  # Profile photo
                ".feed-identity-module"  # Feed module
            ]:
                if page.wait_for_selector(selector, timeout=10000):
                    success = True
                    break
        except Exception as e:
            logger.warning(f"Login success check failed: {e}")
            
        if success:
            logger.info("LinkedIn login successful")
            return True
        else:
            logger.error("Login seemed to fail - no success indicators found")
            return False
            
    except Exception as e:
        logger.error(f"Login failed with error: {str(e)}")
        # Capture screenshot on failure
        try:
            page.screenshot(path="login_error.png")
            logger.info("Saved error screenshot to login_error.png")
        except:
            pass
        return False

def perform_job_search(page, keywords: str, location: str, config: Config) -> bool:
    """
    Navigate to LinkedIn Jobs search with advanced filters for Easy Apply and Remote jobs.
    Ensures we get the two-pane layout for proper job list viewing.
    Returns True if search successful, False otherwise.
    """
    try:
        logger.info(f"Initiating job search for '{keywords}' in '{location}'")
        
        # Construct clean search URL with only necessary parameters
        base_url = "https://www.linkedin.com/jobs/search/"
        
        # URL encode parameters properly
        encoded_keywords = keywords.replace(" ", "%20")
        encoded_location = location.replace(" ", "%20") if location.lower() != "remote" else "Remote"
        
        # Build essential query parameters - order matters for LinkedIn
        query_params = [
            f"keywords={encoded_keywords}",
            f"location={encoded_location}",
            "f_LF=f_AL",     # Easy Apply filter
            "f_WT=2",        # Remote filter
            "sortBy=DD"      # Sort by date to get fresh postings
        ]
        
        # Add any additional filters from config, excluding problematic ones
        search_filters = config.get_nested("search", "filters", default={})
        excluded_params = ["currentJobId", "miniJob", "pageNum"]  # Parameters to exclude
        
        for key, value in search_filters.items():
            if value and key not in excluded_params:
                query_params.append(f"{key}={value}")
        
        # Construct final URL
        search_url = f"{base_url}?{'&'.join(query_params)}"
        logger.debug(f"Navigating to search URL: {search_url}")
        
        # Navigate to the search URL
        page.goto(search_url)
        
        # First check if we're in a single-job view and try to exit it
        logger.debug("Checking for single-job view...")
        try:
            # Look for close/dismiss buttons that might appear in single-job view
            close_selectors = [
                "button[aria-label='Dismiss']",
                "button[aria-label='Close']",
                "button.jobs-search__close-button",
                "button.jobs-home-close-button"
            ]
            
            for selector in close_selectors:
                close_button = page.query_selector(selector)
                if close_button:
                    logger.debug(f"Found close button with selector: {selector}")
                    close_button.click()
                    time.sleep(2)  # Wait for UI to update
                    break
        except Exception as e:
            logger.debug(f"Error handling single-job view: {str(e)}")

        # Wait for the two-pane layout to appear
        logger.debug("Waiting for jobs list container...")
        
        # Try multiple possible selectors for the job list container
        list_container_selectors = [
            "div.jobs-search-two-pane__results",
            "ul.jobs-search__results-list",
            ".jobs-search-results-list",
            "div.jobs-search-results-list",
            "ul.scaffold-layout__list-container"
        ]
        
        list_container = None
        for selector in list_container_selectors:
            try:
                list_container = page.wait_for_selector(selector, timeout=5000)
                if list_container:
                    logger.debug(f"Found jobs list container with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not list_container:
            logger.error("Could not find jobs list container with any known selector")
            page.screenshot(path="no_jobs_list_found.png")
            return False
            
        # Wait for the page to stabilize
        page.wait_for_load_state("networkidle", timeout=5000)
        time.sleep(2)  # Extra stability wait
        
        # Verify we have job listings
        job_card_selectors = [
            "ul.jobs-search__results-list li",
            "div.jobs-search-two-pane__results li",
            "ul.scaffold-layout__list-container li"
        ]
        
        total_jobs = 0
        for selector in job_card_selectors:
            cards = page.query_selector_all(selector)
            if len(cards) > 0:
                total_jobs = len(cards)
                logger.info(f"Found {total_jobs} job cards with selector: {selector}")
                break
        
        if total_jobs == 0:
            logger.error("No job cards found in the list")
            page.screenshot(path="empty_jobs_list.png")
            return False
            
        # Take a screenshot of the successful state
        page.screenshot(path="jobs_search_success.png")
        return True
            
    except Exception as e:
        logger.error(f"Job search failed: {str(e)}")
        try:
            page.screenshot(path="job_search_error.png")
        except:
            pass
        return False

def collect_easy_apply_jobs(page) -> list:
    """
    Collect visible job postings with 'Easy Apply' from the left-side jobs list.
    Returns a list of dictionaries, each containing job info and the card element.
    """
    logger.info("Starting detailed collection of Easy Apply jobs...")

    # Take screenshot of initial state
    try:
        page.screenshot(path="initial_jobs_page.png")
        logger.debug("Captured initial jobs page state")
    except Exception as e:
        logger.error(f"Failed to capture initial screenshot: {e}")

    # Wait for job cards to be visible with detailed logging
    try:
        logger.debug("Waiting for jobs list to become visible...")
        list_elem = page.wait_for_selector("ul.jobs-search__results-list", timeout=10000)
        if list_elem:
            logger.debug("Jobs list container found")
            # Log the HTML structure for debugging
            list_html = list_elem.inner_html()
            logger.debug(f"Jobs list HTML structure (first 500 chars): {list_html[:500]}")
        else:
            logger.error("Jobs list container found but returned None")
            return []
    except TimeoutError:
        logger.error("Timeout waiting for jobs list - not found after 10s")
        return []
    except Exception as e:
        logger.error(f"Unexpected error waiting for jobs list: {str(e)}")
        return []

    # Get all job cards with detailed counts
    job_cards = page.query_selector_all("ul.jobs-search__results-list li")
    total_cards = len(job_cards)
    logger.info(f"Found {total_cards} total job cards")

    if total_cards == 0:
        logger.error("No job cards found - possible loading issue or anti-automation measure")
        page.screenshot(path="no_job_cards_found.png")
        return []

    easy_apply_jobs = []
    
    # Debug each card's structure
    for index, card in enumerate(job_cards, 1):
        try:
            logger.debug(f"\nAnalyzing job card {index}/{total_cards}")
            
            # Get card's HTML for debugging
            card_html = card.inner_html()
            logger.debug(f"Card {index} HTML structure (first 200 chars): {card_html[:200]}")
            
            # Log all buttons in this card for debugging
            all_buttons = card.query_selector_all("button")
            logger.debug(f"Found {len(all_buttons)} total buttons in card {index}")
            for btn in all_buttons:
                btn_text = btn.inner_text().strip()
                btn_class = btn.get_attribute("class")
                logger.debug(f"Button found: text='{btn_text}', class='{btn_class}'")

            # Extract job info with validation
            title_elem = card.query_selector(".job-card-list__title") or card.query_selector("h3.base-search-card__title")
            company_elem = card.query_selector(".job-card-container__company-name") or card.query_selector("h4.base-search-card__subtitle")
            location_elem = card.query_selector(".job-card-container__metadata-item") or card.query_selector(".job-search-card__location")

            # Validate each element
            title = title_elem.inner_text().strip() if title_elem else "Unknown Title"
            company = company_elem.inner_text().strip() if company_elem else "Unknown Company"
            location = location_elem.inner_text().strip() if location_elem else "Unknown Location"
            
            logger.debug(f"Card {index} basic info - Title: {title}, Company: {company}, Location: {location}")

            # Detailed Easy Apply button detection
            easy_apply_selectors = [
                "button.jobs-apply-button",
                "button:has-text('Easy Apply')",
                "[aria-label='Easy Apply']",
                ".jobs-apply-button",
                "button.artdeco-button--icon-right"
            ]

            easy_apply_indicator = None
            matched_selector = None

            for selector in easy_apply_selectors:
                try:
                    button = card.query_selector(selector)
                    if button:
                        button_text = button.inner_text().strip()
                        button_class = button.get_attribute("class")
                        button_disabled = button.get_attribute("disabled")
                        logger.debug(f"Found potential Easy Apply button with selector '{selector}':")
                        logger.debug(f"  - Text: '{button_text}'")
                        logger.debug(f"  - Class: '{button_class}'")
                        logger.debug(f"  - Disabled: {button_disabled}")
                        
                        if button_disabled:
                            logger.debug("Button is disabled, skipping")
                            continue
                            
                        if "Easy Apply" in button_text:
                            easy_apply_indicator = button
                            matched_selector = selector
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector '{selector}': {str(e)}")

            if easy_apply_indicator:
                logger.info(f"Found valid Easy Apply button in card {index} using selector: {matched_selector}")
                
                # Verify button is interactable
                try:
                    is_visible = easy_apply_indicator.is_visible()
                    is_enabled = not easy_apply_indicator.get_attribute("disabled")
                    logger.debug(f"Button state - Visible: {is_visible}, Enabled: {is_enabled}")
                except Exception as e:
                    logger.error(f"Error checking button state: {str(e)}")

                job_info = {
                    "element": card,
                    "easy_apply_button": easy_apply_indicator,
                    "title": title,
                    "company": company,
                    "location": location,
                    "matched_selector": matched_selector
                }
                easy_apply_jobs.append(job_info)
                logger.info(f"Added job to collection: {title} at {company}")
            else:
                logger.debug(f"No valid Easy Apply button found in card {index}")

        except Exception as e:
            logger.error(f"Error processing card {index}: {str(e)}")
            continue

    logger.info(f"Collection complete. Found {len(easy_apply_jobs)} Easy Apply jobs out of {total_cards} total cards")
    
    # Take final screenshot
    try:
        page.screenshot(path="jobs_collection_complete.png")
    except Exception as e:
        logger.error(f"Failed to capture final screenshot: {e}")

    return easy_apply_jobs

def apply_single_job(page, job: dict, config: Config):
    """
    Execute the Easy Apply flow for a single job, including multi-step forms.
    """
    try:
        logger.info(f"\nStarting application process for: {job['title']} at {job['company']}")
        logger.debug(f"Using selector that matched during collection: {job.get('matched_selector')}")

        # 1. Verify card is still valid
        try:
            is_card_attached = job["element"].is_attached()
            logger.debug(f"Job card element still attached: {is_card_attached}")
            if not is_card_attached:
                raise RuntimeError("Job card element is no longer attached to DOM")
        except Exception as e:
            logger.error(f"Error verifying card state: {str(e)}")
            raise

        # Take screenshot before clicking
        page.screenshot(path=f"before_card_click_{int(time.time())}.png")

        # 2. Click the job card with validation
        try:
            logger.debug("Attempting to click job card...")
            job["element"].click()
            logger.debug("Successfully clicked job card")
        except Exception as e:
            logger.error(f"Failed to click job card: {str(e)}")
            raise

        # Wait for job details with verification
        try:
            logger.debug("Waiting for job details to load...")
            page.wait_for_load_state("networkidle", timeout=5000)
            time.sleep(2)  # Additional wait for UI stability
            
            # Verify job details loaded
            detail_container = page.query_selector(".jobs-search__job-details")
            if detail_container:
                logger.debug("Job details container found")
            else:
                logger.warning("Job details container not found after click")
        except Exception as e:
            logger.error(f"Error waiting for job details: {str(e)}")

        # Take screenshot after details load
        page.screenshot(path=f"after_details_load_{int(time.time())}.png")

        # 3. Find and verify Easy Apply button
        logger.debug("Searching for Easy Apply button...")
        easy_apply_button = None
        button_states = []

        # Try multiple button selectors
        selectors = [
            "button.jobs-apply-button",
            "button:has-text('Easy Apply')",
            "[aria-label='Easy Apply to jobs']",
            job.get("easy_apply_button")
        ]

        for selector in selectors:
            if isinstance(selector, str):
                button = page.query_selector(selector)
                if button:
                    try:
                        visible = button.is_visible()
                        enabled = not button.get_attribute("disabled")
                        text = button.inner_text().strip()
                        button_states.append({
                            "selector": selector,
                            "visible": visible,
                            "enabled": enabled,
                            "text": text
                        })
                        if visible and enabled and "Easy Apply" in text:
                            easy_apply_button = button
                            logger.debug(f"Found valid Easy Apply button with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Error checking button state for selector {selector}: {str(e)}")

        if not easy_apply_button:
            logger.error("No valid Easy Apply button found. Button states found:")
            for state in button_states:
                logger.error(f"  Selector: {state['selector']}")
                logger.error(f"    Visible: {state['visible']}")
                logger.error(f"    Enabled: {state['enabled']}")
                logger.error(f"    Text: {state['text']}")
            raise RuntimeError("No valid Easy Apply button found")

        # 4. Click Easy Apply button
        try:
            logger.debug("Attempting to click Easy Apply button...")
            easy_apply_button.click()
            logger.debug("Successfully clicked Easy Apply button")
        except Exception as e:
            logger.error(f"Failed to click Easy Apply button: {str(e)}")
            raise

        # 5. Wait for the application modal
        try:
            page.wait_for_selector("div#artdeco-modal-outlet", timeout=8000)
            logger.debug("Application modal appeared")
        except TimeoutError:
            raise RuntimeError("Application modal did not appear")

        # 6. Fill out the application form
        fill_application_form(page, config, job)

        # 7. Submit the application
        submit_button = (
            page.query_selector("button:has-text('Submit application')") or
            page.query_selector("button:has-text('Submit')") or
            page.query_selector("button:has-text('Send')")
        )

        if submit_button:
            submit_button.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            logger.info(f"Successfully submitted application for {job['title']} at {job['company']}")
        else:
            raise RuntimeError("Submit/Send button not found")

    except Exception as e:
        logger.error(f"Failed to apply to {job['title']}: {str(e)}")
        # Take debug screenshot
        try:
            page.screenshot(path=f"failed_application_{int(time.time())}.png")
        except:
            pass
        raise e

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

    # Step 4: Some Easy Apply forms have multiple "Next" steps
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
        # If additional questions appear, you'd fill them in here, then proceed.

def fetch_job_description(page) -> str:
    """
    Extract the complete job description from the job detail panel.
    Handles multiple possible selectors and formats.
    """
    try:
        # Wait for job details to load
        detail_selectors = [
            "div#job-details",
            "div.jobs-description__content",
            "div.jobs-description",
            "div.description",
            "[data-job-detail-type='description']"
        ]
        
        description = ""
        
        # Try each selector
        for selector in detail_selectors:
            try:
                # Wait briefly for this specific selector
                desc_elem = page.wait_for_selector(selector, timeout=5000)
                if desc_elem:
                    # Get the text content
                    description = desc_elem.inner_text().strip()
                    if description:
                        logger.debug(f"Found job description using selector: {selector}")
                        break
            except Exception:
                continue
        
        if not description:
            # If we still don't have a description, try a more general approach
            # Look for any div containing job-related keywords
            content_selectors = [
                "div:has-text('Requirements')",
                "div:has-text('Responsibilities')",
                "div:has-text('Qualifications')",
                "div:has-text('About the role')"
            ]
            
            for selector in content_selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem:
                        text = elem.inner_text().strip()
                        if len(text) > 100:  # Reasonable minimum length for a job description
                            description = text
                            break
                except Exception:
                    continue
        
        if description:
            # Clean up the description
            # Remove excessive whitespace
            description = " ".join(description.split())
            logger.debug(f"Successfully extracted job description ({len(description)} chars)")
            return description
        else:
            logger.warning("Could not find job description")
            return ""
            
    except Exception as e:
        logger.error(f"Error fetching job description: {str(e)}")
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
