# Deploy (DigitalOcean Droplets)

## Layout

- **Droplet A:** clone this repo, set secrets, `docker compose --profile v01 up -d`  
  Open firewall TCP **22** (SSH) and **8080–8082** (Freqtrade UI), restricted to your IP if possible.

- **Droplet B:** same repo, `docker compose --profile v02 up -d`  
  Open **8083–8085** (or remap ports via compose override if you prefer 8080–8082 on this host only).

## Secrets

1. Edit each `config/*.json` or use server-only copies: `exchange.key`, `exchange.secret`, and `api_server` JWT + password (replace `CHANGE_ME_*`).
2. Do not commit real keys.

## Logs (quick checks)

```bash
docker compose logs -f cointpairs_v01_btceth
grep -iE 'error|warning|disconnect' user_data/logs/freqtrade_v01_btceth.log
```

## Sizing

Three Freqtrade processes per Droplet need enough **RAM/CPU**; upgrade the Droplet if OOM or high CPU persist.
