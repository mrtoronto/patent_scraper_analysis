import json
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.firefox.options import Options
import requests, re, time, collections
from tqdm import tqdm as tqdm

DEBUG = False


def term_to_patents(term):
    """
    Function will take a search term and return a list of links to all the patents returned for that search term.
    Data pulled from:
        http://patft.uspto.gov/netahtml/PTO/search-bool.html

        Args:
            `term` - Str: Search term to query with.
        Returns:
            `patent_link_list` - List: List of links to all the patents returned when PatFT is queried with `term`.

    """
    search_url = f'http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r=0&f=S&l=50&TERM1={term}&FIELD1=&co1=AND&TERM2=&FIELD2=&d=PTXT'
    search_text = requests.get(search_url).text

    ### Grab the number of results for the search term
    n_results = int(re.search('DOCS: \d*', search_text).group().split(' ')[1])
    patent_link_list=[]
    ### Build a list of patent links with a length of `n_results`
    for i in range(1, n_results):
        patent_url = f'http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r={i}&f=G&l=50&co1=AND&d=PTXT&s1={term}&OS={term}&RS={term}'
        patent_link_list.append(patent_url)

    return patent_link_list


def patent_scrape(patent_url, patent_count):
    """
    Function will take a `patent_url` and return a dictionary of patent meta-data dictionary.

        Args:
            `patent_url` - Str: URL to scrape meta-data from.
        Returns:
            `page_dict` - Dict: Dictionary of meta-data.
    """

    ### Try to open a selenium browser.
    options = Options()
    options.headless = True
    try:
        browser = webdriver.Firefox(options=options)
        #browser = webdriver.Safari()
    ### If session fails, try to close any pre-existing browsers and re-try.
    except SessionNotCreatedException as e:
        print('Closing Session\n', e)
        browser.close()
        browser.quit()
        browser = webdriver.Firefox(options=options)
        #browser = webdriver.Safari()

    try:
        browser.get(patent_url)
        time.sleep(5)
    except:
        print('sleeping 5 seconds.')
        time.sleep(5)
        try:
            browser.get(patent_url)
            time.sleep(5)
        except:
            print('sleeping 60 seconds.')
            time.sleep(60)
            try:
                browser.get(patent_url)
                time.sleep(5)
            except:
                print(f'Returning blank for {patent_url}.')
                return {'page_url' : patent_url}, patent_count

    ### Grab the raw page_source
    html = browser.page_source

    ### Grab all the td elements from the browser and grab the text from each
    elements_list = browser.find_elements_by_xpath('//body/table/tbody/tr/td')
    elements_list = [i.text for i in elements_list]

    ### Grab all the "tables" with the width attribute set to 100% and grab the text from each
    tables_list = browser.find_elements_by_xpath('//body/table[@width="100%"]')
    tables_list = [i.text for i in tables_list]
    while len(tables_list) < 6:
        tables_list.append('')
    ### Grab the abstract section
    try:
        abstract = re.sub('\s+', ' ', browser.find_element_by_xpath('//body/p').text).strip()
    except:
        abstract = ''
    ### Grab the other_references using their unique width attribute.
    try:
        other_references = browser.find_element_by_xpath('//body/table[@width="90%"]').text
        other_references = [re.sub("^\.", "", i) for i in other_references.split('\n')]
    except:
        other_references = ''
    ### Close the browser for speed boost
    browser.close()
    browser.quit()
    ### Remove tags and new-line characters from page source.
    subbed_html = re.sub('(<.{1,7}>)|(\n)', "", html)

    page_dict = {}

    if re.search('Primary Examiner:.*', html):
        primary_examiner = re.search('Primary Examiner:.*', html).group()
    else:
        primary_examiner = ''
    if re.search('Attorney, Agent or Firm:.*', html):
        attorney = re.search('Attorney, Agent or Firm:.*', html).group()
        attorney = re.sub('(<.{1,7}>)|(Attorney, Agent or Firm:)', "", attorney)
    else:
        attorney = ''
    if re.search('.{3} \d{1,2}, \d{4}', tables_list[3]):
        publication_date = re.search('.{3} \d{1,2}, \d{4}', tables_list[3]).group()
    else:
        publication_date = ''
    if re.search('(\d{1,3},)+(\d{1,3})', tables_list[1]):
        document_number = re.search('(\d{1,3},)+(\d{1,3})', tables_list[1]).group()
    else:
        document_number = ''

    main_references = re.findall('.*\\n.*\\n.*\\n?', tables_list[5].strip())
    main_references = [re.sub('\\n', '; ', i).strip() for i in main_references]

    ### Box starts with "United States Patent"
    box_1 = [i.strip() for i in tables_list[1].split('\n') if i.strip() != '']
    while len(box_1) < 2:
        box_1.append('')
    ### Box starts with "Inventors"
    box_2 = [i.strip() for i in tables_list[2].split('\n') if i.strip() != '']
    while len(box_2) < 3:
        box_2.append('')

    if re.search("Type *.*", box_2[2]):
        applicant = re.search("Type *.*", box_2[2]).group()[5:].strip()
    else:
        applicant = ''
    ### Use this regex pattern to isolate the claims from the subbed page source
    claims = re.search("  Claims.{1,30}1\. {1,2}.*  ((Description)|(DESCRIPTION))", subbed_html)

    ### If pattern finds claims,
    if claims:
        claims = claims.group()
        claims = re.sub(' +Description', "", claims)
        ### Split on pattern with 1-2 digits followed by . and two spaces
        ###     Example: 1.  Example text example text. 2.  Blah blah blhah
        claims = [i.strip() for i in re.split('\d{1,2}.  ', claims) if i != '']
    if DEBUG == True:
        print(patent_url)

    page_dict['page_url'] = patent_url
    page_dict['primary_examiner'] = re.sub("Primary Examiner:</i> ", "", primary_examiner)
    page_dict['attorney'] = re.sub("Attorney, Agent or Firm:</i> ", "", attorney)
    page_dict['publication_date'] = publication_date
    page_dict['document_number'] = document_number
    page_dict['patent_number'] = box_1[1]
    page_dict['inventors'] = box_2[1]
    page_dict['applicant'] = applicant
    page_dict['abstract'] = abstract
    page_dict['claims'] = claims
    page_dict['cited_references'] = main_references
    page_dict['other_references'] = [reference.strip() for reference in other_references]
    if DEBUG == True:
        if claims:
            print(document_number, '\n', box_2[1], '\n', claims[:2000], '\n')
        else:
            with open(f'{patent_count}.txt', 'w') as f:
                f.write(subbed_html)
            patent_count += 1
            print(document_number, '\n', box_2[1], '\n', 'No claims', '\n')

    return page_dict, patent_count



def patents_metadata_extraction(term, res_start = 1, n_results = 0, export_path = None):
    """
    This function will take a term, gather all the patent links for the term then scrape the requested number of results from those links.
    """

    url_list = term_to_patents(term = term)

    patents_dict = {}

    if res_start < 1:
        print('res_start must be >= 1. Adjusted to 1.')
        res_start = 1

    if n_results > 0:
        url_list = url_list[res_start - 1 : n_results + res_start - 1]

    if export_path is not None:
        try:
            with open(f'{export_path}.json', 'r') as f:
                pre_existing_data = json.load(f)
                #pre_existing_data = {k : v for (k,v) in pre_existing_data.items() if v.get('document_number', '') != ''}
        except FileNotFoundError as e:
            print('No pre-existing data.', e)
            pre_existing_data = dict()
        pre_existing_valid_urls = [v.get('page_url', '') for (k,v) in pre_existing_data.items() if v.get('document_number', '') != '']
        url_list = [i for i in url_list if i not in pre_existing_valid_urls]

    patent_count = 0
    for patent in tqdm(url_list, total=len(url_list)):
        patent_dict = {}
        patent_dict, patent_count = patent_scrape(patent, patent_count)
        index_value = re.search("&r=\d*", patent_dict['page_url']).group()
        index_value = index_value.split('=')[1]
        index_value = int(index_value)
        patents_dict.update({f'{term}_{index_value:06d}' : patent_dict})

    if export_path is not None:
        patents_dict = {k : v for (k,v) in patents_dict.items() if (k not in pre_existing_data.keys())}
        patents_dict = {k : v for (k,v) in patents_dict.items() if v.get('document_number', '') != ''}
        pre_existing_data.update(patents_dict)

        pre_existing_data = {k : v for k, v in pre_existing_data.items()}
        pre_existing_data = collections.OrderedDict(sorted(pre_existing_data.items()))

        with open(f'{export_path}.json', 'w') as fout:
            json.dump(pre_existing_data, fout, indent = 4)
    return patents_dict


patents_metadata_extraction('microbiome', res_start = 1, n_results = 300, export_path = 'test1k2')
