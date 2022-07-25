import streamlit as st


class Concept:
  
    @staticmethod
    def write(state):
        st.header("Project Descriptions")
        st.markdown("### Motivation")
        st.markdown("""
1. We estimate the _**residential CO2 emsssion_** for the big cities in the developing coutries, which is important to understanding the ...
2. Will be completed later...
    * _...._             
                    """)
                 
        try:
            c1, c2 = st.columns(2)
            # c1.image("concept1.png")
            # c2.image("concept.png")
            

        except Exception as e:
            st.error("hum... something is going wrong here...")
            st.error(e)

