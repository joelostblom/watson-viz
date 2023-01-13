#! /home/joel/miniconda3/envs/altdev5/bin/python

import sys

import pandas as pd
import altair as alt
from datetime import datetime, timedelta


if len(sys.argv) > 1:
    num_weeks = int(sys.argv[1]) - 1
else:
    num_weeks = 2

frames = pd.read_json(
    '/home/joel/.config/watson/frames',
).rename(
    columns={0: 'start', 1: 'stop', 2: 'project', 3: 'hash', 4: 'tags', 5: 'notsure'}
).assign(
    length=lambda df: (df['stop'] - df['start']) / 3600,
    # Maybe easier to just subtract 7 hours in seconds manually?
    # Unfortunate that watson doens't store tz info, I wonder what happens to times worked in another country if they are all stored in seconds.
    # I guess they are always stored in UTC time, so it will look like I worked in the middle of the night some days
    start=lambda df: pd.to_datetime(df['start'], unit='s').dt.tz_localize('UTC', ambiguous=True).dt.tz_convert('US/Pacific'),
    stop=lambda df: pd.to_datetime(df['stop'], unit='s').dt.tz_localize('UTC', ambiguous=True).dt.tz_convert('US/Pacific'),
)

frames[['year', 'month', 'day', 'week', 'weekday', 'day_of_week']] = (
    frames['start'].dt.strftime(
        '%Y %b %d %W %a %w'
    ).str.split(
        expand=True
    )
)

def hour_and_min(x):
    return f'{int(x)} h {round(x % int(x) * 60): >2} min'

past_weeks_included = num_weeks
year, week = (datetime.now() - timedelta(days=past_weeks_included * 7)).strftime('%Y %W').split()
week_frames = frames[(frames['year'] >= year) & (frames['week'] >= week)]
print(week_frames.groupby(['year', 'week'])['length'].sum().apply(hour_and_min).to_string())
