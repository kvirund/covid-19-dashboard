import os
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output


def load_by_country_data():
    daily_reports_dir = 'COVID-19/csse_covid_19_data/csse_covid_19_daily_reports'
    files = [f for f in os.listdir(daily_reports_dir) if os.path.isfile(os.path.join(daily_reports_dir, f))]
    pattern = re.compile("^(\\d+)-(\\d+)-(\\d+).csv$")
    output_data = {}
    counter = 0
    output_countries = set()
    for file in files:
        matches = pattern.search(file)
        if matches:
            counter = 1 + counter
            date_id = "{}-{}-{}".format(matches.group(3), matches.group(1), matches.group(2))
            file_path = os.path.join(daily_reports_dir, file)
            csv = pd.read_csv(file_path)
            output_data[date_id] = csv
            output_countries.update(csv["Country/Region"].unique())
    print("Loaded {} files".format(counter))
    print({c: c for c in output_countries})
    return output_data, output_countries


def get_countries_data(input_data, input_countries):
    result = {c: {} for c in input_countries}
    for date, csv_values in input_data.items():
        for value in csv_values.values:
            country = value[1]
            if date not in result[country]:
                result[country][date] = 0
            result[country][date] = result[country][date] + value.item(3)
    return result


def build_app():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    result = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    result.layout = html.Div(children=[
        html.H1("COVID-19 dashboard"),
        dcc.Tabs(children=[dcc.Tab(label='General', children=[dcc.Dropdown(id='general-selection',
                                                                           options=[{'label': c, 'value': c} for c in
                                                                                    {"Confirmed", "Deaths", "Recovered",
                                                                                     "Active"}], multi=True),
                                                              dcc.Graph(id='general-graph', figure={'layout': {
                                                                  'title': 'Select type to display its graph'}})]),
                           dcc.Tab(label='By Countries', children=[
                               dcc.Dropdown(id='by-country-selection',
                                            options=[{'label': c, 'value': c} for c in sorted(countries)],
                                            multi=True),
                               dcc.Graph(id='by-country-graph',
                                         figure={'layout': {'title': 'Select country to display developing graph'}})])])
    ])
    return result


def load_general_data():
    _confirmed = pd.read_csv('COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv')
    _deaths = pd.read_csv('COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv')
    _recovered = pd.read_csv('COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv')
    return {'Confirmed': _confirmed.sum()[3:], 'Deaths': _deaths.sum()[3:], 'Recovered': _recovered.sum()[3:],
            'Active': _confirmed.sum()[3:] - _recovered.sum()[3:] - _deaths.sum()[3:]}


if __name__ == '__main__':
    data, countries = load_by_country_data()
    countries_data = get_countries_data(data, countries)
    general_data = load_general_data()

    app = build_app()


    @app.callback(Output(component_id='by-country-graph', component_property='figure'),
                  [Input(component_id='by-country-selection', component_property='value')])
    def update_by_countries_graph(_countries):
        result = {
            'data': [
            ],
            'layout': {
                'title': "Developing COVID-19 cases day-by-day in countries: [{}]".format(
                    ", ".join(_countries) if _countries else "")}
        }
        for country in _countries if _countries else []:
            result['data'].append({'type': 'scatter',
                                   'x': list(countries_data[country].keys()),
                                   'y': list(countries_data[country].values()),
                                   'name': country}
                                  )
        return result


    @app.callback(Output(component_id='general-graph', component_property='figure'),
                  [Input(component_id='general-selection', component_property='value')])
    def update_general_graph(types):
        result = {
            'data': [
            ],
            'layout': {
                'title': "Developing COVID-19 cases day-by-day: [{}]".format(", ".join(types) if types else "")}
        }
        for _type in types if types else []:
            result['data'].append({'type': 'scatter',
                                   'x': list(general_data[_type].keys()),
                                   'y': list(general_data[_type]),
                                   'name': _type}
                                  )
        return result


    app.run_server(debug=False)
