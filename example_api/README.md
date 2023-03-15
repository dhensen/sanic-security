# Example Api using <my package name>

## Regenerate key.pem and cert.pem

```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
```
