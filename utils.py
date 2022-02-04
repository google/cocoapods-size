#!/usr/bin/python3
#
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess

def shell(command, capture_stdout=False, timeout=None):
  try:
    print("[Cocoapods-size] Shell: {}".format(command))
    proc = subprocess.run(
            command, shell=True, check=True, timeout=timeout,
            stdout=subprocess.PIPE if capture_stdout else None)
    return proc.stdout
  except subprocess.CalledProcessError as e:
    print ('Command error: {} \n {}'.format(command, e))
  except subprocess.TimeoutExpired as e:
    if timeout:
      print ('Time out is set to {} secs.'.format(timeout))
    print ('Command times out: {} \n {}'.format(command, e))
