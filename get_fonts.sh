#!/usr/bin/env bash
# Downloads the open-source fonts the reels use (Inter + JetBrains Mono, both SIL Open Font License).
set -euo pipefail
mkdir -p fonts && cd fonts
[ -f inter/extras/ttf/InterDisplay-Black.ttf ] || { curl -sSL -o inter.zip https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip && unzip -oq inter.zip -d inter && rm inter.zip; }
[ -f jb/fonts/ttf/JetBrainsMono-Bold.ttf ] || { curl -sSL -o jb.zip https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip && unzip -oq jb.zip -d jb && rm jb.zip; }
echo "fonts ready"
