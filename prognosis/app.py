import streamlit as st
import prognosis

st.title('Covid-19 Prognosis')
data_load_state = st.text('Loading data...')
death_data = prognosis.get_global_death_data()
data_load_state.text('Loading data... done!')

country = st.sidebar.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
'You selected: ', country
data_load_state = st.text('Loading data...')
daily_country, cummulative_country = prognosis.get_metrics_by_country(country,
                                           lockdown_date='20200316')
data_load_state.text('Loading data... done!')

if st.checkbox('Show raw data'):
    st.subheader('Raw Data')
    st.write(daily_country)

st.subheader('Daily')
st.line_chart(daily_country)

st.subheader('Cummulative')
st.line_chart(cummulative_country)


