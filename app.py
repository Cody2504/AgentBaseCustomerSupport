import streamlit as st
from chatbot import app
from langchain_core.messages import AIMessage, HumanMessage
from tools import customers_database, data_protection_checks

st.set_page_config(layout='wide', page_title='Cake Shop Chatbot', page_icon='🍰')

if 'message_history' not in st.session_state:
    st.session_state.message_history = [AIMessage(content="Hiya, I'm the cake shop chatbot. How can I help you today? Let's make your day a little sweeter!")]

left_col, main_col, right_col = st.columns([1, 2, 1])

with left_col:
    if st.button('Clear Chat'):
        st.session_state.message_history = []

with main_col:
    user_input = st.chat_input("Type here...")

    if user_input:
        st.session_state.message_history.append(HumanMessage(content=user_input))

        response = app.invoke({
            'messages': st.session_state.message_history
        })

        st.session_state.message_history = response['messages']

    for i in range(1, len(st.session_state.message_history) + 1):
        this_message = st.session_state.message_history[-i]
        if isinstance(this_message, AIMessage):
            message_box = st.chat_message('assistant')
        else:
            message_box = st.chat_message('user')
        message_box.markdown(this_message.content)

with right_col:
    st.title('customers database')
    st.write(customers_database)
    st.title('data protection checks')
    st.write(data_protection_checks)