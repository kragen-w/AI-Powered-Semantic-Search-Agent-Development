import logging

# Set the logging level to only show warnings and errors
logging.basicConfig(level=logging.WARN)

import weaviate
import weaviate.classes as wvc
import os
import json


def create_client(weaviate_version = "1.24.10") -> weaviate.WeaviateClient:
    # create the client
    client = weaviate.connect_to_embedded(
        version=weaviate_version,
        headers={
            # this pulls your OPENAI_API_KEY from your environment (do not put it here)
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")  # Replace with your API key
        }
    ) 

    return client

def create_collection(client : weaviate.WeaviateClient, 
                      collection_name : str,
                      embedding_model : str = 'text-embedding-3-small',
                      model_dimensions : int = 512):
    """
    Create a collection, which you can roughly think of as a table in a database.
    If it already exists, just return it.
    """
    collection = None
    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)

    # otherwise, create the collection
    collection = client.collections.create(
        name = collection_name,
        # configure the vectorizer, which will get your embeddings
        vectorizer_config = wvc.config.Configure.Vectorizer.text2vec_openai(
            model = embedding_model,
            dimensions = model_dimensions
        ),
        # default to the openai LLM for generative work
        generative_config = wvc.config.Configure.Generative.openai(),
        properties=[
            wvc.config.Property(
                name="name", data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="body_part", data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="muscle_group", data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="difficulty", data_type=wvc.config.DataType.INT
            ),
            wvc.config.Property(
                name="at_home", data_type=wvc.config.DataType.BOOL
            ),
            wvc.config.Property(
                name="description", data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="rep_range", data_type=wvc.config.DataType.TEXT
            )
        ]
    )
    
    # now return the collection
    return collection
def load_database(client, collection):


    data = {}
    objs = []
    with open('Project3-Retrieval/bodybuilding.json', 'r') as file:
        data = json.loads(file.read())
        for item in data:
            objs.append({
    # note, you’d use your json keys here
        'name': item['name'],
        'body_part': item['body_part'],
        'muscle_group': item['muscle_group'],
        'difficulty': item['difficulty'],
        'at_home': item['at_home'],
        'description': item['description'],
        'rep_range': item['rep_range'],
            })
    # now add it to the collection
    collection.data.insert_many(objs)



def make_everything(collection_name: str):
    client = create_client()
    collection = create_collection(client, collection_name)
    load_database(client,collection)
    return client, collection