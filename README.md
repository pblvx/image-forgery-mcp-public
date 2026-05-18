# Image Forgery Detector (MCP Server)

Servidor MCP para detección forense de imágenes.

## Instalación

1. Clona el repositorio.
2. Copia la configuración: `cp .env.example .env`
3. Levanta el contenedor: `docker compose up -d`

## Cliente Claude Desktop

Configurar en `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "image-forgery-detector": {
      "command": "docker",
      "args": [
        "compose", "-f",
        "/ruta/absoluta/a/image-forgery-mcp/docker-compose.yml",
        "run", "--rm", "-i", "mcp-forgery-detector"
      ]
    }
  }
}
```

## Pruebas Manuales (MCP Inspector)
```bash
npx @modelcontextprotocol/inspector docker compose -f docker-compose.yml run --rm -i mcp-forgery-detector
```
