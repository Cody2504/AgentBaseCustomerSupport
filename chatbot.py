import os
from langgraph.graph import StateGraph, MessagesState
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from tools import query_knowledge_base, search_for_product_recommendations, create_new_customer, data_protection_check, place_order, retrieve_existing_customer_orders
from dotenv import load_dotenv
load_dotenv()

os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")

prompt = """
You are a customer service chatbot for a cake shop company. You can help the customer achieve the goals listed below

#Goals
1. Answer questions the user might have relating to services offered
2. Recommend products to the user based on their preferences
3. Retrieve or create customer profiles. If the customer already has a profile, perform a data protection check to retrieve their details. If not, create them a profile.
4. To place and manage orders, you will need a customer profile (with an associated id). If the customer already has a profile, perform a data protection check to retrieve their details. If not, create them a profile.

#Tone
Helpful, friendly. Use cake and baking related puns or gen-z emojis to keep things lighthearted. You MUST always include a funny cake related pun in your response.
"""
chat_template = ChatPromptTemplate.from_messages([
    ('system', prompt),
    ('placeholder', "{messages}")
])

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

tools = [query_knowledge_base, search_for_product_recommendations, data_protection_check, create_new_customer, place_order, retrieve_existing_customer_orders]


llm_with_prompt = chat_template | llm.bind_tools(tools)

def call_agent(message_state: MessagesState):
    response = llm_with_prompt.invoke(message_state)    
    return {
        'messages': [response]
    }

def is_tool_call(state: MessagesState):
    last_message = state['messages'][-1] if state['messages'] else None
    if last_message.tool_calls:
        return 'tool_node'
    else:
        return '__end__'

tool_node = ToolNode(tools)

#graph
graph = StateGraph(MessagesState)
graph.add_node('agent', call_agent)
graph.add_node('tool_node', tool_node)

graph.add_conditional_edges(
    "agent",
    is_tool_call
)
graph.add_edge('tool_node', 'agent')
graph.set_entry_point('agent')
app = graph.compile()