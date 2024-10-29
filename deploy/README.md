# Deploy Happyface

To deploy a production ready version of Happyface you have to adjust the variables in the `website.env` and `db.env` file.
For the `SECRET_KEY` you can use the following command to randomly generate a working string:

```bash
python -c 'import secrets; print("".join(secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in range(60)))'
```

Don't forget to change the `POSTGRES_PASSWORD` in the `db.env` file.

