import os
from langchain import LLMMathChain
from langchain.agents import Tool
from dayatani_llm_core.constant import CALCULATOR_DESC, INTERNET_SEARCH_DESC
from langchain.utilities.bing_search import BingSearchAPIWrapper

def get_calculator_tool(llm):
    calculator_chain = LLMMathChain.from_llm(llm=llm, verbose=False)
    calculator_tool = Tool(
        name="Calculator",
        func=calculator_chain.run,
        description=f"{CALCULATOR_DESC}"
    )
    return calculator_tool

def get_internet_search_tool():
    wrapper = BingSearchAPIWrapper(bing_subscription_key=os.environ['BING_SUBSCRIPTION_KEY'],
                         bing_search_url=os.environ['BING_SEARCH_URL'],
                         k=5)
    internet_search_tool = Tool(
        name="Agriculture_Internet_Search",
        func=wrapper.run,
        description=f"{INTERNET_SEARCH_DESC}"
    )
    return internet_search_tool