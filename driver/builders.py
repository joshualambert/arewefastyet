# vim: set ts=4 sw=4 tw=99 et:
import os
import sys
import puller
import subprocess
from utils import Run

class Engine(object):
    def __init__(self, conf):
        self.testroot = conf.get('main', 'testroot')
        self.cpu = conf.get('main', 'cpu')
        
    def updateAndBuild(self, update, forceRebuild):
        pop = os.getcwd()
        os.chdir(os.path.join(self.testroot, self.source))
    
        if self.puller == 'svn':
            scm = puller.SVN
        elif self.puller == 'hg':
            scm = puller.HG
        shell = self.shell()
    
        if not os.path.isfile(shell):
            forceRebuild = True
    
        updated = False
        if update:
            updated = scm.Update()
    
        if forceRebuild or updated:
            try:
                os.unlink(shell)
            except:
                pass
            pop2 = os.getcwd()
            self.build()
            os.chdir(pop2)
            updated = True
    
        version = scm.Identify()
    
        if not os.path.isfile(shell):
            print(shell)
            os.chdir(pop)
            raise Exception('could not find shell')
    
        os.chdir(pop)
        return [version, updated]

    def env(self):
        return None

class Nitro(Engine):
    def __init__(self, conf):
        super(Nitro, self).__init__(conf)
        self.puller = 'svn'
        self.source = conf.get('jsc', 'source')
        self.args = None
        self.important = False
        self.modes = [
                {
                    'mode': 'jsc',
                    'args': None
                }
            ]

    def env(self):
        env = os.environ.copy()
        env['DYLD_FRAMEWORK_PATH'] = os.path.abspath(os.path.join('WebKitBuild', 'Release'))
        return env

    def build(self):
        pop = os.getcwd()
        os.chdir(os.path.join('Tools', 'Scripts'))
        if self.cpu == 'x86':
            Run(['/usr/bin/perl', 'build-jsc', '--32-bit'])
        else:
            Run(['/usr/bin/perl', 'build-jsc'])
        os.chdir(pop)

    def shell(self):
        return os.path.join('WebKitBuild', 'Release', 'jsc')

class V8(Engine):
    def __init__(self, conf):
        super(V8, self).__init__(conf)
        self.puller = 'svn'
        self.source = conf.get('v8', 'source')
        self.args = ['--expose-gc']
        self.important = True
        self.modes = [
                {
                    'mode': 'v8',
                    'args': None
                }
            ]

    def build(self):
        Run(['make', 'dependencies'])
        if self.cpu == 'x64':
            Run(['make', 'x64.release'])
        elif self.cpu == 'arm':
            Run(['make', 'arm.release'])
        elif self.cpu == 'x86':
            Run(['make', 'ia32.release'])
  
    def shell(self):
        if self.cpu == 'x64':
            return os.path.join('out', 'x64.release', 'd8')
        elif self.cpu == 'arm':
            return os.path.join('out', 'arm.release', 'd8')
        elif self.cpu == 'x86':
            return os.path.join('out', 'ia32.release', 'd8')

class Mozilla(Engine):
    def __init__(self, conf):
        super(Mozilla, self).__init__(conf)
        self.puller = 'hg'
        self.source = conf.get('jm', 'source')
        self.args = None
        self.important = True
        self.modes = [
                {
                    'mode': 'ti',
                    'args': ['-m', '-n', '--no-ion']
                },
                {
                    'mode': 'jmim',
                    'args': ['--ion', '-m', '-n', '--ion-parallel-compile=on']
                }
            ]

    def env(self):
        env = os.environ.copy()
        if self.cpu == 'x64':
            env['DYLD_LIBRARY_PATH'] = "/usr/local/nspr64/lib"
        elif self.cpu == 'x86':
            env['DYLD_LIBRARY_PATH'] = "/usr/local/nspr32/lib"
        return env

    def build(self):
        os.system("make -j 3 -C " + os.path.join('js', 'src', 'Opt'))

    def shell(self):
        return os.path.join('js', 'src', 'Opt', 'js')

