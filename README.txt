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

New DN formats
==============

CA:
DC=org, DC=dataone, CN=DataONE Root CA
DC=org, DC=dataone, CN=DataONE Production CA

Nodes:
DC=org, DC=dataone, CN=urn:node:SOMENODE

CA Certificate validity: 100 years
Node Certificate validity: 3 years

Creating the Root CA
====================
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
============================
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
=================================
$ cd ..
$ cat DataONERootCA/certs/DataONERootCA.pem DataONEProdCA/certs/DataONEProdCA.pem > DataONECAChain.crt

Creating and Signing Node Requests
==================================
$ cd DataONEProdCA
$ openssl genrsa -passout pass:temp -des3 -out private/NodeNPass.key 2048 
$ openssl rsa -passin pass:temp -in private/NodeNPass.key -out private/NodeN.key
$ rm private/NodeNPass.key
$ openssl req -config ./openssl.cnf -new -key private/NodeNPass.key -out req/NodeN.csr 
$ openssl ca -config ./openssl.cnf  -create_serial -days 1095 -out certs/NodeN.pem -infiles req/NodeN.csr

To revoke a certificate
=======================
$ openssl ca -config ./openssl.cnf -revoke certs/NodeN.pem 
$ openssl ca -config ./openssl.cnf -gencrl -out crl/DataONEProdCA_CRL.pem
