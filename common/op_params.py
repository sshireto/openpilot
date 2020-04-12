#!/usr/bin/env python3
import os
import json
import time
from selfdrive.swaglog import cloudlog
from common.travis_checker import travis


def write_params(params, params_file):
  if not travis:
    with open(params_file, "w") as f:
      json.dump(params, f, indent=2, sort_keys=True)
    os.chmod(params_file, 0o764)


def read_params(params_file, default_params):
  try:
    with open(params_file, "r") as f:
      params = json.load(f)
    return params, True
  except Exception as e:
    cloudlog.error(e)
    params = default_params
    return params, False


class KeyInfo:
  has_allowed_types = False
  live = False
  has_default = False
  has_description = False
  hidden = False


class opParams:
  def __init__(self):
    """
      To add your own parameter to opParams in your fork, simply add a new dictionary entry with the name of your parameter and its default value to save to new users' op_params.json file.
      The description, allowed_types, and live keys are no longer required but recommended to help users edit their parameters with opEdit correctly.
        - The description value will be shown to users when they use opEdit to change the value of the parameter.
        - The allowed_types key is used to restrict what kinds of values can be entered with opEdit so that users can't reasonably break the fork with unintended behavior.
          Limiting the range of floats or integers is still recommended when `.get`ting the parameter.
          When a None value is allowed, use `type(None)` instead of None, as opEdit checks the type against the values in the key with `isinstance()`.
        - Finally, the live key tells both opParams and opEdit that it's a live parameter that will change. Therefore, you must place the `op_params.get()` call in the update function so that it can update.
      Here's an example of the minimum required dictionary:

      self.default_params = {'camera_offset': {'default': 0.06}}
    """

    self.default_params = {'camera_offset': {'default': 0.06, 'allowed_types': [float, int], 'description': 'Your camera offset to use in lane_planner.py', 'live': True},
                           'awareness_factor': {'default': 3.0, 'allowed_types': [float, int], 'description': 'Multiplier for the awareness times', 'live': False},
                           'lane_hug_direction': {'default': None, 'allowed_types': [type(None), str], 'description': "(None, 'left', 'right'): Direction of your lane hugging, if present. None will disable this modification", 'live': False},
                           'lane_hug_angle_offset': {'default': 0.0, 'allowed_types': [float, int], 'description': ('This is the angle your wheel reads when driving straight at highway speeds.\n'
                                                                                                                    'Replaces both offsets from the calibration learner to help fix lane hugging.\n'
                                                                                                                    'Enter absolute value here, direction is determined by parameter \'lane_hug_direction\''), 'live': True},
                           'dynamic_follow': {'default': 'relaxed', 'allowed_types': [str], 'description': "Can be: ('traffic', 'relaxed', 'roadtrip'): Left to right increases in following distance.\n"
                                                                                                           "All profiles support dynamic follow so you'll get your preferred distance while\n"
                                                                                                           "retaining the smoothness and safety of dynamic follow!", 'live': True},
                           'alca_nudge_required': {'default': True, 'allowed_types': [bool], 'description': ('Whether to wait for applied torque to the wheel (nudge) before making lane changes. '
                                                                                                             'If False, lane change will occur IMMEDIATELY after signaling'), 'live': False},
                           'alca_min_speed': {'default': 25.0, 'allowed_types': [float, int], 'description': 'The minimum speed allowed for an automatic lane change (in MPH)', 'live': False},
                           'steer_ratio': {'default': None, 'allowed_types': [type(None), float, int], 'description': '(Can be: None, or a float) If you enter None, openpilot will use the learned sR.\n'
                                                                                                                      'If you use a float/int, openpilot will use that steer ratio instead', 'live': True},
                           'use_dynamic_lane_speed': {'default': True, 'allowed_types': [bool], 'description': 'Whether you want openpilot to adjust your speed based on surrounding vehicles', 'live': False},
                           'min_dynamic_lane_speed': {'default': 20.0, 'allowed_types': [float, int], 'description': 'The minimum speed to allow dynamic lane speed to operate (in MPH)', 'live': False},
                           'upload_on_hotspot': {'default': False, 'allowed_types': [bool], 'description': 'If False, openpilot will not upload driving data while connected to your phone\'s hotspot', 'live': False},
                           'reset_integral': {'default': False, 'allowed_types': [bool], 'description': 'This resets integral whenever the longitudinal PID error crosses or is zero.\nShould help it recover from overshoot quicker', 'live': False},
                           'disengage_on_gas': {'default': True, 'allowed_types': [bool], 'description': 'Whether you want openpilot to be disengage on gas input or not. It can cause issues on specific cars'},
                           'no_ota_updates': {'default': False, 'allowed_types': [bool], 'description': 'Set this to True to disable all automatic updates. Reboot to take effect'},
                           'dynamic_gas': {'default': True, 'allowed_types': [bool], 'description': 'Whether to use dynamic gas if your car is supported'},

                           'enable_long_derivative': {'default': True, 'allowed_types': [bool], 'description': 'Whether to use derivative in the longcontrol loop', 'live': True},
                           'write_errors': {'default': False, 'allowed_types': [bool], 'description': 'Write errors for debugging', 'live': True},
                           'restrict_sign_change': {'default': True, 'allowed_types': [bool], 'description': 'Unrestricted derivative modification of integral', 'live': True},
                           'kd': {'default': 1.2, 'allowed_types': [float, int], 'description': 'Derivative gain', 'live': True},
                           'use_kd': {'default': True, 'allowed_types': [bool], 'description': 'To use the opParam `kd` instead of the defined gains in longcontrol.py', 'live': True},

                           'op_edit_live_mode': {'default': False, 'allowed_types': [bool], 'description': 'This parameter controls which mode opEdit starts in. It should be hidden from the user with the hide key', 'hide': True}}

    self.params = {}
    self.params_file = "/data/op_params.json"
    self.last_read_time = time.time()
    self.read_frequency = 5.0  # max frequency to read with self.get(...) (sec)
    self.force_update = False  # replaces values with default params if True, not just add add missing key/value pairs
    self.to_delete = ['dynamic_lane_speed', 'longkiV', 'following_distance', 'static_steer_ratio', 'uniqueID']  # a list of params you want to delete (unused)
    self.run_init()  # restores, reads, and updates params

  def add_default_params(self):
    prev_params = dict(self.params)
    for key in self.default_params:
      if self.force_update:
        self.params[key] = self.default_params[key]['default']
      elif key not in self.params:
        self.params[key] = self.default_params[key]['default']
    return prev_params == self.params

  def format_default_params(self):
    return {key: self.default_params[key]['default'] for key in self.default_params}

  def run_init(self):  # does first time initializing of default params
    if travis:
      self.params = self.format_default_params()
      return
    self.params = self.format_default_params()  # in case any file is corrupted
    to_write = False
    if os.path.isfile(self.params_file):
      self.params, read_status = read_params(self.params_file, self.format_default_params())
      if read_status:
        to_write = not self.add_default_params()  # if new default data has been added
        if self.delete_old():  # or if old params have been deleted
          to_write = True
      else:  # don't overwrite corrupted params, just print to screen
        cloudlog.error("ERROR: Can't read op_params.json file")
    else:
      to_write = True  # user's first time running a fork with op_params, write default params
    if to_write:
      write_params(self.params, self.params_file)

  def delete_old(self):
    prev_params = dict(self.params)
    for i in self.to_delete:
      if i in self.params:
        del self.params[i]
    return prev_params == self.params

  def put(self, key, value):
    self.params.update({key: value})
    write_params(self.params, self.params_file)

  def get(self, key=None, default=None, force_update=False):  # can specify a default value if key doesn't exist
    self.update_params(key, force_update)
    if key is None:
      return self.get_all()

    if key in self.params:
      key_info = self.key_info(key)
      if key_info.has_allowed_types:
        value = self.params[key]
        allowed_types = self.default_params[key]['allowed_types']
        if type(value) not in allowed_types:
          cloudlog.warning('op_params: User\'s value is not valid!')
          if key_info.has_default:  # invalid value type, try to use default value
            default_value = self.default_params[key]['default']
            if type(default_value) in allowed_types:  # actually check if the default is valid
              # return default value because user's value of key is not in the allowed_types to avoid crashing openpilot
              return default_value
          else:  # else use a standard value based on type (last resort to keep openpilot running if user's value is of invalid type)
            return self.value_from_types(allowed_types)
        else:
          return value  # all good, returning user's value
      else:
        return self.params[key]  # no defined allowed types, returning user's value

    return default  # not in params

  def get_all(self):  # returns all non-hidden params
    return {k: v for k, v in self.params.items() if not self.key_info(k).hidden}

  def key_info(self, key):
    key_info = KeyInfo()
    if key is None:
      return key_info
    if key in self.default_params:
      if 'allowed_types' in self.default_params[key]:
        allowed_types = self.default_params[key]['allowed_types']
        if isinstance(allowed_types, list) and len(allowed_types) > 0:
          key_info.has_allowed_types = True
      if 'live' in self.default_params[key]:
        key_info.live = self.default_params[key]['live']
      if 'default' in self.default_params[key]:
        key_info.has_default = True
      if 'description' in self.default_params[key]:
        key_info.has_description = True
      if 'hide' in self.default_params[key]:
        key_info.hidden = self.default_params[key]['hide']
    return key_info

  def value_from_types(self, allowed_types):
    if list in allowed_types:
      return []
    elif float in allowed_types or int in allowed_types:
      return 0
    elif type(None) in allowed_types:
      return None
    elif str in allowed_types:
      return ''
    return None  # unknown type

  def update_params(self, key, force_update):
    if force_update or self.key_info(key).live:  # if is a live param, we want to get updates while openpilot is running
      if not travis and (time.time() - self.last_read_time >= self.read_frequency or force_update):  # make sure we aren't reading file too often
        self.params, read_status = read_params(self.params_file, self.format_default_params())
        if not read_status:
          time.sleep(1/100.)
          self.params, _ = read_params(self.params_file, self.format_default_params())  # if the file was being written to, retry once
        self.last_read_time = time.time()

  def delete(self, key):
    if key in self.params:
      del self.params[key]
      write_params(self.params, self.params_file)
