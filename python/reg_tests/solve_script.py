############################################################
# DO NOT USE THIS SCRIPT AS A REFERENCE FOR HOW TO USE SUMB
# THIS SCRIPT USES PRIVATE INTERNAL FUNCTIONALITY THAT IS
# SUBJECT TO CHANGE!!
############################################################
import sys, os, copy
from mpi4py import MPI
from mdo_regression_helper import *
from baseclasses import AeroProblem
from pygeo import DVGeometry
from pywarp import MBMesh
import pyspline

# ###################################################################
# DO NOT USE THIS IMPORT STRATEGY! THIS IS ONLY USED FOR REGRESSION
# SCRIPTS ONLY. Use 'from sumb import SUMB' for regular scripts.
sys.path.append(os.path.abspath('../../'))
from python.pySUmb import SUMB
# ###################################################################

# First thing we will do is define a complete set of default options
# that will be reused as we do differnt tests.  These are the default
# options as Dec 8, 2014.

defOpts = {
    # Common Paramters
    'gridfile': 'default.cgns',
    'restartfile': 'default_restart.cgns',
    'solrestart': False,

    # Output Parameters
    'storerindlayer': True,
    'outputdirectory': './',
    'writesymmetry': True,
    'writefarfield': False,
    'writesurfacesolution':True,
    'writevolumesolution':True,
    'solutionprecision':'single',
    'gridprecision':'double',
    'isosurface': {},
    'isovariables': [],
    'viscoussurfacevelocities': True,

    # Physics Paramters
    'discretization': 'central plus scalar dissipation',
    'coarsediscretization': 'central plus scalar dissipation',
    'limiter': 'vanalbeda',
    'smoother': 'runge kutta',
    'equationtype':  'euler',
    'equationmode':  'steady',
    'flowtype': 'external',
    'turbulencemodel': 'sa',
    'turbulenceorder': 'first order',
    'usewallfunctions': False,
    'useapproxwalldistance': True,
    'walltreatment': 'linear pressure extrapolation',
    'dissipationscalingexponent': 0.67,
    'vis4': 0.0156,
    'vis2': 0.25,
    'vis2coarse': 0.5,
    'restrictionrelaxation': .80,
    'liftindex': 2,
    'lowspeedpreconditioner': False,
    'turbresscale': 10000.0,

    # Common Paramters
    'ncycles': 500,
    'ncyclescoarse': 500,
    'nsubiterturb': 1,
    'nsubiter': 1,
    'cfl': 1.7,
    'cflcoarse': 1.0,
    'mgcycle': '3w',
    'mgstartlevel': -1,
    'resaveraging':'alternateresaveraging',
    'smoothparameter': 1.5,
    'cfllimit': 1.5,

    # Unsteady Paramters
    'timeintegrationscheme': 'bdf',
    'timeaccuracy': 2,
    'ntimestepscoarse': 48,
    'ntimestepsfine': 400,
    'deltat': .010,
    
    # Time Spectral Paramters
    'timeintervals':  1,
    'alphamode': False,
    'betamode': False,
    'machmode': False,
    'pmode': False,
    'qmode': False,
    'rmode': False,
    'altitudemode': False,
    'windaxis': False,
    'tsstability':  False,

    # Convergence Paramters
    'l2convergence': 1e-6,
    'l2convergencerel': 1e-16,
    'l2convergencecoarse': 1e-2,
    'maxl2deviationfactor': 1.0,
    'coeffconvcheck': False,
    'miniterationnum': 0,

    # Newton-Krylov Paramters
    'usenksolver': False,
    'nklinearsolver': 'gmres',
    'nkswitchtol': 2.5e-4,
    'nksubspacesize': 60,
    'nklinearsolvetol': 0.3,
    'nkuseew': True,
    'nkpc': 'additive schwartz',
    'nkadpc': False,
    'nkviscpc': False,
    'nkasmoverlap': 1,
    'nkpcilufill': 2,
    'nklocalpcordering': 'rcm',
    'nkjacobianlag': 20,
    'rkreset': False,
    'nrkreset': 5,
    'applypcsubspacesize': 10,
    'nkinnerpreconits': 1,
    'nkouterpreconits': 1,
    'nkls': 'cubic',
    
    # Load Balance/partitioning parameters
    'blocksplitting': True,
    'loadimbalance': 0.1,
    'loadbalanceiter': 10,
    'partitiononly': False,

    # Misc Paramters
    'metricconversion': 1.0,
    'autosolveretry': False,
    'autoadjointretry': False,
    'storehistory': False,
    'numbersolutions': True,
    'printiterations': True,
    'printtiming': True,
    'setmonitor': True,
    'printwarnings': True,
    'monitorvariables': ['cpu','resrho','cl', 'cd'],
    'surfacevariables': ['cp','vx', 'vy','vz', 'mach'],
    'volumevariables': ['resrho'],
    
    # Multidisciplinary Coupling Parameters:
    'forcesastractions': True,

    # Adjoint Paramters
    'adjointl2convergence': 1e-6,
    'adjointl2convergencerel': 1e-16,
    'adjointl2convergenceabs': 1e-16,
    'adjointdivtol': 1e5,
    'approxpc':  True,
    'adpc':  False,
    'viscpc':False,
    'usediagtspc': True,
    'restartadjoint': True,
    'adjointsolver':  'gmres',
    'adjointmaxiter':  500,
    'adjointsubspacesize' :  100,
    'adjointmonitorstep':  10,
    'dissipationlumpingparameter': 6.0,
    'preconditionerside':  'right',
    'matrixordering':  'rcm',
    'globalpreconditioner':  'additive schwartz',
    'localpreconditioner' :  'ilu',
    'ilufill':  2,
    'asmoverlap' :  1,
    'innerpreconits': 1,
    'outerpreconits': 3,
    'usereversemodead': False,
    'applyadjointpcsubspacesize': 20,
    'frozenturbulence': True,
    'usematrixfreedrdw': False,
    'usematrixfreedrdx': True,

    # ADjoint debugger
    'firstrun': True,
    'verifystate': True,
    'verifyspatial': True,
    'verifyextra': True,
}

# First thing we will test is the euler mesh of the MDO tutorial. This
# is a very small mesh that can be run very quickly. We therefore do a
# lot of testing with it.

def printHeader(testName):
    if MPI.COMM_WORLD.rank == 0:
        print '+' + '-'*78 + '+'
        print '| Test Name: ' + '%-66s'%testName + '|'
        print '+' + '-'*78 + '+'

def test1():
    # ****************************************************************************
    printHeader('MDO tutorial Euler Mesh - Python functionality testing')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_euler.cgns',
         'MGCycle':'2w',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'nCyclesCoarse':250,
         'nCycles':10000,
         'monitorvariables':['resrho','cl','cd','cmz','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-2,
         'nkswitchtol':1e-2,
         'adjointl2convergence': 1e-14,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cl','cd','cfx','cfy','cfz',
                                                             'cmx','cmy','cmz'])
    ap.addDV('alpha')
    ap.addDV('mach')
    ap.addDV('altitude')
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_euler.cgns'})
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver.addLiftDistribution(10, 'z')
    CFDSolver.addSlices('z', [0.1, 1, 10.0], sliceType='relative')
    CFDSolver.addSlices('z', [5.0], sliceType='absolute')
    surf = CFDSolver.getTriangulatedMeshSurface()
    if MPI.COMM_WORLD.rank == 0:
        print 'Sum of Triangulated Surface:'
        reg_write(numpy.sum(surf[0]))
        reg_write(numpy.sum(surf[1]))
        reg_write(numpy.sum(surf[2]))

    CFDSolver(ap)
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-10, 1e-10)

    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-10, 1e-10)

    # Get the forces...these are the sumb forces:
    forces = CFDSolver.getForces()
    forces = MPI.COMM_WORLD.allreduce(numpy.sum(forces), MPI.SUM)
    if MPI.COMM_WORLD.rank == 0:
        reg_write(forces,1e-10, 1e-10)
    CFDSolver.setOption('forcesAsTractions', False)

    forces = CFDSolver.getForces()
    forces = MPI.COMM_WORLD.allreduce(numpy.sum(forces), MPI.SUM)
    if MPI.COMM_WORLD.rank == 0:
        reg_write(forces,1e-10, 1e-10)
    CFDSolver.writeForceFile('forces.txt')

    # Now test the different discretization options:
    printHeader('MDO tutorial Euler Mesh - Matrix dissipation')
    CFDSolver.setOption('discretization','central plus matrix dissipation')
    CFDSolver.setOption('coarsediscretization','central plus matrix dissipation')
    CFDSolver.setOption('vis4',0.1)
    CFDSolver.setOption('CFLCoarse',0.75)
    CFDSolver.resetFlow(ap)
    CFDSolver(ap)
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        reg_write_dict(funcs, 1e-10, 1e-10)

    printHeader('MDO tutorial Euler Mesh - Upwind dissipation')
    CFDSolver.setOption('discretization','upwind')
    CFDSolver.setOption('coarseDiscretization','upwind')
    CFDSolver.resetFlow(ap)
    CFDSolver(ap)
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        reg_write_dict(funcs, 1e-10, 1e-10)

    # Test the solve CL Routine
    printHeader('MDO tutorial Euler Mesh - SolveCL Check')
    CFDSolver.resetFlow(ap)
    CFDSolver.solveCL(ap, 0.475, alpha0=0, delta=0.1, tol=1e-4, autoReset=True)
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs, evalFuncs=['cl'])
    if MPI.COMM_WORLD.rank == 0:
        print 'CL-CL*'
        reg_write(funcs['mdo_tutorial_cl'] - 0.475, 1e-4, 1e-4)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')

def test2():
    # ****************************************************************************
    printHeader('MDO tutorial Random Euler Mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_euler_random.cgns',
         'MGCycle':'2w',
         'smoother':'dadi',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'nCyclesCoarse':250,
         'nCycles':10000,
         'monitorvariables':['resrho','cl','cd','cmz','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-2,
         'nkswitchtol':1e-2,
         'adjointl2convergence': 1e-14,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cl','cd','cfx','cfy','cfz',
                                                             'cmx','cmy','cmz'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_euler_random.cgns'})
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-10, 1e-10)

    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-10, 1e-10)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')


def test3():
    # ****************************************************************************
    printHeader('MDO tutorial DADI Euler Mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_euler.cgns',
         'MGCycle':'2w',
         'smoother':'dadi',
         'CFL':10.0,
         'CFLCoarse':1.25,
         'nCyclesCoarse':250,
         'nCycles':10000,
         'monitorvariables':['resrho','cl','cd','cmz','totalr'],
         'L2Convergence':1e-12,
         'L2ConvergenceCoarse':1e-2,
         'adjointl2convergence': 1e-14,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cl','cd','cfx','cfy','cfz',
                                                             'cmx','cmy','cmz'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions)
    CFDSolver(ap)
    # Just check the functions
    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-10, 1e-10)
   
    # Clean up:
    del CFDSolver
    os.system('rm -fr *.cgns *.dat')

def test4():
    # ****************************************************************************
    printHeader('MDO tutorial 1-Processor Test')
    # ****************************************************************************
    if MPI.COMM_WORLD.rank == 0:
        aeroOptions = copy.deepcopy(defOpts)

        # Now set the options that need to be overwritten for this example:
        aeroOptions.update(
            {'gridFile': '../inputFiles/mdo_tutorial_euler.cgns',
             'MGCycle':'2w',
             'CFL':1.5,
             'CFLCoarse':1.25,
             'nCyclesCoarse':250,
             'nCycles':10000,
             'monitorvariables':['resrho','cl','cd','cmz','totalr'],
             'L2Convergence':1e-14,
             'L2ConvergenceCoarse':1e-2,
             'adjointl2convergence': 1e-14,
             'useNKSolver':True,
             'NKSwitchTol':1e-2,
         }
        )

        # Setup aeroproblem, cfdsolver, mesh and geometry.
        ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, altitude=10000.0,
                         areaRef=45.5, chordRef=3.25, evalFuncs=['cl', 'drag'])
        ap.addDV('alpha')
        ap.addDV('mach')
        CFDSolver = SUMB(options=aeroOptions, comm=MPI.COMM_SELF)
        DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
        nTwist = 6
        DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                                y=numpy.zeros(nTwist),
                                                z=numpy.linspace(0,14, nTwist), k=2))
        def twist(val, geo):
            for i in xrange(nTwist):
                geo.rot_z['wing'].coef[i] = val[i]

        DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
        DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
        mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_euler.cgns'}, comm=MPI.COMM_SELF)
        CFDSolver.setMesh(mesh)
        CFDSolver.setDVGeo(DVGeo)
        CFDSolver(ap)
        print 'Eval Functions:'
        funcs = {}
        CFDSolver.evalFunctions(ap, funcs)
        reg_write_dict(funcs, 1e-10, 1e-10)
        print 'Eval Functions Sens:'
        funcsSens = {}
        CFDSolver.evalFunctionsSens(ap, funcsSens)
        reg_write_dict(funcsSens, 1e-10, 1e-10)

        # Clean up:
        del CFDSolver
        del mesh
        del DVGeo
        os.system('rm -fr *.cgns *.dat')

def test5():
    # THIS TEST NEEDS TO BE VERIFIED WITH CS AND IT IS NEEDS TO BE READDED TO REGRESSIONS
    # ****************************************************************************
    printHeader('MDO tutorial Euler Time Spectral Test')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_euler_l2.cgns',
         'MGCycle':'sg',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'nCyclesCoarse':250,
         'nCycles':10000,
         'monitorvariables':['resrho','cl','cd','cmz','totalr'],
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-2,
         'adjointl2convergence': 1e-14,
         'timeIntervals':3,
         'equationMode':'Time Spectral',
         'tsstability':True,
         'alphamode':True,
         'useNKSolver':True,
         'NKSwitchTol':1e-2,
         'usediagtspc':False,
         'asmoverlap':2,
         'ilufill':3,
         'adjointmaxiter':1000,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, 
                     degreeFourier=1, omegaFourier=6.28, degreePol=0,
                     cosCoefFourier=[0.0,0.0], sinCoefFourier=[0.01], 
                     coefPol=[0],
                     evalFuncs=['cl', 'cl0','clalpha', 'clalphadot'])
    ap.addDV('alpha')
    # Note that the mach number derivative for the timspectral is
    # broken and needs to be fixed. 
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_euler_l2.cgns'})
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)

    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-10, 1e-10)

    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-10, 1e-10)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns* *.dat')
    
def test6():
    # ****************************************************************************
    printHeader('MDO tutorial Viscous Mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_rans.cgns',
         'MGCycle':'2w',
         'equationType':'Laminar NS',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'nCyclesCoarse':250,
         'nCycles':10000,
         'monitorvariables':['resrho','resturb','cl','cd','cmz','yplus','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-2,
         'nkswitchtol':1e-2,
         'adjointl2convergence': 1e-14,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.50, 
                     reynolds=50000.0, reynoldsLength=3.25, T=293.15,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cd','lift'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions, debug=True)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_rans.cgns'}, debug=True)
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)

    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-8, 1e-8)

    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-8, 1e-8)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')

def test7():
    # ****************************************************************************
    printHeader('MDO tutorial RANS Mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_rans.cgns',
         'MGCycle':'2w',
         'equationType':'RANS',
         'smoother':'dadi',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'resaveraging':'noresaveraging',
         'nsubiter':3,
         'nsubiterturb':3,
         'nCyclesCoarse':100,
         'nCycles':1000,
         'monitorvariables':['resrho','resturb','cl','cd','cmz','yplus','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-4,
         'nkswitchtol':1e-3,
         'adjointl2convergence': 1e-14,
         'frozenTurbulence':False,
     }
    )
    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, 
                     reynolds=50000.0, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cd','lift','cmz'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_rans.cgns'})
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)

    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-8, 1e-8)
    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-8, 1e-8)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')

def test8():
    # ****************************************************************************
    printHeader('MDO tutorial Random RANS mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/mdo_tutorial_rans_random.cgns',
         'MGCycle':'2w',
         'equationType':'RANS',
         'smoother':'dadi',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'resaveraging':'noresaveraging',
         'nsubiter':3,
         'nsubiterturb':3,
         'nCyclesCoarse':100,
         'nCycles':1000,
         'monitorvariables':['resrho','resturb','cl','cd','cmz','yplus','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-4,
         'nkswitchtol':1e-3,
         'adjointl2convergence': 1e-14,
         'frozenTurbulence':False,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='mdo_tutorial', alpha=1.8, mach=0.80, 
                     reynolds=50000.0, altitude=10000.0,
                     areaRef=45.5, chordRef=3.25, evalFuncs=['cd','lift','cmz'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/mdo_tutorial_ffd.fmt')
    nTwist = 6
    DVGeo.addRefAxis('wing', pyspline.Curve(x=numpy.linspace(5.0/4.0, 1.5/4.0+7.5, nTwist), 
                                            y=numpy.zeros(nTwist),
                                            z=numpy.linspace(0,14, nTwist), k=2))
    def twist(val, geo):
        for i in xrange(nTwist):
            geo.rot_z['wing'].coef[i] = val[i]

    DVGeo.addGeoDVGlobal('twist', [0]*nTwist, twist, lower=-10, upper=10, scale=1.0)
    DVGeo.addGeoDVLocal('shape', lower=-0.5, upper=0.5, axis='y', scale=10.0)
    mesh = MBMesh(options={'gridFile':'../inputFiles/mdo_tutorial_rans_random.cgns'})
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)

    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-8, 1e-8)
    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-8, 1e-8)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')

def test9():
    # ****************************************************************************
    printHeader('CRM WBT Euler Mesh')
    # ****************************************************************************
    aeroOptions = copy.deepcopy(defOpts)

    # Now set the options that need to be overwritten for this example:
    aeroOptions.update(
        {'gridFile': '../inputFiles/dpw4_38k.cgns',
         'MGCycle':'sg',
         'CFL':1.5,
         'CFLCoarse':1.25,
         'resaveraging':'noresaveraging',
         'nCycles':1000,
         'monitorvariables':['resrho','cl','cd','cmy','yplus','totalr'],
         'useNKSolver':True,
         'L2Convergence':1e-14,
         'L2ConvergenceCoarse':1e-4,
         'nkswitchtol':1e-1,
         'adjointl2convergence': 1e-14,
         'liftIndex':3,
     }
    )

    # Setup aeroproblem, cfdsolver, mesh and geometry.
    ap = AeroProblem(name='crm', alpha=1.0, mach=0.85, 
                     reynolds=50000.0, altitude=8000.0,
                     areaRef=594720*.0254**2/2.0, chordRef=275.8*.0254, 
                     evalFuncs=['cd','lift','cmy'])
    ap.addDV('alpha')
    ap.addDV('mach')
    CFDSolver = SUMB(options=aeroOptions)
    DVGeo = DVGeometry('../inputFiles/CRM_ffd.fmt')

    # Setup curves for ref_axis
    leRoot = numpy.array([25.22, 3.08, 4.46])
    leTip = numpy.array([45.1735, 29.4681, 4.91902])
    rootChord = 11.83165
    breakChord = 7.25894
    tipChord = 2.7275295

    # We have to be careful with the reference axis...We need to ensure
    # that there is a point on the ref axis *right* at the symmetry plane.
    # X1 information is taken directly from the CRM section data table in
    # Vassberg.
    
    X1 = numpy.array([22.97+.25*13.62, 0, 4.42])
    X2 = leRoot + numpy.array([1.0, 0.0, 0.0])*rootChord*.25
    X3 = leTip + numpy.array([1.0, 0.0, 0.0])*tipChord*.25
    X = []
    X.append(X1)
    nTwist = 8
    for i in range(nTwist):
        fact = float(i)/(nTwist-1)
        X.append((1.0-fact)*X2 + fact*X3)

    c1 = pyspline.Curve(X=X, k=2)
    DVGeo.addRefAxis('wing', c1, volumes=[0,5])

    x = numpy.array([2365.0 , 2365.0])*.0254
    y = numpy.array([0, 840/2.0])*.0254
    z = numpy.array([255.0, 255.0])*.0254
    c2 = pyspline.Curve(x=x, y=y, z=z, k=2)
    DVGeo.addRefAxis('tail', c2, volumes=[25])

    def twist(val, geo):
        # Set all the twist values
        for i in xrange(nTwist-1):
            geo.rot_y['wing'].coef[i+2] = val[i]

    def tailTwist(val, geo):
        # Set one twist angle for the tail
        geo.rot_y['tail'].coef[:] = val[0]

    def ssd(val, geo):
        # Span-sweep-dihedreal --- move the tip in any direction
        C = geo.extractCoef('wing')
        s = geo.extractS('wing')
        # Get a second s that only scaled from the 2nd pt out:
        ss = (s[1:] - s[1])/(s[-1] - s[1])
        for i in xrange(len(C)-1):
            C[i+1, 0] = C[i+1, 0] + ss[i]*val[0]
            C[i+1, 1] = C[i+1, 1] + ss[i]*val[1]
            C[i+1, 2] = C[i+1, 2] + ss[i]*val[2]
        geo.restoreCoef(C, 'wing')

    def chord(val, geo):
        geo.scale['wing'].coef[:] = val[0]

    DVGeo.addGeoDVGlobal('twist', numpy.zeros(nTwist-1), twist, lower=-10, upper=10)
    DVGeo.addGeoDVGlobal('ssd', [0,0,0], ssd, lower=-20, upper=20)
    DVGeo.addGeoDVGlobal('chord', [1.0], chord, lower=0.75, upper=1.25)
    DVGeo.addGeoDVLocal('shape', lower=-1.0, upper=1.0, axis='z', scale=1.0, 
                        volList=[0])
    meshOptions ={
        'gridFile':'../inputFiles/dpw4_38k.cgns',
        'warpType':'solid',
        'solidWarpType':'n',
        'n':3, 
        'fillType':'linear'}

    mesh = MBMesh(options=meshOptions)
    CFDSolver.setMesh(mesh)
    CFDSolver.setDVGeo(DVGeo)
    CFDSolver(ap)

    funcs = {}
    CFDSolver.evalFunctions(ap, funcs)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions:'
        reg_write_dict(funcs, 1e-10, 1e-10)
    funcsSens = {}
    CFDSolver.evalFunctionsSens(ap, funcsSens)
    if MPI.COMM_WORLD.rank == 0:
        print 'Eval Functions Sens:'
        reg_write_dict(funcsSens, 1e-10, 1e-10)

    # Clean up:
    del CFDSolver
    del mesh
    del DVGeo
    os.system('rm -fr *.cgns *.dat')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        test1()
        test2()
        test3()
        test4()
        test6()
        test7()
        test8()
        test9()
    else:
        # Run individual ones
        if 'test1' in sys.argv:
            test1()
        if 'test2' in sys.argv:
            test2()
        if 'test3' in sys.argv:
            test3()
        if 'test4' in sys.argv:
            test4()
        if 'test5' in sys.argv:
            test5()
        if 'test6' in sys.argv:
            test6()
        if 'test7' in sys.argv:
            test7()
        if 'test8' in sys.argv:
            test8()
        if 'test9' in sys.argv:
            test9()