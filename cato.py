'''
Reporting on certificate expirations.

Example: Report on production MN certificates ordered by expiration:

  python cato.py -m -e 

Example: Report on test env MN certificates ordered by expiration:

  python cato.py -m -e -t

'''
import sys
import os
import logging
import argparse
import glob
import operator
from OpenSSL import crypto
from datetime import datetime

def cnvstr(o, encoding='utf-8'):
  return str(o, encoding=encoding)


def getSubjectFromName(xName):
  '''Given a DN, returns a DataONE subject
  TODO: This assumes that RDNs are in reverse order...
  
  @param 
  '''
  parts = xName.get_components()
  res = []
  for part in parts:
    res.append(str("%s=%s" % (cnvstr(part[0]).upper(), cnvstr(part[1]))))
  res.reverse()
  return ",".join(res)


def certDateStringToDate(cert_date):
  try:
    cert_date = cert_date.decode("ascii")
  except:
    pass
  return datetime.strptime(cert_date, "%Y%m%d%H%M%SZ")


def getCertificateInfo(pem_file):
  res = {
    "file": pem_file,
    "subject": None,
    "created": None,
    "expires": None,
    "nodeid": None,
    }
  x509 = None
  with open(pem_file, "rb") as cert_file:
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
  if x509 is None:
    logging.warn("Unable to load certificate from %s", pem_file)
    raise(ValueError("Unable to load certificate from {}".format(pem_file)))
  res["subject"] = getSubjectFromName(x509.get_subject())
  res["created"] = certDateStringToDate(x509.get_notBefore())
  res["expires"] = certDateStringToDate(x509.get_notAfter())
  cn = res["subject"].split(",")[0].split("=")[1]
  if cn.startswith("urn:node:"):
    res["nodeid"] = cn
  return res


def listCertificateFiles(path):
  path = os.path.join(path,"*.pem")
  files = glob.glob(path)
  return files


def main():
  parser = argparse.ArgumentParser(description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-l', '--log_level',
                      action='count',
                      default=0,
                      help='Set logging level, multiples for more detailed.')
  parser.add_argument('-c', '--cert_file',
                      default=None,
                      help='Report on the single certificate specified.')
  parser.add_argument("-t", "--test_ca",
                      action="store_true",
                      help="Report on test CA certificates instead of Production")
  parser.add_argument("-m","--mns_only",
                      action="store_true",
                      help="Report on MN client certs only (CN=urn:node:NodeID)")
  parser.add_argument("-e","--sort_expired",
                      action="store_true",
                      help="Sort by expiration date instead of name")
  args = parser.parse_args()
  # Setup logging verbosity
  levels = [logging.WARNING, logging.INFO, logging.DEBUG]
  level = levels[min(len(levels) - 1, args.log_level)]
  logging.basicConfig(level=level,
                      format="%(asctime)s %(levelname)s %(message)s")

  cert_file_path = "DataONEProdCA/certs"
  if args.test_ca:
    cert_file_path = "DataONETestIntCA/certs"
  if args.cert_file is not None:
    cert_file_path = args.cert_file

  if os.path.isfile(cert_file_path):
    result = getCertificateInfo(cert_file_path)
    print("Expires   Subject  File")
    print("{expires:%Y-%m-%d} {subject} {file}".format(**result))
    return 0
  cert_files = listCertificateFiles(cert_file_path)
  results = {}
  for file_name in cert_files:
    result = getCertificateInfo(file_name)
    if args.mns_only and result["nodeid"] is None:
      pass
    else:
      try:
        existing = results[result["subject"]]
        if result["created"] > existing["created"]:
          results[result["subject"]] = result
      except KeyError as e:
        results[result["subject"]] = result
  sort_on = "expires"
  format_str = "{expires:%Y-%m-%d} {subject:<45} {file}"
  header = "{:<10} {:<45} FileName".format("Expires","Subject")
  if args.mns_only:
    sort_on = "nodeid"
    format_str = "{expires:%Y-%m-%d} {nodeid:<20} {file}"
    header = "{:<10} {:<20} FileName".format("Expires","NodeId")
  if args.sort_expired:
    sort_on = "expires"
  unsorted_result_list = results.values()
  sorted_results = sorted( unsorted_result_list, key=lambda cert: cert[sort_on])
  print(header)
  for result in sorted_results:
    print(format_str.format(**result))
  return 0

if __name__ == "__main__":
  sys.exit(main())


