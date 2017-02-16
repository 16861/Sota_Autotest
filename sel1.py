from sota import Sota
import sys, codecs

# sys.stdin = codecs.getwriter('utf-8')(sys.stdin.detach())
# sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

class Simple_test(Sota):
    def runTest(self):
        self.login()
        self.changeOrg('3693693691')
        # self.copyOpenDoc('primarydocs', '18369087')
        
        self._signDoc('18748205')

s = Simple_test('https://sota-buh.com.ua')
s.runTest()
