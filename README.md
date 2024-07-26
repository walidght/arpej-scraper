# ARPEJ Scraper

ARPEJ Scraper is a tool designed to scrape the ARPEJ website for available residences and send email notifications when matching properties are found.

## Description

This tool automates the process of checking the ARPEJ website for available residences. It filters results based on user-defined criteria such as maximum price and location, and notifies the user via email and desktop notifications.

## Installation

To get started, follow these steps:

1. **Install Python Dependencies:**

    - Ensure you have Python installed.
    - Install the required Python packages using the command:
        ```bash
        pip install -r requirements.txt
        ```

2. **Set Up ChromeDriver:**

    - Download [ChromeDriver](https://getwebdriver.com/chromedriver) and ensure it matches your installed version of Chrome.
    - Add ChromeDriver to your system's PATH or note its path for later use.

3. **Install Google Chrome:**
    - Ensure Google Chrome is installed on your system.

## Usage

1. **Configuration:**

    - Create a `configs.json` file based on the `configs.json.example`. Fill in the following details:
        - `windows_chromedriver_path`: Path to your ChromeDriver.
        - `NOTIFICATION_EMAIL`: The email address where notifications will be sent.
        - `arpej_link`: The URL of the ARPEJ page with your desired filters.
        - `max_price`: The maximum price you're willing to pay for a residence.
        - `SMTP_HOST` and `SMTP_PORT`: Set to your email provider's SMTP settings (defaults are for Hotmail).

2. **Excluding Unwanted Residences:**

    - Create an `all_unwanted_arpej.txt` file and list URLs of residences you are not interested in. If there are no unwanted residences, keep this file empty.

3. **Email Setup:**

    - Create a `.env` file based on the `.env.example` and include the email credentials for the account that will send notifications.

4. **Running the Script:**
    - Ensure the path to `main.py` is correctly set in `run_script.bat`.
    - Use Windows Task Scheduler to run the script periodically by creating a basic task.

## Features

-   Scrapes the ARPEJ page for available residences.
-   Filters out unwanted residences and those exceeding the budget.
-   Stores details of matching residences.
-   Sends email notifications with a table of available residences.
-   Displays a Windows desktop notification upon finding a match.

## Contributing

Contributions are welcome! Feel free to open a pull request or issue on GitHub. For any questions, bug reports, or feature requests, contact the developer at [walidghenaiet02@gmail.com](mailto:walidghenaiet02@gmail.com).
