"""
Plugins - Community maintained plugins to openaps
"""

##########################################
#
# openaps vendor example:
# The following shows what is needed to make the module available as a vendor
# plugin to openaps.
#

# Inherit from openaps.uses.use.Use class
from openaps.uses.use import Use

class Example (Use):
  """ Example use
  """

  # get_params helps openaps save your configurations
  def get_params (self, args):
    """
    Create a dict data type from args namespace so that config serializer can
    save these args for report generation.
    """
    return dict(input=args.input)

  # configure_app allows your plugin to specify command line parameters
  def configure_app (self, app, parser):
    """
    Set up any arguments needed by this use.
    """
    # get file based argument called input.
    # add as many as you like, these use arguments are enshrined into config
    # when adding reports
    parser.add_argument('input', default='glucose.txt')

  def prerender_text (self, data):
    out = [ ]
    """
    # do something to format data into text
    for hour, minute, vals in data:
      out.append(' '.join(map(str, [hour, minute, ','.join(map(str, vals))])))
    """
    return "\n".join(out)

  # main logic for the app
  def main (self, args, app):
    """
    Main logic for plugin.
    """
    # print args
    # get parameters
    params = self.get_params(args)
    print params.get('input')
    out = [ ]
    with open(params.get('input'), 'r') as f:
      pass
      # calculate for all input
    return out

# set_config is needed by openaps for all vendors.
# set_config is used by `device add` commands so save any needed
# information.
# See the medtronic builtin module for an example of how to use this
# to save needed information to establish sessions (serial numbers,
# etc).
def set_config (args, device):
  # no special config
  return

# display_device allows our custom vendor implementation to include
# special information when displaying information about a device using
# our plugin as a vendor.
def display_device (device):
  # no special information needed to run
  return ''

# openaps calls get_uses to figure out how how to use a device using
# agp as a vendor.  Return a list of classes which inherit from Use,
# or are compatible with it:
def get_uses (device, config):
  # make an Example, openaps use command
  # add your Uses here!
  return [ Example ]

######################################################
# openaps definitions are complete
######################################################

