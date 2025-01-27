import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
from time import sleep
import urllib
from tqdm import tqdm
import os

DEBUG = False
# if DEBUG: import pdb

# header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
# 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0'

list_interesting_col = ['Alcohol', 'Appellation', 'Bottle Size', 'Category', 'Country',
                         'Date Published', 'Description', 'Designation', 'rating',
                         'Name', 'Price', 'Province', 'Rating', 'Region', 'Reviewer',
                         'Reviewer Twitter Handle', 'Subregion', 'User Avg Rating',
                         'Variety', 'Vintage', 'Winery']

# wine_varieties = ['Pinot Noir', 'Chardonnay', 'Cabernet Sauvignon', 'Red Blend', 'Bordeaux-style Red Blend', 'Shiraz/Syrah',
# 'Sauvignon Blanc', 'Riesling', 'Sparkling', 'Merlot', 'White Blend', 'Sangiovese', 'Zinfandel', 'Rose',
# 'Tempranillo', 'Pinot Grigio/Gris', 'Italian Red', 'Italian White', 'Nebbiolo', 'Portuguese Red', 'Malbec',
# 'Rhone-style Red Blend', 'Cabernet Franc', 'Other White', 'Portuguese White', 'Other Red', 'Gruner Veltliner',
# 'Viognier', 'Gamay']

wine_varieties = ['Pinot Noir', 'Chardonnay', 'Cabernet Sauvignon', 'Red Blend', 'Bordeaux-style Red Blend', 'Shiraz/Syrah',
'Sauvignon Blanc', 'Sparkling', 'Merlot', 'White Blend', 'Sangiovese', 'Zinfandel', 'Rose',
'Tempranillo', 'Pinot Grigio/Gris', 'Italian Red', 'Italian White', 'Nebbiolo', 'Portuguese Red', 'Malbec',
'Rhone-style Red Blend', 'Cabernet Franc', 'Other White', 'Portuguese White', 'Other Red', 'Gruner Veltliner',
'Viognier', 'Gamay', 'Grenache', 'Gewurztraminer', 'Port Blend', 'Petite Sirah', 'Barbera', 'Muscat', 'Pinot Blanc', 'Spanish White', 'Chenin Blanc', 
'Albarino', 'Carmenere', 'Rhone-style White Blend']

# Grenache(1,949)
# Gewurztraminer(1,831)
# Port Blend(1,612)
# Petite Sirah(1,586)
# Barbera(1,451)
# Muscat(1,395)
# Pinot Blanc(1,284)
# Spanish White(1,256)
# Chenin Blanc(1,194)
# Albarino(1,138)
# Carmenere(1,120)
# Rhone-style White Blend(1,030)
# Mourvedre(665)
# Petit Verdot(519)
# Spanish Red(516)
# Torrontes(471)
# Semillon(395)
# Pinotage(366)
# Roussanne(322)
# Sherry(283)
# Carignan(248)
# Greek White(240)
# Greek Red(221)
# Marsanne(194)
# White blend(42)
# Madeira(33)
# Bordeaux-style White Blend(7)
# Other(7)
# Portuguese red(3)

def find_max_page_number(base_url, header):
    """
    Find the last page number for the wine in question 
    """
    url_to_mine = base_url + str(1)
    r = requests.Session()
    r.headers = header
    response = r.get(url_to_mine)
    soup = BeautifulSoup(response.content, 'html.parser')
    max_page_number = int(soup.find_all("div", class_="pagination-wrapper")[0].find_all('a')[-1].text)
    print ('return max_page_number : %d'%max_page_number)
    return max_page_number

def scrape_wine_links(base_url, min_page_number, max_page_number, header, wine_variety, proxies=None):
    wine_pages_to_mine = []
    print('scrap wine_pages_to_mine for: %s'%wine_variety)
    
    if not max_page_number:
        max_page_number = find_max_page_number(base_url, header)
    
    for page_number in tqdm(range(min_page_number, max_page_number+1)):   
        url_to_mine = base_url + str(page_number)
        r = requests.Session()
        # r.proxies = proxies
        r.headers = header
        try:
            response = r.get(url_to_mine)
            soup = BeautifulSoup(response.content, 'html.parser')

            all_wine_links = soup.find_all("a", class_="review-listing")
            all_wine_links = [a.get('href') for a in all_wine_links]
            wine_pages_to_mine.extend(all_wine_links)
        except:
            continue

    l_ini = len (wine_pages_to_mine)        
    wine_pages_to_mine = list(set(wine_pages_to_mine))
    l_end = len (wine_pages_to_mine) 
    if not (l_ini-l_end): print('%d duplicated web addresses suppr...'%(l_ini-l_end))

    series_wine_pages = pd.Series(wine_pages_to_mine)
    series_wine_pages.to_csv('data/wine_pages_to_mine_%s.csv'%wine_variety.replace(' ', '_').replace('/', '_'))
    return wine_pages_to_mine


class WineInfoScraper:

    def __init__(self, wine_page_to_mine, header, proxies=None):
        self.page = wine_page_to_mine
        # self.proxies = proxies
        self.user_agent = header
        self.get_name_in_process = False


    def get_soup_wine_page(self):

        r = requests.Session()
        # r.proxies = self.proxies
        r.headers = self.user_agent
        wine_review_response = r.get(self.page)
        if DEBUG: print(wine_review_response)

        wine_review_soup = BeautifulSoup(wine_review_response.content, 'html.parser')
        return wine_review_soup


    def get_wine_name(self, soup):
        # wine_name_raw = soup.find(class_='article-title')
        wine_name_raw = soup.find(class_='title')
        wine_name_clean = wine_name_raw.text
        # print(wine_name_clean)
        return wine_name_clean


    def get_vintage(self, wine_name_clean):
        name_strings = wine_name_clean.split(' ')
        number_strings = [i for i in name_strings if (i.isnumeric())]
        for n in number_strings:
            if 1900 < int(n) < datetime.datetime.now().year:
                vintage = n
                return vintage
            else:
                continue


    def get_wine_rating(self, soup):
        wine_rating_raw = soup.find(class_='rating')
        wine_rating_text = wine_rating_raw.text
        wine_rating_list = wine_rating_text.split('\n')
        wine_rating_clean = wine_rating_list[1]
        return wine_rating_clean


    def get_wine_description(self, soup):
        wine_description_raw = soup.find(class_='description')
        if DEBUG: 
            print('wine_description_raw', wine_description_raw)
            # pdb.set_trace()
        wine_description_clean = wine_description_raw.text
        if DEBUG: print('wine_description_clean', wine_description_clean)
        return wine_description_clean


    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]


    def get_wine_info(self, soup, primary_secondary):
        wine_info_raw = soup.find(class_=primary_secondary)
        wine_info_text = wine_info_raw.text
        wine_info_list = wine_info_text.split('\n')
        wine_info_list_no_blanks = [w for w in wine_info_list if len(w) > 1]

        # Break the list of wine information up into chunks of two
        wine_info_list_chunked = list(self.chunks(wine_info_list_no_blanks, 2))

        # Each chunk will consist of a label and a value. Put these into a dictionary format for easier navigating
        wine_info_dict = {}
        for w in wine_info_list_chunked:
            # When extracting the price make sure to eliminate the 'noise' in the text string
            if w[0] == 'Price':
                clean_price_list = str(w[1]).split(',')
                wine_info_dict['Price'] = clean_price_list[0]
                continue

            # when extracting hte appellation then ma
            if w[0] == 'Appellation':
                appellation_split = w[1].split(',')
                wine_info_dict['Country'] = appellation_split[-1]
                if len(appellation_split) > 1:
                    wine_info_dict['Province'] = appellation_split[-2]
                if len(appellation_split) > 2:
                    wine_info_dict['Region'] = appellation_split[-3]
                if len(appellation_split) > 3:
                    wine_info_dict['Subregion'] = appellation_split[-4]

            if len(w) >= 2:
                if w[0] in list_interesting_col:
                    wine_info_dict[w[0]] = w[1]
                elif w[1] in list_interesting_col:
                    wine_info_dict[w[1]] = w[0]

            else:
                continue

        return wine_info_dict


    def get_reviewer_name(self, soup):
        wine_reviewer_raw = soup.find(class_='taster')
        wine_reviewer_clean = wine_reviewer_raw.text
        wine_reviewer_info_list = wine_reviewer_clean.split('\n')
        wine_reviewer_info_list_no_blanks = [w for w in wine_reviewer_info_list if len(w) > 1]
        wine_reviewer_clean = wine_reviewer_info_list_no_blanks[0]
        return wine_reviewer_clean


    def get_reviewer_twitter_handle(self, soup):
        wine_reviewer_twitter_raw = soup.find(class_='twitter-handle')
        try:
            wine_reviewer_twitter_clean = wine_reviewer_twitter_raw.text
            return wine_reviewer_twitter_clean
        except:
            return None


    def scrape_all_info(self):
        wine_info_dict = {}
        if DEBUG: print(self.page)
        wine_info_dict['url'] = self.page

        wine_review_soup = self.get_soup_wine_page()

        # if DEBUG: print(wine_review_soup)

        wine_info_dict['Name'] = self.get_wine_name(wine_review_soup)
        wine_info_dict['Vintage'] = self.get_vintage(wine_info_dict['Name'])
        wine_info_dict['Rating'] = self.get_wine_rating(wine_review_soup)
        wine_info_dict['Description'] = self.get_wine_description(wine_review_soup)

        wine_info_dict.update(self.get_wine_info(wine_review_soup, primary_secondary='primary-info'))
        wine_info_dict.update(self.get_wine_info(wine_review_soup, primary_secondary='secondary-info'))

        if self.get_name_in_process:
            try:
                wine_info_dict['Reviewer'] = self.get_reviewer_name(wine_review_soup)
            except:
                des_split = wine_info_dict['Description'].split('                      ') # 22 spaces
                try:
                    wine_info_dict['Description_bis'] = des_split[1]
                    wine_info_dict['Reviewer'] = des_split[-1]

                except:
                    try:
                        wine_info_dict['Reviewer'] = soup.find(class_='description').find(class_='taster-area').text
                    except:
                        wine_info_dict['Reviewer'] = ''
            try:
                wine_info_dict['Reviewer Twitter Handle'] = self.get_reviewer_twitter_handle(wine_review_soup)
            except:
                wine_info_dict['Reviewer Twitter Handle'] = ''

        return wine_info_dict


def mine_all_wine_info(wine_variety):
    
    # proxies = {'http': 'http://user:pass@13.59.204.225:8080'}
    proxies = None
    
    file_pages_to_mines = 'data/wine_pages_to_mine_%s.csv'%wine_variety.replace(' ', '_').replace('/', '_')
    if (os.path.isfile(file_pages_to_mines)):
        all_wine_links = pd.read_csv(file_pages_to_mines, index_col=0).values#[:5]
        
        all_wine_links = [k[0] for k in all_wine_links]
    else:
        all_wine_links = scrape_wine_links(base_url='https://www.winemag.com/?s=&drink_type=wine&varietal=%s&page='%wine_variety,
                                           min_page_number=1,
                                           max_page_number=0,
                                           proxies=proxies,
                                           header={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}, 
                                           wine_variety=wine_variety)

    if DEBUG: print(all_wine_links)

    all_wine_info = []


    wine_info_file_path = 'data/all_scraped_wine_info_%s.csv'%(wine_variety.replace(' ', '_').replace('/', '_')) + '_test'*DEBUG

    # if the file exists
    bool_is_wine_info_file = False
    idx_begin = 0
    if os.path.isfile(wine_info_file_path):
        bool_is_wine_info_file = True
        df_wine_info = pd.read_csv(wine_info_file_path, index_col=0)
        idx_begin = len(pd.read_csv(wine_info_file_path))
        # all_wine_links = all_wine_links[len(pd.read_csv(wine_info_file_path)):]
        print('start at', idx_begin)

    idx_link = 0
    for link in tqdm(all_wine_links):
        if idx_link >= idx_begin:
            if DEBUG:
                scraper = WineInfoScraper(wine_page_to_mine=link, proxies=proxies, header={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
                wine_info = scraper.scrape_all_info()
                print('wine info = ', wine_info)
                all_wine_info.append(wine_info)
            else:
                try:
                    scraper = WineInfoScraper(wine_page_to_mine=link, proxies=proxies, header={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
                    wine_info = scraper.scrape_all_info()
                    all_wine_info.append(wine_info)
                except:
                    continue
                    print('%s na pas pu etre scrappe'%link)
            # sleep(5)
        idx_link += 1

    
    full_wine_info_dataframe = pd.DataFrame(all_wine_info)
    # pd.DataFrame(all_wine_info).to_csv('data/dump_test.csv')
    if DEBUG: print(all_wine_info)
    # Si on ne veut garder que quelques colonnes 
    # full_wine_info_dataframe = full_wine_info_dataframe[['Alcohol', 'Appellation', 'Bottle Size', 'Category', 'Country',
    #                                                      'Date Published', 'Description', 'Designation', 'rating',
    #                                                      'Name', 'Price', 'Province', 'Rating', 'Region', 'Reviewer',
    #                                                      'Reviewer Twitter Handle', 'Subregion', 'User Avg Rating',
    #                                                      'Variety', 'Vintage', 'Winery']]

    # if already a file, just concat the old one and the new one together ! 
    if bool_is_wine_info_file:
        full_wine_info_dataframe = pd.concat((df_wine_info, full_wine_info_dataframe))
        full_wine_info_dataframe = full_wine_info_dataframe[~full_wine_info_dataframe.duplicated()]
    
    full_wine_info_dataframe.to_csv(wine_info_file_path)

    print(full_wine_info_dataframe)


if __name__ == '__main__':
    
    wine_variety = 'Riesling'
    # for wine_variety in wine_varieties[::-1][4:]:

    wine_varieties = wine_varieties[14:17]
    wine_varieties = ['Chardonnay']
    wine_varieties = ['Zinfandel']
    # wine_varieties = ['Malbec', 'Rhone-style Red Blend']
    print(wine_varieties)

    for wine_variety in wine_varieties:
        mine_all_wine_info(wine_variety)
