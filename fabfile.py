from fabric.api import sudo, env, run, task, execute, settings
from fabric.context_managers import shell_env
from os.path import expanduser

user = 'ubuntu'
env['user'] = user
env['host_string'] = '54.172.36.252'
env['key_filename'] = expanduser('~/.ssh/nuclio-ci.pem')
src_dir = '~/go/src/github.com/nuclio/nuclio'


@task
def install_docker():
    sudo('apt-get update')
    packages = [
        'apt-transport-https',
        'ca-certificates',
        'curl',
        'make',
        'software-properties-common',
    ]
    sudo(f'apt-get install -y {" ".join(packages)}')
    run('curl -o key -fsSL https://download.docker.com/linux/ubuntu/gpg')
    sudo('apt-key add key')
    run('rm key')
    version = str(run('lsb_release -cs'))
    url = 'https://download.docker.com/linux/ubuntu'
    repo = f'deb [arch=amd64] {url} {version} stable'
    sudo(f'sudo add-apt-repository "{repo}"')
    sudo('apt-get update')
    sudo('apt-get install -y docker-ce')
    sudo('groupadd docker', warn_only=True)
    sudo(f'usermod -aG docker {user}')


@task
def install_go():
    run('curl -LO https://dl.google.com/go/go1.10.linux-amd64.tar.gz')
    run('tar xzf go1.10.linux-amd64.tar.gz')
    run('rm go1.10.linux-amd64.tar.gz')
    sudo('mv go /opt')
    run('echo \'PATH=/opt/go/bin:$PATH\' >> ~/.bashrc')


@task
def clone_nuclio():
    run(f'git clone https://github.com/tebeka/nuclio.git {src_dir}')
    packages = [
        'github.com/nuclio/amqp',
        'github.com/nuclio/logger',
        'github.com/nuclio/nuclio-sdk-go',
        'github.com/v3io/v3io-go-http',
    ]
    for pkg in packages:
        run(f'/opt/go/bin/go get {pkg}')


@task
def install():
    execute(install_docker)
    execute(install_go)
    execute(clone_nuclio)


@task
def make_images():
    with settings(cwd=src_dir), shell_env(GOPATH=f'/home/{user}/go'):
        run('make docker-images')


@task
def run_tests(branch):
    with settings(cwd=src_dir), shell_env(GOPATH=f'/home/{user}/go'):
        run(f'git checkout {branch}')
        run('git pull')
        run('make lint test')
