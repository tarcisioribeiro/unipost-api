"""
Django signals para vetorização automática de posts
"""

import os
import logging
import time
from typing import Optional, List
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
import google.generativeai as genai
from texts.models import Text

# Import condicionado para evitar erro de inicialização
try:
    from embeddings.models import Embedding
except ImportError:
    Embedding = None

# Configuração de logging
logger = logging.getLogger(__name__)

# Configuração do Google Gemini
GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
if GOOGLE_GEMINI_API_KEY:
    genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
else:
    logger.warning("GOOGLE_GEMINI_API_KEY não configurada - vetorização automática desabilitada")


def generate_embedding_for_text(text_content: str, max_retries: int = 3, retry_delay: float = 2.0) -> Optional[List[float]]:
    """
    Gera embedding usando Google Gemini para um texto com retry automático
    
    Args:
        text_content: Texto para gerar embedding
        max_retries: Número máximo de tentativas
        retry_delay: Delay entre tentativas em segundos
    
    Returns:
        Lista de floats representando o embedding ou None se falhar
    """
    if not GOOGLE_GEMINI_API_KEY:
        logger.error("API Key do Google Gemini não configurada")
        return None
    
    # Limita tamanho do texto para a API
    if len(text_content) > 2048:
        text_content = text_content[:2048] + "..."
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Tentativa {attempt + 1}/{max_retries} para gerar embedding")
            
            # Gera embedding
            result = genai.embed_content(
                model='models/embedding-001',
                content=text_content,
                task_type="retrieval_document"
            )
            
            logger.info(f"Embedding gerado com sucesso na tentativa {attempt + 1}")
            return result['embedding']
            
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou: {error_str}")
            
            # Verifica se é erro de quota/rate limit
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:  # Não é a última tentativa
                    delay = retry_delay * (2 ** attempt)  # Backoff exponencial
                    logger.info(f"Rate limit detectado. Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Falha definitiva após {max_retries} tentativas - Rate limit excedido")
                    return None
            else:
                # Para outros erros, não tenta novamente
                logger.error(f"Erro não recuperável ao gerar embedding: {error_str}")
                return None
    
    logger.error(f"Falha ao gerar embedding após {max_retries} tentativas")
    return None


def process_embedding_creation(text_instance):
    """
    Processa a criação/atualização de embedding de forma isolada
    
    Args:
        text_instance: Instância do modelo Text
    
    Returns:
        bool: True se foi processado com sucesso, False caso contrário
    """
    if not Embedding:
        logger.warning("Modelo Embedding não disponível - embedding não processado")
        return False
        
    try:
        # Verifica se já existe embedding para este texto
        existing_embedding = Embedding.objects.filter(
            origin='generated',
            metadata__text_id=text_instance.id
        ).first()
        
        if existing_embedding:
            logger.info(f"Atualizando embedding existente para Text {text_instance.id}")
            
            # Gera novo embedding
            embedding_vector = generate_embedding_for_text(text_instance.content)
            
            if not embedding_vector:
                logger.error(f"Falha ao gerar embedding para atualização - Text {text_instance.id}")
                return False
            
            # Atualiza embedding existente
            existing_embedding.content = text_instance.content
            existing_embedding.title = f"{text_instance.get_platform_display()}: {text_instance.theme}"
            existing_embedding.embedding_vector = embedding_vector
            existing_embedding.metadata.update({
                "platform": text_instance.platform,
                "platform_display": text_instance.get_platform_display(),
                "theme": text_instance.theme,
                "text_id": text_instance.id,
                "is_approved": text_instance.is_approved,
                "updated_at": text_instance.updated_at.isoformat() if text_instance.updated_at else None,
                "last_embedding_update": time.time()
            })
            existing_embedding.save()
            
            logger.info(f"Embedding atualizado com sucesso: {existing_embedding.id}")
            return True
        
        # Cria novo embedding
        logger.info(f"Criando novo embedding para Text {text_instance.id}")
        
        # Gera embedding do conteúdo
        embedding_vector = generate_embedding_for_text(text_instance.content)
        
        if not embedding_vector:
            logger.error(f"Falha ao gerar embedding para novo texto - Text {text_instance.id}")
            return False
        
        # Prepara metadados
        metadata = {
            "platform": text_instance.platform,
            "platform_display": text_instance.get_platform_display(),
            "theme": text_instance.theme,
            "text_id": text_instance.id,
            "is_approved": text_instance.is_approved,
            "created_at": text_instance.created_at.isoformat() if text_instance.created_at else None,
            "updated_at": text_instance.updated_at.isoformat() if text_instance.updated_at else None,
            "auto_generated": True,
            "signal_triggered": True,
            "embedding_created_at": time.time()
        }
        
        # Título descritivo
        title = f"{text_instance.get_platform_display()}: {text_instance.theme}"
        
        # Cria embedding no banco usando transação
        with transaction.atomic():
            embedding = Embedding.objects.create(
                origin='generated',
                content=text_instance.content,
                title=title,
                embedding_vector=embedding_vector,
                metadata=metadata
            )
        
        logger.info(f"Embedding criado com sucesso: {embedding.id} para Text {text_instance.id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar embedding: {e}")
        return False


@receiver(post_save, sender=Text)
def create_embedding_on_text_save(sender, instance, created, **kwargs):
    """
    Signal que cria automaticamente um embedding quando um Text é salvo
    
    Args:
        sender: O modelo Text
        instance: A instância do Text que foi salva
        created: True se foi criado, False se foi atualizado
        **kwargs: Argumentos adicionais
    """
    # Verifica se deve processar
    should_process = created or (not created and instance.is_approved)
    
    if not should_process:
        logger.debug(f"Text {instance.id} não processado - created={created}, approved={instance.is_approved}")
        return
    
    # Verifica se API está configurada
    if not GOOGLE_GEMINI_API_KEY:
        logger.warning(f"Embedding não processado para Text {instance.id} - API não configurada")
        return
    
    logger.info(f"Processando embedding para Text {instance.id} (created={created})")
    
    # Processa em função separada para melhor controle de erro
    success = process_embedding_creation(instance)
    
    if not success:
        logger.warning(f"Falha ao processar embedding para Text {instance.id} - será tentado novamente na próxima atualização")