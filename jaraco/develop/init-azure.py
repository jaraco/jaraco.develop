import subprocess
import json
import getpass

import keyring
import autocommand


def create_project(project, user):
    cmd = [
        'az',
        'devops',
        'project',
        'create',
        '--name',
        project,
        '--organization',
        f'https://dev.azure.com/{user}',
        '--visibility',
        'public',
    ]
    subprocess.run(cmd)


def create_service_endpoint(project, user):
    github_token = keyring.get_password('Github', user)
    env = dict(AZURE_DEVOPS_EXT_GITHUB_PAT=github_token)
    cmd = [
        'az',
        'devops',
        'service-endpoint',
        'github',
        'create',
        '--github-url',
        f'https://github.com/{user}/{project}',
        '--name',
        user,
        '--project',
        project,
    ]
    subprocess.run(cmd, env=env)


def find_endpoint_id(project):
    cmd = ['az', 'devops', 'service-endpoint', 'list', '--project', project]
    txt = subprocess.check_output(cmd)
    dat = json.loads(txt)
    return dat[0]['id']


def create_pipeline(svc, project):
    cmd = [
        'az',
        'pipelines',
        'create',
        '--name',
        project,
        '--project',
        project,
        '--service-connection',
        svc,
        '--yaml-path',
        'azure-pipelines.yml',
    ]
    subprocess.run(cmd)


@autocommand.autocommand(__name__)
def main(project, user=None):
    user = user or getpass.getuser()
    create_project(project, user)
    create_service_endpoint(project, user)
    svc = find_endpoint_id(project)
    create_pipeline(svc, project)
