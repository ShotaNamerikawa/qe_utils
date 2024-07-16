from qe_utils.io_file import IOFiles
def test_io_file():
    #TODO: implement test for checking order of caltype.
    test_io_dict = {"scf":{"input":"scf.in","output":"scf.out"}, "nscf":{"input":"nscf.in","output":"nscf.out"},
                    "bands":{"input":"bands.in","output":"bands.out"},
                    "projwfc":{"input":"projwfc.in","output":"projwfc.out"},
                    "bandsx":{"input":"bandsx.in","output":"bandsx.out"},
                    "plotband":{"input":"plotband.in","output":"plotband.out"}
                    }
    iofiles = IOFiles(test_io_dict)
    script_str = iofiles.make_run_script()
    print(script_str)
    
def test_io_file_toml():
    iofiles = IOFiles.from_toml("tests/models/qe.toml")
    script_str = iofiles.make_run_script()
    print(script_str)