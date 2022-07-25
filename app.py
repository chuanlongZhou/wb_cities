import streamlit as st
from web_pages import *
import pickle
import os

from setup import SETUP

# import matplotlib.pyplot as plt
# import seaborn as sns
# sns.set_theme("paper", font_scale=0.7)
# sns.set_style("ticks")
# plt.rcParams["figure.figsize"] = (3.5,2.5)


PAGES = [
    {"Concept": Concept, "button": False},
    {"V0 - Census data": V0, "button": False},
    {"V1 - Builidng density": V0, "button": False},
    {"V2 - LCZ/night light/satellite": V0, "button": False},
    {"V3 - ML combined": V0, "button": False},
    {"VF - 500×500m grid": V0, "button": False},
    # {"Countres": Country, "button": False},
    # {"Network": NetWork, "button": False},
    # {"divider": None, },
    # {"Dataset and Results": DataSet, "button": False},
]


def init_state(state):
    if "curr_page" not in state:
        state.curr_page = "Concept"
        state.curr_page_index = 0
        state.pages = PAGES

    if "setup" not in state:
        # note: to correctly update UI, apply button is needed, once UI re-render again, the value will be correctly assigned
        state.setup = SETUP
        state.setup_dict = {}

    if "Adana" not in state:
        state.Adana = pickle.load(open(os.path.join("data","Adana_v1.pkl"),"rb"))

    state.autoload = True

    vars = ["df", "task", "exp"]
    for v in vars:
        if v not in state:
            setattr(state, v, None)
    
    return state


def run():
    state = st.session_state
    init_state(state)
    st.set_page_config(
        page_title="Carbon Monitor City - residential",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state='expanded'
    )

    for k in state.setup:
        state.setup[k]["init_val"] = state.setup[k]["val"]
        
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        width: 80%;
        float: right;
    }
    </style>""", unsafe_allow_html=True)

    st.sidebar.markdown(
        "<h2 style='text-align: right;'> 🌍 Carbon Monitor City <br> 🏠 <i>Residential</i></h1>", unsafe_allow_html=True)
    st.sidebar.markdown(
        "<p style='text-align: right;'> Estimations of carbon emissions from cities of developing countires.</p>", unsafe_allow_html=True)

    st.sidebar.markdown("""<hr style="margin:3px;" /> """,
                        unsafe_allow_html=True)
    
    for p in state.pages:
        if "divider" in p:
            st.sidebar.markdown(
                """<hr style="margin:0px;" /> """, unsafe_allow_html=True)
        elif "title" in p:
            st.sidebar.markdown(f'**{p["title"]}**')
        else:
            p["button"] = st.sidebar.button(list(p.keys())[0])

    
    for index, p in enumerate(state.pages):
        k = list(p.keys())[0]
        if not k in ["divider", "title"] and p["button"]:
            state.curr_page = k
            state.curr_page_index = index

    state.pages[state.curr_page_index][state.curr_page].write(state)

if __name__ == '__main__':
    run()
