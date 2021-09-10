#!/usr/bin/python
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

"""measure_cocoapod_size.py provides size impact of a given set of cocoapods.

Usage: ./measure_cocoapod_size.py -cocoapods $POD_NAME:$POD_VERSION

"""

import argparse
import json
import os
import tempfile
from collections import OrderedDict
from xcode_project_diff import GenerateSizeDifference
from utils import shell

OBJC_APP_DIR = 'sizetestproject'
OBJC_APP_NAME = 'SizeTest'
SWIFT_APP_DIR = 'SwiftApp'
SWIFT_APP_NAME = 'SwiftApp'

MODE_SWIFT = 'swift'
MODE_OBJC = 'objc'

DEFAULT_SPEC_REPOS = ['https://cdn.cocoapods.org/']

SPEC_REPO_DICT = {
    'cpdc-internal': 'sso://cpdc-internal/spec',
    'cpdc-eap': 'sso://cpdc-eap/spec',
    'master': 'https://cdn.cocoapods.org/'
}



def GetSampleApp(mode):
  if mode == MODE_SWIFT:
    return SWIFT_APP_DIR, SWIFT_APP_NAME
  else:
    return OBJC_APP_DIR, OBJC_APP_NAME


def InstallPods(cocoapods, target_dir, spec_repos, target_name, mode, pod_sources):
  """InstallPods installs the pods.

  Args:
    cocoapods: Mapping from pod names to pod versions.
    target_dir: The target directory.
    spec_repos: The set of spec repos.
    target_name: The name of the target.
    mode: The type of cocoapods.
    pod_sources: A dict of Pod mapping to its source.

  Returns:
    The path to the workspace.
  """
  cwd = os.getcwd()
  os.chdir(target_dir)
  shell('pod init')
  shell('touch Podfile')

  with open('Podfile', 'w') as podfile:
    for repo in spec_repos:
      podfile.write('source "{}"\n'.format(repo))
    podfile.write('\n')
    if mode == MODE_SWIFT:
      podfile.write('use_frameworks!\n')
    podfile.write('target \'{}\' do\n'.format(target_name))
    for pod, version in cocoapods.items():
      if version:
        podfile.write(' pod \'{}\', \'{}\'\n'.format(pod, version))
      elif pod_sources is not None:
        # pod_sources[pod] should have pairs like:
        # "sdk":"FirebaseDatabase" and
        # "git":"sdk/repo.git", "branch":"main" or
        # "path":"~/Documents/SDKrepo"
        for pod_config in pod_sources['pods']:
          if pod_config['sdk'] == pod:
            pod_source_config = []
            for config in pod_config.items():
              if config[0] != 'sdk':
                pod_source_config.append(":{} => \'{}\'".format(config[0], config[1]))
            podfile.write(' pod \'{}\', {}\n'.format(pod, ",".join(pod_source_config)))
            break
      else:
        podfile.write(' pod \'{}\'\n'.format(pod))
    podfile.write('end')
  shell('cat Podfile')
  shell('pod install')
  os.chdir(cwd)
  return os.path.join(target_dir, '{}.xcworkspace'.format(target_name))


def CopyProject(source_dir, target_dir):
  """CopyProject copies the project from the source to the target.

  Args:
    source_dir: The path to the source directory.
    target_dir: The path to the target directory.
  """
  shell('cp -r {} {}'.format(source_dir, target_dir))

def ValidateSourceConfig(pod_sources):
  if 'pods' not in pod_sources:
    raise ValueError(
            "The JSON config file should have 'pods' object containing pod configs.")

  for pod_config in pod_sources['pods']:
    source_keys = list(pod_config.keys())
    try:
      sdk = pod_config['sdk']
    except KeyError:
      print("SDK should be specified.")
      raise
    if sdk.strip() == "":
      raise ValueError( "SDK should not be empty or blank.")
    elif pod_config and ( source_keys[1] not in {"git", "path"} ):
      raise ValueError(
              "Pod source of SDK {} should be `git` or `path`.".format(sdk))
    elif len(source_keys) == 3:
      if source_keys[1] != "git":
        raise ValueError(
                "For multiple specs for the SDK {} ,`git` should be added with `branch`, `tag` or `commit`".format(sdk))
      if source_keys[2] not in {"branch", "tag", "commit"}:
        raise ValueError(
                "A specified version of the SDK {} should be from `branch`, `tag` or `commit`.".format(sdk))
    elif len(source_keys) > 3:
      raise ValueError(
        "Pod source of SDK {} can only specify `sdk` with `path`, `git`, or `git` and a reference (like a `branch`, `tag`, or `commit`)."
        "See --help for an example config."
        .format(sdk)
      )

def GetPodSizeImpact(parsed_args):
  """GetPodSizeImpact gets the size impact of the set of pods.

  Args:
    parsed_args: The set of arguments passed to the program.
  """
  sample_app_dir, sample_app_name = GetSampleApp(parsed_args.mode)
  cocoapods = {}
  if parsed_args.spec_repos:
    spec_repos = []
    for repo in parsed_args.spec_repos:
      if repo in SPEC_REPO_DICT:
        spec_repos.append(SPEC_REPO_DICT[repo])
      else:
        spec_repos.append(repo)
  else:
    spec_repos = DEFAULT_SPEC_REPOS
  for pod in parsed_args.cocoapods:
    pod_info = pod.split(':')
    pod_name = pod_info[0].strip()
    if len(pod_info) > 1:
      pod_version = pod_info[1].strip()
    else:
      pod_version = ''
    cocoapods[pod_name] = pod_version
  # Load JSON in order since in bleeding edge version of a Pod, `git` and
  # `branch`/`tag`/`commit` are required and should be in order. e.g.
  # pod 'Alamofire', :git => 'https://github.com/Alamofire/Alamofire.git', :branch => 'dev'
  try:
    if pod_version and parsed_args.cocoapods_source_config:
      print("Since a version for the pod {} is specified, The config file {} \
              will be validated but not used for binary measurement.".format(
                  pod_name, parsed_args.cocoapods_source_config.name))
    pod_sources = json.load(parsed_args.cocoapods_source_config, \
            object_pairs_hook=OrderedDict) if parsed_args.cocoapods_source_config else None
    if pod_sources: ValidateSourceConfig(pod_sources)
  except ValueError as e:
    raise ValueError("could not decode JSON value %s: %s" % (parsed_args.cocoapods_source_config.name, e))
  base_project = tempfile.mkdtemp()
  target_project = tempfile.mkdtemp()
  target_dir = os.path.join(target_project, sample_app_dir)
  CopyProject(sample_app_dir, base_project)
  CopyProject(sample_app_dir, target_project)

  target_project = InstallPods(cocoapods,
                               target_dir,
                               spec_repos, sample_app_name, parsed_args.mode,
                               pod_sources)
  source_project = os.path.join(base_project,
                                '{}/{}.xcodeproj'.format(sample_app_dir, sample_app_name))

  source_size, target_size = GenerateSizeDifference(
      source_project, sample_app_name, target_project, sample_app_name, parsed_args.build_timeout)
  if parsed_args.json:
    # Transfer Podfile to JSON format.
    podfile = shell('pod ipc podfile-json {}/Podfile'.format(target_dir), capture_stdout=True)
    podfile_dict = json.loads(podfile)
    podfile_dict['combined_pods_extra_size'] = target_size - source_size
    with open(parsed_args.json, 'w') as json_file:
      json.dump(podfile_dict, json_file)
  print('The pods combined add an extra size of {} bytes'.format(
      target_size - source_size))



def Main():
  """Main generates the PodSize impact.
  """
  parser = argparse.ArgumentParser(description='The size impact of a cocoapod',
          formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument(
      '--cocoapods',
      metavar='N',
      type=str,
      nargs='+',
      required=True,
      help='The set of cocoapods')
  parser.add_argument(
      '--mode',
      type=str,
      choices=[MODE_SWIFT, MODE_OBJC],
      default=MODE_OBJC,
      help='Type of cocoapod'
  )
  parser.add_argument(
      '--spec_repos',
      metavar='N',
      type=str,
      nargs='+',
      required=False,
      help='The set of spec_repos')
  parser.add_argument(
      '--cocoapods_source_config',
      metavar='CONFIG_JSON',
      type=argparse.FileType('r'),
      nargs='?',
      required=False,
      default=None,
      help=''' A JSON file with customized pod source.E.g.
        {
          "pods":[
                {
                  "sdk":"FirebaseDatabase",
                  "git":"https://github.com/firebase/firebase-ios-sdk",
                  "branch":"master"
                }
            ]
        }
      If versions are specified in the `cocoapods` arg, config here will be skipped.
      ''')
  parser.add_argument(
      '--build_timeout',
      metavar='SECONDS',
      nargs='?',
      required=False,
      default=None,
      help='Timeout to build testapps.')
  parser.add_argument(
      '--json',
      metavar='OUTPUT_FILE_NAME',
      nargs='?',
      required=False,
      default=None,
      help='Output JSON file.')

  args = parser.parse_args()

  GetPodSizeImpact(args)


if __name__ == '__main__':
  Main()
