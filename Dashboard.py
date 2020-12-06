# File Name: Dashboard.py

# Description:

# ------------
# imports
# -----------
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output

# ----------
# read data
# ---------
def read_and_clean():
    '''
    Reads in data from .csv file and then cleans it
    '''
    df = pd.read_csv("data.csv", dtype={"FIPS":str})
    df.drop(columns=["Unnamed: 0"], inplace=True)

    # Filter for US Data only
    us_filter = df['Country_Region'] == 'US'
    df = df[us_filter]

    # Filter out weird 'Recovered US' in combined key
    rec_us = df['Combined_Key'] != 'Recovered, US'
    df = df[rec_us]

    return df

# -------
# transform_timeseries
# -------
def transform_timeseries( df, region=None):
    '''
    Transforms the passed dataframe into time series by grouping by "Date"
    Also adds some other columns for arguments. Args takes a list of dictionaries
    '''
    # perform filerting first
    if region:
        df = df[df['Province_State']==region]


    by_date = df.groupby('Date')[['Deaths','Confirmed','Active','Recovered']].sum()

    for col in ['Deaths', 'Confirmed', 'Active', 'Recovered']:
        by_date['Previous_'+col] = by_date[col].shift(periods=1, fill_value=0)

    for col in ['Deaths', 'Confirmed', 'Active', 'Recovered']:
        by_date['New_'+col] = by_date[col] - by_date['Previous_'+col]

    for col in ['Active', 'Confirmed', 'Deaths','New_Deaths','New_Active', 'New_Confirmed']:
        by_date['Rolling_'+col] = by_date[col].rolling(window=5).mean()

    return by_date

# --------
# generate input fields
# -------
def get_input_fields(df):
    '''
    Generates input field options
    '''


    # get labels
    cols = list( df.columns )
    def check(string):
        if 'Recovered' in string:
            return True
        if 'Deaths' in string:
            return True
        if 'Active' in string:
            return True
        if 'Confirmed' in string:
            return True
        return False

    value_options = [ {'label':x, 'value':x} for x in cols if x ]




    return value_options

def filters(df, *args):
    '''
    Working on filtering data by state, county, date
    '''
    for arg in args:
        print(arg)
        for key, value in arg.items():
            if value not in ['All', 'All U.S.']:
                filters = df[key] == value
                df = df[filters]

    return df


# ----------------
# main
# ---------------

# -----
# get counties
# ----
# from urllib.request import urlopen
# import json
# with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
#     counties = json.load(response)



# Set up dashboard
app = dash.Dash()
df = read_and_clean()

scope = list( df['Province_State'].unique() )
scope.insert(0, 'All U.S.')
scope_options = [ {'label':x, 'value':x } for x in scope]

df = transform_timeseries(df)

value_options = get_input_fields(df)


app.layout = html.Div([
                        html.Div([
                                    html.H1('COVID-19 Dashboard'),
                                    html.H3('Data From John Hopkins University.')
                                ], style = {'text-align':'center', 'width':'100%','height':'125px', 'background-color':'#63A088'}),

                        html.Div([
                            html.Label(['Region'], style={'margin':'50px'}),
                            dcc.Dropdown(id='scope-input',
                                        options=scope_options,
                                        value='All U.S.',
                                        multi=True,
                                        placeholder="Select a region")

                            ], style={'width':'50%', 'display':'inline-block'}),

                        html.Div([
                            html.Label(['Value Type:'], style={'margin':'50px'}),
                            dcc.Dropdown(id='z-input',
                                        options=value_options,
                                        multi=True,
                                        value='Confirmed')
                            ], style = {'width':'50%', 'display':'inline-block'}),

                        html.Div([
                                    dcc.Graph(id='timeseries')

                            ], style={"background-color":"#FFFCF7", 'text-align':'center'})])

@app.callback( Output('timeseries', 'figure'),
               [Input('scope-input', 'value'),
                Input('z-input', 'value')
                ])
def update_figure(scope, z):
    if isinstance(scope, str):
        scope = [scope]
    if isinstance(z, str):
        z = [z]
    df = read_and_clean()


    traces = []

    for region in scope:
        print(region)
        data = read_and_clean()
        if region=='All U.S.':
            data = transform_timeseries(data)
        else:
            data = transform_timeseries(data, region)


        for value in z:
            print(value)
            traces.append( {'x':data.index, 'y':data[value], 'name':region})

    return {'data':traces, 'layout':go.Layout(title='COVID')}


if __name__ == '__main__':
    app.run_server()
