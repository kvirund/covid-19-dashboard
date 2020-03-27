import json
import os
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output


def save_state(_state):
    with open("state.json", "wt") as f:
        json.dump(_state, f)


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
            if "Country_Region" in csv:
                csv.rename(columns={"Country_Region": "Country/Region", "Province_State": "Province/State"},
                           inplace=True)
                csv.drop(columns={"FIPS", "Admin2", "Lat", "Long_"}, inplace=True)
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


def get_by_countries(_countries):
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


def build_app(_state):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    result = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    result.layout = html.Div(children=[
        html.H1("COVID-19 dashboard"),
        dcc.Tabs(children=[dcc.Tab(label='General', children=[dcc.Dropdown(id='general-selection',
                                                                           options=[{'label': c, 'value': c} for c in
                                                                                    {"Confirmed", "Deaths", "Recovered",
                                                                                     "Active", "Death/Outcome"}],
                                                                           multi=True,
                                                                           value=state["types"]["types"]),
                                                              dcc.Dropdown(id='general-countries',
                                                                           options=[{'label': c, 'value': c} for c in
                                                                                    sorted(countries)] + [
                                                                                       {
                                                                                           'label': "Total",
                                                                                           'value': "Total"}],
                                                                           multi=True,
                                                                           value=state["types"]["countries"]),
                                                              dcc.Graph(id='general-graph',
                                                                        figure={'layout': {
                                                                            'title': 'Select type to display its graph'}})]),
                           dcc.Tab(label='By Countries', children=[
                               dcc.Dropdown(id='by-country-selection',
                                            options=[{'label': c, 'value': c} for c in sorted(countries)],
                                            multi=True, value=_state["countries"]),
                               dcc.Graph(id='by-country-graph',
                                         figure=get_by_countries(_state["countries"]))])])
    ])
    return result


def fixdate(match):
    day = int(match.group(1))
    month = int(match.group(2))
    year = re.sub("^20(\\d+)$", "\\1", match.group(3))
    result = "{:02d}/{:02d}/20{}".format(day, month, year)
    return result


def load_general_data():
    _confirmed = pd.read_csv(
        'COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
    _confirmed.rename(columns=lambda x: re.sub("^(\\d+)/(\\d+)/(\\d+)$", fixdate, x),
                      inplace=True)
    _deaths = pd.read_csv('COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
    _deaths.rename(columns=lambda x: re.sub("^(\\d+)/(\\d+)/(\\d+)$", fixdate, x),
                   inplace=True)
    _recovered = pd.read_csv(
        'COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')
    _recovered.rename(columns=lambda x: re.sub("^(\\d+)/(\\d+)/(\\d+)$", fixdate, x),
                      inplace=True)

    return {
               'Confirmed': _confirmed.sum()[3:],
               'Deaths': _deaths.sum()[3:],
               'Recovered': _recovered.sum()[3:],
               'Active': _confirmed.sum()[3:] - _recovered.sum()[3:] - _deaths.sum()[3:],
               'Death/Outcome': 100 * _deaths.sum()[3:] / (_recovered.sum()[3:] + _deaths.sum()[3:])}, {
               'Confirmed': _confirmed.groupby("Country/Region").sum().T[3:],
               'Deaths': _deaths.groupby("Country/Region").sum().T[3:],
               'Recovered': _recovered.groupby("Country/Region").sum().T[3:],
               'Active': _confirmed.groupby("Country/Region").sum().T[3:] - _recovered.groupby(
                   "Country/Region").sum().T[3:] - _deaths.groupby("Country/Region").sum().T[3:],
               'Death/Outcome': 100 * _deaths.groupby(
                   "Country/Region").sum().T[3:] / (_recovered.groupby(
                   "Country/Region").sum().T[3:] + _deaths.groupby("Country/Region").sum().T[3:])
           }


if __name__ == '__main__':
    data, countries = load_by_country_data()
    countries_data = get_countries_data(data, countries)
    general_data, general_countries = load_general_data()

    state = {"countries": [], "types": {"types": [], "countries": []}}
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
    except IOError:
        pass

    app = build_app(state)


    @app.callback(Output(component_id='by-country-graph', component_property='figure'),
                  [Input(component_id='by-country-selection', component_property='value')])
    def update_by_countries_graph(_countries):
        result = get_by_countries(_countries)
        state["countries"] = _countries
        save_state(state)
        return result


    @app.callback(Output(component_id='general-graph', component_property='figure'),
                  [Input(component_id='general-selection', component_property='value'),
                   Input(component_id='general-countries', component_property='value')])
    def update_general_graph(types, _countries):
        result = {
            'data': [
            ],
            'layout': {
                'title': "Developing COVID-19 cases day-by-day: [{}], [{}]".format(", ".join(types) if types else "",
                                                                                   ", ".join(
                                                                                       _countries) if _countries else "")}
        }
        for _type in types if types else []:
            if "Total" in _countries:
                result['data'].append({'type': 'scatter',
                                       'x': list(general_data[_type].keys()),
                                       'y': list(general_data[_type]),
                                       'name': "{1} ({0})".format("Total", _type)}
                                      )
            for _country in _countries if _countries else []:
                if "Total" != _country:
                    result['data'].append({'type': 'scatter',
                                           'x': list(general_countries[_type][_country].keys()),
                                           'y': list(general_countries[_type][_country]),
                                           'name': "{1} ({0})".format(_country, _type)}
                                          )
        state["types"]["types"] = types
        state["types"]["countries"] = _countries
        save_state(state)
        return result


    app.run_server(debug=False)
