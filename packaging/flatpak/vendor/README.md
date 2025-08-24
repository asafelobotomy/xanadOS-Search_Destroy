# Vendored Python Wheels

This directory stores pre-fetched Python wheel files for offline Flatpak builds.

Place required .whl files here when building without internet access. The Flatpak
manifest is configured with pip --find-links to discover wheels from this folder.

Do not commit large binaries to the main branch unless approved. Prefer release
artifacts or a separate distribution channel.
