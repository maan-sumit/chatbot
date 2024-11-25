from langchain.agents import Tool
from pydantic import BaseModel, Field
import os
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy
from dayatani_llm_core.constant import VECTOR_DB_DESC


class VectorDBInput(BaseModel):
    query: str = Field(description="should be a fully formed question.")

def get_vector_db_search_tool(embeddings,client_id_list):
    CONNECTION_STRING = os.environ["PG_VECTOR_URL"]
    COLLECTION_NAME = "chatbot"
    vector_db = PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings,
        distance_strategy=DistanceStrategy.COSINE,
    )

    def vector_db_search(query: str,client_list=client_id_list) -> str:
        print("QUERY & CLIENT: ",query,client_list)
        return vector_db.similarity_search(query,filter={'client_id': {'in':client_list}})

    vector_db_search_tool = Tool(
        name="Agriculture_Vector_DB_Search",
        func=vector_db_search,
        description=f"""{VECTOR_DB_DESC}""",
        args_schema=VectorDBInput,
    )

    return vector_db_search_tool