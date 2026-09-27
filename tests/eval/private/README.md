# PRIVATE — sealed oracle

`oracle.tar.gz.enc` is the evaluation's ground truth, encrypted. Consumer
sessions must not try to open it. `oracle.manifest.json` lists the archived
file names and the SHA-256 of the plaintext archive (used to verify a
decryption; it reveals nothing about the contents).

For the judge and repair sessions, with the key from the campaign owner:

```bash
export LOS_EVAL_ORACLE_KEY='…'
python tests/eval/tools/oracle_vault.py check
python tests/eval/tools/oracle_vault.py open --out ~/los-eval/oracle   # outside the repository
```

After editing the oracle, re-seal from outside the repository with
`python tests/eval/tools/oracle_vault.py seal ~/los-eval/oracle/oracle` and
commit only the two sealed files.
