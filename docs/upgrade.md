# Pedido de upgrade

2. **Fluxo do módulo**:
- O `unipost_automation` aciona o `unipost_image_generator` após replicar um novo post.  
- O texto do post é enviado ao **Claude Prompt MCP** para gerar um prompt.  
- O prompt é enviado à **API DALL-E** (usar chave configurável em `settings.py`).  
- A imagem é salva em `unipost_automation/src` (subpasta `images/`), com nome baseado em `data_id_título.png`.  
- Criar link simbólico no **PostgreSQL + PGVector** (sem duplicar arquivo, apenas armazenando o caminho).  
- Retornar o caminho da imagem para o `unipost_automation`, que adiciona a imagem ao post final.

---

## Integrações e reaproveitamento de código
- Reaproveitar **serializers e modelos** já existentes no app `embeddings` (ex.: para registrar metadados da imagem e do post).
- Usar lógica de conexão com banco que já existe em `unipost_automation/storage/db.py`.
- Reaproveitar convenções de logs usadas em `logs/` e `unipost_automation/src/bot/async_bot.py`.
- A nomenclatura de arquivos pode seguir a já usada em `scraping/webscraper.py`.

---

## Alterações nos arquivos existentes
1. **`app/settings.py`**  
- Adicionar configuração de chave para API DALL-E:  
  ```python
  DALLE_API_KEY = os.getenv("DALLE_API_KEY", "")
  IMAGE_STORAGE_PATH = BASE_DIR / "unipost_automation/src/images"
  ```

2. **`app/urls.py`**  
- Incluir rota opcional para testes/debug da geração de imagens:
  ```python
  path("api/images/generate/", include("unipost_image_generator.urls")),
  ```

3. **`requirements.txt`**  
- Garantir dependências:
  ```
  openai>=1.0.0
  pillow
  ```
- (Claude Prompt MCP já deve estar configurado; caso contrário, adicionar SDK necessário).

4. **`docs/instructions.md`**  
- Atualizar documentação explicando o fluxo:
  - Quando e como o `unipost_image_generator` é chamado.  
  - Como configurar a variável `DALLE_API_KEY`.  
  - Onde as imagens são armazenadas (`src/images`).  

---

## Testes
- Criar testes unitários em `unipost_image_generator/tests/test_generator.py` para validar:
- Geração de prompt a partir de texto de post.  
- Chamada fake/mock à API DALL-E.  
- Salvamento correto do arquivo no `src/images/`.  
- Registro no banco via PGVector.  

---

## Passo seguinte
Implemente o módulo **passo a passo**, começando pelo `prompt_builder.py` (Claude MCP → prompt), depois `clients.py` (DALL-E), em seguida `storage.py`, e por último `generator.py` para orquestrar todo o fluxo.  
Finalize criando a rota em `urls.py` para debug/testes e atualize a documentação em `README.md` e o arquivo `.env.example`.

---
