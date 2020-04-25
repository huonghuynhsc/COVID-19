import streamlit as st
import datetime as dt
import model_utils as mu
import plotly.graph_objects as go
import plotly.offline as py_offline
import cufflinks as cf
cf.go_offline()
py_offline.__PLOTLY_OFFLINE_INITIALIZED = True

mu.DEATH_RATE = 1.0
mu.ICU_RATE = 2.2
mu.HOSPITAL_RATE = 6.0
mu.SYMPTOM_RATE = 20.0
mu.INFECT_2_HOSPITAL_TIME = 12
mu.HOSPITAL_2_ICU_TIME = 2
mu.ICU_2_DEATH_TIME = 5
mu.ICU_2_RECOVER_TIME = 11
mu.NOT_ICU_DISCHARGE_TIME = 7

st.title('Covid-19 Prognosis using death cases')
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)
st.markdown('Our answer to understand COVID-19: how many deaths in the future, the real infected number'
            ', how many hospital beds or ICU needed. In every countries and US states. ')

def main(scope, local, lockdown_date, forecast_fun, debug_fun, metrics, show_debug, show_data):
    data_load_state = st.text('Forecasting...')
    try:
        daily, cumulative, model_beta = forecast_fun(local, lockdown_date=lockdown_date)
    except ValueError:
        st.error('Not enough fatality data to provide prognosis, please check input and lockdown date')
        return None
    data_load_state.text('Forecasting... done!')

    st.subheader('Deaths')
    show_metrics = ['death', 'predicted_death']
    fig = daily[show_metrics].rename(columns={'death':'observed', 'predicted_death': 'predicted'})\
        .drop(columns=['ICU', 'hospital_beds'], errors='ignore').iplot(asFigure=True)
    x = daily.index
    y_upper = daily.upper_bound.values
    y_lower = daily.lower_bound.values
    fig.add_trace(go.Scatter(
        x=x,
        y=y_upper,
        fill=None,
        line_color='rgba(128,128,128,0)',
        legendgroup='Confidence Interval',
        showlegend=True,
        name='Upper Bound'))

    fig.add_trace(go.Scatter(
        x=x,
        y=y_lower,
        fill='tonexty',
        fillcolor='rgba(66, 164, 245,0.1)',
        line_color='rgba(128,128,128,0)',
        showlegend=True,
        legendgroup='Confidence Interval',
        name='Lower Bound'
    ))
    fig.update_layout(
        title="Daily",
        yaxis_title="Death",
        hovermode='x',
        legend_title='<b> Death </b>',
    )
    st.plotly_chart(fig)

    fig = cumulative[show_metrics].rename(columns={'death':'observed', 'predicted_death': 'predicted'})\
        .iplot(asFigure=True)
    x = cumulative.index
    y_upper = cumulative.upper_bound.values
    y_lower = cumulative.lower_bound.values
    fig.add_trace(go.Scatter(
        x=x,
        y=y_upper,
        fill=None,
        line_color='rgba(128,128,128,0)',
        legendgroup = 'CI',
        name='Upper Bound'))

    fig.add_trace(go.Scatter(
        x=x,
        y=y_lower,
        fill='tonexty',
        fillcolor='rgba(66, 164, 245,0.1)',
        line_color='rgba(128,128,128,0)',
        legendgroup='CI',
        name='Lower Bound'
    ))
    fig.update_layout(
        title="Cumulative",
        yaxis_title="Death",
        hovermode='x',
        legend_title='<b> Death </b>'
    )

    st.plotly_chart(fig)

    log_fit, _ = debug_fun(local, lockdown_date=lockdown_date)
    if show_debug:
        fig = log_fit.rename(columns={'death':'observed', 'predicted_death': 'predicted'})\
            .drop(columns=['lower_bound', 'upper_bound'], errors='ignore').iplot(asFigure=True)
        x = log_fit.index
        y_upper = log_fit.upper_bound.values
        y_lower = log_fit.lower_bound.values
        fig.add_trace(go.Scatter(
            x=x,
            y=y_upper,
            fill=None,
            line_color='rgba(128,128,128,0)',
            legendgroup='CI',
            name='Upper Bound'))

        fig.add_trace(go.Scatter(
            x=x,
            y=y_lower,
            fill='tonexty',
            fillcolor='rgba(66, 164, 245,0.1)',
            line_color='rgba(128,128,128,0)',
            legendgroup='CI',
            name='Lower Bound'
        ))
        fig.update_layout(
            title="Fitted log of daily death before and after lock down being effective",
            yaxis_title="Log Daily Death",
            hovermode='x',
            legend_title='<b> Death </b>',
        )
        st.plotly_chart(fig)

    st.subheader('Estimated Cases and Essential Resources')
    st.markdown('Since health care systems vary widely between geographic location, if this is used for planning, please'
                ' check the advance box on the sidebar to update with the appropriate parameters')
    fig = daily[metrics].drop(columns=['ICU', 'hospital_beds'], errors='ignore').iplot(asFigure=True)
    x = daily.index
    y_upper = daily.upper_bound.values
    y_lower = daily.lower_bound.values
    # fig.add_trace(go.Scatter(
    #     x=x,
    #     y=y_upper,
    #     fill=None,
    #     line_color='rgba(128,128,128,0)',
    #     showlegend=False,
    #     name='Upper Bound'))
    #
    # fig.add_trace(go.Scatter(
    #     x=x,
    #     y=y_lower,
    #     fill='tonexty',
    #     fillcolor='rgba(128,128,128,0.1)',
    #     line_color='rgba(128,128,128,0)',
    #     showlegend=False,
    #     name='Lower Bound'
    # ))
    fig.update_layout(
        title="Daily",
        hovermode='x',
        legend_title='<b> Estimated Cases </b>',
    )

    st.plotly_chart(fig)

    fig = cumulative[metrics].iplot(asFigure=True)
    x = cumulative.index
    y_upper = cumulative.upper_bound.values
    y_lower = cumulative.lower_bound.values
    # fig.add_trace(go.Scatter(
    #     x=x,
    #     y=y_upper,
    #     fill=None,
    #     line_color='rgba(128,128,128,0)',
    #     showlegend=False,
    #     name='Upper Bound'))
    #
    # fig.add_trace(go.Scatter(
    #     x=x,
    #     y=y_lower,
    #     fill='tonexty',
    #     fillcolor='rgba(128,128,128,0.1)',
    #     line_color='rgba(128,128,128,0)',
    #     showlegend=False,
    #     name='Lower Bound'
    # ))
    fig.update_layout(
        title="Cumulative",
        hovermode='x',
        legend_title='<b> Estimated Cases </b>',
    )

    st.plotly_chart(fig)

    if show_data:
        st.subheader('Raw Output Data')
        st.markdown(mu.get_table_download_link(daily, filename= 'daily_'+local+'_'+str(dt.date.today())+'.csv'),
                    unsafe_allow_html=True)
        st.write('Daily metrics', daily)
        st.markdown(mu.get_table_download_link(cumulative,
                                               filename='cumulative_' + local + '_' + str(dt.date.today()) + '.csv'),
                    unsafe_allow_html=True)
        st.write('Cumulative metrics', cumulative)
    mu.append_row_2_logs([dt.datetime.today(), scope, local, model_beta], 'logs/fitted_models.csv')

scope = st.sidebar.selectbox('Country or US State', ['Country', 'State'], index=0)
if scope=='Country':
    #data_load_state = st.text('Loading data...')
    death_data = mu.get_global_death_data()
    #data_load_state.text('Loading data... done!')
    local = st.sidebar.selectbox('Which country do you like to see prognosis', death_data.Country.unique(), index=156)
    lockdown_date = st.sidebar.date_input('When did full lockdown happen? Very IMPORTANT to get accurate prediction',
                                          mu.get_lockdown_date_by_country(local))
    forecast_fun = mu.get_metrics_by_country
    debug_fun = mu.get_log_daily_predicted_death_by_country
else:
    #data_load_state = st.text('Loading data...')
    death_data = mu.get_US_death_data()
    #data_load_state.text('Loading data... done!')
    local = st.sidebar.selectbox('Which US state do you like to see prognosis', death_data.State.unique(), index=9)
    lockdown_date = st.sidebar.date_input('When did full lockdown happen? Very IMPORTANT to get accurate prediction',
                                          mu.get_lockdown_date_by_state_US(local))
    forecast_fun = mu.get_metrics_by_state_US
    debug_fun = mu.get_log_daily_predicted_death_by_state_US



'You selected: ', local, 'with lock down date: ', lockdown_date, '. Click **Run** on left sidebar to see forecast. Plot' \
                                                                 ' is interactive.'
metrics = st.sidebar.multiselect('Which metrics you like to calculate?',
                        ('death', 'predicted_death', 'infected', 'symptomatic',
                         'hospitalized', 'ICU', 'hospital_beds'),
                        ['death', 'predicted_death', 'infected', 'symptomatic',
                         'hospitalized', 'ICU', 'hospital_beds'])

#metrics = ['death', 'predicted_death', 'infected', 'symptomatic', 'hospitalized', 'ICU', 'hospital_beds']
show_debug = st.sidebar.checkbox('Show fitted log death', value=True)
show_data = st.sidebar.checkbox('Show raw output data')
if st.sidebar.checkbox('Advance: change assumptions'):
    if st.sidebar.checkbox('Change rates'):
        mu.DEATH_RATE = st.sidebar.slider('Overall death rate', value=mu.DEATH_RATE,
                                       min_value=0.1, max_value=100.0, step=0.1)
        mu.ICU_RATE = st.sidebar.slider('ICU rate', value=max(mu.ICU_RATE, mu.DEATH_RATE),
                                       min_value=mu.DEATH_RATE, max_value=100.0, step=0.1)
        mu.HOSPITAL_RATE = st.sidebar.slider('Hospitalized rate', value=max(mu.ICU_RATE, mu.HOSPITAL_RATE),
                                       min_value=mu.ICU_RATE, max_value=100.0, step=0.1)
        mu.SYMPTOM_RATE = st.sidebar.slider('Symptomatic rate', value=max(mu.SYMPTOM_RATE, mu.HOSPITAL_RATE),
                                       min_value=mu.HOSPITAL_RATE, max_value=100.0, step=0.1)
    if st.sidebar.checkbox('Change time'):
        mu.INFECT_2_HOSPITAL_TIME = st.sidebar.slider('Time to hospitalized since infected',
                                                      value=mu.INFECT_2_HOSPITAL_TIME, min_value=1, max_value=21)
        mu.HOSPITAL_2_ICU_TIME = st.sidebar.slider('Time to ICU since hospitalized',
                                                      value=mu.HOSPITAL_2_ICU_TIME, min_value=1, max_value=21)
        mu.ICU_2_DEATH_TIME = st.sidebar.slider('Time to death since ICU ',
                                                      value=mu.ICU_2_DEATH_TIME, min_value=1, max_value=21)
        mu.ICU_2_RECOVER_TIME = st.sidebar.slider('Time to recover since ICU ',
                                                      value=mu.ICU_2_RECOVER_TIME, min_value=1, max_value=30)
        mu.NOT_ICU_DISCHARGE_TIME = st.sidebar.slider('Time to discharge',
                                                      value=mu.NOT_ICU_DISCHARGE_TIME, min_value=1, max_value=21)

if st.sidebar.button('Run'):
    main(scope, local, lockdown_date, forecast_fun, debug_fun, metrics, show_debug,show_data)
    model_params = [dt.datetime.today(), scope, local, lockdown_date, mu.DEATH_RATE, mu.ICU_RATE, mu.HOSPITAL_RATE,
                    mu.SYMPTOM_RATE, mu.INFECT_2_HOSPITAL_TIME, mu.HOSPITAL_2_ICU_TIME, mu.ICU_2_DEATH_TIME, 
                    mu.ICU_2_RECOVER_TIME, mu.NOT_ICU_DISCHARGE_TIME]
    mu.append_row_2_logs(model_params)

if st.checkbox('Show authors'):
    st.subheader('Authors')
    st.markdown('[Quoc Tran](https://www.linkedin.com/in/quoc-tran-wml) - Principal Data Scientist - WalmartLabs')
    st.markdown('[Huong Huynh](https://www.linkedin.com/in/huonghuynhsjsu) - Data Scientist - Virtual Power Systems')
    st.markdown('Feedback: hthuongsc@gmail.com')
    st.markdown('[Gibhub](https://github.com/QuocTran/COVID-19.git)')
    if st.checkbox('Leave feedback directly'):
        feedback = st.text_input('Write your feedback directly hear, include your email if you would like a reply')
        if feedback != '':
            mu.append_row_2_logs([dt.datetime.today(), feedback], log_file='logs/feedback_logs.csv')
if st.checkbox('Show Datasource'):
    st.markdown('https://coronavirus.jhu.edu/map.html')
if st.checkbox('About the model'):
    st.subheader('Assumptions')
    st.markdown('''
            Number of **DEATH** is the most accurate metric, despite [undercount]
            (https://www.nytimes.com/2020/04/10/nyregion/new-york-coronavirus-death-count.html), especially near peak.  
            It will be used to project other metrics under these [assumptions]
            (https://midasnetwork.us/covid-19/) for Covid19:  
            - The overall case fatality rate: 1 percent.    
            - Patients need ICU: 2.2 percent (critical)  
            - Patients need hospitalized: 6 percent (severe)  
            - Patients with symptom: 20 percent   
            - Time to hospitalized since infectected: 12 days (5 days incubation and 7 days from symptom to severe)  
            - Time to ICU since hospitalized: 2 days (assume only severe case needs to be hospitalized)  
            - Time to death since ICU use: 5 days  
            - Time to recover since ICU use: 11 days  
            - 7 days discharge if not in ICU or coming back from ICU  
            Average ICU time use: 10 (included both dead (5) and alive(11)): (5+11*4)/5  
            Only ICU (critical) patients can develop death  
            
            [Here]
            (https://www.mercurynews.com/2020/04/11/when-coronavirus-kills-its-like-death-by-drowning-and-doctors-disagree-on-best-treatment/)
            is an account from the news.   
            In the assumptions, we mostly use the lower range from medical literature
            because we want to calculate the minimum ICU and hospital beds needed. These assumptions are not valid in
            local where resource is limited, while people die sooner and more often on ICU just because of not enough
            ICU to put people on. E.g. Iran, Italy, New York when dead cases peak.''')
    st.subheader('Projections')
    st.markdown('''
            1. Total number of infection at large: death*100 (not too meaningful) or infected rate in population 
            (for individual and company to quantify risk of infection, for public health dept to declare herd immunity, 
            relax lock down measurements).
            This has a **20 days lag**, ie. this number is of 20 days ago. 
            Only in total lockdown setting, we can use the cummulative death from day 20th times 100 to get 
            total number of infection at large accurately. 
            Other alternative is whole population testing to get this number immediately. 
            2. With a correct forecast on number of death, we can get the forecast for number of hospital beds needed. 
            This is  used to build more hospital beds in advance.
            Each new death equal to 6 hospitalized (5+2)7 days before the death and continue for 10 days
            (using the 6% hospital rate and 1% death rate and 10 days average hospitalized and 
            5 days from ICU to death, 2 days from hospital to ICU)
            3. With a correct forecast number of death, we can get the forecast for number of ICU needed. 
            This is used to prepare ICU and buying ventilators or prepare for hospital white flags moment, 
            when doctors have to decide who to treat and who left to death due to constraint on ICU, ventilator. 
            This is also needed to prepare for social unrest.
            Each new death equal to 2.2 ICU beds 5 days before the death and continue for 10 days 
            (using the 2.2% ICU rate and 1% death rate and 10 days average ICU used)
            ''')
    st.subheader('Forecasting death')
    st.markdown('''
    Since this is highly contagious disease, daily new death, which is a proxy for daily new infected cases
    is modeled as $d(t)=a*d(t-1)$ or equivalent to $d(t) = b*a^t$.   
    After a log transform, it becomes linear: $log(d(t))=logb+t*loga$ , so we can use linear regression to 
    provide forecast.   
    We actually use robust linear regressor to avoid data anomaly in death reporting.  
    There are two seperate linear curves, one before the lockdown is effective (21 days after lockdown) and one after.
    For using this prediction to infer back the other metrics (infected cases, hospital, ICU, etc..) only the before
    curve is used and valid. If we assume there is no new infection after lock down (perfect lockdown), the after
    curve only depends on the distribution of time to death since ICU. Since this is unknown, we have to fit the second
    curve. So for this piecewise linear function, we use package 
    [pwlf](https://jekel.me/piecewise_linear_fit_py/index.html#) with breakpoints set at lockdown effective date.
    
    
    WARNING: if lockdown_date is not provided, we will default to no lockdown to raise awareness of worst case
    if no action. If you have info on lock down date please use it to make sure the model provide accurate result
            ''')
    st.subheader('Implications')
    st.markdown('''
            Implications are observed in data everywhere:  
            
            
            0. ***Do not use only confirmed case to make decision***. It is misleading and distorted by testing capicity
            1. Country with severe testing constraint will see death rate lurking around 10-15%, 
            which is 1% death/6% hospitalized. E.g. Italy, Spain, Iran at the beginning. 
            While country with enough testing for all symptomatic patients see rate less than 5% (1%/20%).
            And country that can test most of potential patients, through contact tracing like South Korea and Germany,
            can get closer to 1%. It is very hard to get under 1% unless an effective cure is in hand. Maybe Vietnam?   
            2. After lock down, we need at least 15 days to see daily new cases peaks and around 20 days to see daily 
            new deaths peak, which is just in the most effective lock down. 
            For a less successful one, or severe limit on testing, this number of lag day is higher on new cases and 
            deaths.           
            3. The death peak is about 5 days after the cases peak, but cases depends on testing.   
            4. It needs about a month from the peak for new cases completely dissipate. 
            The number of death is also slow down but have a fat tail and a about 20 days longer than the cases tail.            
            5. The above does not apply to country using widespread testing in place of SIP/lockdown like Korea.            
            6. When no ICU, ventilator available, death rate can increase at most 2.2 times
            ''')
    st.subheader('TODO')
    st.markdown('''
            1. Need to understand how long since infection, patient is no longer a source of infection to forecast
            curve after lock down period relaxed.          
            2. Upgrade the calculation using mean to use distribution if enough data is available.''')
if st.checkbox('Medical myths'):
    st.markdown('I am not a medical doctor. I am a statistician but I strongly believe in this:')
    st.subheader('How Vietnamese doctors treat SARS before and COVID19 now?')
    st.markdown('''
    The doctors open all doors and windows to let sunlight in and sick air out. Patients with mild symptom are suggested
    to [gargling with salt water.]
    (https://www.webmd.com/cold-and-flu/features/does-gargling-wlth-salt-water-ease-a-sore-throat#1) 
    Some rare severe patients need treatment, ventilator and/or ECMO anyway. We have no other secrete weapon beside the
    hot humid weather. By doing that, we get very low death rate, zero for now, and low infection rate for doctors. Why
    does it work? We think utmostly, this is an ***airborne*** disease. People got infected or death because of the air 
    they breath in, or more precisely by how much viruses in the air they put into their lungs at that particular 
    moment. That is why we see a mild progression, when patient's lung adapts to virus in the air, might suddenly turn to
    a [death end]
    (https://www.mercurynews.com/2020/04/11/when-coronavirus-kills-its-like-death-by-drowning-and-doctors-disagree-on-best-treatment/)
    ''')
    st.subheader('How does patient die from COVID-19?')
    st.markdown('''
    Short answer: mostly not because of the virus but because of their own immune system, particularly the cytokine 
    release syndrome. 
    
    Long answer: When patient got infected, virus can be everywhere from their respiratory tracts, blood, stool,.. even
    brain, but the critical center is in their tonsils. When the density of virus is enough, around 5-14 days after 
    infection, patients start to get a lot of dry cough, which release the virus to the air and to their lungs. 
    And then the lungs cells die very fast due to the immune system rush in and kill everything, the viruses and the
    lung cells. Hence, the disease is named severe acute respiratory syndrome (SARS). How to prevent the death happen?
    Keep patient's lung away from the viruses in the air. And as soon as you can.''')
    st.subheader('Why ventilator is so important? or not?')
    st.markdown('''
    - When lots of lung cells die, the air sacs of the lungs become filled with a gummy yellow fluid, 
    other organs got cut off from the oxygen in blood, and dying too.
    Among those who are critically ill, profound acute hypoxemic respiratory failure from ARDS is the dominant finding.
    The need for mechanical ventilation in those who are critically ill is high ranging from 42 to 100 percent. [Link]
    (https://www.uptodate.com/contents/coronavirus-disease-2019-covid-19-critical-care-issues)  
    - But the ventilator also serves a very important purpose: keep the virus away from the air patient breathes in. So if 
    your local does not have any ventilator left, you can make a cheap breathing device that can filter virus from the 
    air intake and fan away air out of patient. Like open door with big fan. Or fancier, using the [helmet]
    (https://www.nbcnews.com/news/us-news/texas-mom-pop-business-flooded-orders-helmet-ventilators-amid-coronavirus-n1173466)
    , which is proved working through [medical trial]
    (https://www.uchicagomedicine.org/forefront/patient-care-articles/helmet-based-ventilation-is-superior-to-face-mask-for-patients-with-respiratory-distress)
    . For patient that can not breath on their own, something like [this]
    (https://newatlas.com/medical/british-engineers-modern-iron-lung-covid-19-ventilator-alternative/)
    will help. Try to not let patient bubble in their own viruses, just as the patients died in the 
    [adult care facility]
    (https://abc7news.com/health/6-dead-53-infected-with-covid-19-at-hayward-assisted-living-facility/6088815/)''')
    st.subheader('How to be in the 95 percent patients that are not in critical condition?')
    st.markdown('''
    When you are positive for COVID19 but not have enough symptoms to be admitted to hospital, keep your place well 
    ventilated (open windows or fan out), well lit with sun light, and warmer than normal. 
    Gargle with salt water at least 3 times a day or when
    you want to cough. Try to cough as less as you can using any method you know, or go outside if you need to. And then
    watch your vitals, temperature and blood oxygen level for sign that you can be admitted to hospital for proper care.
    ''')
    st.subheader('How to prevent the transmission?')
    st.markdown('''
    The main thing this website show is that lockdown is actually working. So follow the lock down guideline, 
    particularly avoid close air spaces with lots of people, such as airplane, subway, church, etc.., 
    and ***wear mask***.''')
    st.markdown('***Splease spread the message and stay safe!***')
    mu.append_row_2_logs([dt.datetime.today(), ], log_file='logs/medical_myths_logs.csv')

if st.checkbox('References'):
    st.markdown('[IHME COVID-19 Infection Spread](https://covid19.healthdata.org) '
                'Reason we speed up our development. Lots of thing to like. One thing '
                'we would do differently, the forecasting model.')
    st.markdown('https://www.streamlit.io Fast prototype.')
    st.markdown('[pwlf](https://jekel.me/piecewise_linear_fit_py/index.html) Key tool for my model')
    st.markdown('https://www.uptodate.com/contents/coronavirus-disease-2019-covid-19')
    st.markdown('https://midasnetwork.us/covid-19/')
    st.markdown('[Letter from the frontline, Italy]'
                '(https://www.atsjournals.org/doi/pdf/10.1164/rccm.202003-0817LE)')
    st.markdown('[COVID-19 Hospital Impact Model for Epidemics (CHIME)](https://penn-chime.phl.io)')
    st.markdown('[UW-Madison AFI DSI Covid-19 Research Portal](https://datascience.wisc.edu/covid19/)')
    st.markdown('[Fast fact on US hospital beds]'
                '(https://www.aha.org/statistics/fast-facts-us-hospitals)')
    st.markdown('[Number of ventilators] '
                '(https://www.centerforhealthsecurity.org/resources/COVID-19/COVID-19-fact-sheets/200214-VentilatorAvailability-factsheet.pdf)')
    st.markdown('[Universal Screening for SARS-CoV-2](https://www.nejm.org/doi/10.1056/NEJMc2009316)')

    st.subheader('On the news')
    st.markdown('https://www.mercurynews.com/2020/04/11/when-coronavirus-kills-its-like-death-by-drowning-and-doctors-disagree-on-best-treatment/')
    st.markdown('https://www.statnews.com/2020/04/08/doctors-say-ventilators-overused-for-covid-19/')
    st.markdown('https://www.uchicagomedicine.org/forefront/patient-care-articles/helmet-based-ventilation-is-superior-to-face-mask-for-patients-with-respiratory-distress')
    st.markdown('https://www.cnn.com/2020/04/17/asia/china-wuhan-coronavirus-death-toll-intl-hnk/index.html')
    st.markdown('I never believe that some days I see this long sad story in [New Yorker]'
                '(https://www.newyorker.com/news/our-local-correspondents/the-body-collectors-of-the-coronavirus-pandemic)'
                )

if st.checkbox('Changelog'):
    st.markdown('2020/04/22 Big change on the default parameters about rates using the New York study, which suggests '
                'asymptomatic rate is 88 percent and death rate is 1 percent. This is now in line with the Chinese study'
                ' . We only need to divide every rate in Chinese study by 2.3. So hospitalized reduced to 6 pct and ICU'
                ' rate to 2.2 pct')
