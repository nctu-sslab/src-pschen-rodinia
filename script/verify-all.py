#!/usr/bin/env python3

import os
import subprocess
import threading
import time
import datetime
import sys
import pickle
import copy

import nvprof_parser
import libtarget_parser
from dataTy import dataTy
from dataTy import Output

class Config:
    dry_run = False

class Opt:
    # Not working need to wrap to command
    #timer_suffix = "&> /dev/null".split()
    test_count = 3
    prof = True
    def __init__(self):
        self.env = copy.deepcopy(os.environ)
        self.offload = False
        self.bulk = False
        self.at = False
        self.timeout = 1000
        self.clean_cmd = "make clean".split()
        self.make_cmd = "make".split()
        self.reg_run_cmd = "./run".split()
        self.verify_cmd = "./verify".split()
        self.timer_prefix = "/usr/bin/time -o .time -f %e".split()
        self.nvprof_prefix = "nvprof --profile-child-processes".split()
        self.cuda = False

class Test:
    def __init__(self, name, path, opt):
        self.name = name
        self.root = path
        self.opt = opt
    def run (self, projs):
        print(self.name)

        # init result
        self.result = {}
        Result[self.name] = self.result
        for proj in projs:
            os.chdir(self.root)
            print(proj)
            # Real run
            output = self.runOnProj(proj)

            self.result[proj] = output

            # Print output
            proj_name = proj

    def runOnProj(self, proj):
        output = Output()
        os.chdir(proj)
        self.opt.run_cmd = self.opt.reg_run_cmd

        #  TODO test verify

        # make clean
        subprocess.run(self.opt.clean_cmd, capture_output=True)
        # make
        CP = subprocess.run(self.opt.make_cmd, capture_output=True, env=self.opt.env)
        if CP.returncode != 0 :
            output.CE = True
            print(CP.stdout)
            print(CP.stderr)
            return output

        # Run/verify w/ timeout
        # Profiling and Get data
        for i in range(self.opt.test_count):
            ret = self.runWithTimer(output)
            if ret != 0:
                print("(!) Error occured")
                return output

        if self.opt.prof:
            ret = self.runWithProfiler(output)
            if ret != 0:
                return output

        # make clean
        subprocess.run(self.opt.clean_cmd, capture_output=True)
        return output

    def runWithTimer(self, output):
        time.sleep(1)
        time_cmd = self.opt.timer_prefix + self.opt.run_cmd
        if Config.dry_run:
            print(time_cmd)
            return 0
        try:
            CP = subprocess.run(time_cmd, capture_output=True, timeout=self.opt.timeout, env=self.opt.env)
        except subprocess.TimeoutExpired:
            output.TL = True
            return -1
        if self.checkRet(CP, output, True) != 0:
            return -1
        return 0
    def runWithProfiler(self, output):
        time.sleep(1)
        prof_cmd = self.opt.timer_prefix + self.opt.run_cmd
        if self.opt.cuda:
            prof_cmd = self.opt.nvprof_prefix + self.opt.run_cmd
        else:
            env = self.opt.env
            env["Perf"] = "1"
        if Config.dry_run:
            print(prof_cmd)
            return 0
        try:
            CP = subprocess.run(prof_cmd, capture_output=True, timeout=self.opt.timeout, env=env)
        except subprocess.TimeoutExpired:
            output.TL = True
            return -1

        if self.checkRet(CP, output, True, True) != 0:
            return -1

        # Process result
        result = CP.stderr.decode("utf-8")
        # todo abstract cuda opt
        if self.opt.cuda:
            nvprof_parser.parse(output, result)
        else:
            libtarget_parser.parse(output, result)
        return 0
    def checkRet(self, CP, output, getTime=False, isProf=False):
        # Store result
        output.stdouts += CP.stdout.decode("utf-8")
        output.stderrs += CP.stderr.decode("utf-8")
        if CP.returncode != 0 :
            output.RE = True
            return -1
        if getTime:
            if os.path.exists(".time"):
                f = open(".time", "r")
                f = float(f.read())
                if isProf:
                    output.prof_time = f
                else:
                    output.times.append(f)
                os.remove(".time")
                return 0
            else:
                print("No .time gen")
                return -1

def run_cpu():
    opt1 = Opt()
    T1 = Test("omp", os.path.join(rodinia_root, "openmp"), opt1)
    T1.run(projects)

def run_omp():
    opt2 = Opt()
    opt2.env["OFFLOAD"] = "1"
    T2 = Test("omp-offload", os.path.join(rodinia_root, "openmp"), opt2)
    T2.run(projects)

def run_bulk():
    opt3 = Opt()
    opt3.env["OFFLOAD"] = "1"
    opt3.env["OMP_BULK"] = "1"
    T3 = Test("omp-offload-bulk", os.path.join(rodinia_root, "openmp"), opt3)
    T3.run(projects)

def run_at():
    opt4 = Opt()
    opt4.env["OFFLOAD"] = "1"
    opt4.env["OMP_BULK"] = "1"
    opt4.env["OMP_AT"] = "1"
    T4 = Test("omp-offload-at", os.path.join(rodinia_root, "openmp"), opt4)
    T4.run(projects)

def run_cuda():
    opt5 = Opt()
    opt5.cuda = True
    T5 = Test("cuda", os.path.join(rodinia_root, "cuda"), opt5)
    T5.run(projects)

def run_1d():
    opt6 = Opt()
    opt6.env["OFFLOAD"] = "1"
    opt6.env["RUN_1D"] = "1"
    T6 = Test("omp-offload-1d", os.path.join(rodinia_root, "openmp"), opt6)
    T6.run(projects)

script_dir = os.path.dirname(os.path.realpath(__file__))
rodinia_root = os.path.dirname(script_dir)
os.chdir(rodinia_root)

projects = ["backprop", "kmeans", "myocyte", "pathfinder"]
#projects = ["backprop", "kmeans",  "pathfinder"]
#projects = ["myocyte"]
#projects = ["pathfinder"]
#projects = ["backprop"]

#Config.dry_run = True
#Opt.prof = False
os.environ["RUN_LARGE"] = "1"

# Final result
Result = {}
Opt.test_count = 1
#run_cpu()
#run_cuda()
run_omp()
run_1d()
run_bulk()
run_at()


# save result to pickle
os.chdir(script_dir)
now = datetime.datetime.now()
timestamp = now.strftime("%d%m_%H%M")
pickle_file = "./results/result_" + timestamp + ".p"
with open(pickle_file, "wb") as f:
    pickle.dump(Result, f)
# save as last result
pickle_file = "./results/result.p"
with open(pickle_file, "wb") as f:
    pickle.dump(Result, f)
