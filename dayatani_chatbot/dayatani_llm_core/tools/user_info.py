from langchain.agents import Tool
from pydantic import BaseModel, Field
from dayatani_llm_core.constant import USER_INFO_DESC, USER_INFO_NOT_FOUND_MSG


class UserInfoInput(BaseModel):
    category: str = Field(description="should be a category name in lower case.")

def get_user_info_tool(user_info):
    def dummy(category):
        return user_info.get(category,USER_INFO_NOT_FOUND_MSG)
    
    user_info_search_tool = Tool(
        name="USER_INFORMATION_SEARCH",
        func=dummy,
        description=f"""{USER_INFO_DESC}""",
        args_schema=UserInfoInput,
    )

    return user_info_search_tool


