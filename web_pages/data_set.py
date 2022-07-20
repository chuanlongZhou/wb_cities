# from numpy import correlate
import pandas as pd
import streamlit as st

from gas_net_new import pd_utils
from gas_net_new.constant import AGG_FUN

class DataSet:

    @staticmethod
    def gen_report(g, view_df, view_period):
        df = None
        fun = "sum"
        period ={
            "Daily":"D", 
            "Weekly":"W", 
            "Monthly":"M"
        }
        agg= None

        if view_df=="Original Data (Physical Flow)":
            df = g.flow_data.drop(columns=["date_value"])
            groups = ["fromCountryKey", "toCountryKey"]
            
        if view_df=="Simulation (consumption)":
            df = g.res_node[(g.res_node["DIS"]>0)|(g.res_node["FNC"]>0)]
            agg = AGG_FUN.copy()
            agg["DIS"] = ('DIS','sum')
            agg["FNC"] = ('FNC','sum')
            groups = ["country"]
            
        if view_df=="Simulation (direct supply)":
            df = g.gen_direct_supply(g)
            agg = AGG_FUN.copy()
            agg["supply"] = ('supply','sum')
            groups = ["country"]
            
        if view_df=="Simulation (storage)":
            df = g.res_storage[(g.res_storage["supply"]>0)&(g.res_storage["stored"]>0)]
            agg = AGG_FUN.copy()
            agg["supply"] = ('supply','sum')
            agg["stored"] = ('stored','sum')
            groups = ["country"]
            
        if view_df=="Simulation (pipelines)":
            df = g.res_link[g.res_link["flow"]>0]
            agg = AGG_FUN.copy()
            agg["flow"] = ('flow','sum')
            groups = ["st", "ed"]

        if view_df=="Simulation (Overall)":
            df = g.gen_combined_share(g)
            fun="mean"
            groups = ["country"]    

        
        res, _ = pd_utils.group_by_time(df, 
                               date_col="date",
                               period= period[view_period],
                               fun=fun,
                               agg=agg,
                               groupby=groups)
        res = res.drop(columns=["period", "date_value"])
        first_column = res.pop('date')
        res.insert(0, 'date', first_column)
        
        return res      
            
            
    @staticmethod
    def write(state):
        st.header("Dataset and Simulation Results")
        try:
            c1, c2, _ = st.columns(3)
            view_df = c1.selectbox(
                "Select Dataset",
                (
                 "Simulation (Overall)",
                 "Simulation (consumption)",
                 "Simulation (direct supply)",
                 "Simulation (storage)",
                 "Simulation (pipelines)",
                 "Original Data (Physical Flow)",
                 )
            )
            view_period = c2.selectbox(
                "Period",
                ("Daily", "Weekly", "Monthly")
            )
            
            # drop_zeros = st.checkbox("Drop zeros (exporting countries in simulation results)")
            dispaly_all = st.checkbox("Display full dataset")
            report = DataSet.gen_report(state.g, view_df, view_period)
            
            if dispaly_all:
                st.dataframe(report, height=800)
            else:
                st.dataframe(report.head(100), height=800)
                
            download_bt = st.download_button(
                "Download current dataset",
                report.to_csv(index=False).encode('utf-8'),
                "dataset.csv",
                "text/csv",
                key='download-csv'
            )
        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)
