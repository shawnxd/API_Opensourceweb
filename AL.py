
# coding: utf-8

# In[1]:


from selenium import webdriver
from urllib import parse
import bs4
import re
import time
import pandas as pd
def load_data(State):
    dblocation = '/Users/graceli/Desktop/SBR automation/Company Database.db'
    import pandas as pd
    import sqlite3
    conn = sqlite3.connect(dblocation)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    data = pd.read_sql_query("SELECT CompanyName from CompanyData WHERE State='"+State+"'", conn)
    return data['CompanyName']
def get_soup(driver):
    html = driver.page_source
    soup = bs4.BeautifulSoup(html,'html.parser')
    return soup
def save_result(results,State):
    results = pd.DataFrame(results)[['CompanyName','regName','regNumber','RegDate', 'Jurisdiction','entType','status','address']]
    results.to_csv(State+'_results.csv',index=False)
    return results


# ## Connect database

# In[20]:


AL = load_data('AL')


# In[21]:


AL


# ## Search function

# In[12]:


def ALbusiness(business):
    url = 'http://arc-sos.state.al.us/CGI/CORPNAME.MBR/INPUT'
    driver = webdriver.Chrome()
    driver.get(url)
 
    search = driver.find_element_by_xpath('//*[@id="block-sos-content"]/div/div/div[1]/form/div[1]/input')
    search.send_keys(business)
 
    submit = driver.find_element_by_xpath('//*[@id="block-sos-content"]/div/div/div[1]/form/div[6]/input')
    submit.click()
 

    time.sleep(1)
 
    if get_soup(driver)       .find(string = 'No matches found. ') != None:
        driver.quit()
        return [' ']*7
 
    driver    .find_element_by_xpath('//*[@id="block-sos-content"]/div/div/div/table/tbody/tr[1]/td[1]/a')    .click()
 
    time.sleep(3)
 
    soup = get_soup(driver)
    entType = soup.find("span",{"id":"MainContent_lblEntityType"}).text
    regNumber = soup.find("span",{"id":"MainContent_lblIDNumber"}).text
    regName = soup.find("span",{"id":"MainContent_lblEntityName"}).text
    status = ' '
    RegDate = soup.find("span",{"id":"MainContent_lblOrganisationDate"}).text
    try:
        Jurisdiction = soup.find("span",{"id":"MainContent_lblJurisdiction"}).text.split(":")[1].strip()
    except:
        Jurisdiction = ' '
    address = ' '
    driver.quit()
    return [regNumber, regName, RegDate, Jurisdiction, entType, status, address]


# In[32]:


def F1(search,entity_name):
    try:
        search = search.lower().replace(',','').split()
        entity_name = entity_name.lower().replace(',','').split()               
        a = len([x for x in entity_name if x in search])
        b = len(entity_name)
        c = len(search)
        recall = a/b
        precision = a/c
        return 2*recall*precision/(recall + precision)
    except:
        return 0


# In[35]:


def ALbusiness(business):
    driver = webdriver.Chrome()
    url = "http://arc-sos.state.al.us/CGI/CORPNAME.MBR/INPUT"
    driver.get(url)
    text = driver.find_element_by_name("search")
    text.send_keys(business)
    search_button = driver.find_element_by_xpath('//*[@id="block-sos-content"]/div/div/div[1]/form/div[6]/input')
    search_button.click()
    time.sleep(3)
    soup = get_soup(driver)
    company_info = list(map(lambda x: x.text, soup.find_all('td')[:-1]))
    company_list = []
    if len(company_info) < 5:
        driver.quit()
        print('No result')
        return [' ']*7
    company_list = []
    for i in range(len(company_info)//5):
        company_list.append({
        "Entity ID": company_info[i*5],
        "Entity Name": company_info[i*5+1]
        })
    company_list = pd.DataFrame(company_list)
    company_list['score'] = company_list['Entity Name'].apply(lambda x: F1(x,business))
    if max(company_list['score']) < 0.1:
        driver.quit()
        print('No result')
        return [' ']*7
    best_match = company_list.loc[company_list.score.idxmax(),'Entity Name']
    ## get details
    button = driver.find_element_by_xpath('//*[text()="'+best_match+'"]')
    button.click()
    time.sleep(3)
    soup_best = get_soup(driver)
    best_details = list(map(lambda x: x.text,soup_best.find_all('td')))
    best_details = list(map(lambda x: ' '.join(x.replace('\n','').replace('\xa0','').split()),best_details))[1:]
    idx1 = best_details.index('Capital Paid In')
    company_name  = best_details[:idx1]
    infodic = {'Principal Address':' ',
               'Entity Type':' ',
               'Principal Address':' ',
               'Formation Date':' ',
               'Status':' '
              }
    for i in range(len(company_name)//2):
        infodic[company_name[2*i]] = company_name[2*i + 1]
    address = infodic['Principal Address']
    Jurisdiction = ' '
    entType = infodic['Entity Type']
    regNumber = infodic['Entity ID Number']
    regName = best_match
    status = infodic['Status']
    RegDate = infodic['Formation Date']
    driver.quit()
    return [regNumber, regName, RegDate, Jurisdiction, entType, status, address]


# ## Save Results

# In[16]:


AL_results = []


# In[36]:


for business in AL[len(AL_results):100]:
    searchResult = ALbusiness(business)
    AL_results.append({'CompanyName':business,'regNumber':searchResult[0], 'regName':searchResult[1],
                                    'RegDate':searchResult[2], 'Jurisdiction':searchResult[3],
                                     'entType':searchResult[4],
                                     'status': searchResult[5],'address':searchResult[6]})


# In[38]:


save_result(AL_results,'AL')

