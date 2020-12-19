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
        by_date['7_Day_Avg_'+col] = by_date[col].rolling(window=7).mean()

    by_date = by_date[7:]
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
# get county json data
# ----
#from urllib.request import urlopen
import json
#with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
#    counties = json.load(response)
with open("counties.json") as json_file:
    counties = json.load(json_file)


# Set up dashboard
df = read_and_clean()


# Get list of regions for dropdown menu
scope = list( df['Province_State'].unique() )
scope.insert(0, 'All U.S.')
scope_options = [ {'label':x, 'value':x } for x in scope]


# Get the list of value options (Confirmed, Active, Deaths) for drop down menu
df = transform_timeseries(df)
value_options = get_input_fields(df)

# -----
# app
# -----
app = dash.Dash()
app.layout = html.Div([
                        html.Div([
                                    html.H1('COVID-19 Dashboard'),
                                    html.H3('Data From John Hopkins University.')
                                ], style = {'text-align':'center', 'width':'100%','height':'125px', 'background-color':'#63A088'}),

                        dcc.Tabs(id='tabs-selector', value='tab-1', children=[
                            dcc.Tab(label='Time Series', value='tab-1'),
                            dcc.Tab(label='Heat Map', value='tab-2'),
                        ]),
                        html.Div(id='tabs-content')
                    ])





@app.callback(Output('tabs-content','children'),
              [Input('tabs-selector', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([

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

            ], style={"background-color":"#63A088", 'text-align':'center'})])

    else:
        return html.Div([
                        html.Div([
                            html.Label(['Region'], style={'margin':'50px'}),
                            dcc.Dropdown(id='state-selector',
                                        options=scope_options,
                                        value='Texas',
                                        multi=False,
                                        placeholder="Select a region")

                            ], style={'width':'50%', 'display':'inline-block'}),
                        html.Div([
                            html.Label(['Value Type:'], style={'margin':'50px'}),
                            dcc.Dropdown(id='z_selector',
                                        options=value_options,
                                        multi=False,
                                        value='Confirmed')
                            ], style = {'width':'50%', 'display':'inline-block'}),
                        html.Div([
                                    dcc.Graph(id='choropleth')

                            ], style={"background-color":"#63A088", 'text-align':'center'}),

                        html.Div(
                                dcc.Graph(id="click-timeseries")
                                )

        ])



@app.callback( Output("choropleth", "figure"),
              [Input("state-selector", "value"),
               Input("z_selector", "value")])
def display_choropleth(state, z_value):
    '''
    Call back that updates the choropleth heat map for the secondary tab
    Takes string of state name and string column value as input from drop downs
    NOTE: This works! If the heatmap is not rendering try running it while connected
    to the Interent (bug I encountered) or running alone to ensure libraries are
    up to date.
    '''
    data = read_and_clean()
    data = data[data["Province_State"]==state]
    date = list(data["Date"])[-1] # gets the most recent date
    data = data[data["Date"]==date]
    fig = px.choropleth(
                        data,
                        geojson=counties,
                        locations="FIPS",
                        color=z_value

    )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig

@app.callback( Output("click-timeseries", "figure"),
               [Input("choropleth", "clickData")])
def update_click_graph(clickData):
    data = read_and_clean()
    print("clickData =>",clickData)
    data = data[data["FIPS"]==clickData["points"][0]["location"]] # filters by county fipsCodes
    data_ts = transform_timeseries(data)

    traces = []
    for col in data_ts.columns:
        traces.append( {'x':data_ts.index, 'y':data_ts[col], 'name':str(col)})
    return {'data':traces, 'layout':go.Layout(title='COVID')}


@app.callback( Output('timeseries', 'figure'),
               [Input('scope-input', 'value'),
                Input('z-input', 'value')
                ])
def update_figure(scope, z):
    '''
    Callback that updates the the TimeSeries graph on the first tab.
    Takes 1 or more states and 1 or more columns as input
    '''
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
            traces.append( {'x':data.index, 'y':data[value], 'name':str(region)+' '+str(value)})

    return {'data':traces, 'layout':go.Layout(title='COVID')}


if __name__ == '__main__':
    app.run_server()
