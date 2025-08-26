# ClamAV Database (optional)

Place pre-fetched ClamAV database files here to bundle with the Flatpak build:

- main.cvd (or main.cvd.xz)
- daily.cvd (or daily.cvd.xz)
- bytecode.cvd (or bytecode.cvd.xz)

Notes:

- These files can be large; prefer distributing via release artifacts.
- Ensure licenses and redistribution terms for ClamAV DB are followed.
- The Flatpak manifest installs any files in this folder to /app/share/clamav.
