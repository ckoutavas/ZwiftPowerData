# ZwiftPowerData
A python class that allows you to pull race event and GC standings data from ZwiftPower.<br>I do not work for and am not affliated Zwift, ZwiftPower or any of its affliates and assume no liability.

## Cloning the Repo and Setup
1. Create a virtual environment: `conda create -n py_zp python=3.10`
2. Change directory to site-packages: `cd ~/opt/anaconda3/envs/py_zp/lib/python3.10/site-packages`
3. Clone the repo: `git clone https://github.com/ckoutavas/ZwiftPowerData`
4. Change directory to GoogleAnalytics4: `cd ZwiftPowerdata`
5. Activate your new environment: `conda activate py_zp`
6. Install requirements.txt: `pip install -r requirements.txt`

## league_gc_results
This method is used to pull the GC results for a league series and will return three dataframe:
the overall gc, the female gc and the team gc data. You can find the `league_id`
in the url by clicking on an event in the "Leagues" dropdown menu on zwiftpower.com

```
from ZwiftPowerData import ZwiftPower


zp = ZwiftPower(username='zwift_email', password='zwift_password')
gc_df, fem_gc_df, team_df = zp.league_gc_results(league_id='1234')
```

## league_event_results
This method is used to pull the individual race series results across multiple events.
The results from all races in the event are concatenated into one DataFrame. 
You can find the `league_id` in the url by clicking on an event in the "Leagues" dropdown menu on zwiftpower.com
You can see all the event results that will be returned by clicking on "events"

```
from ZwiftPowerData import ZwiftPower


zp = ZwiftPower(username='zwift_email', password='zwift_password')
events_df = zp.league_gc_results(league_id='1234')
```

## team_roster
This method is used to pull the team roster data from zwiftpower.com. You can get the team id from the url
clicking on "team" -- `https://zwiftpower.com/team.php?id=`

```
from ZwiftPowerData import ZwiftPower


zp = ZwiftPower(username='zwift_email', password='zwift_password')
team_roster = zp.team_roster(team_id='1234')
```

## Custom requests
You can make custom requests if you are familiar with `requests.Session()`

```
from ZwiftPowerData import ZwiftPower


session = ZwiftPower(username='zwift_email', password='zwift_password').session
# make whatever request you want
resp = session.get(...)
```