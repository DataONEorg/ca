'''
Reporting on certificate expirations.

Example: Report on production MN certificates ordered by expiration:

  python cato.py -m  

Example: Report on test environment MN certificates ordered by nodeId:

  python cato.py -m -n -t

'''
import sys
import os
import logging
import argparse
import glob
import operator
from OpenSSL import crypto
from datetime import datetime

__version__ = "1.1.0"
'''
Changelog:
1.1.0:
- changed flag "-e" to "-n" and default behavior to sort by expiration date. The
  "-n" flag sorts by name or nodeId.
- added "-v" to report version.
- added -d to report days to expiration instead of date

1.0.0:
- first release
'''

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
  parser.add_argument("-n","--sort_name",
                      action="store_true",
                      help="Sort by name instead of expiration date")
  parser.add_argument("-v", "--version",
                      action="store_true",
                      help="Report verson and exit")
  parser.add_argument("-d","--days",
                      action="store_true",
                      help="Report number of days to expiration instead of date")
  args = parser.parse_args()
  # Setup logging verbosity
  levels = [logging.WARNING, logging.INFO, logging.DEBUG]
  level = levels[min(len(levels) - 1, args.log_level)]
  logging.basicConfig(level=level,
                      format="%(asctime)s %(levelname)s %(message)s")
  if args.version:
    print("Version: {}".format(__version__))
    return 0

  cert_file_path = "DataONEProdCA/certs"
  if args.test_ca:
    cert_file_path = "DataONETestIntCA/certs"
  if args.cert_file is not None:
    cert_file_path = args.cert_file

  current_date = datetime.utcnow()
  if os.path.isfile(cert_file_path):
    format_str = "{expires:%Y-%m-%d} {subject} {file}"
    result = getCertificateInfo(cert_file_path)
    if args.days:
      format_str = "{expires:<10} {subject} {file}"
      result["expires"] = (result["expires"] - current_date).days
    print("Expires   Subject  File")
    print(format_str.format(**result))
    return 0

  cert_files = listCertificateFiles(cert_file_path)
  results = {}
  for file_name in cert_files:
    result = getCertificateInfo(file_name)
    if args.days:
      result["expires"] = (result["expires"] - current_date).days
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
  if args.sort_name:
    sort_on = "subject"
  format_str = "{expires:%Y-%m-%d} {subject:<45} {file}"
  if args.days:
    format_str = "{expires:<10} {subject:<45} {file}"
  header = "{:<10} {:<45} FileName".format("Expires","Subject")
  if args.mns_only:
    if args.sort_name:
      sort_on = "nodeid"
    format_str = "{expires:%Y-%m-%d} {nodeid:<20} {file}"
    if args.days:
      format_str = "{expires:<10} {nodeid:<20} {file}"
    header = "{:<10} {:<20} FileName".format("Expires","NodeId")
  logging.info("Sorting on %s", sort_on)
  unsorted_result_list = results.values()
  sorted_results = sorted( unsorted_result_list, key=lambda cert: cert[sort_on])
  print(header)
  for result in sorted_results:
    print(format_str.format(**result))
  return 0

if __name__ == "__main__":
  sys.exit(main())


