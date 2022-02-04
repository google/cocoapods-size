#!/usr/bin/python3
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""xcode_project_diff.py provides size difference between two Xcode targets.

This tool takes in an Xcode project file and targets of source and destination
and computes the size difference between them.

"""

import argparse
import json
import os
import subprocess
from utils import shell

SIZE_CONFIG_PATH = 'size_build_configuration.json'
ARCHIVE_PATH = 'out.xcarchive'
TARGET = 'SizeTest'



def GetConfigDict():
  """GetConfigDict gets you the configuration dictionary.

  Returns:
    A dictionary corresponding to the json file.
  """

  with open(SIZE_CONFIG_PATH, 'r') as size_config:
    config_info = json.loads(size_config.read())
  return config_info


def GetSwiftVersion():
  """GetSwiftVersion returns the current swift version."""
  try: 
    cmd = "xcrun swift -version"
    out = subprocess.check_output(cmd.split(" ")).strip()
    # Example output 
    #'Apple Swift version 3.0 (swiftlang-800.0.46.2 clang-800.0.38)')
    version = out.split(' ')[3]
    return version
  except:
    return None


def CreateBasicCommandArgs(config_info, archive_path):
  """CreateBasicCommandArgs creates the basic command arguments.

  Args:
    config_info: The config_info dictionary from the json file.
    archive_path: The path to store the archive.

  Returns:
    The list of arguments for the xcodebuild command.
  """
  cmd_args = [
      '-configuration Release', 'archive',
      '-archivePath {}'.format(archive_path)
  ]
  swift_version = GetSwiftVersion()
  if swift_version:
    cmd_args.append('SWIFT_VERSION={}'.format(swift_version))
  for flag, value in config_info['compilerFlags'].items():
    cmd_args.append('{}={}'.format(flag, value))
  return cmd_args


def GenerateBuildCommand(project, scheme, basic_args):
  """GenerateBuildCommand generates the build command.

  Args:
    project: The path to the project.
    scheme: The scheme of the project.
    basic_args: The basic arguments that are passed in.

  Returns:
    A string representing the command.
  """
  project_args = []
  if project.endswith('workspace'):
    project_args.append('-workspace {}'.format(project))
  else:
    project_args.append('-project {}'.format(project))
  project_args.append('-scheme {}'.format(scheme))
  cmd = 'xcodebuild {} {}'.format(' '.join(project_args), ' '.join(basic_args))
  return cmd


def GetFinalBinarySize(archive_path):
  """GetFinalBinarySize gets the final binary size.

  Args:
    archive_path: The path to the archive directory.

  Returns:
    binary_size:  The final binary size corresponding to the archive path.
  """
  binary_size = 0
  app_path = os.path.join(archive_path, 'Products/Applications')
  for (dirpath, _, filenames) in os.walk(app_path):
    for filename in filenames:
      filepath = os.path.join(dirpath, filename)
      binary_size += int(
          subprocess.check_output(['wc', '-c', filepath]).strip().split(b' ')[0])
  return binary_size


def GenerateSizeDifference(source_project, source_scheme, target_project,
                           target_scheme, build_timeout):
  """GenerateSizeDifference generates the final binary size.

  Args:
    source_project: The path to the source project.
    source_scheme:  The scheme of the source project.
    target_project: The path to the target project.
    target_scheme:  The scheme of the target project.
    build_timeout:  Timeout to build testapps.

  Returns:
    a touple containing the final binary sizes.
  """

  basic_args = CreateBasicCommandArgs(GetConfigDict(), ARCHIVE_PATH)
  if source_project.endswith('/'):
    source_project = source_project[:-1]
  if target_project.endswith('/'):
    target_project = target_project[:-1]
  source_project_file = os.path.basename(source_project)
  target_project_file = os.path.basename(target_project)
  source_cmd = GenerateBuildCommand(source_project_file, source_scheme,
                                    basic_args)
  target_cmd = GenerateBuildCommand(target_project_file, target_scheme,
                                    basic_args)
  source_project_dir = os.path.dirname(source_project)
  target_project_dir = os.path.dirname(target_project)
  cur_dir = os.getcwd()
  os.chdir(source_project_dir)
  shell(source_cmd, timeout=build_timeout)
  source_final_binary_size = GetFinalBinarySize(ARCHIVE_PATH)
  os.chdir(cur_dir)
  os.chdir(target_project_dir)
  shell(target_cmd, timeout=build_timeout)
  target_final_binary_size = GetFinalBinarySize(ARCHIVE_PATH)
  os.chdir(cur_dir)
  return source_final_binary_size, target_final_binary_size


def Main():
  """Main generates the size difference between two targets.
  """
  parser = argparse.ArgumentParser(
      description='Size difference between two targets')

  parser.add_argument(
      '--source_project', required=True, help='The path to the source project')
  parser.add_argument(
      '--source_scheme', required=True, help='The scheme of the source project')
  parser.add_argument(
      '--target_project', required=True, help='The path to the target project')
  parser.add_argument(
      '--target_scheme', required=True, help='The scheme of the target project')
  parser.add_argument(
      '--build_timeout', default=None, required=False, help='Timeout to build testapps')

  args = parser.parse_args()

  source_size, target_size = GenerateSizeDifference(
      args.source_project, args.source_scheme, args.target_project,
      args.target_scheme, build_timeout)
  diff_size = source_size - target_size
  if source_size > target_size:
    print('{} is {} larger than {}'.format(args.source_project, diff_size,
                                           args.target_project))
  elif source_size == target_size:
    print('{} and {} are the same size'.format(args.source_project,
                                               args.target_project))
  else:
    print('{} is {} smaller than {}'.format(args.source_project, -1 * diff_size,
                                            args.target_project))


if __name__ == '__main__':
  Main()
