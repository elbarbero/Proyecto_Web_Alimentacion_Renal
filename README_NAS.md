# Guía de Despliegue en TrueNAS (Dockge)

Como ya tienes un servidor TrueNAS con Dockge (`192.168.1.151`), el despliegue es muy sencillo.

## 1. Preparar los archivos

Necesitamos mover los archivos de tu ordenador al NAS, para que Dockge pueda "construir" el contenedor.

1.  Accede a los archivos de tu TrueNAS (normalmente por carpeta compartida SMB `\\192.168.1.151\...`).
2.  Busca la carpeta donde Dockge guarda los **Stacks** (suele ser `/opt/stacks` o una carpeta `stacks` en tu dataset de Docker).
3.  Crea una nueva carpeta llamada `web-renal`.
4.  **Copia TODO el contenido de este proyecto** dentro de esa carpeta `web-renal` en el NAS.
    *   *Incluyendo: backend/, js/, server.py, Dockerfile, docker-compose.yml, renal_diet.db, etc.*

## 2. Crear el Stack en Dockge

1.  Abre Dockge en tu navegador (ej: `http://192.168.1.151:5001`).
2.  Verás que si has copiado la carpeta `web-renal` en el directorio correcto, Dockge **ya debería detectarla** y mostrarla en la lista de la izquierda.
    *   Si no la ves, dale al botón de **"+ Compose"** (Crear Stack), ponle nombre `web-renal` y asegúrate de que apunta a esa carpeta.
3.  Verifica que el `docker-compose.yml` aparece en el editor de Dockge.
4.  **Importante:** Asegúrate de que el puerto `8005` (que he puesto por defecto) está libre en tu NAS. Si no, cámbialo en el editor.

## 3. Desplegar

1.  Dale al botón **"Deploy"** (o Start).
2.  Dockge empezará a leer el `Dockerfile` y construirá la aplicación (verás logs de "Building...").
3.  Cuando termine, pondrá "Active".

## 4. Acceder y configurar Nginx Proxy Manager

Tu web ya está activa en: `http://192.168.1.151:8005`

Si quieres acceder desde fuera de casa (o con un dominio bonito) usando tu **Nginx Proxy Manager**:
1.  Entra a tu Nginx Proxy Manager.
2.  Añade un nuevo **Proxy Host**.
3.  Domain Names: `renal.tu-dominio.com` (o lo que uses).
4.  Scheme: `http`
5.  Forward Hostname / IP: `192.168.1.151` (la IP del NAS).
6.  Forward Port: `8005`.
7.  Save.

## Solución de Problemas (Troubleshooting)

### Error: "Dockerfile not found"
Si Dockge no encuentra los archivos (porque busca en su carpeta privada y no en ARCHIVOS), tienes que moverlos manualmente usando la **Shell** de TrueNAS.

1.  Abre **System Settings > Shell**.
2.  Ejecuta este comando (copiar y pegar) para mover los archivos de la carpeta compartida a la carpeta de Dockge:
    ```bash
    sudo mkdir -p /mnt/DATOS/docker/web_renal && sudo cp -r /mnt/DATOS/ARCHIVOS/PROYECTOS/web_alimentacion_renal/* /mnt/DATOS/docker/web_renal/
    ```
3.  Vuelve a Dockge y dale a **Deploy**.
