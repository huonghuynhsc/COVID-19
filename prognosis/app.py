import streamlit as st
import prognosis

st.title('Covid-19 Prognosis')
scope = st.sidebar.selectbox('Country or US State', ['Country', 'State'], index=0)
if scope=='Country':
    data_load_state = st.text('Loading data...')
    death_data = prognosis.get_global_death_data()
    data_load_state.text('Loading data... done!')
    country = st.sidebar.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
    'You selected: ', country
    data_load_state = st.text('Loading data...')
    daily, cumulative = prognosis.get_metrics_by_country(country, lockdown_date='20200316')
    data_load_state.text('Loading data... done!')
else:
    data_load_state = st.text('Loading data...')
    death_data = prognosis.get_US_death_data()
    data_load_state.text('Loading data... done!')
    state = st.sidebar.selectbox('Which US state do you like to see prognosis', death_data.State.unique(), index=9)
    'You selected: ', state
    data_load_state = st.text('Loading data...')
    daily, cumulative = prognosis.get_metrics_by_state_US(state, lockdown_date='20200316')
    data_load_state.text('Loading data... done!')

if st.checkbox('Show raw data'):
    st.subheader('Raw Data')
    st.write(daily)
    st.write(cumulative)

st.subheader('Daily')
st.line_chart(daily)

st.subheader('Cumulative')
st.line_chart(cumulative)


