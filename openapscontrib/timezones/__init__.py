
"""
Timezones - manage timezones in diabetes data with ease.
"""

from openaps.uses.use import Use
from openaps.uses.registry import Registry

import json
import argparse
from dateutil.tz import gettz
from dateutil.parser import parse

def set_config (args, device):
  return device

def display_device (device):
  return ''


use = Registry( )

class ConvertInput (Use):
  FIELDNAME = ['date']
  def get_params (self, args):
    return dict(input=args.input, timezone=args.timezone, adjust=args.adjust, field=args.field)
  def configure_app (self, app, parser):
    parser.add_argument('--timezone','-z', default=gettz( ), type=gettz)
    parser.add_argument('--adjust','-a', default='missing', choices=['missing', 'replace'])
    parser.add_argument('--field','-f', action='append', default=self.FIELDNAME)
    parser.add_argument('input', default='-')
  def get_program (self, args):
    params = self.get_params(args)
    program = json.load(argparse.FileType('r')(params.get('input')))
    return program
  def set_converter (self, args):
    params = self.get_params(args)
    self.FIELDNAME = params.get('field')
    self.adjust = params.get('adjust')
    self.timezone = params.get('timezone')

  def rezone (self, dt):
    if (self.adjust == 'missing' and dt.tzinfo == None) or self.adjust == 'replace':
      return dt.replace(tzinfo=self.timezone)
    return dt
  def range (self, program):
    return [ program ]

  def convert (self, program):
    for record in self.range(program):
      fields = self.FIELDNAME
      for field in fields:
        value = record.get(field, None)
        if value is not None:
          record[field] = self.rezone(parse(value)).isoformat( )
    return program
  def main (self, args, app):
    self.set_converter(args)
    inputs = self.get_program(args)
    results = self.convert(inputs)
    return results

@use( )
class clock (ConvertInput):
  """
    Manage timezones of device clock.
  """
  FIELDNAME = None
  def get_date_value (self, record):
    return parse(record)
  def convert (self, program):
    program = self.rezone(parse(program)).isoformat( )
    return program

@use( )
class glucose (ConvertInput):
  """
    Manage timezones on glucose times.
  """
  FIELDNAME = ['dateString']
  def range (self, program):
    for record in program:
      yield record

@use( )
class rezone (glucose):
  """
    Manage timezones on glucose times.
  """
  FIELDNAME = ['timestamp', 'dateString', 'start_at', 'end_at', 'created_at']


def get_uses (device, config):
  all_uses = use.get_uses(device, config)
  all_uses.sort(key=lambda usage: getattr(usage, 'sortOrder', usage.__name__))
  return all_uses

