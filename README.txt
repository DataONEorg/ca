DataONE Certificate Authority: README
=====================================

This directory contains configuration files and notes on how to set up the
DataONE Certificate Authority using openssl as the CA application.  OpenSSL
easily generates all files needed for the CA, including certificate requests,
keys, certificates, and certificate revocation lists.

The DataONE Certificate Authority is governed by a Root CA, which delegates all
certificate signing and management to an Production CA.  The private key for
the Root CA is offline and completely protected, which protects the CA should
somehow the Production CA private key be compromised. This document shows the
steps used to create both the Root CA and the Production CA, as well as to
perform common options such as creation and revocation of certificates with the
Production CA.  The operations have been encapsulated in the 'ca' shell
script.

There is also a Test CA, used for generating certificates for servers in the
dev, staging, and sandbox environments, but this CA is completely independent of
the Production CA and its certificates should not be accepted in the production
server environments.

Key Security
------------
The private keys associated with the three DataONE certificate authorities are not
stored online, nor are they made available on the network.  To use the keys, you
must have access to the physical media on which the keys reside, which is an
encrypted volume on the device. TrueCrypt has been used to encrypt the volume on
which keys reside, so you must have both TRueCrypt installed and you must know the
volume encryption password in order to access the keys.

Installation and Usage
----------------------
The shell program 'ca' can be used to manage certificates from both the Test CA
and the Production CA.  It determines which CA to use based on commandline
arguments.  Type './ca -h' to see the usage help for the ca utility.

To install the DataONE certificate authority, simply:
1) install openssl on your machine
2) install TrueCrypt
3) Check out a working copy of the CA from the DataONE SVN repository
4) Mount the private key volume under /Volumes/DataONE

The 'ca' utility can create, revoke, and display certificates, and can generate
the Certificate Revocation List (CRL) for either of the CAs. Examples follow:

* To create a Production certificate for the MN with nodeid "KNB"
** ./ca -c Prod urn:node:KNB
* To display a Production certificate for the MN with nodeid "KNB"
** ./ca -d Prod urn:node:KNB
* To revoke a Production certificate for the MN with nodeid "KNB"
** ./ca -r Prod urn:node:KNB
* To generate a CRL for the Prod CA
** ./ca -g urn:node:Prod

Any of these commands can be made to work on the Test CA instead by switching
'Prod' to 'Test'.

Once new CSRs, Certificates, and CRLs have been generated, they should be added to
SVN and all modified files should be checked in to SVN so that others managing the 
CA can access all of the updated content.  The only exception are the private keys
that are generated, which should be given to the MN operator along with
instructions on how to protect the private key, and then deleted from the CA to
avoid exposure of the keys.

Additional notes on openssl setup and usage
-------------------------------------------
OpenSSL was used to create the various CA files and operate the CA.  The following
sections are a synopsis of how all of the CAs were created and how various CA
functions can be run using OpenSSL alone.  The 'ca' shell script automates most of
these functions, so their inclusion here is mainly as a reference and not intended
for typical usage.

New DN formats
~~~~~~~~~~~~~~

CA:
DC=org, DC=dataone, CN=DataONE Root CA
DC=org, DC=dataone, CN=DataONE Production CA
DC=org, DC=dataone, CN=DataONE Test CA

Nodes:
DC=org, DC=dataone, CN=urn:node:SOMENODE

CA Certificate validity: 100 years
Node Certificate validity: 3 years

Creating the Root CA
~~~~~~~~~~~~~~~~~~~~
$ mkdir /var/ca
$ cd /var/ca
$ mkdir DataONERootCA
$ cd DataONERootCA
$ mkdir certs crl newcerts private req
$ touch index.txt
# Edit the openssl.cnf config file
$ openssl req -new -newkey rsa:4096 -keyout /Volumes/DataONE/DataONERootCA.key -out req/DataONERootCA.csr -config ./openssl.cnf 
$ openssl ca -create_serial -out certs/DataONERootCA.pem -days 36500 -keyfile /Volumes/DataONE/DataONERootCA.key -selfsign -config ./openssl.cnf -extensions v3_ca -infiles req/DataONERootCA.csr
$ cp serial crlnumber
# Edit crlnumber to be a different hex number
$ openssl ca -config ./openssl.cnf -gencrl -out crl/DataONERootCA_CRL.pem

Creating the Production CA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ cd ..
$ mkdir DataONEProdCA
$ cd DataONEProdCA
$ mkdir certs crl newcerts private req
$ touch index.txt
#  Edit openssl.cnf
$ openssl req -new -newkey rsa:4096 -keyout /Volumes/DataONE/DataONEProdCA.key -out req/DataONEProdCA.csr -config ../DataONERootCA/openssl.cnf
$ cd ../DataONERootCA
$ openssl ca -out ../DataONEProdCA/certs/DataONEProdCA.pem -days 36500 -keyfile /Volumes/DataONE/DataONERootCA.key -config ./openssl.cnf -extensions v3_ca -infiles ../DataONEProdCA/req/DataONEProdCA.csr

Create the Certificate Chain File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ cd ..
$ cat DataONERootCA/certs/DataONERootCA.pem DataONEProdCA/certs/DataONEProdCA.pem > DataONECAChain.crt

Creating and Signing Node Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ cd DataONEProdCA
$ openssl genrsa -passout pass:temp -des3 -out private/NodeNPass.key 2048 
$ openssl rsa -passin pass:temp -in private/NodeNPass.key -out private/NodeN.key
$ rm private/NodeNPass.key
$ openssl req -config ./openssl.cnf -new -key private/NodeNPass.key -out req/NodeN.csr 
$ openssl ca -config ./openssl.cnf  -create_serial -days 1095 -out certs/NodeN.pem -infiles req/NodeN.csr

To revoke a certificate
~~~~~~~~~~~~~~~~~~~~~~~
$ openssl ca -config ./openssl.cnf -revoke certs/NodeN.pem 
$ openssl ca -config ./openssl.cnf -gencrl -out crl/DataONEProdCA_CRL.pem

Creating the Test CA
~~~~~~~~~~~~~~~~~~~~
$ mkdir /var/ca
$ cd /var/ca
$ mkdir DataONETestCA
$ cd DataONETestCA
$ mkdir certs crl newcerts private req
$ touch index.txt
# Edit the openssl.cnf config file
$ openssl req -new -newkey rsa:4096 -keyout /Volumes/DataONE/DataONETestCA.key -out req/DataONETestCA.csr -config ./openssl.cnf 
$ openssl ca -create_serial -out certs/DataONETestCA.pem -days 36500 -keyfile /Volumes/DataONE/DataONETestCA.key -selfsign -config ./openssl.cnf -extensions v3_ca -infiles req/DataONETestCA.csr
$ cp serial crlnumber
# Edit crlnumber to be a different hex number
$ openssl ca -config ./openssl.cnf -gencrl -out crl/DataONETestCA_CRL.pem

