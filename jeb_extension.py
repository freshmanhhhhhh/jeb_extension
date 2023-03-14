from com.pnfsoftware.jeb.client.api import IScript
from com.pnfsoftware.jeb.core import RuntimeProjectUtil
from com.pnfsoftware.jeb.core.units.code.android import IDexUnit, IDexDecompilerUnit, IJLSMethod
from com.pnfsoftware.jeb.core.actions import Actions, ActionContext, ActionCommentData, ActionRenameData
from java.lang import Runnable


class DeguardRenameClass(IScript):
    def run(self, ctx):
        ctx.executeAsync("Loading mapping.txt from deguard ...", LoadMapping(ctx))
        print('Done')


class LoadMapping(Runnable):
    def __init__(self, ctx):
        self.ctx = ctx

    def run(self):
        ctx = self.ctx
        engctx = ctx.getEnginesContext()
        if not engctx:
            print('Back-end engines not initialized')
            return

        projects = engctx.getProjects()
        if not projects:
            print('There is no opened project')
            return

        prj = projects[0]
        print('Decompiling code units of %s...' % prj)

        # open mapping file
        file_name = "E:\COLLEGE\Grade2\semester_2\PoRe\lab0_Setup\JEB_demo_4.2.0" \
                    ".202106271614_JEBDecompiler_121820464987384330\jeb-demo-4.2.0.202106271614-JEBDecompiler" \
                    "-121820464987384330\scripts\mapping.txt"
        File = open(file_name, 'r')
        file_data = File.readlines()

        units = RuntimeProjectUtil.findUnitsByType(prj, IDexUnit, False)
        for unit in units:
            classes = unit.getClasses()
            pkgs = unit.getPackages()

            if classes:
                for clazz in classes:
                    clazzAddress = clazz.getAddress()
                    clazzfullname = clazzAddress[1:-1].replace('/', '.')  # delete L and ;
                    clzname = clazzfullname.split('.')[-1]
                    pkgname = '.'.join(clazzfullname.split('.')[:-1])

                    for z, row in enumerate(file_data):
                        if row[:4] != "    ":  # class info
                            # rename package and class
                            oldClazzfullName = row.split(' -> ')[0]
                            oclzName = oldClazzfullName.split('.')[-1]
                            opkgName = '.'.join(oldClazzfullName.split('.')[:-1])
                            newClazzfullName = row.split(" -> ")[1].replace('\n', '')
                            nclzName = newClazzfullName.split('.')[-1]
                            npkgname = '.'.join(newClazzfullName.split('.')[:-1])

                            if clazzfullname + " -> " in row:
                                self.rename_method(unit, clazz, file_data, z)
                                if clazzfullname != newClazzfullName:  # rename class or pkg
                                    if pkgname != npkgname:
                                        self.rename_pkg(unit, clazz, pkgs, clazzfullname, pkgname, npkgname)
                                    if clzname != nclzName:
                                        self.comment(unit, clazz, clazzfullname)
                                        self.rename(unit, clazz, nclzName, True)
                            # pkg is changed but not sure if clz need to be changed
                            elif (" -> " + pkgname in row) and (clzname == oclzName) and (oclzName != nclzName):
                                self.rename_method(unit, clazz, file_data, z)
                                self.comment(unit, clazz, clazzfullname)
                                self.rename(unit, clazz, nclzName, True)

    def rename_pkg(self, unit, clazz, pkgs, clazzfullname, pkgname, npkgname):
        pkgNameSeg = pkgname.split('.')
        npkgNameSeg = npkgname.split('.')
        arr = [[] for i in range(len(pkgNameSeg))]  # line i store Index of i-layer pkgname
        for i in range(len(pkgNameSeg)):
            if pkgNameSeg[i] == npkgNameSeg[i]:
                for j, pkg in enumerate(pkgs):
                    if pkgNameSeg[i] == pkg.getName(True):
                        arr[i].append(j)
            elif i != 0:  # != && at least two layer
                # in case same pkgname to get the index of right pkg need to be modified
                for j, pkg in enumerate(pkgs):
                    if pkgNameSeg[i] == pkg.getName(True):
                        arr[i].append(j)
                for k in range(len(pkgNameSeg)):
                    if k == 0:  # top-layer pkgname won't be the same
                        continue
                    else:
                        count = len(pkgs)
                        for l in range(len(arr[k])):
                            dif = arr[k][l] - arr[k - 1][0]
                            if 0 < dif < count:
                                count = dif
                                arr[k][0] = arr[k][l]
                for m in range(len(pkgNameSeg)):
                    if pkgNameSeg[i] != npkgNameSeg[i]:
                        print "PACKAGE %s " % pkgNameSeg[i] + "rename to %s " % npkgNameSeg[i]
                        self.rename(unit, pkgs[arr[i][0]], npkgNameSeg[i], True)
            else:
                for pkg in pkgs:
                    if pkg.getName(True) == pkgname:
                        print "PACKAGE %s " % pkgname + "rename to %s " % npkgname
                        self.rename(unit, pkg, npkgname, True)

    def rename_method(self, unit, clazz, file_data, z):
        methods = clazz.getMethods()
        for row1 in file_data[z+1:]:
            if row1[:4] != "    ":
                break
            if '(' in row1:
                methodName = row1.split('(')[0].strip().split(' ')[1]
                newMethodName = row1.split(' -> ')[1].replace('\n', '')
                for method in methods:
                    if method.getName(True) == methodName:
                        self.comment(unit, method, row1.split('->')[0].strip())
                        self.rename(unit, method, newMethodName, True)

    def rename(self, unit, originItem, newName, isBackup):
        actCtx = ActionContext(unit, Actions.RENAME, originItem.getItemId(), originItem.getAddress())
        actData = ActionRenameData()
        actData.setNewName(newName)

        if unit.prepareExecution(actCtx, actData):
            try:
                result = unit.executeAction(actCtx, actData)
                if result:
                    print('rename to %s success!' % newName)
                else:
                    print('rename to %s failed!' % newName)
            except Exception, e:
                print (Exception, e)

    def comment(self, unit, originItem, commentStr):
        actCtx = ActionContext(unit, Actions.COMMENT, originItem.getItemId(), originItem.getAddress())
        actData = ActionCommentData()
        actData.setNewComment(commentStr)

        if unit.prepareExecution(actCtx, actData):
            try:
                result = unit.executeAction(actCtx, actData)
                if result:
                    print('comment to %s success!' % commentStr)
                else:
                    print('comment to %s failed!' % commentStr)
            except Exception, e:
                print (Exception, e)