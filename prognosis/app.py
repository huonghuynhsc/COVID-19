import streamlit as st
from model_utils import *

st.title('Covid-19 Prognosis using death cases')

scope_box = st.sidebar.empty()
local_box = st.sidebar.empty()
lockdown_date = st.sidebar.date_input('When did full lockdown happen? Very IMPORTANT to get accurate prediction')
scope = scope_box.selectbox('Country or US State', ['Country', 'State'], index=0)
if scope=='Country':
    #data_load_state = st.text('Loading data...')
    death_data = get_global_death_data()
    #data_load_state.text('Loading data... done!')
    country = local_box.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
    'You selected: ', country
    data_load_state = st.text('Forecasting...')
    try:
        daily, cumulative = get_metrics_by_country(country, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough data to provide prognosis, please check input lockdown date')
    data_load_state.text('Forecasting... done!')
else:
    #data_load_state = st.text('Loading data...')
    death_data = get_US_death_data()
    #data_load_state.text('Loading data... done!')
    state = local_box.selectbox('Which US state do you like to see prognosis', death_data.State.unique(), index=9)
    'You selected: ', state
    data_load_state = st.text('Forecasting...')
    try:
        daily, cumulative = get_metrics_by_state_US(state, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough data to provide prognosis, please check input lockdown date')
    data_load_state.text('Forecasting... done!')

metrics = st.multiselect('Which metrics you like to plot?',
                        ('death', 'predicted_death', 'infected', 'symptomatic', 'hospitalized', 'ICU', 'hospital_beds'),
                        ['death', 'predicted_death', 'ICU'])

st.subheader('Daily')
st.line_chart(daily[metrics])

st.subheader('Cumulative')
st.line_chart(cumulative[metrics])

if st.checkbox('Show fitted log death'):
    st.subheader('Fitted log of daily death before and after lock down being effective')
    log_fit = get_log_daily_predicted_death_by_country(country, lockdown_date=lockdown_date)
    st.line_chart(log_fit)
#.plot(title="Log of daily death over time for {}".format(country))
if st.checkbox('Show raw data'):
    st.subheader('Raw Data')
    st.write('Daily metrics', daily)
    st.write('Cumulative metrics', cumulative)

