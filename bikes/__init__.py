import os
import urllib
from functools import lru_cache

import requests

import pandas as pd
from ipywidgets import interact
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (8, 8)
plt.rcParams["font.size"] = 14
plt.rcParams["lines.linewidth"] = 4
plt.rcParams["lines.markersize"] = 10
plt.rcParams['axes.titlesize'] = 'x-large'
plt.rcParams['axes.labelsize'] = 'x-large'


@lru_cache(10)
def _get_velo_data(location, year=2016):
    BASE = "https://data.stadt-zuerich.ch/dataset/verkehrszaehlungen_werte_fussgaenger_velo/resource/"
    URLS = {
        2018: BASE + '13af0d7d-41e6-4212-aea3-cd04a4646665/download/2018verkehrszaehlungenwertefussgaengervelo.csv',
        2017: BASE + 'd17a0a74-1073-46f0-a26e-46a403c061ec/download/2017verkehrszaehlungenwertefussgaengervelo.csv',
        2016: BASE + "ed354dde-c0f9-43b3-b05b-08c5f4c3f65a/download/2016verkehrszaehlungenwertefussgaengervelo.csv",
        2015: BASE + "5c994056-eda6-48c5-8e61-28e96bcd04a3/download/2015verkehrszaehlungenwertefussgaengervelo.csv",
        2014: BASE + "bd2c9dd9-5b05-4303-a4c9-4a9f5b73e8f7/download/2014verkehrszaehlungenwertefussgaengervelo.csv",
        }

    if year not in URLS:
        raise ValueError("Year has to be one of 2014, 2015, 2016, 2017 "
                         "not %s." % year)

    fname = "bikes-%i.csv" % year
    if not os.path.exists(fname):
        with requests.get(URLS[year], stream=True) as r:
            r.raise_for_status()
            with open(fname, 'wb') as w:
                for chunk in r.iter_content(chunk_size=65535):
                    w.write(chunk)

    if year in (2016, 2017, 2018):
        data = pd.read_csv(fname, parse_dates=True, dayfirst=True, index_col='datum')
    else:
        data = pd.read_csv(fname, parse_dates=True, dayfirst=True, index_col='Datum')

    return data


@lru_cache(10)
def get_velo_data(location, year=2016):
    data = _get_velo_data(location, year)

    if year == 2015:
        data.columns = ["Objectid", "fk_zaehler", "velo_in",
                        "velo_out", "fuss_in", "fuss_out"]
    # filter by location
    data = data[data.fk_zaehler == location]

    # subselect only the Velo data
    data = data[["velo_in", "velo_out"]]

    data['total'] = data.velo_in + data.velo_out

    data.columns = ['North', 'South', 'Total']

    return data


@lru_cache(10)
def get_weather_data(year=2016):
    """Zurich weather data"""
    fname = 'weather-%i.html' % year
    if not os.path.exists(fname):
        data = ('messw_beg=01.01.{year}&messw_end=31.12.{year}&'
                'felder[]=Temp2m&felder[]=Windchill&'
                'felder[]=Regen&'
                'felder[]=Strahlung&felder[]=Feuchte&'
                'auswahl=2&combilog=mythenquai&suchen=Werte anzeigen')
        data = data.format(year=year)
        data = data.encode('ascii')

        req = urllib.request.Request(
            'https://www.tecson-data.ch/zurich/mythenquai/uebersicht/messwerte.php',
            method='POST',
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     'User-Agent': 'http://github.com/wildtreetech/talk-swiss-python-summit-2018'
                     },
            )

        with urllib.request.urlopen(req) as web:
            with open(fname, 'w') as local:
                local.write(web.read().decode('iso-8859-1'))

    df = pd.read_html(fname, attrs={'border': '1'}, skiprows=1)
    # take the first data frame from the list of data frames
    df = df[0]
    # this refers to the first column of the data frame now
    df[0] = pd.to_datetime(df[0], dayfirst=True)
    df.columns = ['Date', 'Temp', 'Windchill', 'Rain', 'Radiation', 'Humidity']
    df = df.set_index('Date')

    return df


def plot_by_year():
    @interact(station=['ECO09113499', 'Y2G12102806'],
              year=[2015, 2016, 2017, 2018])
    def plot(station, year=2017):
        data = get_velo_data(station, year=year)
        ax = data.resample("W").sum().plot()
        ax.set_xlabel("")

    return plot


def plot_weather():
    @interact(year=[2015, 2016, 2017, 2018])
    def plot(year=2017):
        weather = get_weather_data(year)
        ax = weather.resample("W").mean().Temp.plot()
        ax.set_ylabel('Temperature')
        ax2 = weather.resample("W").sum().Rain.plot.line(ax=ax, secondary_y=True)
        ax2.set_ylabel('Percipitation')
        ax2.set_ylim([0, weather.resample("W").sum().Rain.max() * 2.])
        ax.legend(loc=2)
        ax2.legend(loc='best')

    return plot


def plot_bike_weather():
    @interact(station=['ECO09113499', 'Y2G12102806'],
              year=[2015, 2016, 2017, 2018])
    def plot(station='ECO09113499', year=2017):
        data = get_velo_data(station, year=year)
        weather = get_weather_data(year)

        ax = data.resample("W").sum().Total.plot()
        ax.set_ylabel("Riders")
        ax2 = weather.resample("W").sum().Rain.plot.line(ax=ax,
                                                         secondary_y=True)
        ax2.set_ylabel('Percipitation')
        ax2.set_ylim([0, weather.resample("W").sum().Rain.max() * 2.])
        ax.grid()
        ax2.legend(loc=1)
        ax.legend(loc=2)

    return plot
