from fastapi import FastAPI
from py2neo import Graph
from fastapi import status

from server.models.responses import ErrorResponseModel

import ai.config
import ai.utils
from ai.neo4j_wrapper import Neo4jDatabase
from ai.graph_algos import GraphAlgos
from ai.utils import counter
from ai.select import summarize_communities
from ai.create import (
    extract_node_groups,
    create_discussion_nodes,
    create_similarity_graph
)

app = FastAPI(docs_url='/docs', redoc_url=None)
en_nlp, el_nlp, lang_det = ai.utils.Models.load_models()


@app.get('/', tags=['Root'])
async def read_root():
    return {'message': 'Welcome to the Main back-end!'}


@app.get('/analyze', tags=['Root'])
async def analyze():
    # Connect to the database.
    database = Neo4jDatabase(ai.config.uri, ai.config.username, ai.config.password)
    graph = Graph(ai.config.uri, auth = (ai.config.username, ai.config.password))

    # Retrieve data from the Ergologic backend.
    # data json format: {'workspaces': [], 'discussions': []}
    try:
        workspaces, discussions = ai.utils.get_data_from_ergologic()
    except Exception as e:
        return ErrorResponseModel.return_response(
            str(e), status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Failed to communicate properly with the ergologic endpoint!'
        )

    # Each workspace will hold a list of results.
    results = {wsp['id']: None for wsp in workspaces}

    for wsp in workspaces:
        # Delete the entire workspace graph.
        database.execute('MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r', 'w')

        # Only include discussions that match the current workspace.
        wsp_discussions = [
            discussion for discussion in discussions 
            if discussion['SpaceId'] == wsp['id']
        ]

        # Create node groups from the wsp_discussions object.
        node_groups = \
            extract_node_groups(wsp_discussions, ai.config.node_types, ai.config.fields)

        # Create the discussion nodes in the Neo4j Database.
        create_discussion_nodes(graph, node_groups, ai.config.fields)
    
        # Create the similarity graph.
        create_similarity_graph(graph, node_groups, 
                            ai.config.node_types, ai.config.fields, 
                            en_nlp, el_nlp, lang_det, ai.config.cutoff)

        # Calculate the community score for the similarity graph.
        with GraphAlgos(database, ['Node'], ['is_similar']) as similarity_graph:
            similarity_graph.louvain(write_property = 'community')

        # Group results based on their node types.
        node_groups = {k: [] for k in ai.config.node_types if k != 'Issue'}

        # Summarize each community of discussions and group them based on their position.
        for id, [position, _, summary, keyphrases] in summarize_communities(
                                                      database, en_nlp, el_nlp, 
                                                      lang_det, ai.config.top_n, 
                                                      ai.config.top_sent).items():   
            node_groups[position].append({
                'Summary': summary,
                'Keyphrases': keyphrases
            })
        
        # Assign the node groups to the specific workspace.
        results[wsp['id']] = node_groups
    return results