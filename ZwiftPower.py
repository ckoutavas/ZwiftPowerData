import requests
from bs4 import BeautifulSoup
from typing import Tuple
import datetime
from zwift_routes import routes
import pandas as pd
import pycountry
import json


class ZwiftPower:
    def __init__(self, username: str, password: str) -> None:
        """
        Calling this class authenticates you to ZwiftPower and creates the country codes
        Once the requests.Session is created, you can make your own requests or use the functions:

        session = ZwiftPower('username', 'password').session
        resp = session.get('https://www...')

        :param username: str - Your Zwift email
        :param password: str - Your Zwift password
        """
        self.session = self._auth(username, password)
        self.countries = self._country_codes()

    def league_gc_results(self, league_id: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """

        :param league_id: str - The league id for the gc results
        :return: Tuple of pandas.DataFrame
        """
        gc_data = self.session.get(
            f'https://zwiftpower.com/cache3/global/league_standings_{league_id}.json'
        ).json()
        team_data = self.session.get(
            f'https://zwiftpower.com/cache3/global/league_team_standings_{league_id}.json'
        ).json()
        fem_gc_data = self.session.get(
            f'https://zwiftpower.com/api3.php?do=league_standings&gender=W&id={league_id}'
        ).json()

        # now convert to a dataframe
        gc_df = pd.json_normalize(gc_data['data'])
        team_df = pd.json_normalize(team_data['data'])
        try:
            fem = True
            fem_gc_df = pd.json_normalize(fem_gc_data['data'])
        except:
            fem = False
            fem_gc_df = pd.DataFrame()

        teams = {k: v['tname'] for k, v in gc_data['teams'].items()}

        # GC data
        gc_df['tname'] = gc_df['tid'].map(teams).fillna('')
        gc_df['name'] = gc_df['name'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
        gc_df['tname'] = gc_df['tname'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
        gc_df['history'] = gc_df['history'].agg(lambda x: [int(v) for v in x])
        gc_df['points'] = gc_df['points'].astype(int)
        gc_df['flag'] = gc_df['flag'].replace(self.countries)
        gc_df['time'] = pd.to_datetime(gc_df['points'] / 1000, unit='s').dt.time
        gc_df = gc_df.sort_values(['events', 'time'], ascending=[False, True])
        gc_df['Position'] = range(1, len(gc_df) + 1)

        # Female GC data
        if fem:
            fem_gc_df['tname'] = fem_gc_df['tid'].map(teams).fillna('')
            fem_gc_df['name'] = fem_gc_df['name'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
            fem_gc_df['tname'] = fem_gc_df['tname'].apply(
                lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
            fem_gc_df['history'] = fem_gc_df['history'].agg(lambda x: [int(v) for v in x])
            fem_gc_df['points'] = fem_gc_df['points'].astype(int)
            fem_gc_df['flag'] = fem_gc_df['flag'].replace(self.countries)
            fem_gc_df['time'] = pd.to_datetime(fem_gc_df['points'] / 1000, unit='s').dt.time
            fem_gc_df = fem_gc_df.sort_values(['events', 'time'], ascending=[False, True])
            fem_gc_df['Position'] = range(1, len(fem_gc_df) + 1)
        else:
            fem_gc_df = pd.DataFrame()

        # Team standings data
        team_df['tname'] = team_df['tname'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
        team_df['pos'] = team_df['pos'].astype(int)
        team_df = team_df.sort_values(['category', 'pos'], ascending=True)

        return gc_df, fem_gc_df, team_df

    def league_event_results(self, league_id) -> pd.DataFrame:
        data = self.session.get(f'https://zwiftpower.com/api3.php?do=league_event_results&id={league_id}').json()

        dfs = []  # empty list to append data
        # iterate of the event ids
        for d in data['data']:
            url = f'https://zwiftpower.com/cache3/results/{d["DT_RowId"]}_view.json?'
            r = self.session.get(url).json()  # make the GET request
            if r['data']:  # if there is data to return
                df = pd.json_normalize(r['data'])
                # add date of race in UTC
                df['Date_UTC'] = datetime.datetime.fromtimestamp(d['tm'], datetime.timezone.utc)
                df['Distance_km'] = d['km'] / 1000  # add race distance - convert from meters to km
                df['Title'] = d['t']  # add race title
                df['Route'] = routes[d['rt']]['name']  # add the route name
                df['Laps'] = d['laps']  # add number of laps
                dfs.append(df)
        # concat all the frames together
        df = pd.concat(dfs)

        # covert nested lists to string objects
        df['time'] = df['time'].agg(lambda x: x[0])
        df['speed_kph'] = df['Distance_km'].div(df['time']).mul(3600)  # calculate speed in kph
        df['time'] = df['time'].agg(lambda x: str(datetime.timedelta(seconds=x)))
        df['gap'] = df['gap'].agg(lambda x: str(datetime.timedelta(seconds=x)))
        df['np'] = df['np'].agg(lambda x: x[0])
        df['avg_power'] = df['avg_power'].agg(lambda x: x[0])
        df['avg_wkg'] = df['avg_wkg'].agg(lambda x: x[0])
        df['avg_hr'] = df['avg_hr'].agg(lambda x: x[0])
        df['name'] = df['name'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
        df['tname'] = df['tname'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)  # handle emojis
        # assign country name from the country code
        df['flag'] = df['flag'].replace(self.countries)
        # convert the time to timedelta and only keep one digit after decimal
        df['time'] = df['time'].replace(r'(?<=\.\d{1}).*$', '', regex=True).apply(pd.Timedelta)
        # sort the values based on finish time and only keep the fastest time for each person
        df = df.sort_values('time')
        df = df[df['time'] == df.groupby('zwid')['time'].transform(min)].copy()
        # rename some columns
        df = df.rename(columns={'tname': 'team_name', 'flag': 'country'})

        return df

    def team_roster(self) -> pd.DataFrame:
        team_data = self.session.get('https://zwiftpower.com/api3.php?do=team_riders&id=16219').json()
        df = pd.json_normalize(team_data['data'])

        div = {0: '', 5: 'A+', 10: 'A', 20: 'B', 30: 'C', 40: 'D'}
        df['div'] = df['div'].map(div)

        df = df[['zwid', 'name', 'flag', 'div', 'age', 'ftp', 'h_1200_wkg', 'h_15_wkg', 'h_1200_watts', 'h_15_watts']]

        df['flag'] = df['flag'].replace(self.countries)
        df['ftp'] = df['ftp'].apply(lambda x: x[0])

        cat_sort = {'A+': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, '': 5}
        roster = df.sort_values(['div', 'name'],
                                ascending=True,
                                key=lambda x: x.map(cat_sort)
                                ).copy()
        roster['Name'] = '<a href="https://zwiftpower.com/profile.php?z=' + roster['zwid'].astype(str) + '">' + roster[
            'name'] + '</a>'
        roster = roster[['Name', 'flag', 'div', 'age', 'ftp', 'h_1200_wkg', 'h_15_wkg', 'h_1200_watts', 'h_15_watts']]
        roster.columns = ['Name', 'Country', 'Grade', 'Age', 'FTP', '20m WKG', '15s WKG', '20m Power', '15s Power']
        return roster

    @staticmethod
    def _auth(username: str, password: str) -> requests.Session:
        """
        This is a static method that is used to create the requests.Session and store the correct cookies

        You can use this method is you want to use the session to make custom get requests.

        session = ZwiftPower('username', 'password').session

        :param username: str - Zwift email
        :param password: str - Zwift password
        :return: requests.Session
        """
        # set the user-agent header
        headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, '
                                 'like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        # ZP redirect uri
        redirect_uri = 'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
        # payload
        payload = {'username': username,
                   'password': password,
                   'rememberMe': 'on'}
        # create the session and set the headers
        session = requests.Session()
        session.headers = headers
        # this is where the magic happens for authentication
        redirect_resp = session.get(redirect_uri, allow_redirects=False)
        loc_resp = session.get(redirect_resp.headers['location'], allow_redirects=False)
        form_submit_resp = session.post(BeautifulSoup(loc_resp.text, 'html.parser').find(id='form')['action'],
                                        data=payload,
                                        allow_redirects=False)
        session.get(form_submit_resp.headers['location'])

        return session

    @staticmethod
    def _country_codes() -> dict:
        """
        static method to add the UK iso3166 country codes to the pycountry data
        :return: dict - iso3166 country codes used by zwift with the country name
        """
        # we need to get the iso3166 country codes and add the UK country codes
        with open(pycountry.DATABASE_DIR + '/iso3166-1.json') as f:
            iso3166_1 = json.load(f)
        with open(pycountry.DATABASE_DIR + '/iso3166-2.json') as f:
            iso3166_2 = json.load(f)

        # create a dictionary of country codes
        countries = {x['alpha_2'].lower(): x['name'] for x in iso3166_1['3166-1']}
        country_2 = {x['code'].lower(): x['name'] for x in iso3166_2['3166-2']}
        countries.update(country_2)
        gb = {'gb-eng': 'England', 'gb-nir': 'Northern Ireland', 'gb-sct': 'Scotland', 'gb-wls': 'Wales'}
        countries.update(gb)

        return countries
