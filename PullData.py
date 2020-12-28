# FileName: PullData.py

# Description: Pulls data from John Hopkins University. Designed
#              to run daily

# Date Last Modified: 26 Nov 2020

# -----------------------------

# imports
import pandas as pd 
import datetime
from datetime import date
import time
##################################

def timer( func ):
    '''
    decorator
    prints the time of a function for logging purposes
    '''
    def inner():
        today = datetime.date.today()
        start = time.time()
        func()
        end = time.time()
        delta = end - start
        print("Function ran:{} taking {} minutes and {} seconds".format( today,round( (delta // 60 ),2), round( delta % 60, 2)))
        print()

    return inner


def convertDate( dateObj ):
    '''
    takes a datetime.date object as input
    and returns it in "MM-DD-YYYY" format
    '''
    year = str(dateObj.year)
    month = dateObj.month
    if month < 10:
        month = '0' + str(month)
    else:
        month = str( month )
    day = dateObj.day
    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)

    return month + '-' + day + '-' + year



def makeRequest(dateObj):
    '''
    takes a datetime object, makes request to get data,
    and returns dataframe object
    '''

    path = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/'

    strDate = convertDate( dateObj ) 

    try:
        df = pd.read_csv(path + strDate + '.csv', dtype={"FIPS":str} )
        df['Date'] = strDate # add a date column

        

        # clean the fips code
        df['FIPS'] = df['FIPS'].map(cleanFips )


    except Exception as e:
        print( e )


    return df

def cleanFips(string):
    '''
    Function to clean the fips code and ensure that it is 5 characters
    Takes a string as input
    '''
    string = str(string)

    if (len(string) < 5):
        string = '0' + string

    return string

@timer
def pullData():
    '''
    Pulls data from John Hopkins University's GitHub. 
    Designed to run daily
    '''
    startDate = date(2020,4,20) # day records start 
    endDate = date.today() # day to stop collecting records

    masterDf = makeRequest( startDate ) 


    # Start looping through all the days
    delta = endDate - startDate

    for d in range(1, delta.days):

        currentDate = startDate + datetime.timedelta(days=d)

        current = makeRequest( currentDate )

        masterDf = pd.concat( [ masterDf, current ], sort=True  )

    fipsCodes = masterDf['FIPS'].unique()

    print("Last Date seen:", currentDate )


    masterDf.to_csv("data.csv")
    

if __name__ == '__main__':
    pullData()

    
