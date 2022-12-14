from msilib.schema import File
import os
import time
from tqdm import tqdm
from logs import logger
from scraping_manager.automate import Web_scraping
from spreadsheet_manager.xlsx import SS_manager
from selenium.webdriver.common.by import By

class TwitterScraper (Web_scraping):

    def __init__ (self, users:list=[], download_folder="", headless=False):
        """Start scraper and setup options

        Args:
            users (list, optional): List fo users to get followers data. Defaults to [].
            max_followers (int, optional): Maz followers to get from each user. Defaults to None.
            max_minutes (int, optional): maz minutes to run the scraper for each user. Defaults to None.
        """
        
        logger.info ("Running scraper...")
        
        # Scraper options
        self.__users = users

        # Chrome folder
        user_name = os.getlogin()
        chrome_folder = f"C:\\Users\\{user_name}\\AppData\\Local\\Google\\Chrome\\User Data"

        # Class variables
        self.__download_folder = download_folder
        self.__home_page = "https://www.vicinitas.io/"
        self.__followers_data = []

        # Start browser with parent counstructor
        super().__init__ (chrome_folder=chrome_folder, 
                            start_killing=True, 
                            download_folder=self.__download_folder,
                            web_page=self.__home_page,
                            headless=headless)

    def extract (self):

        for user in self.__users:

            logger.info (f"\nUser: {user}")
            
            # Search and download file
            self.__download_files (user)

            # Validate if page requiered twitter autorization
            requiere_autorization = self.__requiere_autorization ()
            if requiere_autorization:
                self.__autorize(user)

            # Wait for download file
            logger.info (f"\tgenerating excel file...")
            selector_progress = "#info > b"
            while True:

                wait = True
                self.refresh_selenium ()

                # Get current progress
                progress = self.get_text (selector_progress)
                if progress:
                    progress_parts = list(map (lambda elem: elem.strip(), progress.split ("/")))

                    # Validate if the page finish
                    if progress_parts[0] == progress_parts[1]:
                        wait = False
                
                if wait:
                    time.sleep (5)
                    continue
                else:
                    break 

            # Download file
            logger.info (f"\tdownloading excel file...")
            selector_download = "#info .btn.btn-success"
            self.click (selector_download)
            time.sleep (20)

            # Add GroupName column
            self.__add_column (user)

            # Go to home page
            self.set_page (self.__home_page)

        # Save summary file
        self.__save_summary ()

    def __download_files (self, user):
        """Go to vicinitas main page and """

        # Search  user and download file
        logger.info (f"\tsearching followers...")
        selector_followers = "#r3"
        selector_search = "#tracker"
        selector_submit = "#free_btn"
        self.click_js (selector_followers)
        self.send_data (selector_search, user)
        self.click_js (selector_submit)

    def __requiere_autorization (self):
        
        """Check if the page need twitter autorization for continue

        Returns:
            bool: return True if the the page requieres autorization
        """

        time.sleep (2)
        self.refresh_selenium ()
        selector_login = "#btn_login"
        text_login = self.get_text (selector_login)
        if text_login:
            return True
        else:
            return False

    def __autorize (self, search_user):
        """ Autorize and detect if it requiered manual login o autorization
        """

        # Login with twitter, if its required
        selector_login = "#btn_login"
        self.click (selector_login)
        time.sleep (2)

        # Validate the current page
        self.refresh_selenium ()
        current_url = self.driver.current_url
        if "api.twitter.com" in current_url:

            # Validate if the page required login
            selector_sign_in = "#allow"
            text_sign_in = self.get_attrib (selector_sign_in, "value")
            if text_sign_in == "Sign In":

                # Message and wait
                logger.warning ("Manual login or is required.\nPlease login and press enter to continue.")
                input ()

                # Redirect to home page and search files
                current_url = self.driver.current_url
                if "www.vicinitas.io" not in current_url:
                    self.set_page (self.__home_page)
                    self.__download_files (search_user)
            else:
                # Click in autorize button
                self.click_js (selector_sign_in)

    def __add_column (self, user):

        # Find new file
        download_files = os.listdir (self.__download_folder)
        file = list(filter (lambda name: "done" not in name and ".xlsx" in name and ".xlsx#" not in name, download_files))[0]

        # Open excel file
        file_path = f"{self.__download_folder}\\{file}"
        spreadsheet = SS_manager (file_path) 
        spreadsheet.set_sheet ("Followers")

        # Get data
        data = spreadsheet.get_data ()

        # Add new column to data
        new_data = list(map (lambda row:[user, *row], data))

        # Set column header
        new_data[0][0] = "GroupName"

        # Save new data
        spreadsheet.write_data (new_data)
        spreadsheet.save ()

        # Rename file
        new_file_path = file_path.replace(file, f"{file.replace('.xlsx', '')} - done.xlsx")
        os.rename (file_path, new_file_path)

        # Save current data
        self.__followers_data += new_data

    def __save_summary (self):
        logger.info ("\nSaving summary file...")

        # Open excel file
        file_path = f"{self.__download_folder}\\combined_data.xlsx"
        spreadsheet = SS_manager (file_path) 
        spreadsheet.create_get_sheet ("Followers")
        spreadsheet.write_data (self.__followers_data)
        spreadsheet.save ()

        logger.info ("Done")



        
        

        
        



