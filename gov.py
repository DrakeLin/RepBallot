from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import csv
import time

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

def runPage(hyperlink):
    raw_html = simple_get(hyperlink)
    soup = BeautifulSoup(raw_html, 'html.parser')
    links = soup.findAll('a')
    li = []
    for l in links:
        link =l.get('href')
        if link != None and link[:16] == '/legislative/LIS':
            li.append('https://www.senate.gov/' + link)
    return li

def runSingleVote(hyperlink):
    #Setup
    print(hyperlink)
    raw_html = simple_get(hyperlink)
    soup = BeautifulSoup(raw_html, 'html.parser')

    #Question Name
    question = soup.find('div', attrs={"style": "padding-bottom:10px;"})
    if not question:
        print(hyperlink)
        return 
    question = question.text.strip()[10:].split()
    ques = ''
    for q in question:
            ques = ques + ' ' + q

    #Measure Number
    measure = soup.find('div', attrs={'class': 'contenttext', "style": "padding-bottom:10px;"})
    meas = ''
    if measure:
        measure = measure.text.strip().split()[2:]
        for m in measure:
            meas = meas + ' ' + m
    else:
        meas = "Motion"

    #Measure URL
    urls = soup.findAll('a')
    url = ''
    for l in urls:
        u =l.get('href')
        if u != None and u[:29] == 'http://www.congress.gov/bill/':
            url = u
            break
    if url is '':
        url = "Motion"

    #votes
    votes = soup.find('span', attrs={'class': 'contenttext'})
    votes = votes.text.strip().split()
    iter_votes = iter(votes)

    #date
    date = soup.findAll('div', attrs={"style": "float:left; min-width:200px; padding-bottom:10px;", 'class': 'contenttext'})
    da = []
    for d in date:
        da.append(d.text.strip())
    date = da[1][11:]

    #writing
    with open('votes.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)
        #for each one write
        for i in range(len(votes)//3):
            try:
                name = next(iter_votes)
                party = next(iter_votes)
                if party[0] != '(':
                    name= name + ' ' + party
                    party = next(iter_votes)
                state = party[3:5]
                party = party[1]
                vote = next(iter_votes)
                writer.writerow([name, party, state, ques, meas, url, date, vote])
            except:
                break
            
def runYear(year):
    congress = (year - 1787)/2.0
    session = 1
    if congress != round(congress):
        session = 2
    congress = int(congress)
    senate_link = 'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_' + str(congress) + '_' + str(session) + '.htm'

    links = runPage(senate_link)
    with open('votes.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Name', 'Party', 'State', 'Question', 'Measure', 'URL', 'Date', 'Vote'])
    for l in links:
        runSingleVote(l)

def searchRep(state):
    with open('votes.csv') as csv_file:
        csv_reader = csv.reader(csv_file)
        info = [[] for i in range(8)]
        for row in csv_reader:
            if row[2] == state:
                for i in range(8):
                    info[i].append(row[i])
    with open('' + state + '_votes.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Name', 'Party', 'State', 'Question', 'Measure', 'URL', 'Date', 'Vote'])
        for i in range(len(info[0])):
            r = []
            for j in info:
                r.append(j[i])
            writer.writerow(r)

if __name__== "__main__":
   runYear(2019)
