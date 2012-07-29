# -*- coding: utf-8 -*-  
import json, time
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta

# NOTE: not multi thread safe
round_hours_dict = {}
round_days_dict = {}
round_months_dict = {}

def getlast12hours(now):
    global round_hours_dict
    if now is None:
        now = datetime.now()
    now_hour = datetime(now.year, now.month, now.day, now.hour)
    mktime_now_hour = time.mktime(now_hour.timetuple())
    if mktime_now_hour in round_hours_dict:
        return round_hours_dict[mktime_now_hour]
    if len(round_hours_dict) > 100:
        round_hours_dict = {}
    round_hours = []
    i = 0
    while i < 12:
        delta_hour = now_hour + timedelta(hours=-i)
        i = i + 1
        round_hours.append(time.mktime(delta_hour.timetuple()))
    round_hours_dict[mktime_now_hour] = round_hours
    return round_hours

def getlast7days(now):
    return getlast30days(now)[0:7]

def getlast30days(now):
    global round_days_dict
    if now is None:
        now = datetime.now()
    now_day = datetime(now.year, now.month, now.day)
    mktime_now_day = time.mktime(now_day.timetuple())
    if mktime_now_day in round_days_dict:
        return round_days_dict[mktime_now_day]
    if len(round_days_dict) > 100:
        round_days_dict = {}
    fullfill_days_dict(now_day)
    return round_days_dict[mktime_now_day]

def getlast12months(now):
    global round_months_dict
    if now is None:
        now = datetime.now()
    now_month = datetime(now.year, now.month, 1)
    mktime_now_month = time.mktime(now_month.timetuple())
    if mktime_now_month in round_months_dict:
        return round_months_dict[mktime_now_month]
    if len(round_months_dict) > 100:
        round_months_dict = {}
    round_months = []
    i = 0
    while i < 12:
        delta_month = now_month + relativedelta(months=-i)
        i = i + 1
        round_months.append(time.mktime(delta_month.timetuple()))
    round_months_dict[mktime_now_month] = round_months
    return round_months

def get_round_day(now):
    round_day = datetime(now.year, now.month, now.day)
    return round_day

def get_round_week(now):
    round_day = datetime(now.year, now.month, now.day)
    round_week = round_day + timedelta(days=-now.weekday())
    return round_week

def get_round_month(now):
    round_month = datetime(now.year, now.month, 1)
    return round_month

def get_round_year(now):
    round_year = datetime(now.year, 1, 1)
    return round_year

def fullfill_days_dict(now_day):
    global round_days_dict
    round_days = []
    i = 0
    while i < 30:
        delta_day = now_day + timedelta(days=-i)
        i = i + 1
        round_days.append(time.mktime(delta_day.timetuple()))
    mktime_now_day = time.mktime(now_day.timetuple())
    round_days_dict[mktime_now_day] = round_days

