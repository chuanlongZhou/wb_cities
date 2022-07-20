import streamlit as st

import pandas as pd
import numpy as np
import altair as alt
from gas_net_new.constant import COUNTRY, COUNTRY_COLOR_2, COUNTRY_COLOR
import matplotlib.pyplot as plt
from gas_net_new import pd_utils


class NetWork:
    @staticmethod
    def plot_net(g, supply, y1, y2, base_size):
        node1 = pd_utils.get_period_data(g.res_node,f"{y1}-01-01", f"{y2}-12-31")
        link1 = pd_utils.get_period_data(g.res_link,f"{y1}-01-01", f"{y2}-12-31")
        fig = g.plot_net_flow(node1, link1, g.net, column=supply, base_size=base_size)
        plt.title("Gas network flow \n(share => color, amount => size/width)")
        st.pyplot(fig)
        
    
    @staticmethod
    def write(state):
        st.header("NetWork View")
        try:
            cc1, _, _ = st.columns(3)
            
            supply =  cc1.selectbox(
                "Supply",
                ["RU", "all", "LNG", "PRO", "AZ", "DZ","LY", "RS","TR", "NO"]
            )
            
            c1, c2 = st.columns(2)
            
            y1 = c1.selectbox(
                "Starting Year",
                (2017, 2018, 2019, 2020, 2021),
                index=0,                
            )
            y2 = c2.selectbox(
                "Ending Year",
                (2017, 2018, 2019, 2020, 2021),
                index=4,
            )
            base_size =c1.slider('Base node size', 100, 800, 300)
            
            NetWork.plot_net(state.g, supply, y1, y2, base_size=base_size)
            
            
            
        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)
