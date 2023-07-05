#! /home/joel/miniconda3/envs/altdev5/bin/python

import sys
from datetime import datetime, timedelta

import pandas as pd
import plotext as plt


if len(sys.argv) > 1:
    # TODO support '4-6' syntax for a range of weeks
    # if '-' in sys.argv[1]:
    #     start_week, end_week = [int(num) for num in sys.argv[1].split('-')]
    # else:
    #     past_weeks_included = int(sys.argv[1]) - 1
    past_weeks_included = int(sys.argv[1]) - 1
else:
    past_weeks_included = 4

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
    # If x is so close to a full hour that the minutes would round to 60, then
    # just round x up to show the full hour. For example, if the number is
    # 42.998, then we show 43 h instead of showing 42 h and 60 min.
    if round(x * 60) == 60 or (int(x) !=0 and round(x % int(x) * 60) == 60):
        x = round(x)

    # Find the minutes
    if int(x) == 0:
        print('happens')
        minutes = round(x * 60)
    else:
        minutes = round(x % int(x) * 60)
    # return f'{int(x)} h {minutes: >2} min'
    return f'{int(x)}:{minutes:0>2}'

year, week = (datetime.now() - timedelta(days=past_weeks_included * 7)).strftime('%Y %W').split()
# We need to add a '0' weekday to be able to use the %W for week of the year
# https://stackoverflow.com/questions/55222420/converting-year-and-week-of-year-columns-to-date-in-pandas
week_frames = frames[
    pd.to_datetime(frames['year'] + frames['week'] + '0', format='%Y%W%w')
    >= pd.to_datetime(year + week + '0', format='%Y%W%w')
]

# Prep df for plotting
sorted_projects = week_frames.groupby('project')['length'].sum().sort_values().index.tolist()[::-1]
time_per_week_per_project = (
    week_frames
    # Need to make these ordered categorical to be able to sort on all three columns
    .assign(
        project=lambda df: pd.Categorical(
            df['project'],
            ordered=True,
            categories=sorted_projects
        )
    )
    .groupby(['project', 'year', 'week'], as_index=False)
    ['length']
    .sum()
    # Sorting only on the project sometimes mixes up the dates within the same project
    .sort_values(['project', 'year', 'week'])
)
# The label for each bar will be the year and week
year_and_week = [f'{year}-w{week}' for year, week in time_per_week_per_project.set_index(['year', 'week']).index]

# Create a list of lists (each with the values from a separate projects) for the plotting
time_per_project = [
    time_per_week_per_project
    .query('project == @proj')
    ['length']
    # .round()
    .tolist()
    for proj in sorted_projects
]

# Make all projects have as many entries since the plotting requires this
max_proj_length = max([len(ls) for ls in time_per_project])
[x.extend([0] * (max_proj_length - len(x))) for x in time_per_project]

# Plot
plt.simple_stacked_bar(
    [f'{year_week} {hour_min: >5}' for year_week, hour_min in zip(year_and_week, time_per_week_per_project.groupby(['year', 'week'])['length'].sum().apply(hour_and_min).tolist())],
    time_per_project,
    labels=sorted_projects,
    colors=['blue', 'orange', 'magenta', 'green', 'red', 'cyan'][:len(sorted_projects)],
    width=50,
    title='Weekly Timelog',
    bar_texts=[''] * len(time_per_week_per_project.groupby(['year', 'week'])['length'].sum().apply(hour_and_min).tolist())
)
plt.show()
