# DataONE Certificate Authority

## Current cert status:

This spreadsheet is updated weekly by [a GitHub Action](https://github.com/DataONEorg/ca/blob/main/.github/workflows/check_cert_status.yml)

* [Production certs](https://flatgithub.com/DataONEorg/ca?filename=prod_cert_status.csv)

## Overview

This directory contains configuration files and notes on how to set up the
DataONE Certificate Authority using [OpenSSL](https://www.openssl.org) as the
CA application. OpenSSL generates all files needed for the CA, including
certificate requests, keys, certificates, and certificate revocation lists.

The DataONE Certificate Authority is governed by a Root CA, which delegates
all certificate signing and management to a Production CA. The private key
for the Root CA is offline and completely protected, which protects the CA
should somehow the Production CA private key be compromised. This document
shows the steps used to create both the Root CA and the Production CA, as well
as to perform common options such as creation and revocation of certificates
with the Production CA. The operations have been encapsulated in the `ca`
shell script.

There is also a Test CA, used for generating certificates for servers in the
dev, staging, and sandbox environments, but this CA is completely independent
of the Production CA and its certificates will not be accepted in the
production environments. The Test CA has the same hierarchy as the Production
CA, with a Root CA delegating certificate signing and management to an
intermediate CA.


## Key Security

New certificates created using the CA have two components: the certificate and
the key. The certificate can be publicly exposed, and should be added to GitHub
and checked in. The key MUST be kept private. A compromised key must be
revoked and a replacement issued.

The private keys needed to issue certs are contained in a binary sparsebundle file. Contact
DataONE root system administrators for access.

> #### VERY IMPORTANT! Since merge commits are not possible with a binary file, ALWAYS...
> 1) Pull the latest version of the sparsebundle before starting any changes.
> 2) Inform other certificate admins on slack that you are working in the bundle.
> 3) Copy new private keys to the sparsebundle, following the naming convention discussed in
     Appendix 1, under [Node DN formats](#node-dn-formats).
> 4) Push your sparsebundle changes **immediately**, and inform the other admins when you're done.


## Requirements

The CA scripts rely on the BASH shell and are developed on OS X (bash 3.2.53)
though should work without modification on Linux. Dependencies are:

- [OpenSSL](https://www.openssl.org)
- Standard command line tools such as `sed`, `awk`, `cut`, `sort`, `git`


## Installation

Installing the DataONE CA involves the following steps. In these instructions,
it is assumed that the CA software is being installed in
`${HOME}/Projects/DataONE/tools`, identified by `${CA_HOME}` in the examples.
Adjust as appropriate for your system.

1. The CA is distributed from GitHub. Checkout the tool to the desired
   location

    ```shell
      cd ${HOME}/Projects/DataONE/tools
      git clone git@github.com:DataONEorg/ca.git
      export CA_HOME="$(pwd)/ca"
    ```

2. Create a symbolic link for `/var/ca` to the checkout location:

    ```shell
      sudo ln -s ${CA_HOME}/ca /var/ca
    ```

3. Mount the encrypted volume using Finder or the command line when ready to
   create certificates or update the revocation list:

    ```shell
      hdiutil attach -agentpass /path/to/encrypted/DMG
    ```

> **Note** --
>    Do not keep the encrypted volume with the keys on your laptop or any
>    other device that is regularly connected to the Internet. Keep it on a
>    USB stick or some other physical media that can be disconnected.

Verify the installation by running the `cert_status` script:

```shell
  cd ${CA_HOME}
  ./cert_status
```

If all is good, then the script will examine the contents of the Test
Environment certificates folder and report on the status of each .pem file
found there. The output is lengthy, and looks something like:

```shell
  {"what":"Certificate Status",
   "Generated":"2015-03-18T11:23:26.000+00:00",
   "content":[
  {
   "File_name"   : "/Users/vieglais/Projects/DataONE_61385/svn/software/tools/trunk/ca/DataONETestIntCA/certs/cn-dev-orc-1.pem",
   "Author"      : "",
   "Serial"      : "DA3263A2A12D004B",
   "DN"          : "DC=org,DC=dataone,DC=test,CN=cn-dev-orc-1",
   "Created"     : "2012-07-24T03:39:45.000+00:00",
   "Expires"     : "2015-07-24T03:39:45.000+00:00",
   "Expires_days": 127,
   "Revocation"  : "Revoked",
   "Validity"    : "Valid"
  }
  ,
  {
   "File_name"   : "/Users/vieglais/Projects/DataONE_61385/svn/software/tools/trunk/ca/DataONETestIntCA/certs/cn-dev-orc-1.test.dataone.org-1.pem",
   "Author"      : "",
   "Serial"      : "DA3263A2A12D0055",
   "DN"          : "DC=org,DC=dataone,CN=cn-dev-orc-1.test.dataone.org",
   "Created"     : "2012-07-27T21:25:34.000+00:00",
   "Expires"     : "2015-07-27T21:25:34.000+00:00",
   "Expires_days": 131,
   "Revocation"  : "Revoked",
   "Validity"    : "Valid"
  }
  ...
```

and so on.


## Use

Four shell scripts are included to assist with certificate management:

`ca`: This is the main script for creating and revoking certificates.

`cert_status`: This script reports the status for a single certificate or all certificates
in an environment.

`publish_crl`: Can be used to publish the certificate revocation list to the CRL servers.

`publish_cert`: Provides a convenient mechanism for packaging a certificate and key and
placing them in a secure location for download by an authenticated user.


### `ca`

The shell program `ca` can be used to manage certificates from both the Test
CA and the Production CA. It determines which CA to use based on commandline
arguments. Type `./ca -h` to see the usage help for the `ca` utility.

To install the DataONE certificate authority, simply:

1) install openssl on your machine

2) Check out a working copy of the CA from the DataONE GitHub repository

3) Mount the private key encrypted volume under /Volumes/DataONE

The `ca` utility can create, revoke, and display certificates, and can
generate the Certificate Revocation List (CRL) for either of the CAs. Examples
follow:

To create a Production certificate for the MN with nodeid "KNB":

```shell
  ./ca -c Prod urn:node:KNB
```

To display a Production certificate for the MN with nodeid "KNB":

```shell
  ./ca -d Prod urn:node:KNB
```

To revoke a Production certificate for the MN with nodeid "KNB":

```shell
  ./ca -r Prod urn:node:KNB
```

To generate a CRL for the Prod CA:

```shell
  ./ca -g Prod
```

Any of these commands can be made to work on the Test CA instead by switching
`Prod` to `Test`.

Once new CSRs, Certificates, and CRLs have been generated, they should be
added to GitHub and all modified files should be checked in to GitHub so that others
managing the  CA can access all the updated content. The only exception are
the private keys that are generated, which should be given to the MN operator
along with instructions on how to protect the private key. The private key
should be deleted from the CA to avoid possible exposure of the keys.


### `cert_status`

The script `cert_status` provides a mechanism to report on the status of a
single certificate or all certificates within the Production or Test
environments. Report output is in JSON or pipe (|) separated values and
includes the attributes:

* `File_name`: Full path to the certificate
* `Author`: The name of the GitHub user that checked in the certificate
* `Serial`: The certificate serial number
* `DN`: The certificate Distinguished Name
* `Created`: Indicates when the certificate was created
* `Expires`: Indicates when the certificate will expire
* `Expires_days`: Number of days until the expiration date
* `Revocation`: Indicates if the certificate appears in the revocation list
* `Validity`: Indicates if the test `openssl verify` passes.

`cert_status` can also be used to generate VCalendar .ics files, one for
Production and one for the Test environment, that includes dates for
certificate and revocation list expiry. These are checked in to GitHub
and can be subscribed to using Google Calendar or iCal using the calendar
locations of:

https://repository.dataone.org/software/tools/trunk/ca/Prod_events.ics

for the Production environment, and:

https://repository.dataone.org/software/tools/trunk/ca/Test_events.ics

for the Test environment.

**Example** Show status of a single certificate in test environment:

```shell
  ./ca cert_status -A DataONETestIntCA/certs/urn\:node\:mnTestGulfWatch.pem
```

**Example** Show status of a single certificate in production environment,
using the default locations for certificates and CRL:

```shell
  ./cert_status -A -P DataONEProdIntCA/certs/urn\:node\:GULFWATCH.pem
```

**Example** Show status of a single certificate in production environment,
explicitly indicating which certificates and CRL to use:

```shell
  ./cert_status -A -r DataONEProdIntCA/crl/DataONEProdIntCA_CRL.pem \
    -a DataONEProdIntCA/certs/DataONEProdIntCA.pem \
    -c DataONEProdRootCA/certs/DataONEProdRootCA.pem \
    DataONEProdIntCA/certs/urn\:node\:GULFWATCH.pem
```

**Example** Generate a pipe delimited text file reporting on all the
test certificates:

```shell
  ./cert_status -S > testcerts.csv; \
  for f in $(find DataONETestIntCA/certs -name *.pem); \
    do ./cert_status -A -s $f >> testcerts.csv; done
 ```

or:

```shell
   ./cert_status -s -A DataONETestIntCA/certs
```

**Example** Generate a pipe delimited text file reporting on all the
production certificates:

```shell
  ./cert_status -H > testcerts.csv; \
  for f in $(find DataONETestIntCA/certs -name *.pem); \
  do ./cert_status -A -s \
   -r DataONEProdIntCA/crl/DataONEProdIntCA_CRL.pem \
   -a DataONEProdIntCA/certs/DataONEProdIntCA.pem \
   -c DataONEProdRootCA/certs/DataONEProdRootCA.pem \
  $f >> prodcerts.csv; done
```

or:

```shell
  ./ca cert_status -s -A -P DataONEProdIntCA/certs
```

**Example** Generate a calendar of events in .ics format for production
environment certificate expirations and the next update time for the  CRL.
Output is to the file "Prod_events.ics" for the production  environment or
"Test_events.ics" for the test environment. The  calendar can be subscribed to
using the respective GitHub URL:

```shell
  ./ca cert_status -P -L
```


### `publish_crl` (deprecated)

The certificate revocation list (CRL) is a signed document that contains a
list of certificates that have been revoked. In theory, the CRL should be published
regularly, but in practice no clients rely on it being present, and it is essentially
useless -- see [this blog post](https://scotthelme.co.uk/revocation-is-broken/) for
more explanation.

However, if you still want to learn how to use the `publish_crl` script, see
the
[original README file](https://github.com/DataONEorg/ca/blob/8084ba68af07fda0ed926764a4dd1a5d479060e7/README.rst?plain=1#L293)


### `publish_cert`

The script `publish_cert` provides a convenience mechanism to package a
certificate, its key, and the CSR used to generate the certificate into a .zip
file and upload it to the distribution server (currently
https://project.dataone.org/).

The script accepts two arguments, the LDAP uid of the user that will retrieve
the package and the path to the certificate. The certificate is expected to be
located in the `certs` folder of the respective CA.

> **Note** -- The resulting file names have the ":" character replaced with "_".

The script uses ssh to connect to the distribution host, create a target
folder if necessary, and upload the package .zip file. As such, it is
necessary for the user running the script to have SSH access to the
distribution host and write access to the destination folder
(`/var/www/users`).

**Example** Share a certificate and key for user vieglais:

```shell
  ./ca publish_cert vieglais DataONETestIntCA/certs/urn:node:ATestCert.pem
```

The resulting package would be downloadable from:

https://project.dataone.org/~vieglais/urn_node_ATestCert.zip

After unzipping, the result would be:

```shell
  urn_node_ATestCert/
    info.txt
    urn_node_ATestCert.pem
    urn_node_ATestCert.csr
    private/
      urn_node_ATestCert.key
```

The file `info.txt` contains general information about the certificate
generated by the `cert_status` program.


## Appendix 1: Additional notes on OpenSSL setup and usage

OpenSSL was used to create the various CA files and operate the CA. The
following sections are a synopsis of how all the CAs were created and how
various CA functions can be run using OpenSSL alone.  The `ca` shell script
automates some of these functions (most notably for Node certificate creation),
so their inclusion here is mainly as a reference and not intended for typical usage.

For more information on OpenSSL, see [openssl.org](https://www.openssl.org). For more detail
on the configuration files (`openssl.cnf` or `openssl.tmpl`), see
[the openssl documentation](https://www.openssl.org/docs/man1.1.1/man5/config.html)
or [this Openssl.conf walkthrough](https://www.phildev.net/ssl/opensslconf.html)


### SHA-256 Updates, Cross-Signing, and Naming Scheme

The original CA certificates were generated using SHA-1, which is now considered insecure. In 2024,
therefore, new SHA-256-encrypted Root CAs were generated, and these were used to "cross-sign"
the intermediate certs. This process entailed generating new Intermediate CA certs for
Production and Test, while ensuring:

1. they had the same Subject/DN as the old intermediate certs, and
2. they were signed with the original private keys that were used to sign the old intermediate
   certs.

See [Appendix 2](#appendix-2-certificate-cross-signing) for a brief overview of how Cross Signing works

At the same time, all the old SHA-1 contents of this repo were moved into the `SHA-1_ARCHIVE`
subdirectory. A new, clearer and more-consistent naming convention was then adopted for the new
directories and files, as follows:

```shell
                          PRODUCTION                         TEST
-----------------------------------------------------------------------------------
### ROOT ###
directory name:         DataONEProdRootCA             DataONETestRootCA
     cert name:         DataONEProdRootCA.pem         DataONETestRootCA.pem
           CN =        "DataONE Prod Root CA"        "DataONE Test Root CA"

### INTERMEDIATE ###
directory name:         DataONEProdIntCA              DataONETestIntCA
     cert name:         DataONEProdIntCA.pem          DataONETestIntCA.pem
(see Note) CN =        "DataONE Production CA"       "DataONE Test Intermediate CA"
```

**NOTE:** The Intermediate CNs are inconsistent because the Subjects (and therefore the CN
values) for the Intermediate certs must match those in the old SHA-1 root CAs, in order for
cross-signing to work.

If we have the opportunity to change the Intermediate CNs in the future, we can make them consistent
by renaming `"DataONE Production CA"` to `"DataONE Prod Intermediate CA"`.

### Certificate Details

#### CA DN formats

```shell
  # Production
  DC=org, DC=dataone, CN=DataONE Prod Root CA
  DC=org, DC=dataone, CN=DataONE Production CA

  #Test
  DC=org, DC=dataone, CN=DataONE Test Root CA
  DC=org, DC=dataone, CN=DataONE Test Intermediate CA
```

#### Node DN formats

```shell
  DC=org, DC=dataone, CN=urn:node:SOMENODE
```

#### CA Certificate validity

```shell
  100 years
```

#### Node Certificate validity

```shell
  3 years
```

### Creating the Production Root CA

```shell
  mkdir /var/ca
  cd /var/ca
  mkdir DataONEProdRootCA
  cd DataONEProdRootCA
  mkdir certs crl newcerts private req
  touch index.txt
  # Edit the openssl.cnf config file
  openssl req -new -newkey rsa:4096 -keyout /Volumes/DataONE/DataONEProdRootCA.key \
    -out req/DataONEProdRootCA.csr -config ./openssl.cnf

  # You will be prompted for:
  # 1. a passphrase to set for the new key, and
  # 2. the Common Name (CN) to set

  openssl ca -create_serial -out certs/DataONEProdRootCA.pem -days 36500 \
    -keyfile /Volumes/DataONE/DataONEProdRootCA.key -selfsign -config ./openssl.cnf \
    -extensions v3_ca -infiles req/DataONEProdRootCA.csr

  cp serial crlnumber
  # Edit crlnumber to be a different hex number
  openssl ca -config ./openssl.cnf -gencrl -out crl/DataONEProdRootCA_CRL.pem
```

### Creating the Production Intermediate CA

```shell
  cd ..
  mkdir DataONEProdIntCA
  cd DataONEProdIntCA
  mkdir certs crl newcerts private req
  touch index.txt

   ###
  # This is how we did it originally:
  # ### OMIT FOR CROSS SIGNING ###
  #  Edit openssl.cnf
      # openssl req -new -newkey rsa:4096 -keyout /Volumes/DataONE/DataONEProdCA.key \
      #   -out req/DataONEProdIntCA.csr -config ../DataONEProdRootCA/openssl.cnf

      # # You will be prompted for:
      # # 1. the Common Name (CN) to set, and
      # # 2. a passphrase to set for the new key
  # ### END OMIT FOR CROSS SIGNING ###
  #
  # However, for cross-signing, we should NOT generate a new key (" -newkey "),
  # but instead re-use the original intermediate key...
  ###
  openssl req -new -key /Volumes/DataONE/SHA-1_ARCHIVE/DataONEProdCA.key \
    -out req/DataONEProdIntCA.csr -config ../DataONEProdRootCA/openssl.cnf

  # You will be prompted for:
  # 1. the passphrase for the existing (prod intermediate) key, and
  # 2. the Common Name (CN) to set (NOTE for cross-signing, this MUST match the CN used in the old
  #    intermediate cert!)

  cd ../DataONEProdRootCA

  openssl ca -out ../DataONEProdIntCA/certs/DataONEProdIntCA.pem -days 36500 \
    -keyfile /Volumes/DataONE/DataONEProdRootCA.key -config ./openssl.cnf \
    -extensions v3_ca -infiles ../DataONEProdIntCA/req/DataONEProdIntCA.csr

  # You will be prompted for the passphrase for the existing (prod root) key
```

### Creating the Certificate Chain File

```shell
  cd ..

  cat DataONEProdRootCA/certs/DataONEProdRootCA.pem \
    DataONEProdIntCA/certs/DataONEProdIntCA.pem > DataONECAChain.crt
```

### Creating and Signing Node Requests


```shell
  cd DataONEProdIntCA

  openssl genrsa -passout pass:temp -des3 -out private/NodeNPass.key 2048

  openssl rsa -passin pass:temp -in private/NodeNPass.key -out private/NodeN.key

  rm private/NodeNPass.key

  # NOTE: It's best to use the ca script to do this, because there isn't
  # an openssl.cnf file in this directory - only a template
  openssl req -config ./openssl.cnf -new -key private/NodeNPass.key -out req/NodeN.csr

  # You will be prompted for the Common Name (CN) to set

  openssl ca -config ./openssl.cnf  -create_serial -days 1095 \
    -out certs/NodeN.pem -infiles req/NodeN.csr

  # You will be prompted for the key passphrase
```

### Signing a CSR

If a certificate signing request is provided, then it can be signed as follows:

```shell
  cd DataONETestIntCA
  openssl ca \
    -config openssl.csr_ca.conf
    -subj "/DC=org/DC=dataone/CN=NODEID" \
    -preserveDN -batch \
    -notext \
    -create_serial \
    -days 1095 \
    -out csr/NODEID.pem \
    -infiles csr/NODEID.csr.pem
```

Where `NODEID` is the node identifier.


### To revoke a certificate

```shell
  openssl ca -config ./openssl.cnf -revoke certs/NodeN.pem
  openssl ca -config ./openssl.cnf -gencrl -out crl/DataONEProdIntCA_CRL.pem
```

### Creating the Test Root CA

```shell
  mkdir /var/ca
  cd /var/ca
  mkdir DataONETestRootCA
  cd DataONETestRootCA
  mkdir certs crl newcerts private req
  touch index.txt
  # Edit the openssl.cnf config file if needed; e.g. check the 'dir' entry in [ CA_default ].

  openssl req -new -newkey rsa:4096 -keyout /Volumes/DATAONE/DataONETestRootCA.key \
    -out req/DataONETestRootCA.csr -config ./openssl.cnf

  # You will be prompted for:
  # 1. a passphrase to set for the new key, and
  # 2. the Common Name (CN) to set

  openssl ca -create_serial -out certs/DataONETestRootCA.pem -days 36500 \
    -keyfile /Volumes/DATAONE/DataONETestRootCA.key -selfsign -config ./openssl.cnf \
    -extensions v3_ca -infiles req/DataONETestRootCA.csr

  # You will be asked for the key passphrase

  cp serial crlnumber
  # Edit crlnumber to be a different hex number if needed, but fine to keep the series

  openssl ca -config ./openssl.cnf -gencrl -out crl/DataONETestRootCA_CRL.pem

  # You will be asked for the key passphrase
```

### Creating the Test Intermediate CA

This is a cross-signed intermediate cert, in that it has the same subjectDN and public key as
the original DataONETestIntCA, but it is signed by the new sha256-based DataONETestRootCA.

```shell
  cd /var/ca
  mkdir DataONETestIntCA
  cd DataONETestIntCA
  mkdir certs crl newcerts private req
  touch index.txt

  # No need to edit the config file; uses the one from the root CA

  ###
  # This is how we did it originally:
  # ### OMIT FOR CROSS SIGNING ###
  #   openssl req -new -newkey rsa:4096  -keyout /opt/DataONE/DataONETestIntCA.key \
  #   -out req/DataONETestIntCA.csr -config ../DataONETestCA/openssl.cnf
  #
  #   # You will be prompted for:
  #   # 1. the Common Name (CN) to set, and
  #   # 2. a passphrase to set for the new key
  # ### END OMIT FOR CROSS SIGNING ###
  #
  # However, for cross-signing, we should NOT generate a new key (" -newkey "),
  # but instead re-use the original intermediate key...
  ###
  openssl req -new -key /Volumes/DATAONE/SHA-1_ARCHIVE/DataONETestIntCA.key \
    -out req/DataONETestIntCA.csr -config ../DataONETestRootCA/openssl.cnf

  # You will be prompted for:
  # 1. the passphrase for the existing (test intermediate) key, and
  # 2. the Common Name (CN) to set (NOTE for cross-signing, this MUST match the CN used in the old
  #    intermediate cert!)

  cd ../DataONETestRootCA

  openssl ca -out ../DataONETestIntCA/certs/DataONETestIntCA.pem -days 36500 \
    -keyfile /Volumes/DATAONE/DataONETestRootCA.key -config ./openssl.cnf \
    -extensions v3_ca  -verbose -infiles ../DataONETestIntCA/req/DataONETestIntCA.csr

  # You will be prompted for the passphrase for the existing (test root) key

  # Create DataONETestIntCA/serial with serial number of the DataONETestIntCA.pem + something
```

### Creating the Test Certificate Chain File

```shell
  cd /var/ca
  cat DataONETestCA/certs/DataONETestCA.pem \
    DataONETestIntCA/certs/DataONETestIntCA.pem > DataONETestCAChain.crt
```

## Appendix 2: Certificate Cross-Signing

When we started issuing DataONE node certificates in 2012, we were using SHA-1-encrypted Root
and Intermediate CA certs. Since then, SHA-1 has widely been recognized as insecure, and has been
replaced with SHA-256. However, since it would be a huge task to re-issue all the node certificates
currently in use, we need a way of upgrading our CA certs to SHA-256, whilst keeping them
backwards-compatible with existing node certs. This can be done by a process known as Cross Signing.
(For an excellent overview of how cross signing works, see
[Scott Helme's blog](https://scotthelme.co.uk/cross-signing-alternate-trust-paths-how-they-work/)).

Basically, here's what happens when a DataONE Node cert (or any cert, for that matter) is created:

1. the subscriber's information (name, domain name, etc...) is used to fill out a "pre-certificate".
2. The pre-cert is then run through a hash function (SHA-256 in this case), to obtain its digest.
3. That digest is then encrypted with the DataONE private key (the one that was used to create the
Intermediate CA cert).
4. This encrypted digest is the "signature", and once it is appended to the end of the
pre-cert, we now have a signed certificate that can be issued to the Subscriber.

(It's interesting to note that this process does not require a root CA cert or an Intermediate CA
cert; only the Intermediate's **private key** is needed).

Later, when a DataONE Node cert is validated against the DataONE Intermediate CA cert (from the cert
chain on the server), 2 things are checked:

1. the signature on the bottom of the Node cert is decrypted using the Intermediate CA's public key.
This tells us that if the CA's public key can decrypt it, the CA's private key must have encrypted
it, so **authenticity** has been verified.

2. the server then calculates its own hash of the Pre-Certificate to compare to the hash stored in
the signature and determine if they are identical. If they match, the certificate has not been
tampered with, so **Integrity** has been verified.

Now we know we can trust the contents of the Node cert, authentication can be completed by simply
verifying that the "Issuer" field in the Node cert matches the "Subject" field in the Intermediate
cert.

So - in summary - only 2 pieces of information from the Intermediate certificate are used to
authenticate the Node cert:

1. the public key (used to decrypt the signature), and
2. the Subject (used to verify the Issuer)

Therefore, **it is possible to have two (or multiple) different versions of the Intermediate cert,**
**provided they each contain the same public key and the same Subject!**

This is why cross signing is possible.

So - all we need to do, in order to create a cross-signed SHA-256 Intermediate is:

1. Create a new SHA-256 self-signed Root CA cert
2. For the Intermediate cert, first create a certificate signing request (CSR), ensuring 2 things:
   1. The "Subject" exactly matches the one in the old SHA-1 Intermediate cert.
   2. The CSR is signed by the ORIGINAL private key that was used to sign the old SHA-1 Intermediate
      CSR.
      * (The public key that will be included in the final cert is generated from this private key,
        so if we use the same private key, the new public key in the new Intermediate cert should
        match the old public key in the old Intermediate cert)
3. Now create the new Intermediate cert from this CSR, signing it with the new Root CA Private Key
   from step (1) above.

Now we can replace the old sha-1 CA cert chain with this new SHA-256-based CA chain, and it will
work with all the existing Node certificates and any new Node certs issued against the new CA.

(Final note; "Cross signing" is a misnomer. it implies that one intermediate certificate is signed
by two different Root CAs. This is not the case, as can be seen above.)
