import streamlit as st
import prognosis

st.title('Covid-19 Prognosis')

lockdown_date = st.sidebar.date_input('When did full lockdown happen? Very IMPORTANT to get accurate prediction')
scope = st.sidebar.selectbox('Country or US State', ['Country', 'State'], index=0)
if scope=='Country':
    data_load_state = st.text('Loading data...')
    death_data = prognosis.get_global_death_data()
    data_load_state.text('Loading data... done!')
    country = st.sidebar.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
    'You selected: ', country
    data_load_state = st.text('Loading data...')
    try:
        daily, cumulative = prognosis.get_metrics_by_country(country, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough data to provide prognosis, please check input lockdown date')
    data_load_state.text('Loading data... done!')
else:
    data_load_state = st.text('Loading data...')
    death_data = prognosis.get_US_death_data()
    data_load_state.text('Loading data... done!')
    state = st.sidebar.selectbox('Which US state do you like to see prognosis', death_data.State.unique(), index=9)
    'You selected: ', state
    data_load_state = st.text('Loading data...')
    try:
        daily, cumulative = prognosis.get_metrics_by_state_US(state, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough data to provide prognosis, please check input lockdown date')
    data_load_state.text('Loading data... done!')

metrics = st.multiselect('Which metrics you like to plot?',
                        ('death', 'predicted_death', 'infected', 'symptomatic', 'hospitalized', 'ICU', 'hospital_beds'),
                        ['death', 'predicted_death', 'ICU'])

st.subheader('Daily')
st.line_chart(daily[metrics])

st.subheader('Cumulative')
st.line_chart(cumulative[metrics])

#if st.checkbox('Show fitted log death'):
#    st.subheader('Fitted log of daily death before and after lock down being effective')
#    st.write(prognosis.plot_log_death_new_by_country(country, lockdown_date=lockdown_date))

if st.checkbox('Show raw data'):
    st.subheader('Raw Data')
    st.write(daily)
    st.write(cumulative)

