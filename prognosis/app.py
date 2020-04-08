import streamlit as st
from model_utils import *

st.title('Covid-19 Prognosis using death cases')


def main(scope, local, lockdown_date, forecast_fun, debug_fun, metrics, show_debug, show_data):
    data_load_state = st.text('Forecasting...')
    try:
        daily, cumulative = forecast_fun(local, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough data to provide prognosis, please check input lockdown date')
        return None
    data_load_state.text('Forecasting... done!')

    st.subheader('Daily')
    st.line_chart(daily[metrics])

    st.subheader('Cumulative')
    st.line_chart(cumulative[metrics])

    log_fit = debug_fun(local, lockdown_date=lockdown_date)
    if show_debug:
        st.subheader('Fitted log of daily death before and after lock down being effective')
        st.line_chart(log_fit)
    if show_data:
        st.subheader('Raw Data')
        st.write('Daily metrics', daily)
        st.write('Cumulative metrics', cumulative)

scope = st.sidebar.selectbox('Country or US State', ['Country', 'State'], index=0)
if scope=='Country':
    #data_load_state = st.text('Loading data...')
    death_data = get_global_death_data()
    #data_load_state.text('Loading data... done!')
    local = st.sidebar.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
    forecast_fun = get_metrics_by_country
    debug_fun = get_log_daily_predicted_death_by_country
else:
    #data_load_state = st.text('Loading data...')
    death_data = get_US_death_data()
    #data_load_state.text('Loading data... done!')
    local = st.sidebar.selectbox('Which US state do you like to see prognosis', death_data.State.unique(), index=9)
    forecast_fun = get_metrics_by_state_US
    debug_fun = get_log_daily_predicted_death_by_state_US

lockdown_date = st.sidebar.date_input('When did full lockdown happen? Very IMPORTANT to get accurate prediction')

'You selected: ', local, 'with lock down date: ', lockdown_date
metrics = st.sidebar.multiselect('Which metrics you like to plot?',
                        ('death', 'predicted_death', 'infected', 'symptomatic',
                         'hospitalized', 'ICU', 'hospital_beds'),
                        ['death', 'predicted_death', 'ICU'])
show_debug = st.sidebar.checkbox('Show fitted log death')
show_data = st.sidebar.checkbox('Show raw data')
if st.sidebar.button('Run'):
    main(scope, local, lockdown_date, forecast_fun, debug_fun, metrics, show_debug,show_data)

if st.checkbox('Show authors'):
    st.subheader('Authors')
    st.markdown('Quoc Tran - Principal Data Scientist - WalmartLabs')
    st.markdown('Huong Huynh - Data Scientist - Virtual Power Systems')
if st.checkbox('Show Datasource'):
    st.markdown('https://coronavirus.jhu.edu/map.html')
