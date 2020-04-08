import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
from sklearn import linear_model
import streamlit as st


DEATH_RATE = 0.01
ICU_RATE = 0.05
HOSPITAL_RATE = 0.15
SYMPTOM_RATE = 0.2
INFECT_2_HOSPITAL_TIME = 13
HOSPITAL_2_ICU_TIME = 2
ICU_2_DEATH_TIME = 5
ICU_2_RECOVER_TIME = 11
NOT_ICU_DISCHARGE_TIME = 7

@st.cache
def get_global_death_data(csv_file='../csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'):
    death_data = pd.read_csv(csv_file)
    return death_data.rename(index=str, columns={"Country/Region": "Country", "Province/State": "State"})

@st.cache
def get_US_death_data(csv_file='../csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'):
    death_data = pd.read_csv(csv_file)
    return death_data.rename(index=str, columns={"Country_Region": "Country", 
                                                 "Province_State": "State", 
                                                 "Admin2": "County"})


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
    hospital_beds = dead_hospital_use.add(((ICU_RATE-DEATH_RATE)/DEATH_RATE)*ICU_recovered_hospital_use, fill_value=0)                                     .add(((HOSPITAL_RATE-ICU_RATE)/DEATH_RATE)*no_ICU_hospital_use, fill_value=0)
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
    infected_cases = (1/DEATH_RATE)*local_death_data.tshift(-delay_time)
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
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    #log_daily_death.dropna(inplace=True)
    data_start_date = min(local_death_data.index)
    data_end_date = max(local_death_data.index)
    forecast_end_date = data_end_date + dt.timedelta(forecast_horizon)
    forecast_date_index = pd.date_range(start=data_start_date, end=forecast_end_date)
    if lockdown_date is not None:
        lockdown_date = pd.to_datetime(lockdown_date)
    else:
        lockdown_date = forecast_end_date
    lockdown_effective_date = lockdown_date + dt.timedelta(INFECT_2_HOSPITAL_TIME+HOSPITAL_2_ICU_TIME+ICU_2_DEATH_TIME)
    data_end_date_idx = (data_end_date - lockdown_effective_date).days
    forecast_end_date_idx = data_end_date_idx + forecast_horizon
    forecast_time_idx = (forecast_date_index - lockdown_effective_date).days.values
    data_time_idx = (log_daily_death.index - lockdown_effective_date).days.values
    log_daily_death['time_idx'] = data_time_idx
    log_daily_death = log_daily_death.replace([np.inf, -np.inf], np.nan).dropna()
    log_daily_death_before = log_daily_death[log_daily_death.time_idx<0]
    regr_before = linear_model.HuberRegressor(fit_intercept=True)
    regr_before.fit(log_daily_death_before.time_idx.values.reshape(-1, 1), log_daily_death_before.death)
    log_predicted_death_before_values = regr_before.predict(forecast_time_idx[forecast_time_idx<0].reshape(-1, 1))
    log_predicted_death_before_index = forecast_date_index[forecast_time_idx<0]
    log_predicted_death_before = pd.DataFrame(log_predicted_death_before_values, 
                                              index=log_predicted_death_before_index)
    log_predicted_death_before.columns = ['predicted_death_before_lockdown_effective']
 
    log_daily_death_after = log_daily_death[log_daily_death.time_idx>=0]
    regr_after = linear_model.HuberRegressor(fit_intercept=True)
    if all(data_time_idx<0):
        print("Use default model due to no data")
        regr_after.coef_ = np.array([-0.04])
        regr_after.intercept_ = log_predicted_death_before.iloc[-1,0]
    else:
        regr_after.fit(log_daily_death_after.time_idx.values.reshape(-1, 1), log_daily_death_after.death)
    #print("After Coef: {}".format(regr_after.coef_))
    if all(forecast_time_idx<0):
        print("Lockdown is not effective in forecast range. Second model not needed")
        log_predicted_death_after = None
    else:
        log_predicted_death_after_values = regr_after.predict(forecast_time_idx[forecast_time_idx>=0].reshape(-1, 1))
        log_predicted_death_after_index = forecast_date_index[forecast_time_idx>=0]
        log_predicted_death_after = pd.DataFrame(log_predicted_death_after_values, 
                                                  index=log_predicted_death_after_index)
        log_predicted_death_after.columns = ['predicted_death_after_lockdown_effective']
    return log_predicted_death_before, log_predicted_death_after


def get_daily_predicted_death(local_death_data, forecast_horizon=60, lockdown_date=None):
    log_predicted_death_before, log_predicted_death_after = get_log_daily_predicted_death(local_death_data, 
                                                                                          forecast_horizon, 
                                                                                          lockdown_date)
    
    daily_predicted_death_before = np.exp(log_predicted_death_before).astype(int)
    daily_predicted_death_before.columns = ['predicted_death']
    if log_predicted_death_after is not None:
        daily_predicted_death_after = np.exp(log_predicted_death_after).astype(int)
        daily_predicted_death_after.columns = ['predicted_death']
    else:
        daily_predicted_death_after = None  
    
    daily_predicted_death = pd.concat([daily_predicted_death_before, daily_predicted_death_after], axis=0)
    return daily_predicted_death, daily_predicted_death_before, daily_predicted_death_after 


def get_cumulative_predicted_death(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily_predicted_death, _, _ = get_daily_predicted_death(local_death_data, forecast_horizon, lockdown_date)
    return daily_predicted_death.cumsum()


def get_daily_metrics_from_death_data(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily_predicted_death, daily_predicted_death_before, _ = get_daily_predicted_death(local_death_data, 
                                                                                    forecast_horizon, lockdown_date)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    daily_infected_cases_new = get_infected_cases(daily_predicted_death)
    daily_symptomatic_cases_new = get_symptomatic_cases(daily_predicted_death)
    daily_hospitalized_cases_new = get_hospitalized_cases(daily_predicted_death)
    daily_hospital_beds_need = get_number_hospital_beds_need(daily_predicted_death)
    daily_ICU_need = get_number_ICU_need(daily_predicted_death)
    return pd.concat([daily_local_death_new,
                      daily_predicted_death,
                      daily_infected_cases_new,
                      daily_symptomatic_cases_new,
                      daily_hospitalized_cases_new,
                      daily_hospital_beds_need, 
                      daily_ICU_need], axis=1, sort=True)


def get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon=60, lockdown_date=None):
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = daily_metrics.cumsum()
    cumulative_metrics['ICU'] = daily_metrics['ICU']
    cumulative_metrics['hospital_beds'] = daily_metrics['hospital_beds']
    return cumulative_metrics


def get_metrics_by_country(country, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_death_data_by_country(country)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    return daily_metrics, cumulative_metrics


def get_metrics_by_state_US(state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_state(state)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    return daily_metrics, cumulative_metrics


def get_metrics_by_county_and_state_US(county, state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_county_and_state(county, state)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    return daily_metrics, cumulative_metrics


def plot_log_death_new_by_country(country, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_death_data_by_country(country)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    #log_daily_death.plot(kind='bar', title="Log of daily death over time for {}".format(country))
    log_predicted_death_before, log_predicted_death_after = get_log_daily_predicted_death(local_death_data, 
                                                                                lockdown_date=lockdown_date)
    pd.concat([log_daily_death, log_predicted_death_before, log_predicted_death_after], 
              axis=1).plot(title="Log of daily death over time for {}".format(country))


def plot_log_death_new_by_state_US(state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_state(state)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    log_predicted_death_before, log_predicted_death_after = get_log_daily_predicted_death(local_death_data, 
                                                                                lockdown_date=lockdown_date)
    pd.concat([log_daily_death, log_predicted_death_before, log_predicted_death_after], 
              axis=1).plot(title="Log of daily death over time for {}".format(state))


def plot_log_death_new_by_county_and_state_US(county, state, forecast_horizon=60, lockdown_date=None):
    local_death_data = get_US_death_data_by_county_and_state(county, state)
    daily_local_death_new = local_death_data.diff().fillna(0)
    daily_local_death_new.columns = ['death']
    log_daily_death = np.log(daily_local_death_new)
    log_predicted_death_before, log_predicted_death_after = get_log_daily_predicted_death(local_death_data, 
                                                                                lockdown_date=lockdown_date)
    pd.concat([log_daily_death, log_predicted_death_before, log_predicted_death_after], 
              axis=1).plot(title="Log of daily death over time for {}, {}".format(county, state))


def plot_metrics_by_country(country, forecast_horizon=60, lockdown_date=None, 
                            metrics=['death', 'predicted_death', 'infected', 
                                     'symptomatic', 'hospitalized', 'ICU', 'hospital_beds']):
    plot_log_death_new_by_country(country, forecast_horizon, lockdown_date)
    local_death_data = get_death_data_by_country(country)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    daily_metrics[metrics].plot(title="Daily metrics for country: {}".format(country))
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics[metrics].plot(title="Cumulative metrics for country: {}".format(country))
    

def plot_metrics_by_state_US(state, forecast_horizon=60, lockdown_date=None, 
                            metrics=['death', 'predicted_death', 'infected', 
                                     'symptomatic', 'hospitalized', 'ICU', 'hospital_beds']):
    plot_log_death_new_by_state_US(state, forecast_horizon, lockdown_date)
    local_death_data = get_US_death_data_by_state(state)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    daily_metrics[metrics].plot(title="Daily metrics for {}".format(state))
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics[metrics].plot(title="Cumulative metrics for {}".format(state))
    

def plot_metrics_by_county_and_state_US(county, state, forecast_horizon=60, lockdown_date=None, 
                            metrics=['death', 'predicted_death', 'infected', 
                                     'symptomatic', 'hospitalized', 'ICU', 'hospital_beds']):
    plot_log_death_new_by_county_and_state_US(county, state, forecast_horizon, lockdown_date)
    local_death_data = get_US_death_data_by_county_and_state(county, state)
    daily_metrics = get_daily_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    daily_metrics[metrics].plot(title="Daily metrics for {}, {}".format(county, state))
    cumulative_metrics = get_cumulative_metrics_from_death_data(local_death_data, forecast_horizon, lockdown_date)
    cumulative_metrics[metrics].plot(title="Cumulative metrics for {}, {}".format(county, state))

