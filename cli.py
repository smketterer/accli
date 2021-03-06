#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI App."""
import datetime
import getpass
import os
from typing import Dict

from blessings import Terminal

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import confirm

from completers import DateFuzzyCompleter, FuzzyCompleter, WeekFuzzyCompleter
from pyactivecollab import ActiveCollab, Config
from utils import timestamp_field_to_datetime

t = Terminal()


def prompt_user_for_project(ac) -> Dict:
    """Prompt user for a project."""
    projects = ac.get_projects()
    suggestions = [x['name'] for x in projects]
    completer = FuzzyCompleter(suggestions)
    text = prompt('(Project)> ', completer=completer)
    project = next(x for x in projects if x['name'] == text)
    return project


def prompt_user_for_task(ac, project) -> Dict:
    """Prompt the user for a task."""
    tasks = ac.get_tasks_by_project(project['id'])['tasks']
    suggestions = [x['name'] for x in tasks]
    completer = FuzzyCompleter(suggestions)
    text = prompt('(Task)> ', completer=completer)
    if text:
        task = next(x for x in tasks if x['name'] == text)
    else:
        task = None
    return task


def prompt_user_for_time_value(ac) -> str:
    """Prompt the user for a time value."""
    value = prompt('(Value)> ')
    # If integer is passed then treat it as minutes
    if ('.' not in value) and (':' not in value):
        value = float(value) / 60
    return value


def prompt_user_for_job_type(ac) -> Dict:
    """Prompt the user for a job type."""
    job_types = ac.get_job_types()
    suggestions = [x['name'] for x in job_types]
    completer = FuzzyCompleter(suggestions)
    text = prompt('(Job Type)> ', completer=completer)
    job_type = next(x for x in job_types if x['name'] == text)
    return job_type


def prompt_user_for_date(ac) -> str:
    """Prompt the user for a date."""
    completer = DateFuzzyCompleter()
    text = prompt('(Date)> ', completer=completer)
    choosen_date = datetime.datetime.strptime(text, '%a, %Y-%m-%d')
    return choosen_date.strftime('%Y-%m-%d')


def prompt_user_for_billable_status(ac) -> int:
    """Prompt the user for a billable status."""
    billable_choices = {True: 1, False: 0}
    billable = confirm('(Billable (y/n))> ')
    billable = billable_choices[billable]
    return billable


def prompt_user_for_lift_user(ac) -> Dict:
    """Prompt the user for a user."""
    users = ac.get_users()
    lift_users = [x for x in users if x['company_id'] == 1]
    suggestions = [x['display_name'] for x in lift_users]
    current_user = next(x for x in lift_users if x['email'] == ac.config.user)
    completer = FuzzyCompleter(suggestions)
    text = prompt('(User)> ', default=current_user['display_name'], completer=completer)
    user = next(x for x in lift_users if x['display_name'] == text)
    return user


def create_task(ac):
    """Create a task."""
    project = prompt_user_for_project(ac)
    name = prompt('(Name)> ')
    user = prompt_user_for_lift_user(ac)
    data = {
        'name': name,
        'assignee_id': user['id'],
    }
    url = '/projects/{}/tasks'.format(project['id'])
    ac.post(url, data)


def create_time_record(ac):
    """Super Innefficient calls to create a time record."""
    project = prompt_user_for_project(ac)
    task = prompt_user_for_task(ac, project)
    value = prompt_user_for_time_value(ac)
    job_type = prompt_user_for_job_type(ac)
    billable = prompt_user_for_billable_status(ac)
    date = prompt_user_for_date(ac)
    summary = prompt('(Summary)> ', enable_open_in_editor=True)
    # Get User
    users = ac.get_users()
    user = next(x for x in users if x['email'] == ac.config.user)
    data = {
        'value': value,
        'task_id': task['id'] if task else None,
        'user_id': user['id'],
        'job_type_id': job_type['id'],
        'record_date': date,
        'billable_status': billable,
        'summary': summary,
    }
    url = '/projects/{}/time-records'.format(project['id'])
    ac.post(url, data)


def list_daily_time_records(ac):
    """List current user's time entrys for a specific day."""
    os.system('cal -3')
    # Make sure that the input is valid. This should be broken out to
    # encapsulate all auto-complete inputs
    completer = DateFuzzyCompleter()
    valid = False
    while not valid:
        try:
            date_str = prompt('(Date)> ', completer=completer)
            choosen_date = datetime.datetime.strptime(date_str, '%a, %Y-%m-%d')
        except ValueError:
            print('Bad input, try again.')
        else:
            valid = True
    users = ac.get_users()
    user = next(x for x in users if x['email'] == ac.config.user)
    r = ac.get_time_records(user['id'])
    time_records = r['time_records']
    time_records = [timestamp_field_to_datetime(x, 'record_date') for x in time_records]
    daily_time_records = [x for x in time_records
                          if x['record_date'].date() == choosen_date.date()]
    billable = 0
    non_billable = 0
    daily_hours = 0
    for record in daily_time_records:
        if record['billable_status']:
            print(t.green('{:<6} {}'.format(record['value'], record['summary'][:60])))
            billable += record['value']
        else:
            print(t.blue('{:<6} {}'.format(record['value'], record['summary'][:60])))
            non_billable += record['value']
        daily_hours += record['value']
    print((t.yellow(str(daily_hours)) + ' ' +
           t.green(str(billable)) + ' ' +
           t.blue(str(non_billable))))


def list_weekly_time_records(ac):
    """List current user's time entrys for a specific week."""
    os.system('cal -3')
    # Make sure that the input is valid. This should be broken out to
    # encapsulate all auto-complete inputs
    completer = WeekFuzzyCompleter()
    valid = False
    while not valid:
        try:
            week_str = prompt('(Week)> ', completer=completer)
            monday_dt = datetime.datetime.strptime(week_str.split()[0], '%Y-%m-%d')
            sunday_dt = datetime.datetime.strptime(week_str.split()[2], '%Y-%m-%d')
        except ValueError:
            print('Bad input, try again.')
        else:
            valid = True
    users = ac.get_users()
    user = next(x for x in users if x['email'] == ac.config.user)
    r = ac.get_time_records(user['id'])
    time_records = r['time_records']
    time_records = [timestamp_field_to_datetime(x, 'record_date') for x in time_records]
    weekly_time_records = [x for x in time_records if
                           x['record_date'].date() >= monday_dt.date() and
                           x['record_date'].date() <= sunday_dt.date()]
    days = [(sunday_dt - datetime.timedelta(days=x)) for x in range(7)]
    weekly_billable = 0
    weekly_non_billable = 0
    weekly_hours = 0
    for day in days:
        billable = 0
        non_billable = 0
        daily_hours = 0
        if day.date() > datetime.datetime.now().date():
            continue
        daily_time_records = [x for x in weekly_time_records if
                              x['record_date'].date() == day.date()]
        print(day)
        for record in daily_time_records:
            if record['billable_status']:
                print(t.green('{:<6} {}'.format(record['value'], record['summary'][:60])))
                billable += record['value']
                weekly_billable += record['value']
            else:
                print(t.blue('{:<6} {}'.format(record['value'], record['summary'][:60])))
                non_billable += record['value']
                weekly_non_billable += record['value']
            daily_hours += record['value']
            weekly_hours += record['value']
        print((t.yellow(str(daily_hours)) + ' ' +
               t.green(str(billable)) + ' ' +
               t.blue(str(non_billable))))
    print('Weekly Hours')
    print((t.yellow(str(weekly_hours)) + ' ' +
           t.green(str(weekly_billable)) + ' ' +
           t.blue(str(weekly_non_billable))))
    print('Percent Billable: {:.2f}%'.format(100 - ((37.5-weekly_billable)/37.5*100)))


def main():
    """Run main loop of script."""
    # Load config, ensure password
    config = Config()
    config.load()
    if not config.password:
        config.password = getpass.getpass()

    ac = ActiveCollab(config)
    ac.authenticate()
    actions = {
        'Create Time Record': create_time_record,
        'Create Task': create_task,
        'List Daily Time Records': list_daily_time_records,
        'List Weekly Time Records': list_weekly_time_records,
    }
    completer = FuzzyCompleter(actions.keys())
    print(t.blue('Active Collab CLI (Press <tab> for options)'))
    print('')
    while True:
        action = prompt('(Action)> ', completer=completer)
        try:
            actions[action](ac)
        except KeyError:
            print('Bad Input, please try again.')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('Have a nice day!')
