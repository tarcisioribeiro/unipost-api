from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
import asyncio
import logging

from .models import GeneratedImage
from .serializers import (
    GeneratedImageSerializer,
    ImageGenerationRequestSerializer
)
from .generator import UnipostImageGenerator, ImageGenerationTask

logger = logging.getLogger(__name__)


class GenerateImageView(APIView):
    """View para gerar novas imagens"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Gera uma nova imagem a partir do texto fornecido"""
        try:
            serializer = ImageGenerationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Dados inválidos', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extrair dados validados
            validated_data = serializer.validated_data
            text = validated_data['text']
            embedding_id = str(validated_data['embedding_id'])
            custom_prompt = validated_data.get('custom_prompt')

            # Executar geração de imagem de forma assíncrona
            result = asyncio.run(self._generate_image_async(
                text, embedding_id, custom_prompt
            ))

            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"❌ Erro na view de geração: {e}")
            return Response(
                {'error': 'Erro interno do servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _generate_image_async(self, text: str, embedding_id: str,
                                    custom_prompt: str = None) -> dict:
        """Executa geração de imagem de forma assíncrona"""
        generator = UnipostImageGenerator()

        try:
            await generator.initialize()

            # Criar tarefa de geração
            task = ImageGenerationTask(
                embedding_id=embedding_id,
                text=text,
                title=text[:100],  # Usar início do texto como título
                custom_prompt=custom_prompt
            )

            # Gerar imagem
            result = await generator.generate_image(task)

            if result.success:
                return {
                    'success': True,
                    'message': 'Imagem gerada com sucesso',
                    'image_path': result.image_path,
                    'metadata': result.metadata
                }
            else:
                return {
                    'success': False,
                    'error': result.error_message,
                    'metadata': result.metadata
                }

        except Exception as e:
            logger.error(f"❌ Erro na geração assíncrona: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        finally:
            await generator.close()


class ImageStatusView(APIView):
    """View para consultar status de uma imagem gerada"""
    permission_classes = [IsAuthenticated]

    def get(self, request, image_id):
        """Retorna informações sobre uma imagem gerada"""
        try:
            image = GeneratedImage.objects.get(id=image_id)
            serializer = GeneratedImageSerializer(image)

            # Adicionar informações de status do arquivo
            data = serializer.data
            data['file_status'] = {
                'exists': image.image_path and
                __import__('os').path.exists(image.image_path),
                'path': image.image_path
            }

            return Response(data, status=status.HTTP_200_OK)

        except GeneratedImage.DoesNotExist:
            raise Http404("Imagem não encontrada")
        except Exception as e:
            logger.error(f"❌ Erro ao consultar status: {e}")
            return Response(
                {'error': 'Erro interno do servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListGeneratedImagesView(generics.ListAPIView):
    """View para listar imagens geradas"""
    serializer_class = GeneratedImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por parâmetros opcionais"""
        queryset = GeneratedImage.objects.all().order_by('-created_at')

        # Filtrar por embedding se fornecido
        embedding_id = self.request.query_params.get('embedding_id')
        if embedding_id:
            queryset = queryset.filter(embedding_id=embedding_id)

        # Filtrar por data se fornecida
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override para adicionar metadados na resposta"""
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = self.get_paginated_response(serializer.data).data
            else:
                serializer = self.get_serializer(queryset, many=True)
                response_data = {
                    'results': serializer.data,
                    'count': len(serializer.data)
                }

            # Adicionar estatísticas
            response_data['stats'] = {
                'total_images': GeneratedImage.objects.count(),
                'images_today': GeneratedImage.objects.filter(
                    created_at__date=__import__('datetime').datetime.now().date()
                ).count()
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Erro ao listar imagens: {e}")
            return Response(
                {'error': 'Erro interno do servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
