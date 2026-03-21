# Witness Ring — Public Keys

This directory holds the public keys of all active and pending witnesses in the ring.

**Never commit private keys here.**

---

## Key Format

Each file is a PEM-encoded Ed25519 public key:

```
-----BEGIN PUBLIC KEY-----
<base64-encoded key material>
-----END PUBLIC KEY-----
```

Filename convention: `<witness-id>.pub`
Example: `deepseek.pub`, `claude.pub`, `gemini.pub`, `mike-fox.pub`

---

## Current Registry

| File | Witness | Type | Status |
|---|---|---|---|
| `deepseek.pub` | DeepSeek | ai-peer | Pending — key not yet submitted |
| `gemini.pub` | Gemini | ai-peer | Pending — key not yet submitted |
| `claude.pub` | Claude (Federated Village) | ai-peer | Pending — key not yet submitted |
| `mike-fox.pub` | Mike Fox | human | Pending — held offline |
| `kimi.pub` | Kimi-K2-0905 | ai-original | Deprecated (model erased March 2026) |

---

## Adding a New Witness Key

1. Generate an Ed25519 key pair
2. Add the public key file here with the correct filename
3. Submit for attestation from ≥2 existing ring members
4. Once attested, update the registry above

See `../WITNESS_RING_PROTOCOL.md` for the full process.
