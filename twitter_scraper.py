import os
import time
import csv
from logs import logger
from scraping_manager.automate import Web_scraping
from spreadsheet_manager.xlsx import SS_manager
from selenium.webdriver.common.by import By

class TwitterScraper ():

    def __init__ (self, users:list=[], max_followers:int=None):
        """Start scraper and setup options

        Args:
            users (list, optional): List fo users to get followers data. Defaults to [].
            max_followers (int, optional): Maz followers to get from each user. Defaults to None.
            max_minutes (int, optional): maz minutes to run the scraper for each user. Defaults to None.
        """
        
        logger.info ("Running scraper...")
        
        # Scraper options
        self.__users = users
        self.__max_followers = max_followers

        # Chrome folder
        user_name = os.getlogin()
        chrome_folder = f"C:\\Users\\{user_name}\\AppData\\Local\\Google\\Chrome\\User Data"

        # Start browser
        self.__home_page = "https://twitter.com/"
        self.__scraper = Web_scraping (chrome_folder=chrome_folder, start_killing=True)

        # Connect to excel and clean last sheets
        output_path = os.path.join (os.path.dirname(__file__), "data.xlsx")
        self.__ss_manager = SS_manager (output_path)
        self.__ss_manager.clean_workbook ()

    def __get_user_data (self):
        """Get general data of the current user"""

        self.__scraper.refresh_selenium ()

        # selectors
        selector_name = '[data-testid="UserName"] .css-901oao.r-1awozwy.r-1nao33i.r-6koalj.r-37j5jr.r-adyw6z.r-1vr29t4.r-135wba7.r-bcqeeo.r-1udh08x.r-qvutc0 > span.css-901oao.css-16my406.r-poiln3.r-bcqeeo.r-qvutc0'
        selector_user = '[data-testid="UserName"] .css-901oao.css-1hf3ou5.r-18u37iz.r-37j5jr.r-a023e6.r-16dba41.r-rjixqe.r-bcqeeo.r-qvutc0 > span.css-901oao.css-16my406.r-poiln3.r-bcqeeo.r-qvutc0'
        selector_profileimg = 'a.css-4rbku5.css-18t94o4.css-1dbjc4n.r-1niwhzg.r-1loqt21.r-1pi2tsx.r-1ny4l3l.r-o7ynqc.r-6416eg.r-13qz1uu[href$="photo"]'
        selector_description = '[data-testid="UserDescription"]'
        selector_location = '[data-testid="UserProfileHeader_Items"] [data-testid="UserLocation"]'
        selector_webpage = '[data-testid="UserProfileHeader_Items"] [data-testid="UserUrl"]'
        selector_joindate = '[data-testid="UserProfileHeader_Items"] [data-testid="UserJoinDate"]'
        selector_following = 'a[href$="/following"] > span:nth-child(1)'
        selector_followers = 'a[href$="/followers"] > span:nth-child(1)'

        # Get data
        name = self.__scraper.get_text (selector_name).strip()
        user = self.__scraper.get_text (selector_user).strip()
        profileimg = self.__scraper.get_attrib (selector_profileimg, "href").strip()
        description = self.__scraper.get_text (selector_description).strip()
        location = self.__scraper.get_text (selector_location).strip()

        try:
            webpage = self.__scraper.get_text (selector_webpage).strip()
        except:
            webpage = ""
            
        joindate = self.__scraper.get_text (selector_joindate).strip()
        following = self.__scraper.get_text (selector_following).strip()
        followers = self.__scraper.get_text (selector_followers).strip()

        # Return data
        data = [
            name,
            user,
            profileimg,
            description,
            location,
            webpage,
            joindate,
            following,
            followers
        ]

        return data

    def __get_followers (self):
        """Scrape the list of usernames who follow the current user

        Returns:
            list: twitter users
        """

        # Go to followers page
        selector_followers_link = 'a[href$="/followers"]'
        self.__scraper.click_js (selector_followers_link)
        time.sleep (2)

        followers = []

        more_users = True
        while more_users:
            # Vsairbale for detect where no more users in page
            users_found = False

            # Get followers from current screen
            selector_followers = '[aria-label="Timeline: Followers"] [data-testid="cellInnerDiv"] [data-testid="UserCell"]'
            follower_elems = self.__scraper.get_elems (selector_followers) 


            # Get eact user name
            for follower_elem in follower_elems:

                # Get username
                selector_user = 'a.css-4rbku5.css-18t94o4.css-1dbjc4n.r-1loqt21.r-1wbh5a2.r-dnmrzs.r-1ny4l3l[tabindex="-1"]' 
                try:
                    user = follower_elem.find_element (By.CSS_SELECTOR, selector_user).text
                except:
                    continue

                # Validate and save
                if user not in followers:
                    followers.append (user)
                    users_found = True

                # Validate max number of followers
                if len (followers) >= self.__max_followers:
                    more_users = False
                    break
            
            # End when scrape all followers
            if not users_found:
                more_users = False

            # Load more followers
            for _ in range (5):
                self.__scraper.go_down ('body')
            self.__scraper.refresh_selenium ()

        return followers
        

    def __set_sheet (self, output_sheet:str):
        """Create and set new sheet in excel file for save data"""

        # Connect to google sheets
        self.__ss_manager.create_get_sheet (output_sheet)

    def __save_excel (self):
        """Save data in current excel sheet"""

        # Write data in excel
        self.__ss_manager.write_data (self.__tweets_data)
        self.__ss_manager.auto_width ()
        self.__ss_manager.save ()

    def extract (self):

        # Loop for each user
        for user in self.__users:

            # Set user poage
            user_page = f"https://twitter.com/{user.replace('@', '')}"
            self.__scraper.set_page (user_page)

            # Get general user data
            user_data = self.__get_user_data ()

            # Get followers
            followers_data = []
            followers = self.__get_followers ()
            for follower in followers:

                # Open follower profile
                follower_page = f"https://twitter.com/{follower.replace('@', '')}"
                self.__scraper.set_page (follower_page)

                # Get follower data
                follower_data = self.__get_user_data ()

                followers_data.append (follower_data)

            print ()

