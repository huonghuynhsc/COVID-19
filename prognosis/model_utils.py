# MIT License
#
# Copyright (c) 2020-2022 Quoc Tran
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
from sklearn import linear_model
import streamlit as st
import pwlf_mod as pwlf
from csv import writer

#DEATH_RATE = 0.01
#ICU_RATE = 0.05
#HOSPITAL_RATE = 0.15
#SYMPTOM_RATE = 0.2
#INFECT_2_HOSPITAL_TIME = 13
#HOSPITAL_2_ICU_TIME = 2
#ICU_2_DEATH_TIME = 5
#ICU_2_RECOVER_TIME = 11
#NOT_ICU_DISCHARGE_TIME = 7


def get_global_death_data(csv_file='../csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'):
    death_data = pd.read_csv(csv_file)
    return death_data.rename(index=str, columns={"Country/Region": "Country", "Province/State": "State"})


def get_US_death_data(csv_file='../csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'):
    death_data = pd.read_csv(csv_file)
    return death_data.rename(index=str, columns={"Country_Region": "Country", 
                                                 "Province_State": "State", 
                                                 "Admin2": "County"})


def get_lockdown_date_global(csv_file='data/lockdown_date_country.csv'):
    return pd.read_csv(csv_file)[['country', 'lockdown_date']].set_index('country')


def get_lockdown_date_by_country(country):
    try:
        lockdown_date = pd.to_datetime(get_lockdown_date_global().loc[country][0])
    except KeyError:
        lockdown_date = dt.date.today()
    return lockdown_date


def get_lockdown_date_US(csv_file='data/lockdown_date_state_US.csv'):
    return pd.read_csv(csv_file)[['state', 'lockdown_date']].set_index('state')


def get_lockdown_date_by_state_US(state):
    try:
        lockdown_date = pd.to_datetime(get_lockdown_date_US().loc[state][0])
    except KeyError:
        lockdown_date = dt.date.today()
    return lockdown_date


def get_death_data_by_country(country):
    global_death_data = get_global_death_data()
    local_death_data = global_death_data.query('Country == "{}"'.format(country)).iloc[:,4:].T.sum(axis=1).to_frame()
    local_death_data.index = pd.to_datetime(local_death_data.index)
    return local_death_data[local_death_data>0].dropna()


def get_US_death_data_by_state(state):
    US_death_data = get_US_death_data()
    local_death_data = US_death_data.query('State == "{}"'.format(state)).iloc[:,12:].T.sum(axis=1).to_frame()
    local_death_data.index = pd.to_datetime(local_death_data.index)
    return local_death_data[local_death_data>0].dropna()


def get_US_death_data_by_county_and_state(county, state):
    US_death_data = get_US_death_data()
    local_death_data = US_death_data.query('County == "{}" and State == "{}"'.format(county, state)).iloc[:,12:].T.sum(axis=1).to_frame()
    local_death_data.index = pd.to_datetime(local_death_data.index)
    return local_death_data[local_death_data>0].dropna()


def get_daily_death(local_death_data):
    return local_death_data.diff().fillna(0)


def get_impute_from_death(death_row, periods, end_date_offset=0):
    date_ind = death_row.name
    end_date = date_ind + dt.timedelta(end_date_offset)
    date_range = pd.date_range(end=end_date, periods=periods)
    return pd.DataFrame(death_row.tolist()*periods, index=date_range)


def get_hospital_beds_from_death(death_row):
    '''Get imputation of hospital beds needed from one day record of new death'''
    dead_hospital_use_periods = HOSPITAL_2_ICU_TIME+ICU_2_DEATH_TIME
    dead_hospital_use = get_impute_from_death(death_row=death_row, 
                                              periods=dead_hospital_use_periods)
    ICU_recovered_hospital_use_periods = HOSPITAL_2_ICU_TIME+ICU_2_RECOVER_TIME+NOT_ICU_DISCHARGE_TIME
    ICU_recovered_hospital_use_end_date_offset = ICU_2_RECOVER_TIME-ICU_2_DEATH_TIME+NOT_ICU_DISCHARGE_TIME
    ICU_recovered_hospital_use = get_impute_from_death(death_row=death_row, 
                                                       periods=ICU_recovered_hospital_use_periods,
                                                       end_date_offset=ICU_recovered_hospital_use_end_date_offset)
    no_ICU_hospital_use_periods = NOT_ICU_DISCHARGE_TIME
    no_ICU_hospital_use_end_date_offset = -HOSPITAL_2_ICU_TIME-ICU_2_DEATH_TIME+NOT_ICU_DISCHARGE_TIME
    no_ICU_hospital_use = get_impute_from_death(death_row=death_row, 
                                                periods=no_ICU_hospital_use_periods,
                                                end_date_offset=no_ICU_hospital_use_end_date_offset)
    hospital_beds = dead_hospital_use.add(((ICU_RATE-DEATH_RATE)/DEATH_RATE)*ICU_recovered_hospital_use, fill_value=0)\
            .add(((HOSPITAL_RATE-ICU_RATE)/DEATH_RATE)*no_ICU_hospital_use, fill_value=0)
    hospital_beds.columns = ['hospital_beds']
    return hospital_beds


def get_ICU_from_death(death_row):
    '''Get imputation of ICU needed from one day record of new death'''
    dead_ICU_use = get_impute_from_death(death_row=death_row, periods=ICU_2_DEATH_TIME)
    recovered_ICU_use_end_date_offset = ICU_2_RECOVER_TIME-ICU_2_DEATH_TIME
    recovered_ICU_use = get_impute_from_death(death_row=death_row, 
                                              periods=ICU_2_RECOVER_TIME,
                                              end_date_offset=recovered_ICU_use_end_date_offset)
    ICU_n = dead_ICU_use.add(((ICU_RATE-DEATH_RATE)/DEATH_RATE)*recovered_ICU_use, fill_value=0)
    ICU_n.columns = ['ICU']
    return ICU_n


def get_infected_cases(local_death_data):
    '''This number only is close to number of confirmed case in country very early in the disease and 
    can still do contact tracing or very wide testing, eg. South Korea, Germany'''
    delay_time = INFECT_2_HOSPITAL_TIME + HOSPITAL_2_ICU_TIME + ICU_2_DEATH_TIME
    infected_cases = (100/DEATH_RATE)*local_death_data.tshift(-delay_time)
    infected_cases.columns = ['infected']
    return infected_cases


def get_symptomatic_cases(local_death_data):
    '''This is number of cases that show clear symptoms (severe),
    in country without investigative testing this is close to number of confirmed case, most country'''
    delay_time = HOSPITAL_2_ICU_TIME + ICU_2_DEATH_TIME
    symptomatic_cases = (SYMPTOM_RATE/DEATH_RATE)*local_death_data.tshift(-delay_time)
    symptomatic_cases.columns = ['symptomatic']
    return symptomatic_cases


def get_hospitalized_cases(local_death_data):
    '''In country with severe lack of testing, this is close to number of confirmed case, eg. Italy, Iran'''
    delay_time = HOSPITAL_2_ICU_TIME + ICU_2_DEATH_TIME
    hospitalized_cases = (HOSPITAL_RATE/DEATH_RATE)*local_death_data.tshift(-delay_time)
    hospitalized_cases.columns = ['hospitalized']
    return hospitalized_cases


def get_number_hospital_beds_need(daily_local_death_new):
    '''Calculate number of hospital bed needed from number of daily new death '''
    # Start by first date
    hospital_beds = get_hospital_beds_from_death(daily_local_death_new.iloc[0])
    # Run through all days
    for i in range(len(daily_local_death_new)-1):
        hospital_beds = hospital_beds.add(get_hospital_beds_from_death(daily_local_death_new.iloc[i+1]), 
                                          fill_value=0)
    return hospital_beds


def get_number_ICU_need(daily_local_death_new):
    '''Calculate number of ICU needed from number of daily new death '''
    # Start by first date
    ICU_n = get_ICU_from_death(daily_local_death_new.iloc[0])
    # Run through all days
    for i in range(len(daily_local_death_new)-1):
        ICU_n = ICU_n.add(get_ICU_from_death(daily_local_death_new.iloc[i+1]), fill_value=0)
    return ICU_n


def get_log_daily_predicted_death(local_death_data, forecast_horizon=60, lockdown_date=None):
    '''Since this is highly contagious disease. Daily new death, which is a proxy for daily new infected cases
    is model as d(t)=a*d(t-1) or equivalent to d(t) = b*a^(t). After a log transform, it becomes linear.
    log(d(t))=logb+t*loga, so we can use linear regression to provide forecast (use robust linear regressor to avoid
    data anomaly in death reporting)
    There are two seperate linear curves, one before the lockdown is effective(21 days after lockdown) and one after
    For using this prediction to infer back the other metrics (infected cases, hospital, ICU, etc..) only the before
    curve is used and valid. If we assume there is no new infection after lock down (perfect lockdown), the after
    curve only depends on the distribution of time to death since ICU.
    WARNING: if lockdown_date is not provided, we will default to no lockdown to raise awareness of worst case
    if no action. If you have info on lockdown date please use it to make sure the model provide accurate result'''
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new = daily_local_death_new.rolling(3, min_periods=1).mean()
    #shift ahead 1 day to avoid overfitted due to average of exponential value
    #daily_local_death_new = daily_local_death_new.shift(1)
    #import pdb; pdb.set_trace()
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    # log_daily_death.dropna(inplace=True)
    data_start_date = min(local_death_data.index)
    data_end_date = max(local_death_data.index)
    forecast_end_date = data_end_date + dt.timedelta(forecast_horizon)
    forecast_date_index = pd.date_range(start=data_start_date, end=forecast_end_date)
    if lockdown_date is not None:
        lockdown_date = pd.to_datetime(lockdown_date)
    else:
        lockdown_date = forecast_end_date
    lockdown_effective_date = lockdown_date + dt.timedelta(
        INFECT_2_HOSPITAL_TIME + HOSPITAL_2_ICU_TIME + ICU_2_DEATH_TIME)
    data_start_date_idx = (data_start_date - lockdown_effective_date).days
    data_end_date_idx = (data_end_date - lockdown_effective_date).days
    forecast_end_date_idx = data_end_date_idx + forecast_horizon
    forecast_time_idx = (forecast_date_index - lockdown_effective_date).days.values
    data_time_idx = (log_daily_death.index - lockdown_effective_date).days.values
    log_daily_death['time_idx'] = data_time_idx
    log_daily_death = log_daily_death.replace([np.inf, -np.inf], np.nan).dropna()
    log_daily_death_before = log_daily_death[log_daily_death.time_idx < 0]
    regr_before = linear_model.HuberRegressor(fit_intercept=True)
    regr_before.fit(log_daily_death_before.time_idx.values.reshape(-1, 1), log_daily_death_before.death)
    outliers_before = regr_before.outliers_
    log_predicted_death_before_values = regr_before.predict(forecast_time_idx[forecast_time_idx < 0].reshape(-1, 1))
    log_predicted_death_before_index = forecast_date_index[forecast_time_idx < 0]
    log_predicted_death_before = pd.DataFrame(log_predicted_death_before_values,
                                              index=log_predicted_death_before_index)
    if all(forecast_time_idx < 0):
        print("Lockdown is not effective in forecast range. Second model not needed")
        outliers = outliers_before
        regr_pw = pwlf.PiecewiseLinFit(x=log_daily_death[~outliers].time_idx.values, y=log_daily_death[~outliers].death)
        break_points = np.array([data_start_date_idx, data_end_date_idx])
        regr_pw.fit_with_breaks(break_points)
        variance = regr_pw.variance()
        log_predicted_death_pred_var_oos = variance * (forecast_time_idx[forecast_time_idx > data_end_date_idx] -
                                                       data_end_date_idx)
    elif all(data_time_idx <= 3):
        print("Use default second model due to not enough data")

        if (len(log_daily_death) - len(outliers_before))>0:
            outliers_after = np.array([False] * (len(log_daily_death) - len(outliers_before)))
            outliers = np.concatenate((outliers_before, outliers_after))
        else:
            outliers = outliers_before
        regr_pw = pwlf.PiecewiseLinFit(x=log_daily_death[~outliers].time_idx.values, y=log_daily_death[~outliers].death)
        break_points = np.array([data_start_date_idx, 0, forecast_end_date_idx])
        regr_pw.fit_with_breaks(break_points)
        # Replace second slope by default value, learning from local with same temperature, transportation
        regr_pw.beta[2]= -0.3
        variance = regr_pw.variance()
        log_predicted_death_pred_var_oos = variance*(forecast_time_idx[forecast_time_idx>data_end_date_idx]-
                                                     data_end_date_idx)
        print(regr_pw.variance())
        print(len(forecast_time_idx[forecast_time_idx>data_end_date_idx]))
    else:
        regr_after = linear_model.HuberRegressor(fit_intercept=True)
        log_daily_death_after = log_daily_death[log_daily_death.time_idx >= 0]
        regr_after.fit(log_daily_death_after.time_idx.values.reshape(-1, 1),
                       log_daily_death_after.death)
        outliers_after = regr_after.outliers_
        outliers = np.concatenate((outliers_before, outliers_after))
        regr_pw = pwlf.PiecewiseLinFit(x=log_daily_death[~outliers].time_idx.values, y=log_daily_death[~outliers].death)
        break_points = np.array([data_start_date_idx, 0, data_end_date_idx])
        regr_pw.fit_with_breaks(break_points)

    log_predicted_death_values = regr_pw.predict(forecast_time_idx)
    log_predicted_death_pred_var = regr_pw.prediction_variance(forecast_time_idx)
    if all(data_time_idx <= 3):
        log_predicted_death_pred_var = np.concatenate(
            (log_predicted_death_pred_var[:sum(forecast_time_idx <= data_end_date_idx)],
             log_predicted_death_pred_var_oos))

    log_predicted_death_lower_bound_values = log_predicted_death_values - 1.96 * np.sqrt(log_predicted_death_pred_var)
    log_predicted_death_upper_bound_values = log_predicted_death_values + 1.96 * np.sqrt(log_predicted_death_pred_var)

    log_predicted_death = pd.DataFrame(log_predicted_death_values, index=forecast_date_index)
    log_predicted_death_lower_bound = pd.DataFrame(log_predicted_death_lower_bound_values, index=forecast_date_index)
    log_predicted_death_upper_bound = pd.DataFrame(log_predicted_death_upper_bound_values, index=forecast_date_index)
    log_predicted_death.columns = ['predicted_death']
    log_predicted_death_lower_bound.columns = ['lower_bound']
    log_predicted_death_upper_bound.columns = ['upper_bound']
    return log_predicted_death, log_predicted_death_lower_bound, log_predicted_death_upper_bound, regr_pw.beta


def get_daily_predicted_death(local_death_data, forecast_horizon=60, lockdown_date=None):
    log_daily_predicted_death, lb, ub, model_beta = get_log_daily_predicted_death(local_death_data,
                                                                                  forecast_horizon,
                                                                                  lockdown_date)
    return np.exp(log_daily_predicted_death), np.exp(lb), np.exp(ub), model_beta


def get_cumulative_predicted_death(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily, lb, ub, model_beta = get_daily_predicted_death(local_death_data, forecast_horizon, lockdown_date)
    cumulative = daily.cumsum()
    data_end_date = max(local_death_data.index)+dt.timedelta(-1)
    lb.loc[local_death_data.index] = 0
    lb.loc[data_end_date] = cumulative.loc[data_end_date]
    ub.loc[local_death_data.index] = 0
    ub.loc[data_end_date] = cumulative.loc[data_end_date]

    return cumulative, lb.cumsum(), ub.cumsum(), model_beta


def get_daily_metrics_from_death_data(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily_predicted_death, daily_predicted_death_lb, daily_predicted_death_ub, model_beta  = \
            get_daily_predicted_death(local_death_data, forecast_horizon, lockdown_date)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    daily_infected_cases_new = get_infected_cases(daily_predicted_death)
    daily_symptomatic_cases_new = get_symptomatic_cases(daily_predicted_death)
    daily_hospitalized_cases_new = get_hospitalized_cases(daily_predicted_death)
    daily_hospital_beds_need = get_number_hospital_beds_need(daily_predicted_death)
    daily_ICU_need = get_number_ICU_need(daily_predicted_death)
    return pd.concat([daily_local_death_new,
                      daily_predicted_death,
                      daily_predicted_death_lb,
                      daily_predicted_death_ub,
                      daily_infected_cases_new,
                      daily_symptomatic_cases_new,
                      daily_hospitalized_cases_new,
                      daily_hospital_beds_need,
                      daily_ICU_need], axis=1, sort=True), model_beta


def get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily_metrics, model_beta = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = daily_metrics.drop(columns=['ICU', 'hospital_beds']).cumsum()
    # data_end_date = max(local_death_data.index)
    # cumulative_metrics['lower_bound'] = daily_metrics['lower_bound']
    # cumulative_metrics['lower_bound'].loc[local_death_data.index] = np.nan
    # cumulative_metrics['lower_bound'].loc[data_end_date] = local_death_data.loc[data_end_date][0]
    # cumulative_metrics['lower_bound'] = cumulative_metrics['lower_bound'].cumsum()
    # cumulative_metrics['upper_bound'] = daily_metrics['upper_bound']
    # cumulative_metrics['upper_bound'].loc[local_death_data.index] = np.nan
    # cumulative_metrics['upper_bound'].loc[data_end_date] = local_death_data.loc[data_end_date][0]
    # cumulative_metrics['upper_bound'] = cumulative_metrics['upper_bound'].cumsum()
    cumulative_metrics['ICU'] = daily_metrics['ICU']
    cumulative_metrics['hospital_beds'] = daily_metrics['hospital_beds']

    return cumulative_metrics, model_beta


def get_metrics_by_country(country, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_death_data_by_country(country)
    daily_metrics, model_beta = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = daily_metrics.drop(columns=['ICU', 'hospital_beds']).cumsum()
    cumulative_metrics['ICU'] = daily_metrics['ICU']
    cumulative_metrics['hospital_beds'] = daily_metrics['hospital_beds']
    #cumulative_metrics, model_beta = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    return daily_metrics, cumulative_metrics, model_beta


def get_metrics_by_state_US(state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_state(state)
    daily_metrics, model_beta = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = daily_metrics.drop(columns=['ICU', 'hospital_beds']).cumsum()
    cumulative_metrics['ICU'] = daily_metrics['ICU']
    cumulative_metrics['hospital_beds'] = daily_metrics['hospital_beds']
    return daily_metrics, cumulative_metrics, model_beta


def get_metrics_by_county_and_state_US(county, state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_county_and_state(county, state)
    daily_metrics, model_beta = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = daily_metrics.drop(columns=['ICU', 'hospital_beds']).cumsum()
    cumulative_metrics['ICU'] = daily_metrics['ICU']
    cumulative_metrics['hospital_beds'] = daily_metrics['hospital_beds']
    return daily_metrics, cumulative_metrics, model_beta


def get_log_daily_predicted_death_by_country(country, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_death_data_by_country(country)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    log_predicted_death, log_predicted_death_lb, log_predicted_death_ub, model_beta = \
            get_log_daily_predicted_death(local_death_data, lockdown_date=lockdown_date)
    return  pd.concat([log_daily_death, log_predicted_death, log_predicted_death_lb,
                       log_predicted_death_ub], axis=1).replace([np.inf, -np.inf], np.nan), model_beta


def get_log_daily_predicted_death_by_state_US(state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_state(state)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    log_predicted_death, log_predicted_death_lb, log_predicted_death_ub, model_beta = \
        get_log_daily_predicted_death(local_death_data, lockdown_date=lockdown_date)
    return pd.concat([log_daily_death, log_predicted_death, log_predicted_death_lb,
                      log_predicted_death_ub], axis=1).replace([np.inf, -np.inf], np.nan), model_beta


def get_log_daily_predicted_death_by_county_and_state_US(county, state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_county_and_state(county, state)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    log_predicted_death, log_predicted_death_lb, log_predicted_death_ub, model_beta = \
        get_log_daily_predicted_death(local_death_data, lockdown_date=lockdown_date)
    return pd.concat([log_daily_death, log_predicted_death, log_predicted_death_lb,
                      log_predicted_death_ub], axis=1).replace([np.inf, -np.inf], np.nan), model_beta


def append_row_2_logs(row, log_file='logs/model_params_logs.csv'):
    # Open file in append mode
    with open(log_file, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(row)


def get_table_download_link(df, filename="data.csv"):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" >Download csv file</a>'
    return href

