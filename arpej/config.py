import json
from selenium.webdriver.chrome.options import Options
import os


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as file:
            self.config_data = json.load(file)

    @property
    def chrome_options(self):
        options = self.config_data.get('chrome_options', {})
        chrome_options = Options()
        for key, value in options.items():
            chrome_options.add_argument(
                f"--{key.replace('_', '-')}") if value else None

        return chrome_options

    @property
    def chromedriver_path(self):
        return self.config_data.get('windows_chromedriver_path', '')


# Initialize configs
configs = Config(os.path.dirname(os.path.abspath(__file__))
                 [:-6] + '/configs.json')
