#!/usr/bin/env python3
"""
Debug da busca ElasticSearch
"""

import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

# Configuração do Elasticsearch Cloud
es_config = {
    'cloud_id': os.getenv('ES_CLOUD_ID'),
    'api_key': (
        os.getenv('ES_API_ID'),
        os.getenv('ES_API_KEY')
    ),
    'timeout': 30,
    'max_retries': 3,
    'retry_on_timeout': True
}

es_client = Elasticsearch(**es_config)

if es_client.ping():
    print("✅ Conectado ao ES")
    
    # Testa cada índice
    for index in ['braincomercial', 'consultores', 'unibrain']:
        print(f"\n📊 Testando índice: {index}")
        
        # Count total
        count_response = es_client.count(index=index)
        total = count_response['count']
        print(f"Total no count: {total}")
        
        # Busca simples
        search_response = es_client.search(
            index=index,
            query={"match_all": {}},
            size=1
        )
        hits_total = search_response['hits']['total']['value']
        print(f"Total no search: {hits_total}")
        print(f"Docs retornados: {len(search_response['hits']['hits'])}")
        
        if len(search_response['hits']['hits']) > 0:
            sample_doc = search_response['hits']['hits'][0]
            print(f"Sample doc ID: {sample_doc['_id']}")
            print(f"Sample doc fields: {list(sample_doc['_source'].keys())}")
        
else:
    print("❌ Falha na conexão ES")