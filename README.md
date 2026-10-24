# Python2Shell PoC

The lab pins `Brotli==1.2.0` and reproduces a **target-specific RCE chain** in a disposable Docker container.

## What is included

| File | Purpose |
|---|---|
| `Dockerfile` | Pinned vulnerable image and no-ASLR launcher |
| `compose.yaml` | Disposable target on `127.0.0.1:8080` |
| `setup.sh` | Build, start, log, monitor `/tmp/proof`, and clean up |
| `server.py` | Controlled two-decoder target used by the RCE profile |
| `exploit.py` | Calibrated Brotli stream generator and RCE trigger |
| `noaslr.c` | `ADDR_NO_RANDOMIZE` launcher |
| `requirements-vulnerable.txt` | Hash-pinned `Brotli==1.2.0` dependency |

## Quick start

<img width="1267" height="560" alt="image" src="https://github.com/user-attachments/assets/d8fd76f8-59be-4a7e-bb39-d057c6748f04" />


Terminal 1:
```bash
./setup.sh
```

`setup.sh` builds the image, starts the vulnerable service on `127.0.0.1:8080`, follows its logs, checks `/tmp/proof`, prints the missing-file message until the proof appears, then stops monitoring and runs `docker compose down --remove-orphans`.

Terminal 2:
```bash
python3 exploit.py --url http://127.0.0.1:8080
```

The exploit prints the Docker verification command and attempts to display the proof output:

```text
[+] Proof output from Docker:
    uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
```

## Limitations

The RCE result is valid for the pinned lab target, not a universal exploit for Python applications using Brotli.

The profile depends on all of the following:

- CPython 3.11.14, x86-64, and the pinned Brotli 1.2.0 wheel;
- statically calibrated native addresses and offsets;
- the expected allocator and decoder-object memory layout;
- the expected decoder creation, use, and destruction order;
- ASLR disabled so calibrated addresses remain stable.

Changing the Python build, wheel, architecture, allocator, object lifecycle, request order, or ASLR configuration can break the RCE chain.

## Remediation

Upgrade and rebuild packages that bundle the vulnerable decoder:

```bash
python -m pip install --upgrade "Brotli>=1.2.1" "brotlicffi>=1.2.1.0"
```

Restart processes after replacement. If immediate upgrade is impossible, stop accepting or advertising Brotli until the vulnerable package is removed.

## References

- [GHSA-9v8h-qqgm-4m35](https://github.com/advisories/GHSA-9v8h-qqgm-4m35)
- [Brotli fix commit](https://github.com/google/brotli/commit/0ed4268a4401abcb4472096340477cf4af7d1a2b)
- [OpenSourceMalware Python2Shell analysis](https://opensourcemalware.com/blog/node2shell-affects-python)
- [Imperva Node2Shell background](https://www.imperva.com/blog/node2shell-from-brotli-data-to-remote-code-execution/)

## AI assistance

This research lab was developed with assistance from the OpenAI Codex agent using the `GPT-5.6-Luna` model. Code, claims, and results should be independently reviewed before use.
