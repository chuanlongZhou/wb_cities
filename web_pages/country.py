import streamlit as st

import pandas as pd
import numpy as np
import altair as alt
from gas_net_new.constant import COUNTRY, COUNTRY_COLOR_2, COUNTRY_COLOR
import matplotlib.pyplot as plt
from gas_net_new import pd_utils


class Country:
    @staticmethod
    def plot_country(g, contains, y1, y2, c1, c2):
        if contains=="storage":
            storage = True
        else:
            storage = False
            
        if storage:
            plot_country=["AT", "BE-LU", "BG",  "DE", 
                "ES",  "FR", "GR", "HR", "HU",   "IT",
                "LV-EE", "NL",  "PL",   "PT",  "RO",  "SI", "UK",]
            t="Storage"
        else:
            plot_country=None
            t="Supply"
        
        df_1 = pd_utils.get_period_data(g.res_node,f"{y1}-01-01", f"{y1}-12-31")
        df_2 = pd_utils.get_period_data(g.res_node,f"{y2}-01-01", f"{y2}-12-31")
        
        df_1, fig1= g.plot_share(df_1, title=f"{t} share of {y1}", plot_country=plot_country)
        df_2, fig2= g.plot_share(df_2, title=f"{t} share of {y2}", plot_country=plot_country)
        
        c1.pyplot(fig1)
        c2.pyplot(fig2)
        
        _, fig3 = g.plot_share(df_1-df_2, title=f"{t} share change between {y1} and {y2}", 
                    preprocessed=True,
                    sorting=["RU"],)
        plt.ylabel("Supply share change (%)")
        
        c1.pyplot(fig3)
        
    
    @staticmethod
    def write(state):
        st.header("Country View")
        try:
            cc1, _, _ = st.columns(3)
            
            contains = cc1.selectbox(
                "Aspect",
                ("consumption",
                 "storage")
            )
            
            c1, c2 = st.columns(2)
            
            y1 = c1.selectbox(
                "First Year",
                (2021, 2020, 2019, 2018, 2017),
                index=0,                
            )
            y2 = c2.selectbox(
                "Second Year",
                (2021, 2020, 2019, 2018, 2017),
                index=4,
            )
            
            Country.plot_country(state.g, contains, y1, y2, c1, c2)
            
            
            
        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)
