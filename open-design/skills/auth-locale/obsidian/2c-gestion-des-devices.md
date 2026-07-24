---
tags:
  - skill
  - auth-locale
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système C: Gestion des devices

- **C1**: `activate_device(token, device_name, device_ip)` → crée l'entrée dans `devices`
- **C2**: `revoke_device(device_id, revoked_by)` → flag `est_revoque = TRUE`
- **C3**: `list_devices(etablissement_id)` → retourne les devices non révoqués
