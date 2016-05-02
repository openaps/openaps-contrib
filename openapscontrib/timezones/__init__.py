
"""
Timezones - manage timezones in diabetes data with ease.
"""

from openaps.uses.use import Use
from openaps.uses.registry import Registry

import json
import argparse
from dateutil.tz import gettz
from dateutil.parser import parse
from datetime import datetime
from itertools import tee, islice, chain, izip

def set_config (args, device):
  return device

def display_device (device):
  return ''


use = Registry( )

class ConvertInput (Use):
  FIELDNAME = ['date']
  def to_ini (self, args):
    params = self.get_params(args)
    now = datetime.now( ).replace(tzinfo=args.timezone)
    params['timezone'] = now.tzname( )
    if args.timezone._filename == '/etc/localtime':
      params['timezone'] = ''

    if args.date:
      params['date'] = ' '.join(args.date)
    return params
  def from_ini (self, fields):
    fields['date'] = fields['date'].split(' ')
    zone = fields.get('timezone', None)
    if zone in ['None',  None, '']:
      zone = gettz( )
    else:
      zone = gettz(zone)
    fields['timezone'] = zone
    fields['astimezone'] = fields.get('astimezone', False) is 'True'
    return fields
  def get_params (self, args):
    return dict(input=args.input, timezone=args.timezone, adjust=args.adjust, date=args.date, astimezone=args.astimezone)
  def configure_app (self, app, parser):
    parser.add_argument('--timezone','-z', default=gettz( ), type=gettz)
    parser.add_argument('--adjust','-a', default='missing', choices=['missing', 'replace'])
    parser.add_argument('--date','-d', action='append', default=self.FIELDNAME)
    parser.add_argument('--astimezone','-r', action='store_true',  default=False)
    parser.add_argument('input', default='-')
  def get_program (self, args):
    params = self.get_params(args)
    program = json.load(argparse.FileType('r')(params.get('input')))
    return program
  def set_converter (self, args):
    params = self.get_params(args)
    self.FIELDNAME = params.get('date')
    self.adjust = params.get('adjust')
    self.timezone = params.get('timezone')
    self.astimezone = params.get('astimezone')

  def rezone (self, dt):
    if (self.adjust == 'missing' and dt.tzinfo == None) or self.adjust == 'replace':
      dt = dt.replace(tzinfo=self.timezone) # .astimezone(self.timezone)
    if self.astimezone:
      dt = dt.astimezone(self.timezone)
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
    Manage how timezones are expressed in data.
  """
  FIELDNAME = ['timestamp', 'dateString', 'start_at', 'end_at', 'created_at' ]




def previous_and_next(some_iterable):
  # very clever
  # http://stackoverflow.com/questions/1011938/python-previous-and-next-values-inside-a-loop
  prevs, items, nexts = tee(some_iterable, 3)
  prevs = chain([None], prevs)
  nexts = chain(islice(nexts, 1, None), [None])
  return izip(prevs, items, nexts)

import recurrent
import logging
logging.getLogger('recurrent').setLevel(logging.CRITICAL)
def parse_datetime (candidate):
  try:
    return parse(candidate)
  except (ValueError), e:
    return recurrent.parse(candidate)

@use( )
class lsgaps (Use):
  def configure_app (self, app, parser):
    parser.add_argument('input', nargs=argparse.REMAINDER, default=None)
    # parser.add_argument('input', nargs='?', default=None)
    parser.add_argument('--minutes', type=float, default=10)
    parser.add_argument('--date',  default='display_time')
    parser.add_argument('--before',  default=None)
    parser.add_argument('--after',  default=None)
    parser.add_argument('--timezone','-z', default=None)
    parser.add_argument('--no-timezone', action='store_true', default=False)
  def get_params (self, args):
    return dict(input=args.input, minutes=args.minutes, date=args.date)
  def main (self, args, app):
    params = self.get_params(args)
    for x in params.keys( ):
      setattr(args, x, params[x])
    gaps = [ ]
    all_data = [ ]
    def get (item):
      return parse(item.get(args.date))

    tz = None
    if not args.no_timezone:
      tz = gettz(args.timezone)
    if args.before:
      dt = parse_datetime(args.before).replace(tzinfo=tz)
      if tz:
        dt = dt.astimezone(tz)
      before = {args.date: dt.isoformat( )}
      all_data.insert(0, before)
    # if gaps: data.extend(gaps)


    for stream in params.get('input'):
      data = json.load(argparse.FileType('r')(stream))
      # data = json.load(argparse.FileType('r')(params.get('input')))

      data = sorted(data, key=get)
      all_data.extend(data)

    if args.after:
      dt = parse_datetime(args.after).replace(tzinfo=tz)
      if tz:
        dt = dt.astimezone(tz)
      after = {args.date: dt.isoformat( )}
      all_data.append(after)

    all_data = sorted(all_data, key=get)
    for (prev, item, then) in previous_and_next(all_data):
      if prev:
        delta = get(item) - get(prev)
        # print delta.total_seconds( ), "PREV", get(prev), "ITEM", get(item)
        if delta.total_seconds( ) > args.minutes * 60:
          found = dict(prev=prev[args.date], current=item[args.date], delta=delta.total_seconds( ))
          found[args.date] = found['current']
          gaps.append(found)

      date = item[args.date]
    return gaps


@use( )
class select (Use):
  """ select some data out of a timeseries
  """
  def configure_app (self, app, parser):
    parser.add_argument('input', nargs=argparse.REMAINDER, default=None)
    # parser.add_argument('--minutes', type=float, default=10)
    parser.add_argument('--date',  default='display_time')
    parser.add_argument('--current',  default='now')
    parser.add_argument('--prev',  default=None)
    parser.add_argument('--gaps',  default=None)
    parser.add_argument('--timezone','-z', default=None)
    parser.add_argument('--no-timezone', action='store_true', default=False)

  def to_ini (self, args):
    params = self.get_params(args)
    params['input'] = args.input.join(' ')
    for field in params.keys( ):
      if params[field] is None:
        params[field] = ''
    return params
  def from_ini (self, fields):
    if 'input' in fields:
      fields['input'] = fields['input'].split(' ')
    for field in fields:
      if fields[field] in ['', None]:
        fields[field] = None
    return fields
  def get_params (self, args):
    return dict(input=args.input, timezone=args.timezone, no_timezone=args.no_timezone, date=args.date)
  def get_timezone (self, args):
    tz = None
    if not args.no_timezone:
      tz = gettz(args.timezone)
    return tz
  def main (self, args, app):

    params = self.get_params(args)
    self.tz = self.get_timezone(args)
    def get (item):
      return parse(item.get(args.date))

    gaps = [ ]
    if args.gaps:
      spec = json.load(argparse.FileType('r')(args.gaps))
      gaps.extend(spec)
    else:
      prev = self.get_prelude(args)
      curr = self.get_postlude(args)
      gap = dict(current=None, prev=None, delta=None)
      gap[args.date] = None
      spec = [ ]
      if prev and curr:
        delta = get(prev) - get(curr)
        gap = dict(current=curr[args.date], prev=prev[args.date], delta=delta.total_seconds( ))
        gap[args.date] = curr[args.date]
        spec = [gap]
      else:
        if prev:
          gap.update(prev=prev[args.date])
          gap[args.date] = prev[args.date]
        if curr:
          gap.update(current=curr[args.date])
          gap[args.date] = curr[args.date]
        spec = [gap]
      gaps.extend(spec)

    results = [ ]
    for gap in gaps:
      spec = Gap(**gap)

      for stream in params.get('input'):
        data = json.load(argparse.FileType('r')(stream))
        for elem in data:
          if spec.includes(get(elem)):
            results.append(elem)
    return results

  def get_prelude (self, args):
    tz = self.tz
    if args.prev:
      dt = parse_datetime(args.prev).replace(tzinfo=tz)
      if tz:
        dt = dt.astimezone(tz)
      prev = {args.date: dt.isoformat( ), dt: dt}
      return prev

  def get_postlude (self, args):
    tz = self.tz
    if args.current:
      dt = parse_datetime(args.current).replace(tzinfo=tz)
      if tz:
        dt = dt.astimezone(tz)
      current = {args.date: dt.isoformat( ), dt: dt}
      return current
      # all_data.append(after)

class Gap (object):
  prev = None
  curr = None
  def __init__ (self, prev=None, current=None, **kwds):
    self.props = dict(prev=prev, current=current, **kwds)
    if prev:
      self.prev = parse(prev)
    if current:
      self.curr = parse(current)
  def includes (self, when):
    if self.prev and self.curr:
      if self.prev <= when and when <= self.curr:
        return True
    else:
      if self.prev:
        if self.prev <= when:
          return True
      if self.curr:
        if when <= self.curr:
          return True
    return False

def get_uses (device, config):
  all_uses = use.get_uses(device, config)
  all_uses.sort(key=lambda usage: getattr(usage, 'sortOrder', usage.__name__))
  return all_uses

