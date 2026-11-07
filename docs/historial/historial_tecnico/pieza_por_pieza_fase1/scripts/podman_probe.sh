#!/usr/bin/env bash
set -euo pipefail
# This script only inspects Podman availability and image metadata. It does not run containers.
echo '== Podman: inspeccion sin ejecutar contenedores =='
podman --version
podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null | awk '{print "rootless=" $0}' || true
echo 'Imagenes locales (sin descargar):'
podman images --format '{{.ID}} {{.Architecture}} {{.Repository}}:{{.Tag}}' || true
cat <<'EOF'
PENDIENTE: seleccionar imagen ARM64 local de procedencia confiable y probar en entorno desechable:
  --network none --read-only --cap-drop ALL --security-opt no-new-privileges
  --pids-limit 64 --memory 512m --user 65534:65534
No ejecutar ni montar carpetas personales sin revisar el comando final.
EOF
