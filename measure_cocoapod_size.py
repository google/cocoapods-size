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

#!/usr/bin/python
"""measure_cocoapod_size.py provides size impact of a given set of cocoapods.

Usage: ./measure_cocoapod_size.py -cocoapods $POD_NAME:$POD_VERSION

"""

import argparse
import os
import tempfile
from xcode_project_diff import GenerateSizeDifference

SAMPLE_APP = 'sizetestproject'

DEFAULT_SPEC_REPOS = ['https://github.com/CocoaPods/Specs.git']

SPEC_REPO_DICT = {
    'cpdc-internal': 'sso://cpdc-internal/spec',
    'cpdc-eap': 'sso://cpdc-eap/spec',
    'master': 'https://github.com/CocoaPods/Specs.git'
}

TARGET_NAME = 'SizeTest'


def InstallPods(cocoapods, target_dir, spec_repos, target_name):
  """InstallPods installs the pods.

  Args:
    cocoapods: Mapping from pod names to pod versions.
    target_dir: The target directory.
    spec_repos: The set of spec repos.
    target_name: The name of the target.

  Returns:
    The path to the workspace.
  """
  cwd = os.getcwd()
  os.chdir(target_dir)
  os.system('pod init')
  os.system('touch Podfile')

  with open('Podfile', 'w') as podfile:
    for repo in spec_repos:
      podfile.write('source "{}"\n'.format(repo))
    podfile.write('\n')
    podfile.write('use_frameworks!\n')
    podfile.write('target \'{}\' do\n'.format(target_name))
    for pod, version in cocoapods.items():
      if version:
        podfile.write(' pod \'{}\', \'{}\'\n'.format(pod, version))
      else:
        podfile.write(' pod \'{}\'\n'.format(pod))
    podfile.write('end')
  os.system('pod install')
  os.chdir(cwd)
  return os.path.join(target_dir, 'SizeTest.xcworkspace')


def CopyProject(source_dir, target_dir):
  """CopyProject copies the project from the source to the target.

  Args:
    source_dir: The path to the source directory.
    target_dir: The path to the target directory.
  """
  os.system('cp -r {} {}'.format(source_dir, target_dir))


def GetPodSizeImpact(parsed_args):
  """GetPodSizeImpact gets the size impact of the set of pods.

  Args:
    parsed_args: The set of arguments passed to the program.
  """
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
  base_project = tempfile.mkdtemp()
  target_project = tempfile.mkdtemp()
  CopyProject(SAMPLE_APP, base_project)
  CopyProject(SAMPLE_APP, target_project)
  target_project = InstallPods(cocoapods,
                               os.path.join(target_project, 'sizetestproject'),
                               spec_repos, TARGET_NAME)
  source_project = os.path.join(base_project,
                                'sizetestproject/SizeTest.xcodeproj')

  source_size, target_size = GenerateSizeDifference(
      source_project, TARGET_NAME, target_project, TARGET_NAME)
  print 'The pods combined add an extra size of {} bytes'.format(
      target_size - source_size)


def Main():
  """Main generates the PodSize impact.
  """
  parser = argparse.ArgumentParser(description='The size impact of a cocoapod')
  parser.add_argument(
      '--cocoapods',
      metavar='N',
      type=str,
      nargs='+',
      required=True,
      help='The set of cocoapods')
  parser.add_argument(
      '--spec_repos',
      metavar='N',
      type=str,
      nargs='+',
      required=False,
      help='The set of spec_repos')

  args = parser.parse_args()

  GetPodSizeImpact(args)


if __name__ == '__main__':
  Main()
