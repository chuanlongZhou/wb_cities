
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from gas_net_new.constant import COUNTRY, COUNTRY_COLOR_2, COUNTRY_COLOR
import matplotlib.pyplot as plt
from gas_net_new import pd_utils


class TimeSeries:
    @staticmethod
    def get_plot_df(g, country, period, fig_type, contains, detailed):
        period_key = {
            "Daily": "D",
            "Weekly": "W",
            "Monthly": "M"
        }
        period = period_key[period]

        if contains == "consumption (overview)":
            # df = g.res_node
            contains = ["node", "storage"]
        # if contains == "consumption (detail)":
            # df = g.gen_combined_share(g)
        if contains == "storage":
            # df = g.res_storage
            contains = ["storage"]
        if contains == "direct supply":
            # df = g.gen_direct_supply(g)
            contains = ["node"]

        if fig_type == "physical flow":
            fig_type = "amount"

        temp = g.gene_supply_df(g.res_node, g.res_storage,
                                country=country,
                                period=period,
                                type=fig_type,
                                fun="sum",
                                contains=contains,
                                detailed=detailed,
                                )
        # print(temp)

        fig = g.plot_ts(temp,
                        fig_type=fig_type,
                        detailed=detailed,
                        )
        plt.title("EU gas supply (Overview)")

        st.pyplot(fig)

    @staticmethod
    def get_plot_df_diff(g, country, period, fig_type, contains, y1, y2, detailed):
        period_key = {
            "Daily": "D",
            "Weekly": "W",
            "Monthly": "M"
        }
        period = period_key[period]

        if contains == "consumption (overview)":
            # df = g.res_node
            contains = ["node", "storage"]
        # if contains == "consumption (detail)":
            # df = g.gen_combined_share(g)
        if contains == "storage":
            # df = g.res_storage
            contains = ["storage"]
        if contains == "direct supply":
            # df = g.gen_direct_supply(g)
            contains = ["node"]

        if fig_type == "physical flow":
            fig_type = "amount"

        temp = g.gene_supply_df(g.res_node, g.res_storage,
                                country=country,
                                period=period,
                                type=fig_type,
                                fun="sum",
                                contains=contains,
                                detailed=detailed,
                                )
        
        temp["date_value"] = (pd.to_datetime(temp.index.start_time) - pd.Timestamp('2000-01-01')).days 
        
        diff = pd_utils.period_diff(temp,
                            (f"{y1}-01-01", f"{y1}-12-31"),
                            (f"{y2}-01-01", f"{y2}-12-31"),
                            )
        
        diff["start_date"] = diff.index.start_time.date
        diff = diff.set_index("start_date")
        
        if detailed:
            color = COUNTRY_COLOR
        else:
            color = COUNTRY_COLOR_2
        
        if diff.shape[1] == len(color):
            color = list(map(lambda x: x+"E6", color))
        else:
            color = list(map(lambda x: x+"80", color)) + \
                list(map(lambda x: x+"E6", color))
        
        # color = list(map(lambda x:x+"80", COUNTRY_COLOR_2)) + list(map(lambda x:x+"E6", COUNTRY_COLOR_2))
        fig, ax = plt.subplots()
        
        diff.plot(
            kind='bar',
            stacked=True,
            # color=color,
            width=1,
            color=color,
            edgecolor="none",
            ax=ax
        )
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.2))
        plt.xticks(np.arange(0, diff.shape[0], int(diff.shape[0]/10)))
        plt.xticks(rotation=45, ha="right")
        plt.xlabel("")
        plt.title(f"EU gas supply difference between periods ({y1} - {y2})")

        st.pyplot(fig)

    @staticmethod
    def write(state):
        st.header("Time Series View")
        try:
            c1, c2, c3 = st.columns(3)
            country = c1.selectbox(
                "Select Country",
                ["all"]+COUNTRY
            )

            period = c1.selectbox(
                "Period",
                ("Daily", "Weekly", "Monthly")
            )

            fig_type = c2.selectbox(
                "Data type",
                ("share", "physical flow")
            )

            contains = c2.selectbox(
                "Aspect",
                ("consumption (overview)",
                 #  "consumption(detail)",
                 "storage",
                 "direct supply")
            )

            plot_diff = st.checkbox("Plot difference between two years")
            detail = st.checkbox("Show importing details")

            y1 = c3.selectbox(
                "First Year",
                (2021, 2020, 2019, 2018, 2017),
                index=0,                
                disabled=not plot_diff
            )
            y2 = c3.selectbox(
                "Second Year",
                (2021, 2020, 2019, 2018, 2017),
                index=4,
                disabled=not plot_diff
            )

            if plot_diff:
                TimeSeries.get_plot_df_diff(state.g, country, period, fig_type, contains, y1, y2, detail)
            else:
                TimeSeries.get_plot_df(
                    state.g, country, period, fig_type, contains, detail)

        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)
