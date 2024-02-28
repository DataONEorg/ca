# DataONE Certificate Creation - Quick Reference Guide

(for full details, see [the README file](./README.md))


1. Determine the subject to be used

    * For existing, expired certs, ask for the `subject` and `issuer` lines 
(`openssl x509 -text -in <yourcertname.pem>`)


2. Pull and mount the latest version of the sparsebundle, and inform other certificate admins on
   slack that you are working in the bundle.


3. Pull the latest version of this repo (DataONE/ca)


4. Create the cert. e.g.:

```shell
    ./ca  -c Prod urn:node:MY_NODE_ID
    # or
    ./ca  -c Test urn:node:TestMY_NODE_ID
```


5. Zip and upload to server for retrieval via ORCID login (eg with orcid 
   https://orcid.org/0000-0002-6666-999X)

```shell
./publish_cert_orcid    0000-0002-6666-999X    ./DataONEProdIntCA/certs/urn:node:MY_NODE_ID.pem
```

6. DELETE THE PRIVATE KEY FILE (we no longer keep a copy; a new cert can be generated easily, if 
   key is lost)
```shell
    rm ./DataONEProdIntCA/private/*.key
    # or
    rm ./DataONETestIntCA/private/*.key
```

7. Push your sparsebundle changes immediately, and inform the other admins when you're done.


8. Push your changes to this repo (DataONE/ca)
