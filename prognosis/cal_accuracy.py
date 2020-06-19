import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_data_ihme(last_data_date, file_template='data/ihme_daily_us_{last_data_date}.csv'):
    """
       last_data_date = date_one_month_after_lock down
    """
    output_ihme = pd.read_csv(file_template.format(last_data_date=last_data_date))
    output_ihme_us = output_ihme[output_ihme.location_name == "United States of America"]
    output_ihme_us =  output_ihme_us[output_ihme['date'] < str(datetime.now() - timedelta(days=2))]
    output_ihme_us['deaths_cumulative'] = output_ihme.deaths_mean.cumsum()
    output_ihme_us = output_ihme_us[output_ihme_us['date'] >= last_data_date]
    return output_ihme_us


def get_data_aipert(last_data_date, file_template='data/aipert_{type}_us_{last_data_date}.csv'):
    """
       last_data_date = date_one_month_after_lock down,
       type = enum('daily','cumulative')
    """
    aipert_daily_us = pd.read_csv(file_template.format(type='daily', last_data_date=last_data_date))
    aipert_daily_us.rename(columns={'Unnamed: 0': 'date', 'death': 'observed_death'}, inplace=True)
    aipert_daily_us = aipert_daily_us[aipert_daily_us['date'] >= last_data_date][aipert_daily_us.date <
                                                                                 str(datetime.now() - timedelta(days=1))]
    #aipert_us['deaths_cumulative'] = output_aipert_us.predicted_death.cumsum()
    aipert_cumulative_us = pd.read_csv(file_template.format(type='cumulative', last_data_date=last_data_date))
    aipert_cumulative_us.rename(columns={'Unnamed: 0': 'date', 'death': 'observed_death'}, inplace=True)
    aipert_cumulative_us = aipert_cumulative_us[aipert_cumulative_us['date'] >= last_data_date][aipert_cumulative_us.date <
                                                                    str(datetime.now() - timedelta(days=1))]
    return aipert_daily_us, aipert_cumulative_us


def mean_absolute_percentage_error(y_true, y_predicted):
    y_true, y_predicted = np.array(y_true), np.array(y_predicted)
    return np.mean(np.abs((y_true - y_predicted) / y_true)) * 100


def compare_result(aipert_result_daily, aipert_result_cumulative, ihme_result, model_name_list):

    aipert_daily_mape = mean_absolute_percentage_error(aipert_result_daily.observed_death,
                                                       aipert_result_daily.predicted_death)
    ihme_daily_mape = mean_absolute_percentage_error(aipert_result_daily.observed_death, ihme_result.deaths_mean)
    aipert_cumulative_mape = mean_absolute_percentage_error(aipert_result_cumulative.observed_death,
                                                       aipert_result_cumulative.predicted_death)
    ihme_cumulative_mape = mean_absolute_percentage_error(aipert_result_cumulative.observed_death, ihme_result.deaths_cumulative)
    result = {'Model': model_name_list,
              'MAPE_daily': [aipert_daily_mape, ihme_daily_mape],
              'MAPE_cumulative': [aipert_cumulative_mape, ihme_cumulative_mape]}

    return pd.DataFrame(result, columns=['Model', 'MAPE_daily', 'MAPE_cumulative'])
