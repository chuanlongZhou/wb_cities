import streamlit as st
from streamlit_folium import st_folium
import folium
import pickle
import os

class V0:
  
    @staticmethod
    def write(state):
        st.header("V0 Map - Administrative divisions based")
        try:

            st.sidebar.markdown("""<hr style="margin:3px;" /> """,
                                unsafe_allow_html=True)
            
            cities = st.sidebar.multiselect(
            'Choose city',
            ['Adana', 'Cairo',  'Johannesburg', 'Ordu', 'Trabzon', 'Manisa'],[])
            
            census = st.sidebar.selectbox(
            'Choose data',
            ('population', 'household_number', 'household_size'))
            
            confirm = st.sidebar.button("Confrim selection")
            
            st.write(f"{census}")
            
            if confirm:
                m=None
                for city in cities:
                    if city not in state:
                        setattr(state, city, pickle.load(open(os.path.join("data",f"{city}_v1.pkl"),"rb")))
                    m = state[city].create_map_interactive(census, m)
                    
                st_folium(m, width=1200)

        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)

