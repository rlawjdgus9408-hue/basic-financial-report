"""
세션 상태 초기화
"""
import streamlit as st


def init_session_state():
    defaults = {
        'current_step': 1,
        'company_name': '',
        'biz_type': '',
        'ceo_name': '',
        'biz_start_date': '',
        'biz_no': '',
        'phone': '',
        'email': '',
        'address': '',
        'emp_count': '',
        'erp_system': '',
        'exec_summary': '',
        'special_note': '',
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
