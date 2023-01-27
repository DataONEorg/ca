#!/usr/bin/env python3
"""
Script to generate CSV or JSON that contains basic information about
certificates. Each entry / row has properties:

path: relative path to the certificate.
create_date: date the certificate was generated.
expire_date: date the certificate expires.
expire_days: number of days until certificate expires.
dn: The Subject of the certificate.
node_id: Presumed node_id the certificate applies to. This is parsed from the Subject.
valid: Currently just indicates if certificate is expired or not.


#TODO: be a bit smarter parsing the subject and inferring node id
#TODO: should cross reference with nodes registered in the corresponding 
#      environment, don't report on deprecated nodes
#TODO: use a keyword to identify environment and corresponding cert path
"""
import argparse
import csv
import dataclasses
import datetime
import json
import os, os.path
import pathlib
import subprocess
import sys

CERT_DATE_PATTERN = "%b %d %H:%M:%S %Y %Z"

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


@dataclasses.dataclass
class CertInfo:
    path: str
    create_date: datetime.datetime = None
    expire_date: datetime.datetime = None
    expire_days: int = 0
    valid: bool = False
    dn: str = None
    node_id: str = None

    def __init__(self, path:str):
        self.path = str(path)
        self.load()

    def __str__(self):
        return json.dumps(self, indent=2, cls=DateTimeEncoder)

    def load(self):
        _path = os.path.abspath(self.path)
        cmd = ["openssl", "x509", "-subject", "-noout", "-in", _path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE,text=True)
        parts = result.stdout.split("=",1)
        self.dn = parts[1].strip()
        parts = self.dn.split("/")
        parts = parts[-1].split("=")
        self.node_id = parts[-1]
        cmd = ["openssl", "x509", "-enddate", "-noout", "-in", _path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE,text=True)
        parts = result.stdout.split("=",1)
        self.expire_date = datetime.datetime.strptime(parts[1].strip(), CERT_DATE_PATTERN).replace(tzinfo=datetime.timezone.utc)
        cmd = ["openssl", "x509", "-startdate", "-noout", "-in", _path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE,text=True)
        parts = result.stdout.split("=",1)
        self.create_date = datetime.datetime.strptime(parts[1].strip(), CERT_DATE_PATTERN).replace(tzinfo=datetime.timezone.utc)
        tnow = datetime.datetime.now(tz=datetime.timezone.utc)
        tdelta = self.expire_date - tnow
        self.expire_days = tdelta.days
        if self.expire_days > 0:
            self.valid = True

    def asdict(self):
        return {
            "path": self.path,
            "create_date": self.create_date.isoformat(),
            "expire_date": self.expire_date.isoformat(),
            "expire_days": self.expire_days,
            "valid": self.valid,
            "dn": self.dn,
            "node_id": self.node_id
        }


def get_cert_paths(cert_path:str)->list[str]:
    return list(pathlib.Path(cert_path).rglob("*.pem"))


def main(cert_path:str, out_format:str="json"):
    cert_paths = [cert_path, ]
    if os.path.isdir(cert_path):
        cert_paths = get_cert_paths(cert_path)
    cert_infos = {}
    for cert_path in cert_paths:
        info = CertInfo(cert_path)
        if info.node_id in cert_infos:
            if info.create_date > cert_infos[info.node_id].create_date:
                cert_infos[info.node_id] = info
        else:
            cert_infos[info.node_id] = info
    if out_format == "csv":
        writer = csv.DictWriter(sys.stdout, ["node_id", "valid", "expire_days", "create_date", "expire_date", "dn", "path"])
        writer.writeheader()
        for k,v in cert_infos.items():
            writer.writerow(v.asdict())
    else:
        print(json.dumps(cert_infos, indent=2, cls=DateTimeEncoder))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="cert_status",
        description=__doc__)
    parser.add_argument('certpath')
    parser.add_argument("-c", "--csv", action="store_true")
    args = parser.parse_args()
    fmt = "json"
    if args.csv:
        fmt = "csv"
    sys.exit(main(args.certpath, out_format=fmt))
